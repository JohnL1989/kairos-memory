"""三信号混合检索（竖切组件 3）——语义 + BM25 + 实体加成融合。

权威规格：架构 §7.3a（RC-06 管线结构 + RC-03 加性口径）：
- 路径空间是硬过滤边界（先按路径前缀圈定候选域，再域内三信号融合排序）
- 信号一 语义：1536 维余弦（sqlite-vec 精确扫描，候选池 K=100）
- 信号二 BM25：FTS5 内置 bm25（k1=1.2/b=0.75，data-model config 表基值）
- 信号三 实体加成（RC-03）：score_entity = |Q ∩ E_R| / |Q|（|Q|=0 → 0）
- 融合公式：score_total = α_s·norm(sem) + α_b·norm(bm25) + α_e·norm(entity)
  norm(x) = (x−min)/(max−min) if max>min else 0（对当前候选池独立计算）
- 运行时退化：某信号 max==min 时 norm 恒 0，权重不重新分配
- 实体加成简化方案（竖切）：实体提取用词典/规则匹配（entities 表词典），
  不启用 LLM 实体提取（Deep 模式不在竖切）
- GSPO/MMR/Cross-encoder 不在竖切（对应标志 OFF）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from src.storage.db import Database
from src.storage.vector_index import DEFAULT_CANDIDATE_POOL_SIZE, VectorIndex
from src.utils.embeddings import Embedder, HashEmbedder

if TYPE_CHECKING:
    from src.events.bus import EventBus
    from src.storage.query_analyzer import QueryAnalyzer

# 三信号权重默认值（configuration §6.1；权重和恒为 1）
DEFAULT_WEIGHTS = {"semantic": 0.50, "bm25": 0.35, "entity": 0.15}


@dataclass(frozen=True)
class SearchFilter:
    """检索过滤（硬过滤边界，架构 §7.3a）。"""

    contract: str | None = None
    path_prefix: str | None = None


@dataclass(frozen=True)
class ScoredMemory:
    """融合排序结果。"""

    id: str
    path: str
    content: str
    score: float
    explanation: dict[str, float]


class HybridSearch:
    """三信号混合检索器（竖切组件 3 实现落点 src/storage/hybrid_search.py）。"""

    def __init__(
        self,
        db: Database,
        embedder: Embedder | None = None,
        weights: dict[str, float] | None = None,
        bus: EventBus | None = None,
        analyzer: QueryAnalyzer | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedder or HashEmbedder()
        self.vector_index = VectorIndex(db)
        self.bus = bus  # 事件总线（检索 use_event 发布；首迭代接线）
        self.analyzer = analyzer  # QueryAnalyzer（首迭代增强：意图 + 时间锚定）
        weights = weights or DEFAULT_WEIGHTS
        total = sum(weights.values())
        self.weights = {k: v / total for k, v in weights.items()}  # 权重和恒为 1

    # ------------------------------------------------------------------
    # 检索入口（POST /v1/memories/search / GET /v1/memories?q=）
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        weights: dict[str, float] | None = None,
        limit: int = 10,
        filters: SearchFilter | None = None,
        time_range: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """三信号混合检索。

        mode：hybrid（三信号融合）/ semantic / bm25（单信号，架构 §7.3a 检索模式）。
        weights：请求级权重覆盖（api-spec §1.2；默认 0.50/0.35/0.15）。
        time_range：(start, end) 时间硬过滤（架构 §7.3a 第二重硬过滤边界；
        首迭代由 QueryAnalyzer 时间锚定注入）。
        """
        limit = max(1, min(limit, 100))
        filters = filters or SearchFilter()
        active_weights = dict(self.weights)
        if weights:
            merged = {**self.weights, **weights}
            total = sum(merged.values()) or 1.0
            active_weights = {k: v / total for k, v in merged.items()}

        # QueryAnalyzer 增强（首迭代）：意图分类 + 时间锚定 → 注入时间过滤
        effective_query = query
        if self.analyzer is not None:
            descriptor = await self.analyzer.analyze(query)
            if descriptor.temporal_constraint is not None:
                tc = descriptor.temporal_constraint
                if tc.start and tc.end and not tc.optional:
                    time_range = time_range or (tc.start, tc.end)
                effective_query = descriptor.effective_query

        # 1. 候选域：路径前缀硬过滤边界（语义/BM25/实体均限此域）
        prefix = filters.path_prefix
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        # 2. 三信号召回（并行无依赖，顺序执行即可）
        semantic_hits = await self._semantic_recall(
            effective_query, prefix=prefix, time_range=time_range
        )
        bm25_hits = await self._bm25_recall(effective_query, prefix=prefix, time_range=time_range)
        entity_hits = await self._entity_recall(
            effective_query, prefix=prefix, time_range=time_range
        )

        # 3. 候选池合并（按记忆去重；同一记忆不重复出现，TC-R03-001）
        candidates: dict[str, dict[str, float | None]] = {}
        for hit in semantic_hits:
            candidates.setdefault(
                hit["id"], {"semantic": None, "bm25": None, "entity": None, "path": hit["path"]}
            )
        for hit in bm25_hits:
            candidates.setdefault(
                hit["id"], {"semantic": None, "bm25": None, "entity": None, "path": hit["path"]}
            )
        for hit in entity_hits:
            candidates.setdefault(
                hit["id"], {"semantic": None, "bm25": None, "entity": None, "path": hit["path"]}
            )
        for hit in semantic_hits:
            candidates[hit["id"]]["semantic"] = hit["score"]
        for hit in bm25_hits:
            candidates[hit["id"]]["bm25"] = hit["score"]
        for hit in entity_hits:
            candidates[hit["id"]]["entity"] = hit["score"]

        if not candidates:
            return {"data": [], "total": 0, "meta": {}}

        # 4. 分信号 norm 归一化（对当前候选池独立计算，架构 §7.3a）
        normalized: dict[str, dict[str, float]] = {}
        for signal in ("semantic", "bm25", "entity"):
            scores: list[float] = []
            for cand in candidates.values():
                s = cand[signal]
                if s is not None:
                    scores.append(s)
            if not scores:
                continue
            lo = min(scores)
            hi = max(scores)
            for mem_id, cand in candidates.items():
                raw = cand[signal]
                if raw is None:
                    norm_val = 0.0
                elif hi <= lo:
                    # 单候选/同分退化：唯一得分者信号满配——避免 (raw-lo)/(hi-lo)
                    # 的 0 分母语义把分数归零（entity 词典激活早期常见单候选场景，
                    # 旧逻辑致实体信号恒被压制为 0；语义单候选同理）
                    norm_val = 1.0 if raw > 0 else 0.0
                else:
                    norm_val = (raw - lo) / (hi - lo)
                normalized.setdefault(mem_id, {})[signal] = norm_val

        # 5. 融合加权（mode 单信号时仅取该信号）
        results: list[ScoredMemory] = []
        for mem_id, cand in candidates.items():
            norm_signals = normalized.get(mem_id, {})
            if mode == "semantic":
                score = norm_signals.get("semantic", 0.0)
                signals = {"semantic": norm_signals.get("semantic", 0.0)}
            elif mode == "bm25":
                score = norm_signals.get("bm25", 0.0)
                signals = {"bm25": norm_signals.get("bm25", 0.0)}
            else:
                score = sum(
                    active_weights[s] * norm_signals.get(s, 0.0)
                    for s in ("semantic", "bm25", "entity")
                )
                signals = {s: norm_signals.get(s, 0.0) for s in ("semantic", "bm25", "entity")}
            results.append(
                ScoredMemory(
                    id=mem_id, path=str(cand["path"]), content="", score=score, explanation=signals
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        top = results[:limit]

        # 6. 回填内容（content 截断展示）与过滤契约
        final = []
        for r in top:
            content = await self._load_content(r.id)
            if filters.contract and content.get("contract") != filters.contract:
                continue
            final.append(
                {
                    "id": r.id,
                    "path": r.path,
                    "content": content.get("content", "")[:200],
                    "contract": content.get("contract"),
                    "score": round(r.score, 4),
                    "explanation": {k: round(v, 4) for k, v in r.explanation.items()},
                    "created_at": content.get("created_at"),
                }
            )
        # 检索 use_event（架构 §10.10：检索侧维度丢失以 use_event payload 标记）
        if self.bus is not None:
            await self._publish_retrieval_events([d["id"] for d in final])
        return {"data": final, "total": len(final), "meta": {}}

    async def _publish_retrieval_events(self, memory_ids: list[str]) -> None:
        """检索使用事件（影子副本升温；发布失败不阻断检索结果）。"""
        if not memory_ids:
            return
        try:
            from src.events.types import PRIORITY_USE_EVENT, USE_EVENT

            bus = self.bus
            assert bus is not None
            for memory_id in memory_ids[:20]:  # 上限 20 条防事件洪泛
                await bus.publish(
                    USE_EVENT,
                    "storage",
                    payload={"action": "memory_retrieved"},
                    priority=PRIORITY_USE_EVENT,
                    memory_id=memory_id,
                )
        except Exception:
            pass  # 事件发布失败仅留痕

    # ------------------------------------------------------------------
    # 三信号召回
    # ------------------------------------------------------------------

    async def _semantic_recall(
        self, query: str, *, prefix: str | None, time_range: tuple[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """信号一：语义余弦 top-K（K=KAIROS_HYBRID_CANDIDATE_POOL_SIZE）。"""
        query_vector = await self.embedder.embed(query)
        return await self.vector_index.cosine_search(
            query_vector,
            top_k=DEFAULT_CANDIDATE_POOL_SIZE,
            path_prefix=prefix,
            time_range=time_range,
        )

    async def _bm25_recall(
        self, query: str, *, prefix: str | None, time_range: tuple[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """信号二：FTS5 BM25（contentless-external 表；bm25() 越小越相关）。"""
        # FTS5 查询词规范化：移除标点，空格分词（unicode61 tokenizer 对齐）
        terms = [t for t in re.split(r"\s+", query.strip()) if t]
        if not terms:
            return []
        fts_query = " OR ".join(f'"{t}"' for t in terms[:8])  # 上限 8 词防超限
        sql = (
            # 取 memories.id（非 f.rowid——FTS 行号 ≠ 记忆 id，候选合并按 id 去重）
            "SELECT m.id AS id, m.path AS path, -bm25(memories_fts) AS score "
            "FROM memories_fts f JOIN memories m ON m.rowid = f.rowid "
            "WHERE memories_fts MATCH :q"
        )
        params: dict[str, object] = {"q": fts_query}
        if prefix:
            sql += " AND m.path GLOB :prefix"
            params["prefix"] = f"{prefix}*"  # GLOB 通配符
        if time_range:
            sql += " AND ((m.occurred_at BETWEEN :tr_start AND :tr_end) OR "
            sql += "(m.occurred_at IS NULL AND m.created_at BETWEEN :tr_start AND :tr_end))"
            params["tr_start"], params["tr_end"] = time_range
        sql += " ORDER BY score DESC LIMIT :k"
        params["k"] = DEFAULT_CANDIDATE_POOL_SIZE
        async with self.db.session() as session:
            rows = (await session.execute(text(sql), params)).fetchall()
        return [{"id": str(r[0]), "path": str(r[1]), "score": max(0.0, float(r[2]))} for r in rows]

    async def _entity_recall(
        self, query: str, *, prefix: str | None, time_range: tuple[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """信号三：实体加成（词典匹配简化方案，RC-03 加性口径）。

        score_entity = |Q ∩ E_R| / |Q|——Q 为查询文本中命中 entities 词典的实体名，
        E_R 为记忆 R 的实体集合；|Q|=0 时 score=0（实体信号不参与）。
        """
        query_entities = await self._match_query_entities(query)
        if not query_entities:
            return []
        # IN 列表显式展开占位（SQLAlchemy text() 不支持元组 IN 绑定）
        placeholders = ", ".join(f":n{i}" for i in range(len(query_entities)))
        sql = (
            "SELECT m.id AS id, m.path AS path, "
            "(SELECT count(*) FROM memory_entities me JOIN entities e ON me.entity_id = e.id "
            f" WHERE me.memory_id = m.id AND e.name IN ({placeholders})) AS hit_count "
            "FROM memories m WHERE m.is_deleted = 0 AND m.is_latest = 1"
        )
        params: dict[str, object] = {f"n{i}": name for i, name in enumerate(query_entities)}
        if prefix:
            sql += " AND m.path GLOB :prefix"
            params["prefix"] = f"{prefix}*"  # GLOB 通配符
        if time_range:
            sql += " AND ((m.occurred_at BETWEEN :tr_start AND :tr_end) OR "
            sql += "(m.occurred_at IS NULL AND m.created_at BETWEEN :tr_start AND :tr_end))"
            params["tr_start"], params["tr_end"] = time_range
        sql += " AND hit_count > 0 ORDER BY hit_count DESC LIMIT :k"
        params["k"] = DEFAULT_CANDIDATE_POOL_SIZE
        async with self.db.session() as session:
            rows = (await session.execute(text(sql), params)).fetchall()
        return [
            {
                "id": str(r[0]),
                "path": str(r[1]),
                "score": int(r[2]) / len(query_entities),  # |Q ∩ E_R| / |Q|
            }
            for r in rows
        ]

    async def _match_query_entities(self, query: str) -> list[str]:
        """查询侧实体词典匹配（entities 表名称出现在查询文本中即命中）。"""
        async with self.db.session() as session:
            rows = (await session.execute(text("SELECT name FROM entities"))).fetchall()
        return [r[0] for r in rows if r[0] and r[0] in query]

    async def _load_content(self, memory_id: str) -> dict[str, Any]:
        """按 id 加载展示字段（内容截断 + 契约过滤用）。"""
        async with self.db.session() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT content, contract, created_at FROM memories "
                        "WHERE id = :id AND is_deleted = 0 AND is_latest = 1"
                    ),
                    {"id": memory_id},
                )
            ).fetchone()
        if row is None:
            return {}
        return {"content": row[0], "contract": row[1], "created_at": row[2]}
