"""Litestar 服务组装（竖切 REST 21 端点）——kairos serve 入口。

S-04 本地回环绑定红线：监听地址默认 127.0.0.1（KAIROS_HOST），
非本机请求拒绝（配置校验 + 监听地址双重承载）。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from litestar import Litestar, get
from litestar.datastructures import State

from src.access.api.routes import (  # 竖切 21 端点 handlers
    _error_handler,
    archive_memory,
    audit_log,
    calibrate,
    config_get,
    config_patch,
    create_memories_batch,
    create_memory,
    degradation_switch,
    delete_memory,
    freeze,
    get_memory,
    health,
    list_memories,
    path_list,
    path_tree,
    restore_memory,
    search_memories,
    seed_create,
    seed_list,
    unfreeze,
    update_memory,
)
from src.access.api.extended import (  # MCP 工具契约补齐端点（§6.8）
    entities_extract,
    graph_search,
    memories_heat_top,
    memories_stats,
    memory_feedback,
    memory_traces,
    relation_create,
    relation_query,
    relation_remove,
    sessions_list,
)
from src.app import KairosApp, build_app
from src.config import load_settings
from src.errors import KairosError

_HANDLERS = [
    create_memory,
    create_memories_batch,
    list_memories,
    get_memory,
    update_memory,
    delete_memory,
    archive_memory,
    restore_memory,
    search_memories,
    path_list,
    path_tree,
    calibrate,
    freeze,
    unfreeze,
    degradation_switch,
    audit_log,
    health,
    config_get,
    config_patch,
    seed_create,
    seed_list,
    memories_stats,
    memories_heat_top,
    memory_feedback,
    memory_traces,
    entities_extract,
    graph_search,
    sessions_list,
    relation_create,
    relation_remove,
    relation_query,
]


@get("/", exclude_from_auth=True)
async def root() -> dict[str, str]:
    return {"service": "kairos", "version": "0.1.0-slice", "docs": "/v1/schema"}


def create_app(kairos: KairosApp | None = None) -> Litestar:
    """创建 Litestar 应用（注入组装好的 KairosApp）。"""
    kairos = kairos or build_app()

    import os as _os

    app = Litestar(
        route_handlers=[root, *_HANDLERS],
        on_startup=[_bootstrap(kairos)],
        on_shutdown=[_shutdown(kairos)],
        state=State({"kairos": kairos}),
        # 全局异常处理器：覆盖 guard/参数解析阶段的 KairosError（如鉴权 401）
        exception_handlers={KairosError: _error_handler},
        # KAIROS_DEBUG=true 时返回异常详情（冒烟/故障定位；生产默认关闭）
        debug=_os.environ.get("KAIROS_DEBUG", "false").lower() == "true",
    )
    return app


def _bootstrap(kairos: KairosApp) -> Callable[[], Awaitable[None]]:
    """启动就绪：迁移 + schema 校验（S-01 配置校验由 build_app 承担）。"""

    async def _run() -> None:
        await kairos.db.run_migrations()
        await kairos.db.verify_schema()
        if kairos.scheduler is not None:
            # KAIROS_SCHEDULER_ENABLED 开关（默认 true；测试/冒烟可关）
            import os as _os

            if _os.environ.get("KAIROS_SCHEDULER_ENABLED", "true").lower() != "false":
                kairos.scheduler.start()  # 空闲驱动调度（遗忘/潜伏重估/forgetAfter/降级 tick）

    return _run


def _shutdown(kairos: KairosApp) -> Callable[[], Awaitable[None]]:
    async def _run() -> None:
        await kairos.close()

    return _run


def serve() -> None:
    """kairos serve 入口（uvicorn 启动）。"""
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        create_app(),
        host=settings.get("KAIROS_HOST"),  # S-04：默认 127.0.0.1 本地回环
        port=settings.get("KAIROS_PORT"),
        log_level="info",
    )


if __name__ == "__main__":
    serve()
