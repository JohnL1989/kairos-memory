"""向量索引（竖切组件 3 信号一）——1536 维余弦相似度检索。

权威规格：架构 §7.3a 信号一（1536 维余弦相似度，ANN 召回 top-K 候选池
默认 K=100）；technology-stack §二（轻量模式 sqlite-vec，SQLite 侧 v0.1.0
不建向量索引——brute-force 精确扫描，schema-slice.sql 注记）。

实现选择：numpy 批量余弦扫描（纯 Python 路径）——sqlite-vec 扩展在
Windows 官方 Python 构建不可加载（sqlite3 模块未编译
SQLITE_ENABLE_LOAD_EXTENSION），numpy 向量化扫描在 1 万条 × 1536 维量级
满足 W5 基准 P50 ≤100ms 验收（实现偏差登记 D-447）；扩展就绪环境可切回
SQL 侧 vec_distance_cosine（本模块保持同一返回契约）。

性能设计：嵌入矩阵 + 范数缓存（版本键 = 行数 + 最近 updated_at，
检查间隔 TTL 1s）——嵌入为派生视图（detailed-design 写入管线③），
正常写入路径经 upsert_embedding 即时清缓存（写入后立即可检索）；
TTL 仅防「版本键全表扫描」在连续查询间重复（基准关键路径：版本查询
111ms → 命中路径 ~3ms）。
"""

from __future__ import annotations

import time

import numpy as np
from sqlalchemy import text

from src.storage.db import Database
from src.utils.embeddings import EMBEDDING_DIM, vector_to_bytes

# 语义召回候选池大小（configuration §6.1 KAIROS_HYBRID_CANDIDATE_POOL_SIZE）
DEFAULT_CANDIDATE_POOL_SIZE = 100
# 版本键检查间隔（秒）：写入路径经 upsert 即时清缓存，TTL 仅防重复全表扫描
VERSION_CHECK_TTL = 1.0


class VectorIndex:
    """向量索引（numpy 批量余弦扫描；brute-force 精确召回 + 矩阵缓存）。"""

    def __init__(self, db: Database) -> None:
        self.db = db
        # 嵌入矩阵缓存（版本键失效；嵌入为派生视图，可重建）
        self._cache_key: tuple[int, str] | None = None
        self._matrix: np.ndarray | None = None
        self._norms: np.ndarray | None = None
        self._ids: list[object] = []
        self._paths: list[object] = []
        self._last_version_check = 0.0
        # 路径过滤场景的行序元数据
        self._filter_ids: list[object] = []
        self._filter_paths: list[object] = []

    async def upsert_embedding(self, memory_id: str, vector: list[float]) -> None:
        """写入/更新记忆嵌入（维度校验：1536，schema-slice §约定）。"""
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(f"嵌入维度必须为 {EMBEDDING_DIM}，当前 {len(vector)}")
        async with self.db.session() as session:
            await session.execute(
                text("UPDATE memories SET embedding = :v WHERE id = :id"),
                {"v": vector_to_bytes(vector), "id": memory_id},
            )
            await session.commit()
        self._cache_key = None  # 写入后缓存失效

    async def cosine_search(
        self,
        query_vector: list[float],
        *,
        top_k: int = DEFAULT_CANDIDATE_POOL_SIZE,
        path_prefix: str | None = None,
    ) -> list[dict[str, object]]:
        """余弦相似度 top-K 候选（numpy 批量扫描，跳过 NULL 嵌入）。"""
        if len(query_vector) != EMBEDDING_DIM:
            raise ValueError(f"查询嵌入维度必须为 {EMBEDDING_DIM}，当前 {len(query_vector)}")
        top_k = max(1, min(top_k, 500))
        q = np.asarray(query_vector, dtype="<f4")

        # 无路径过滤时走矩阵缓存（1 万条基准关键路径）；带路径过滤时实时扫描
        if path_prefix is None:
            matrix, norms = await self._cached_matrix()
        else:
            matrix, norms = await self._load_matrix(path_prefix=path_prefix)

        if matrix is None or norms is None or len(matrix) == 0:
            return []

        q_norm = np.linalg.norm(q) or 1.0
        # 余弦相似度 = (M·q) / (|M|·|q|)；零向量置 0
        scores = (matrix @ q) / (norms * q_norm)
        scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)

        k = min(top_k, len(scores))
        top_indices = np.argsort(-scores)[:k]
        ids = self._ids if path_prefix is None else self._filter_ids
        paths = self._paths if path_prefix is None else self._filter_paths
        return [
            {"id": str(ids[i]), "path": paths[i], "score": float(max(0.0, scores[i]))}
            for i in top_indices
        ]

    # ------------------------------------------------------------------
    # 矩阵加载与缓存
    # ------------------------------------------------------------------

    async def _embedding_version(self) -> tuple[int, str]:
        """嵌入集版本键（行数 + 最近 updated_at）——记忆不变时矩阵可复用。"""
        async with self.db.session() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT count(*), COALESCE(MAX(updated_at), '') FROM memories "
                        "WHERE embedding IS NOT NULL AND is_deleted = 0 AND is_latest = 1"
                    )
                )
            ).fetchone()
        assert row is not None
        return int(row[0]), str(row[1])

    async def _cached_matrix(self) -> tuple[np.ndarray | None, np.ndarray | None]:
        """缓存矩阵 + 范数（版本键失效后重载；id/path 与矩阵同序缓存）。

        版本检查 TTL：连续查询在间隔内跳过版本键全表扫描（基准关键路径）；
        正常写入路径经 upsert_embedding 即时清缓存，TTL 不影响写入即时可见。
        """
        now = time.monotonic()
        if self._cache_key is None or now - self._last_version_check >= VERSION_CHECK_TTL:
            key = await self._embedding_version()
            self._last_version_check = now
            if key != self._cache_key:
                self._matrix, self._norms = await self._load_matrix()
                self._cache_key = key
        return self._matrix, self._norms

    async def _load_matrix(
        self, path_prefix: str | None = None
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """加载嵌入矩阵（id/path/embedding 同序三列；单次大块 frombuffer）。"""
        sql = (
            "SELECT id, path, embedding FROM memories "
            "WHERE embedding IS NOT NULL AND is_deleted = 0 AND is_latest = 1 ORDER BY rowid"
        )
        params: dict[str, object] = {}
        if path_prefix:
            sql = sql.replace("WHERE", "WHERE path GLOB :prefix AND", 1)
            params["prefix"] = f"{path_prefix}*"
        async with self.db.session() as session:
            rows = (await session.execute(text(sql), params)).fetchall()
        if not rows:
            return None, None
        matrix = np.frombuffer(b"".join(r[2] for r in rows), dtype="<f4").reshape(-1, EMBEDDING_DIM)
        norms = np.linalg.norm(matrix, axis=1)
        ids = [r[0] for r in rows]
        paths = [r[1] for r in rows]
        if path_prefix:
            self._filter_ids = ids
            self._filter_paths = paths
        else:
            self._ids = ids
            self._paths = paths
        return matrix, norms
