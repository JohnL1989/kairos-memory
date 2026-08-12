"""竖切 21 端点 handlers（Litestar）。

请求/响应模型见 api-contract/openapi.yaml（竖切 21 端点 schema，D-428 补全）。
"""

from __future__ import annotations

import json
from typing import Any

from litestar import Request, Response, delete, get, patch, post
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter

from src.access.auth import ApiKeyGuard
from src.app import KairosApp
from src.config import ConfigError, load_settings, validate_runtime_override
from src.errors import KairosError
from src.storage.hybrid_search import SearchFilter
from src.storage.memory_store import MemoryWriteInput


async def _api_key_guard(connection: Any, handler: Any) -> None:
    """函数式鉴权守卫：运行时解析 KAIROS_API_KEY_HASH（Litestar 类 guard
    无法 DI 构造参数，函数式保 S-01/S-06 认证生效）。"""
    api_key_hash = load_settings().get("KAIROS_API_KEY_HASH")
    await ApiKeyGuard(api_key_hash)(connection, handler)


def _error_handler(_: Any, exc: Exception) -> Response[Any]:
    """KairosError → HTTP 结构化错误响应（错误码体系，error-reference）。"""
    if isinstance(exc, KairosError):
        return Response(
            content=exc.to_response(),
            status_code=exc.status_code,
            media_type="application/json",
        )
    return Response(
        content={"code": "ERR-SYS-001", "message": str(exc)},
        status_code=500,
        media_type="application/json",
    )


# ---------------------------------------------------------------------------
# 记忆（组件 1）
# ---------------------------------------------------------------------------


@post("/v1/memories", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def create_memory(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="MemoryWriteRequest"),
) -> dict[str, Any]:
    """记忆写入（幂等键 Idempotency-Key 可选，api-spec §1.1）。"""
    app: KairosApp = request.app.state["kairos"]
    idempotency_key = request.headers.get("idempotency-key")
    # 必填字段经 .get() 透传——缺失时由 store 层校验抛 KairosError（422 映射）
    result = await app.store.create(
        MemoryWriteInput(
            path=data.get("path", ""),
            content=data.get("content", ""),
            provenance=data.get("provenance", ""),
            contract=data.get("contract", "ondemand"),
            memory_types=data.get("memory_types", ["semantic"]),
            vad=data.get("vad"),
            encoding_context=data.get("encoding_context"),
            occurred_at=data.get("occurred_at"),
        ),
        idempotency_key=idempotency_key,
    )
    return {"id": result.id, "path": result.path, "version": result.version}


@post(
    "/v1/memories/batch",
    status_code=207,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def create_memories_batch(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="BatchWriteRequest"),
) -> dict[str, Any]:
    """批量写入（W-03；最大 100 条，部分失败 207 语义）。"""
    app: KairosApp = request.app.state["kairos"]
    items = data.get("items", [])[:100]
    results = []
    success, failed = 0, 0
    for index, item in enumerate(items):
        try:
            result = await app.store.create(
                MemoryWriteInput(
                    path=item["path"],
                    content=item["content"],
                    provenance=item["provenance"],
                    contract=item.get("contract", "ondemand"),
                    memory_types=item.get("memory_types", ["semantic"]),
                )
            )
            success += 1
            results.append({"index": index, "status": "created", "id": result.id})
        except KairosError as exc:
            failed += 1
            results.append(
                {"index": index, "status": "error", "code": exc.code, "message": exc.message}
            )
    return {"success_count": success, "failed_count": failed, "results": results}


@get("/v1/memories", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def list_memories(
    request: Request[Any, Any, Any],
    q: str | None = None,
    path: str | None = None,
    limit: int = Parameter(default=10, ge=1, le=100),
    offset: int = Parameter(default=0, ge=0),
) -> dict[str, Any]:
    """记忆列表/关键词检索（GET /v1/memories?q=&path=）。"""
    app: KairosApp = request.app.state["kairos"]
    if q:
        return await app.search.search(q, limit=limit, filters=SearchFilter(path_prefix=path))
    items, total = await app.store.list(path_prefix=path, limit=limit, offset=offset)
    return {"data": items, "total": total, "path": path or ""}


@get(
    "/v1/memories/{memory_id:str}",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def get_memory(request: Request[Any, Any, Any], memory_id: str) -> dict[str, Any]:
    app: KairosApp = request.app.state["kairos"]
    return await app.store.get(memory_id)


@patch(
    "/v1/memories/{memory_id:str}",
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def update_memory(
    request: Request[Any, Any, Any],
    memory_id: str,
    data: dict[str, Any] = Body(title="MemoryUpdateRequest"),
) -> dict[str, Any]:
    """记忆更新（If-Match 乐观锁强制，api-spec §1.3）。"""
    app: KairosApp = request.app.state["kairos"]
    if_match = request.headers.get("if-match")
    version = int(if_match) if if_match and if_match.isdigit() else None
    return await app.store.update(
        memory_id,
        if_match_version=version,
        content=data.get("content"),
        content_summary=data.get("content_summary"),
        vad=data.get("vad"),
        memory_types=data.get("memory_types"),
        occurred_at=data.get("occurred_at"),
    )


@delete(
    "/v1/memories/{memory_id:str}",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def delete_memory(request: Request[Any, Any, Any], memory_id: str) -> dict[str, Any]:
    """契约分支删除（api-spec §1.5）。"""
    app: KairosApp = request.app.state["kairos"]
    await app.store.delete(memory_id)
    return {"status": "deleted", "id": memory_id}


@post(
    "/v1/memories/{memory_id:str}/archive",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def archive_memory(
    request: Request[Any, Any, Any],
    memory_id: str,
    data: dict[str, Any] = Body(title="ArchiveRequest"),
) -> dict[str, Any]:
    """归档记忆（M-05，幂等）。"""
    app: KairosApp = request.app.state["kairos"]
    return await app.store.archive(memory_id, reason=(data or {}).get("reason"))


@post(
    "/v1/memories/{memory_id:str}/restore",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def restore_memory(
    request: Request[Any, Any, Any],
    memory_id: str,
    data: dict[str, Any] = Body(title="RestoreRequest"),
) -> dict[str, Any]:
    """归档恢复/抑制解除（M-05 配套；潜伏势能重估端口匹配验证）。"""
    app: KairosApp = request.app.state["kairos"]
    return await app.forgetting.revive(
        memory_id, reason=(data or {}).get("reason", "context_reemerged")
    )


@post(
    "/v1/memories/search",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def search_memories(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="HybridSearchRequest"),
) -> dict[str, Any]:
    """三信号混合检索（架构 §7.3a）。"""
    from src.errors import MissingFieldError

    app: KairosApp = request.app.state["kairos"]
    query = data.get("query", "")
    if not query:
        raise MissingFieldError("缺少必填字段: query（ERR-INPUT-004）")
    filters_data = data.get("filters") or {}
    return await app.search.search(
        query,
        mode=data.get("mode", "hybrid"),
        weights=data.get("weights"),
        limit=data.get("limit", 10),
        filters=SearchFilter(
            contract=filters_data.get("contract"),
            path_prefix=filters_data.get("path_prefix"),
        ),
    )


# ---------------------------------------------------------------------------
# 路径空间（组件 2）
# ---------------------------------------------------------------------------


@get("/v1/path", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def path_list(
    request: Request[Any, Any, Any],
    path: str,
    limit: int = Parameter(default=10, ge=1, le=100),
    offset: int = Parameter(default=0, ge=0),
) -> dict[str, Any]:
    app: KairosApp = request.app.state["kairos"]
    items, total = await app.path_index.list_path(path, limit=limit, offset=offset)
    return {"data": items, "total": total, "path": path}


@get("/v1/path/tree", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def path_tree(
    request: Request[Any, Any, Any],
    path: str,
    depth: int = Parameter(default=2, ge=1, le=10),
) -> dict[str, Any]:
    app: KairosApp = request.app.state["kairos"]
    root = await app.path_index.tree(path, depth=depth)
    return {"tree": [root.__dict__], "truncated": False}


# ---------------------------------------------------------------------------
# 校准与治理（组件 8）
# ---------------------------------------------------------------------------


@post(
    "/v1/calibrate",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def calibrate(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="CalibrateRequest"),
) -> dict[str, Any]:
    """外部校准信号（CAL-01）。"""
    app: KairosApp = request.app.state["kairos"]
    return await app.calibration.calibrate(
        memory_id=data["memory_id"],
        narrative_coherence_score=data["narrative_coherence_score"],
        source=data.get("source", "api"),
    )


@post(
    "/v1/freeze",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def freeze(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="FreezeRequest"),
) -> dict[str, Any]:
    """强制冻结（CAL-03）。"""
    app: KairosApp = request.app.state["kairos"]
    return await app.freeze.freeze(duration_seconds=data["duration_seconds"])


@post(
    "/v1/unfreeze",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def unfreeze(request: Request[Any, Any, Any]) -> dict[str, Any]:
    app: KairosApp = request.app.state["kairos"]
    return await app.freeze.unfreeze()


@post(
    "/v1/degradation/switch",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def degradation_switch(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="DegradationSwitchRequest"),
) -> dict[str, Any]:
    """降级模式切换（CAL-04）。"""
    app: KairosApp = request.app.state["kairos"]
    return await app.degradation.explicit_switch(data["mode"])


# ---------------------------------------------------------------------------
# 审计与系统管理（组件 6/9）
# ---------------------------------------------------------------------------


@get("/v1/audit-log", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def audit_log(
    request: Request[Any, Any, Any],
    limit: int = Parameter(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """审计日志查询（CAL-05，含 HMAC 链完整性校验）。"""
    app: KairosApp = request.app.state["kairos"]
    verify = await app.tribunal.verify_chain(limit=limit)
    async with app.db.session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(
                text(
                    "SELECT id, timestamp, operator, action, target_type, target_id, "
                    "content_hash, hmac, details, redline_id FROM audit_log "
                    "ORDER BY id DESC LIMIT :lim"
                ),
                {"lim": limit},
            )
        ).fetchall()
    return {
        "logs": [
            {
                "id": r[0],
                "timestamp": r[1],
                "operator": r[2],
                "action": r[3],
                "target_type": r[4],
                "target_id": r[5],
                "content_hash": r[6],
                "hmac": r[7],
                "details": json.loads(r[8]) if r[8] else None,
                "redline_id": r[9],
            }
            for r in rows
        ],
        "chain_valid": verify["chain_valid"],
        "total": verify["total"],
    }


@get("/health", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def health(request: Request[Any, Any, Any]) -> dict[str, Any]:
    """健康检查（A-01，无 /v1 前缀）。

    components 含 scheduler 与 embedding 状态（observability 口径：
    调度器/分词器等运行态须在 /health 可见）。
    """
    app: KairosApp = request.app.state["kairos"]
    result = await app.db.verify_schema()
    scheduler_state = (
        "running" if app.scheduler is not None and app.scheduler._scheduler else "stopped"
    )
    return {
        "status": "ok",
        "components": {
            "api": "ok",
            "db": "ok",
            "tables": result["tables"],
            "scheduler": scheduler_state,
            "embedding": app.search.embedder.name,
        },
        "uptime_seconds": 0,
    }


@get("/v1/config", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def config_get(request: Request[Any, Any, Any]) -> dict[str, Any]:
    """配置查看（A-02；竖切参数族）。"""
    app: KairosApp = request.app.state["kairos"]
    from src.config import SLICE_PARAM_NAMES

    return {
        "config": [
            {"key": k, "value": str(app.settings.get(k)), "scope": "static"}
            for k in SLICE_PARAM_NAMES
        ]
    }


@patch("/v1/config", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def config_patch(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="ConfigUpdateRequest"),
) -> dict[str, Any]:
    """运行时配置修改（A-02；仅接受竖切参数族，越界 400）。"""
    app: KairosApp = request.app.state["kairos"]
    from src.storage.models import utc_now

    updated = []
    for item in data.get("updates", []):
        try:
            value = validate_runtime_override(item["key"], item["value"])
        except ConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        async with app.db.session() as session:
            from sqlalchemy import text

            await session.execute(
                text(
                    "INSERT OR REPLACE INTO config (key, value, scope, updated_at, updated_by) "
                    "VALUES (:k, :v, 'dynamic', :ts, 'api')"
                ),
                {"k": item["key"], "v": str(value), "ts": utc_now()},
            )
            await session.commit()
        updated.append({"key": item["key"], "value": str(value)})
    return {"config": updated}


@post(
    "/v1/seeds",
    status_code=200,
    guards=[_api_key_guard],
    exception_handlers={KairosError: _error_handler},
)
async def seed_create(
    request: Request[Any, Any, Any],
    data: dict[str, Any] = Body(title="SeedCreateRequest"),
) -> dict[str, Any]:
    """种子锚点管理（A-04，admin Key）。"""
    app: KairosApp = request.app.state["kairos"]
    from src.storage.models import Seed

    async with app.db.session() as session:
        seed = Seed(
            id=str(__import__("uuid").uuid4()),
            path=data["path"],
            seed_type=data["seed_type"],
            initial_confidence=data["initial_confidence"],
            current_confidence=data["current_confidence"],
            content_snapshot=json.dumps(data.get("content") or {}, ensure_ascii=False),
        )
        session.add(seed)
        await session.commit()
        return {
            "seed": {
                "path": seed.path,
                "seed_type": seed.seed_type,
                "status": seed.status,
                "degradation_level": seed.degradation_level,
                "initial_confidence": seed.initial_confidence,
                "current_confidence": seed.current_confidence,
                "review_count": seed.review_count,
            }
        }


@get("/v1/seeds", guards=[_api_key_guard], exception_handlers={KairosError: _error_handler})
async def seed_list(request: Request[Any, Any, Any]) -> dict[str, Any]:
    """种子状态查看（A-05）。"""
    app: KairosApp = request.app.state["kairos"]
    from src.storage.models import Seed

    async with app.db.session() as session:
        from sqlalchemy import select

        rows = (await session.execute(select(Seed))).scalars().all()
    return {
        "seeds": [
            {
                "path": s.path,
                "seed_type": s.seed_type,
                "status": s.status,
                "degradation_level": s.degradation_level,
                "initial_confidence": s.initial_confidence,
                "current_confidence": s.current_confidence,
                "review_count": s.review_count,
            }
            for s in rows
        ]
    }
