"""扩展端点 handlers（MCP 15 工具契约 §6.8 补齐，竖切语义内实现）。

覆盖：kairos_get_stats / kairos_get_hot_memories / kairos_feedback_memory /
kairos_get_memory_traces / kairos_extract_entities / kairos_search_graph /
kairos_search_sessions / kairos_link / kairos_unlink / kairos_relations。

契约来源：
- api-spec §6.8 MCP Bridge 工具映射（权威工具清单）
- api-spec §6.1 会话列表 / §6.2 实体图谱 / §6.5 聚合统计
- data-model §1 memory_relations（关系表契约）

实现口径：竖切语义内最小完整实现（无 LLM 依赖；实体提取为规则词典法；
图谱为实体-记忆关联查询；会话为记忆流中对话记录的聚合视图）。
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from litestar import Request, delete, get, post
from litestar.params import Body, FromPath, Parameter
from sqlalchemy import func, select, text, update

from src.access.api.routes import _api_key_guard, _error_handler
from src.app import KairosApp
from src.errors import KairosError, MissingFieldError, NotFoundError
from src.storage.models import (
    Entity,
    Memory,
    MemoryEntity,
    MemoryRelation,
    MemoryState,
    UsageWeight,
)

# ---------------------------------------------------------------------------
# 统计与热度（§6.5 / §6.8 stats, heat-top）
# ---------------------------------------------------------------------------


@get(
    "/v1/memories/stats", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler}
)
async def memories_stats(request: Request[Any, Any, Any]) -> dict[str, Any]:
    """记忆库报告（kairos_get_stats）：总量/类型/状态/使用分布。"""
    app: KairosApp = request.app.state["kairos"]
    async with app.db.session() as session:
        total = (await session.execute(select(func.count()).select_from(Memory))).scalar() or 0
        # memory_types 为 JSON 数组列（如 ["semantic","episodic"]）——json_each 展开统计
        by_type_rows = (
            await session.execute(
                text(
                    "SELECT je.value AS mtype, COUNT(*) AS cnt "
                    "FROM memories, json_each(memories.memory_types) je "
                    "GROUP BY je.value ORDER BY cnt DESC"
                )
            )
        ).all()
        by_type = {mtype: cnt for mtype, cnt in by_type_rows}
        by_state_rows = (
            await session.execute(select(Memory.status, func.count()).group_by(Memory.status))
        ).all()
        by_state: dict[str, int] = {r[0]: r[1] for r in by_state_rows}
        used = (
            await session.execute(
                select(func.count()).select_from(UsageWeight).where(UsageWeight.usage_count > 0)
            )
        ).scalar() or 0
    return {
        "total": total,
        "by_type": by_type,
        "by_state": by_state,
        "used_count": used,
        "used_ratio": round(used / total, 4) if total else 0.0,
    }


@get(
    "/v1/memories/heat-top",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def memories_heat_top(
    request: Request[Any, Any, Any],
    limit: Annotated[int, Parameter(ge=1, le=100)] = 10,
) -> dict[str, Any]:
    """热度最高记忆（kairos_get_hot_memories）：按 usage_weight.usage_count 降序。"""
    app: KairosApp = request.app.state["kairos"]
    async with app.db.session() as session:
        rows = (
            await session.execute(
                select(Memory, UsageWeight.usage_count, UsageWeight.activation_weight)
                .join(UsageWeight, UsageWeight.memory_id == Memory.id)
                .where(Memory.is_deleted == 0, Memory.is_latest == 1)
                .order_by(UsageWeight.usage_count.desc(), UsageWeight.activation_weight.desc())
                .limit(limit)
            )
        ).all()
    return {
        "data": [
            {
                "id": m.id,
                "path": m.path,
                "content": (m.content or "")[:200],
                "usage_count": uc,
                "activation_weight": round(aw or 0.0, 4),
            }
            for m, uc, aw in rows
        ],
        "total": len(rows),
    }


# ---------------------------------------------------------------------------
# 可信度反馈（§6.8 feedback）
# ---------------------------------------------------------------------------


@post(
    "/v1/memories/{memory_id:str}/feedback",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def memory_feedback(
    request: Request[Any, Any, Any],
    memory_id: Annotated[str, FromPath],
    data: Annotated[dict[str, Any], Body(title="FeedbackRequest")],
) -> dict[str, Any]:
    """可信度反馈（kairos_feedback_memory）：更新 calibration_confidence + 审计留痕。

    请求体：{"feedback": 0.0~1.0, "reason": "..."}
    """
    app: KairosApp = request.app.state["kairos"]
    feedback = data.get("feedback")
    if feedback is None or not 0 <= float(feedback) <= 1:
        raise MissingFieldError("feedback 必须在 [0,1] 区间（ERR-INPUT-004）")
    async with app.db.session() as session:
        mem = await session.get(Memory, memory_id)
        if mem is None:
            raise NotFoundError(f"记忆不存在: {memory_id}")
        # 指数平滑更新可信度（新反馈 30% 权重，保持历史稳定）
        prev = mem.calibration_confidence or 0.5
        new = round(0.7 * prev + 0.3 * float(feedback), 4)
        await session.execute(
            update(Memory).where(Memory.id == memory_id).values(calibration_confidence=new)
        )
        await session.commit()
    await app.tribunal.record(
        operator="api",
        action="feedback",
        target_type="memory",
        target_id=memory_id,
        details={"feedback": float(feedback), "previous": prev, "new": new},
        redline_id="S-11",
    )
    return {"memory_id": memory_id, "previous": prev, "new": new, "status": "applied"}


# ---------------------------------------------------------------------------
# 生命周期历史（§6.8 memory_traces——数据源 memory_states 表）
# ---------------------------------------------------------------------------


@get(
    "/v1/memories/{memory_id:str}/traces",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def memory_traces(
    request: Request[Any, Any, Any],
    memory_id: Annotated[str, FromPath],
    limit: Annotated[int, Parameter(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    """记忆生命周期历史（kairos_get_memory_traces）：memory_states 五态状态机轨迹。"""
    app: KairosApp = request.app.state["kairos"]
    async with app.db.session() as session:
        rows = (
            (
                await session.execute(
                    select(MemoryState)
                    .where(MemoryState.memory_id == memory_id)
                    .order_by(MemoryState.state_changed_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
    return {
        "memory_id": memory_id,
        "traces": [
            {
                "state": s.state,
                "previous_state": s.previous_state,
                "state_changed_at": s.state_changed_at,
                "reason": s.reason,
                "source": s.source,
            }
            for s in rows
        ],
        "total": len(rows),
    }


# ---------------------------------------------------------------------------
# 实体提取与图谱检索（§6.2 / §6.8 extract_entities, search_graph）
# ---------------------------------------------------------------------------

# 规则实体提取：引号短语、连续大写英文词、中文专名模式（XX项目/系统/协议/框架/模型）
_QUOTED = re.compile(r"[「“]([^」”]{2,30})[」”]")
_EN_ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,10}\b")
_CN_PROPER = re.compile(
    r"[\u4e00-\u9fff]{2,12}(?:项目|系统|协议|框架|模型|引擎|平台|服务|工具|数据库|引擎|网络|记忆|文档|目录)"
)


def _extract_entities_rules(text: str, limit: int = 20) -> list[str]:
    """规则词典法实体提取（无 LLM 依赖；竖切语义内实现）。"""
    found: list[str] = []
    for m in _QUOTED.findall(text):
        if m not in found:
            found.append(m)
    for m in _EN_ACRONYM.findall(text):
        if m not in found:
            found.append(m)
    for m in _CN_PROPER.findall(text):
        if m not in found:
            found.append(m)
    return found[:limit]


@post(
    "/v1/entities/extract",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def entities_extract(
    request: Request[Any, Any, Any],
    data: Annotated[dict[str, Any], Body(title="ExtractRequest")],
) -> dict[str, Any]:
    """从文本提取实体（kairos_extract_entities）：规则提取 + entities 表入库（去重）。"""
    app: KairosApp = request.app.state["kairos"]
    text_content = data.get("text", "")
    if not text_content or len(text_content.strip()) < 2:
        raise MissingFieldError("text 必填且长度 ≥2（ERR-INPUT-004）")
    names = _extract_entities_rules(text_content)
    async with app.db.session() as session:
        created = []
        for name in names:
            exists = (
                await session.execute(
                    select(Entity).where(
                        Entity.name == name, Entity.user_id == data.get("user_id", "default")
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                ent = Entity(
                    user_id=data.get("user_id", "default"),
                    name=name,
                    type="concept",
                    description="",
                )
                session.add(ent)
                created.append({"name": name, "type": "concept"})
            else:
                created.append({"name": name, "type": exists.type})
        await session.commit()
    return {"entities": created, "count": len(created)}


@post("/v1/graph/search", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def graph_search(
    request: Request[Any, Any, Any],
    data: Annotated[dict[str, Any], Body(title="GraphSearchRequest")],
) -> dict[str, Any]:
    """实体图谱检索（kairos_search_graph）：实体名匹配 + 关联记忆统计。"""
    app: KairosApp = request.app.state["kairos"]
    query = data.get("query", "")
    if not query:
        raise MissingFieldError("query 必填（ERR-INPUT-004）")
    limit = min(int(data.get("limit", 10)), 100)
    async with app.db.session() as session:
        entities = (
            (
                await session.execute(
                    select(Entity)
                    .where(
                        Entity.name.like(f"%{query}%"),
                        Entity.user_id == data.get("user_id", "default"),
                    )
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        relations: list[dict[str, Any]] = []
        for ent in entities:
            linked = (
                await session.execute(
                    select(Memory.id, Memory.path)
                    .join(MemoryEntity, MemoryEntity.memory_id == Memory.id)
                    .where(MemoryEntity.entity_id == ent.id)
                    .limit(5)
                )
            ).all()
            relations.append(
                {
                    "entity": ent.name,
                    "type": ent.type,
                    "linked_memories": [{"id": m_id, "path": m_path} for m_id, m_path in linked],
                }
            )
    return {
        "entities": [{"name": e.name, "type": e.type} for e in entities],
        "relations": relations,
        "hops": 1 if entities else 0,
    }


# ---------------------------------------------------------------------------
# 会话列表（§6.1 / §6.8 search_sessions——记忆流中对话记录的聚合视图）
# ---------------------------------------------------------------------------


@get("/v1/sessions", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def sessions_list(
    request: Request[Any, Any, Any],
    limit: Annotated[int, Parameter(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    """最近会话（kairos_search_sessions）：对话记录记忆（content 前缀「对话记录（」）。"""
    app: KairosApp = request.app.state["kairos"]
    async with app.db.session() as session:
        rows = (
            (
                await session.execute(
                    select(Memory)
                    .where(
                        Memory.content.like("对话记录（%"),
                        Memory.is_deleted == 0,
                        Memory.is_latest == 1,
                    )
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
    return {
        "data": [
            {
                "id": m.id,
                "path": m.path,
                # 路径结构 kairos://_user/hermes/sessions/{session_id}/{memory_id}
                "session_id": (m.path or "").rsplit("/", 2)[-2] if m.path else m.id,
                "created_at": m.created_at,
                "preview": (m.content or "")[:200],
            }
            for m in rows
        ],
        "total": len(rows),
    }


# ---------------------------------------------------------------------------
# 关系管理（data-model §1 memory_relations；§6.8 link/unlink/relations）
# ---------------------------------------------------------------------------


@post("/v1/relations", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def relation_create(
    request: Request[Any, Any, Any],
    data: Annotated[dict[str, Any], Body(title="RelationCreateRequest")],
) -> dict[str, Any]:
    """创建关系边（kairos_link）：from_uri → uris 批量；必填 reason。"""
    app: KairosApp = request.app.state["kairos"]
    from_uri = data.get("from_uri")
    uris = data.get("uris") or []
    reason = data.get("reason")
    if not from_uri or not uris or not reason:
        raise MissingFieldError("from_uri / uris / reason 必填（kairos_link 契约，ERR-INPUT-004）")
    relation_type = data.get("relation_type", "reference")
    confidence = data.get("confidence")
    async with app.db.session() as session:
        source = await session.get(Memory, from_uri)
        if source is None:
            raise NotFoundError(f"源记忆不存在: {from_uri}")
        created = []
        for target_uri in uris:
            target = await session.get(Memory, target_uri)
            if target is None:
                raise NotFoundError(f"目标记忆不存在: {target_uri}")
            exists = (
                await session.execute(
                    select(MemoryRelation).where(
                        MemoryRelation.source_id == from_uri,
                        MemoryRelation.target_id == target_uri,
                        MemoryRelation.relation_type == relation_type,
                        MemoryRelation.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if exists is not None:
                created.append({"from": from_uri, "to": target_uri, "status": "exists"})
                continue
            rel = MemoryRelation(
                source_id=from_uri,
                target_id=target_uri,
                relation_type=relation_type,
                strength=float(data.get("strength", 1.0)),
                reason=reason,
                confidence=float(confidence) if confidence is not None else None,
            )
            session.add(rel)
            created.append({"from": from_uri, "to": target_uri, "status": "created"})
        await session.commit()
    return {"created": created, "count": len(created)}


@delete(
    "/v1/relations/{source_id:str}/{target_id:str}",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def relation_remove(
    request: Request[Any, Any, Any],
    source_id: Annotated[str, FromPath],
    target_id: Annotated[str, FromPath],
    relation_type: Annotated[str, Parameter()] = "*",
) -> dict[str, Any]:
    """移除关系边（kairos_unlink）：relation_type=* 全删；软删除保留审计。"""
    app: KairosApp = request.app.state["kairos"]
    async with app.db.session() as session:
        stmt = select(MemoryRelation).where(
            MemoryRelation.source_id == source_id,
            MemoryRelation.target_id == target_id,
            MemoryRelation.deleted_at.is_(None),
        )
        if relation_type != "*":
            stmt = stmt.where(MemoryRelation.relation_type == relation_type)
        rels = (await session.execute(stmt)).scalars().all()
        from src.storage.models import utc_now

        now = utc_now()
        removed = 0
        for rel in rels:
            rel.deleted_at = now
            removed += 1
        await session.commit()
    return {"removed": removed, "source_id": source_id, "target_id": target_id}


@get(
    "/v1/relations/{memory_id:str}",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def relation_query(
    request: Request[Any, Any, Any],
    memory_id: Annotated[str, FromPath],
    direction: Annotated[str, Parameter()] = "both",
    relation_type: Annotated[str, Parameter()] = "*",
    limit: Annotated[int, Parameter(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    """查询关系边（kairos_relations）：direction ∈ {inbound, outbound, both}。"""
    app: KairosApp = request.app.state["kairos"]
    async with app.db.session() as session:
        outbound = (
            (
                await session.execute(
                    select(MemoryRelation)
                    .where(
                        MemoryRelation.source_id == memory_id,
                        MemoryRelation.deleted_at.is_(None),
                    )
                    .limit(limit)
                )
            )
            .scalars()
            .all()
            if direction in ("outbound", "both")
            else []
        )
        inbound = (
            (
                await session.execute(
                    select(MemoryRelation)
                    .where(
                        MemoryRelation.target_id == memory_id,
                        MemoryRelation.deleted_at.is_(None),
                    )
                    .limit(limit)
                )
            )
            .scalars()
            .all()
            if direction in ("inbound", "both")
            else []
        )
    return {
        "memory_id": memory_id,
        "inbound": [
            {
                "id": r.id,
                "source_id": r.source_id,
                "relation_type": r.relation_type,
                "strength": r.strength,
                "reason": r.reason,
            }
            for r in inbound
        ],
        "outbound": [
            {
                "id": r.id,
                "target_id": r.target_id,
                "relation_type": r.relation_type,
                "strength": r.strength,
                "reason": r.reason,
            }
            for r in outbound
        ],
    }
