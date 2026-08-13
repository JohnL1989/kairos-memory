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


async def cmd_health_full() -> dict[str, Any]:
    """kairos health --full（D-430 闭合）：健康 + 记忆库统计 + 遗忘队列全景。"""
    from sqlalchemy import func, select, text

    from src.storage.models import ForgettingQueue, Memory

    app = await _resolve_app()
    try:
        schema = await app.db.verify_schema()
        async with app.db.session() as session:
            total = (await session.execute(select(func.count()).select_from(Memory))).scalar() or 0
            by_state = dict(
                (await session.execute(
                    select(Memory.status, func.count()).group_by(Memory.status)
                )).all()
            )
            by_type = dict(
                (
                    await session.execute(
                        text(
                            "SELECT je.value AS mtype, COUNT(*) AS cnt "
                            "FROM memories, json_each(memories.memory_types) je "
                            "GROUP BY je.value ORDER BY cnt DESC"
                        )
                    )
                ).all()
            )
            pending = (
                await session.execute(
                    select(func.count()).select_from(ForgettingQueue).where(
                        ForgettingQueue.status == "pending_archive"
                    )
                )
            ).scalar() or 0
        return {
            "status": "ok",
            "components": {"api": "ok", "db": "ok", "tables": schema["tables"]},
            "memory": {
                "total": total,
                "by_state": by_state,
                "by_type": by_type,
            },
            "forgetting": {"pending_archive": pending},
        }
    finally:
        await app.close()


async def cmd_audit_log(limit: int = 20) -> dict[str, Any]:
    """kairos audit log [--limit N]（D-430 闭合）：审计日志查询（HMAC 链验证）。"""
    from sqlalchemy import text

    app = await _resolve_app()
    try:
        verify = await app.tribunal.verify_chain(limit=limit)
        async with app.db.session() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT id, timestamp, operator, action, target_type, "
                        "target_id, details, redline_id FROM audit_log "
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
                    "details": r[6],
                    "redline_id": r[7],
                }
                for r in rows
            ],
            "chain_valid": verify.get("chain_valid", False),
            "broken_ids": verify.get("broken_ids", []),
            "verified_total": verify.get("total", 0),
        }
    finally:
        await app.close()


async def cmd_config_reset() -> dict[str, Any]:
    """kairos config reset（D-430 闭合）：清空 config 表运行时覆盖，恢复参数默认。"""
    from sqlalchemy import func, select, text

    from src.storage.models import ConfigEntry

    app = await _resolve_app()
    try:
        async with app.db.session() as session:
            count = (await session.execute(select(func.count()).select_from(ConfigEntry))).scalar() or 0
            await session.execute(text("DELETE FROM config"))
            await session.commit()
        return {"status": "reset", "removed": count}
    finally:
        await app.close()
