"""Kairos CLI 入口（竖切 v0.1.0-slice）。

命令契约单一事实源：docs/specification/api-spec.md §3（全量 25 条）；
竖切交付子集 21 条见 docs/development/slice-implementation-guide.md §三。
本模块按周次渐进注册：W1 骨架（--version + init），后续周次按里程碑补充。

CLI 框架：Typer（W1 定档——与 Litestar 类型安全理念一致，mypy 友好）。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import typer

from src import __version__
from src.config import ConfigError, Settings, load_settings
from src.storage.db import Database

app = typer.Typer(
    name="kairos",
    help="Kairos Memory System — AI agent 记忆系统（竖切 v0.1.0-slice）",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Kairos {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", help="显示版本号并退出", callback=_version_callback
    ),
) -> None:
    """Kairos 命令行入口。"""


@app.command()
def init(
    init_key: bool = typer.Option(
        False,
        "--init-key",
        help="生成 API Key（同时生成 SALT/SECRET_KEY/AUDIT_HMAC_KEY）并写入环境文件",
    ),
    db: str | None = typer.Option(
        None, "--db", help="数据库连接串（如 sqlite:///$HOME/.kairos/kairos.db）"
    ),
    data_dir: str | None = typer.Option(None, "--data-dir", help="数据目录（默认 $HOME/.kairos）"),
) -> None:
    """初始化系统（创建配置、目录和数据库）。

    密钥生成（--init-key）：security-specification §2.1 API Key 生命周期——
    KAIROS_API_KEY 明文仅输出一次（不落盘）；KAIROS_API_KEY_HASH 为
    PBKDF2-HMAC-SHA512(256,000 次迭代) 派生值，写入 .env（文件权限 600）。

    初始化顺序注记：init 阶段不执行 S-01 启动校验（密钥尚不存在），
    密钥生成完成后才加载配置确认可启动。
    """
    from src.utils.keys import bootstrap_keys

    # 数据目录：显式参数 > 环境变量 > 默认 ~/.kairos
    target_dir = Path(data_dir or os.environ.get("KAIROS_DATA_DIR", "$HOME/.kairos")).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    dotenv_path = target_dir / ".env"

    if init_key:
        try:
            plain_key = bootstrap_keys(dotenv_path)
        except (OSError, ConfigError) as exc:
            typer.secho(f"[init] 密钥生成失败: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from exc
        typer.secho(f"[init] 密钥已写入 {dotenv_path}（文件权限 600）", fg=typer.colors.GREEN)
        typer.secho("[init] API Key（仅显示一次，请妥善保存）:", fg=typer.colors.CYAN)
        typer.echo(plain_key)
    else:
        typer.secho(
            f"[init] 未指定 --init-key，跳过密钥生成（数据目录: {target_dir}）",
            fg=typer.colors.YELLOW,
        )

    # --db 指定时直接执行迁移（development-setup §三：kairos init --db sqlite:///...）
    if db:
        _migrate_into(db)

    typer.secho(
        "[init] 完成。数据库初始化与迁移: kairos db migrate（或 init --db 一步完成）",
        fg=typer.colors.GREEN,
    )


def _migrate_into(db_url: str) -> None:
    """对指定连接串执行迁移 + schema 校验（init --db / db migrate 共用逻辑）。"""
    import asyncio

    from src.storage.db import Database

    db = Database(db_url)

    async def _run() -> None:
        try:
            typer.echo(f"[db] 初始化数据库 {db_url} ...")
            await db.run_migrations()
            result = await db.verify_schema()
            typer.secho(
                f"[db] 迁移完成 + schema 校验通过"
                f"（表 {result['tables']} / FK 0 违规 / integrity ok）",
                fg=typer.colors.GREEN,
            )
        finally:
            await db.close()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# 数据库命令组（W2 交付：kairos db migrate / migrate rollback / verify）
# ---------------------------------------------------------------------------

db_app = typer.Typer(help="数据库管理（迁移/校验/回滚）", no_args_is_help=True)
app.add_typer(db_app, name="db")


def _load_db() -> tuple[Database, Settings]:
    """加载配置并建立数据库句柄（S-01 配置校验失败即退出）。"""
    try:
        settings = load_settings()
    except ConfigError as exc:
        typer.secho(f"[db] 配置加载失败: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    return Database(settings.get("KAIROS_DB_URL")), settings


@db_app.command("migrate")
def db_migrate(
    rollback: bool = typer.Option(
        False, "--rollback", "-r", help="回滚一步迁移（等价于 kairos db migrate rollback）"
    ),
) -> None:
    """执行数据库迁移至 head（或回滚一步），随后运行 schema 校验。"""
    import asyncio

    db, settings = _load_db()

    async def _run() -> None:
        try:
            if rollback:
                typer.echo("[db] 回滚一步迁移 ...")
                await db.rollback_migration()
                typer.secho("[db] 回滚完成", fg=typer.colors.GREEN)
                return
            typer.echo("[db] 执行迁移至 head ...")
            await db.run_migrations()
            result = await db.verify_schema()
            typer.secho(
                f"[db] 迁移完成 + schema 校验通过"
                f"（表 {result['tables']} / FK 0 违规 / integrity ok）",
                fg=typer.colors.GREEN,
            )
        finally:
            await db.close()

    asyncio.run(_run())


@db_app.command("verify")
def db_verify() -> None:
    """校验当前数据库 schema（表数/FK/integrity/FTS 存在性）。"""
    import asyncio

    db, _settings = _load_db()

    async def _run() -> None:
        try:
            result = await db.verify_schema()
            typer.secho(
                f"[db] schema 校验通过（表 {result['tables']} / FK 0 违规 / integrity ok）",
                fg=typer.colors.GREEN,
            )
        finally:
            await db.close()

    asyncio.run(_run())


@db_app.command("backfill-entities")
def db_backfill_entities(
    dry_run: bool = typer.Option(False, "--dry-run", help="仅统计候选数不执行回溯"),
    force: bool = typer.Option(False, "--force", help="重建全部关联（词典规则升级后覆盖存量）"),
) -> None:
    """存量实体回溯：无实体关联的活跃记忆批量提取入库（幂等；--force 重建）。"""
    _sync(_cli.cmd_backfill_entities)(dry_run=dry_run, force=force)


# ---------------------------------------------------------------------------
# 竖切命令（W9 全量注册；实现见 src/access/cli.py，契约见 api-spec §3）
# ---------------------------------------------------------------------------

from src.access import cli as _cli  # noqa: E402


def _sync(coro_factory: Any) -> Any:
    """同步执行异步命令并输出 JSON。"""
    import json as _json

    def _runner(*args: Any, **kwargs: Any) -> Any:
        try:
            result = _cli._run(coro_factory(*args, **kwargs))
        except Exception as exc:  # noqa: BLE001 - CLI 顶层错误出口
            typer.secho(f"[kairos] 错误: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from exc
        typer.echo(_json.dumps(result, ensure_ascii=False, indent=2))

    return _runner


@app.command()
def write(
    path: str = typer.Argument(..., help="存储路径（kairos:// 前缀）"),
    content: str = typer.Option(..., "--content", help="记忆内容"),
    source: str = typer.Option(..., "--source", help="来源（必填，S-15）"),
    contract: str = typer.Option("ondemand", "--contract", help="契约（五值枚举）"),
    memory_type: str = typer.Option("semantic", "--memory-type", help="记忆类型"),
) -> None:
    """写入记忆（POST /v1/memories）。"""
    _sync(_cli.cmd_write)(path, content, source=source, contract=contract, memory_type=memory_type)


@app.command()
def read(memory_id: str = typer.Argument(..., help="记忆 UUID")) -> None:
    """读取记忆（GET /v1/memories/{id}）。"""
    _sync(_cli.cmd_read)(memory_id)


@app.command()
def search(
    query: str = typer.Argument(..., help="查询内容"),
    limit: int = typer.Option(10, "--limit", help="返回条数"),
    path: str | None = typer.Option(None, "--path", help="路径前缀过滤"),
) -> None:
    """三信号混合检索（POST /v1/memories/search）。"""
    _sync(_cli.cmd_search)(query, limit=limit, path=path)


@app.command("ls")
def ls(
    path: str = typer.Argument(..., help="路径"), limit: int = typer.Option(10, "--limit")
) -> None:
    """路径下记忆列表（GET /v1/path）。"""
    _sync(_cli.cmd_ls)(path, limit=limit)


@app.command()
def tree(
    path: str = typer.Argument(..., help="起始路径"), depth: int = typer.Option(2, "--depth")
) -> None:
    """路径空间树状浏览（GET /v1/path/tree）。"""
    _sync(_cli.cmd_tree)(path, depth=depth)


@app.command()
def update(
    memory_id: str = typer.Argument(..., help="记忆 UUID"),
    content: str = typer.Option(..., "--content", help="更新内容"),
    if_match: int | None = typer.Option(None, "--if-match", help="当前版本号（乐观锁）"),
) -> None:
    """更新记忆（PATCH /v1/memories/{id}，版本链追加）。"""
    _sync(_cli.cmd_update)(memory_id, content=content, if_match=if_match)


@app.command()
def forget(memory_id: str = typer.Argument(..., help="记忆 UUID")) -> None:
    """契约分支删除（DELETE /v1/memories/{id}）。"""
    _sync(_cli.cmd_forget)(memory_id)


@app.command()
def calibrate(
    memory_id: str = typer.Option(..., "--memory-id", help="记忆 UUID"),
    score: float = typer.Option(..., "--score", help="叙事自洽度 [0,1]"),
) -> None:
    """外部校准（POST /v1/calibrate）。"""
    _sync(_cli.cmd_calibrate)(memory_id, score)


@app.command()
def freeze(duration: int = typer.Option(..., "--duration", help="冻结时长（秒）")) -> None:
    """强制冻结（POST /v1/freeze）。"""
    _sync(_cli.cmd_freeze)(duration)


@app.command()
def unfreeze() -> None:
    """解冻（POST /v1/unfreeze）。"""
    _sync(_cli.cmd_unfreeze)()


degradation_app = typer.Typer(help="降级模式管理", no_args_is_help=True)
app.add_typer(degradation_app, name="degradation")


@degradation_app.command("switch")
def degradation_switch(
    mode: str = typer.Option(
        ..., "--mode", help="conservative_silent / limited_cross_validation / safe_hibernation"
    ),
) -> None:
    """降级模式切换（POST /v1/degradation/switch）。"""
    _sync(_cli.cmd_degradation_switch)(mode)


@app.command()
def status() -> None:
    """系统状态（降级模式/冻结）。"""
    _sync(_cli.cmd_status)()


@app.command()
def health(
    full: bool = typer.Option(False, "--full", help="全景健康报告（含记忆库统计/遗忘队列）"),
) -> None:
    """健康检查（GET /health；--full 聚合报告，D-430 闭合）。"""
    _sync(_cli.cmd_health_full if full else _cli.cmd_health)()


@app.command()
def mcp() -> None:
    """MCP Server（stdio 传输；由 Agent MCP Client 启动，与主进程 localhost HTTP 通信）。"""
    from src.access.mcp.bridge import run as _mcp_run

    _mcp_run()


@app.command()
def serve(
    port: int | None = typer.Option(None, "--port", help="监听端口（默认 8010）"),
    reload: bool = typer.Option(False, "--reload", help="热重载（开发）"),
) -> None:
    """启动服务（REST API，S-04 本地回环绑定）。"""
    import os

    from src.config import load_settings

    load_settings()  # S-01 启动前配置校验（缺 HMAC 密钥拒绝启动）
    if port:
        os.environ["KAIROS_PORT"] = str(port)
    from src.access.server import serve as _serve

    _serve()


config_app = typer.Typer(help="配置管理", no_args_is_help=True)
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show(key: str | None = typer.Argument(None, help="参数名（缺省输出全部）")) -> None:
    """配置查看（GET /v1/config；竖切参数族）。"""
    _sync(_cli.cmd_config_show)(key)


@config_app.command("reset")
def config_reset() -> None:
    """配置重置（D-430 闭合）：清空 config 表运行时覆盖，恢复参数默认。"""
    _sync(_cli.cmd_config_reset)()


audit_app = typer.Typer(help="审计管理（D-430 闭合）", no_args_is_help=True)
app.add_typer(audit_app, name="audit")


@audit_app.command("log")
def audit_log(
    limit: int = typer.Option(20, "--limit", help="返回条数"),
) -> None:
    """审计日志查询（CAL-05，HMAC 链完整性校验）。"""
    _sync(_cli.cmd_audit_log)(limit)


seed_app = typer.Typer(help="种子锚点管理（组件 5 冷启动锚点）", no_args_is_help=True)
app.add_typer(seed_app, name="seed")


@seed_app.command("add")
def seed_add(
    path: str = typer.Option(
        ...,
        "--path",
        help="种子记忆路径（如 kairos://_user/hermes/identity/johnl1989）",
    ),
    seed_type: str = typer.Option(
        "identity", "--type", help="种子类型（config/identity/calibration）"
    ),
    text: str = typer.Option(..., "--text", help="种子内容（身份事实描述）"),
    confidence: float = typer.Option(0.6, "--confidence", help="初始置信度（0-1）"),
) -> None:
    """种子冷启动锚点：identity 种子 → 身份记忆 + 初始赋予（S-10 见证豁免生效）。"""
    _sync(_cli.cmd_seed_add)(path, seed_type, text, confidence=confidence)


if __name__ == "__main__":
    app()
