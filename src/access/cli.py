"""CLI 命令实现（竖切 15 条子集；命令契约单一事实源：api-spec §3）。

竖切 CLI（slice-implementation-guide §三）：init / write / read / search /
ls / tree / update / forget / calibrate / freeze / degradation switch /
status / health / db migrate / config show。
本模块承载命令逻辑（main.py 注册 Typer 命令组）。
"""

from __future__ import annotations

import asyncio
from typing import Any

from src.app import KairosApp, build_app
from src.storage.memory_store import MemoryWriteInput


def _run(coro: Any) -> Any:
    """同步包装异步命令。"""
    return asyncio.run(coro)


async def _resolve_app(db_url: str | None = None) -> KairosApp:
    from src.config import load_settings

    settings = load_settings()
    if db_url:
        from src.storage.db import Database

        app = build_app(settings, db=Database(db_url))
    else:
        app = build_app(settings)
    await app.db.run_migrations()
    await app.db.verify_schema()
    return app


async def cmd_write(
    path: str,
    content: str,
    *,
    source: str,
    contract: str = "ondemand",
    memory_type: str = "semantic",
) -> dict[str, Any]:
    """kairos write <path> --content --source [--contract]（对应 POST /v1/memories）。"""
    app = await _resolve_app()
    try:
        result = await app.store.create(
            MemoryWriteInput(
                path=path,
                content=content,
                provenance=source,
                contract=contract,
                memory_types=[memory_type],
            )
        )
        return {"id": result.id, "path": result.path, "version": result.version}
    finally:
        await app.close()


async def cmd_read(memory_id: str) -> dict[str, Any]:
    """kairos read <id>（对应 GET /v1/memories/{id}）。"""
    app = await _resolve_app()
    try:
        return await app.store.get(memory_id)
    finally:
        await app.close()


async def cmd_search(query: str, *, limit: int = 10, path: str | None = None) -> dict[str, Any]:
    """kairos search <query> [--limit] [--path]（对应 POST /v1/memories/search）。"""
    from src.storage.hybrid_search import SearchFilter

    app = await _resolve_app()
    try:
        return await app.search.search(
            query, limit=limit, filters=SearchFilter(path_prefix=path) if path else None
        )
    finally:
        await app.close()


async def cmd_ls(path: str, *, limit: int = 10) -> dict[str, Any]:
    """kairos ls <path>（对应 GET /v1/path）。"""
    app = await _resolve_app()
    try:
        items, total = await app.path_index.list_path(path, limit=limit)
        return {"data": items, "total": total, "path": path}
    finally:
        await app.close()


async def cmd_tree(path: str, *, depth: int = 2) -> dict[str, Any]:
    """kairos tree <path> --depth（对应 GET /v1/path/tree）。"""
    app = await _resolve_app()
    try:
        root = await app.path_index.tree(path, depth=depth)
        return {
            "tree": [{"path": root.path, "memory_count": root.memory_count}],
            "truncated": False,
        }
    finally:
        await app.close()


async def cmd_update(
    memory_id: str, *, content: str, if_match: int | None = None
) -> dict[str, Any]:
    """kairos update <id> --content [--if-match]（对应 PATCH /v1/memories/{id}）。"""
    app = await _resolve_app()
    try:
        return await app.store.update(memory_id, if_match_version=if_match, content=content)
    finally:
        await app.close()


async def cmd_forget(memory_id: str) -> dict[str, Any]:
    """kairos forget <id>（对应 DELETE /v1/memories/{id} 契约分支删除）。"""
    app = await _resolve_app()
    try:
        await app.store.delete(memory_id)
        return {"status": "deleted", "id": memory_id}
    finally:
        await app.close()


async def cmd_calibrate(memory_id: str, score: float, *, source: str = "cli") -> dict[str, Any]:
    """kairos calibrate --memory-id --score（对应 POST /v1/calibrate）。"""
    app = await _resolve_app()
    try:
        return await app.calibration.calibrate(
            memory_id=memory_id, narrative_coherence_score=score, source=source
        )
    finally:
        await app.close()


async def cmd_freeze(duration: int) -> dict[str, Any]:
    """kairos freeze --duration（对应 POST /v1/freeze）。"""
    app = await _resolve_app()
    try:
        return await app.freeze.freeze(duration_seconds=duration)
    finally:
        await app.close()


async def cmd_unfreeze() -> dict[str, Any]:
    """kairos unfreeze（对应 POST /v1/unfreeze）。"""
    app = await _resolve_app()
    try:
        return await app.freeze.unfreeze()
    finally:
        await app.close()


async def cmd_degradation_switch(mode: str) -> dict[str, Any]:
    """kairos degradation switch --mode（对应 POST /v1/degradation/switch）。"""
    app = await _resolve_app()
    try:
        return await app.degradation.explicit_switch(mode)
    finally:
        await app.close()


async def cmd_status() -> dict[str, Any]:
    """kairos status（系统状态）。"""
    app = await _resolve_app()
    try:
        return {
            "degradation": await app.degradation.status(),
            "frozen": await app.freeze.guard.is_frozen(),
        }
    finally:
        await app.close()


async def cmd_health() -> dict[str, Any]:
    """kairos health（对应 GET /health）。"""
    app = await _resolve_app()
    try:
        result = await app.db.verify_schema()
        return {
            "status": "ok",
            "components": {"api": "ok", "db": "ok", "tables": result["tables"]},
            "uptime_seconds": 0,
        }
    finally:
        await app.close()


async def cmd_config_show(key: str | None = None) -> dict[str, Any]:
    """kairos config show [KEY]（对应 GET /v1/config；竖切参数族）。"""
    from src.config import SLICE_PARAM_NAMES

    app = await _resolve_app()
    try:
        if key:
            return {"config": [{"key": key, "value": str(app.settings.get(key))}]}
        return {
            "config": [{"key": k, "value": str(app.settings.get(k))} for k in SLICE_PARAM_NAMES]
        }
    finally:
        await app.close()
