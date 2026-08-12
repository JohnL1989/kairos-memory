"""数据库连接管理（轻量模式 SQLite，ADR-001：竖切以 SQLite 优先）。

- 异步引擎（aiosqlite + SQLAlchemy 2.0 async）
- 迁移执行（Alembic upgrade/downgrade 承载，见 migrations/）
- 迁移后校验（schema-slice.sql 后置校验断言：表数 15 / FK 检查 / integrity）
- 测试支持内存数据库（StaticPool）
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from src.storage.models import FTS_TABLE, SLICE_TABLES

# 迁移后校验：非 sqlite_ 系统表期望计数（schema-slice.sql 后置校验 §）
_EXPECTED_USER_TABLES = len(SLICE_TABLES)


def _async_sqlite_url(path: str | Path) -> str:
    """SQLite 连接串转 async 形态（sqlite:/// → sqlite+aiosqlite:///）。"""
    url = str(path)
    if url.startswith("sqlite+aiosqlite"):
        return url
    if url.startswith("sqlite:///"):
        return "sqlite+aiosqlite:///" + url[len("sqlite:///") :]
    raise ValueError(f"轻量模式仅支持 sqlite:/// 连接串（竖切决策，ADR-001）: {url}")


def create_engine(db_url: str, *, is_memory: bool = False) -> AsyncEngine:
    """创建异步引擎。

    is_memory：pytest 内存数据库（sqlite:///:memory: 每连接独立，须 StaticPool 共享）。
    SQLite 连接级 PRAGMA（schema-slice.sql 头部声明，由应用层承载）：
    - foreign_keys=ON：SQLite 默认不强制外键，未开启则 FK 静默失效
    - journal_mode=WAL / synchronous=NORMAL：写并发与持久性
    """
    kwargs: dict[str, object] = {}
    if is_memory:
        kwargs["poolclass"] = StaticPool
        kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_async_engine(_async_sqlite_url(db_url), echo=False, **kwargs)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
        # 注：sqlite-vec 扩展在 Windows 官方 Python 构建不可加载
        # （sqlite3 未编译 SQLITE_ENABLE_LOAD_EXTENSION）——向量检索由
        # vector_index 的 numpy 批量余弦扫描承担（同契约，brute-force 精确召回）
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        if not is_memory:
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.close()

    return engine


class Database:
    """SQLite 数据库句柄：引擎 + 会话工厂 + 迁移与校验。"""

    def __init__(self, db_url: str, *, is_memory: bool = False) -> None:
        self.db_url = db_url
        self.engine = create_engine(db_url, is_memory=is_memory)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    def session(self) -> AsyncSession:
        return self.session_factory()

    async def close(self) -> None:
        await self.engine.dispose()

    # ------------------------------------------------------------------
    # 迁移
    # ------------------------------------------------------------------

    async def run_migrations(self) -> None:
        """执行 Alembic 迁移至 head（kairos db migrate 语义）。"""
        from alembic import command
        from alembic.config import Config as AlembicConfig

        from src.paths import PROJECT_ROOT

        cfg = AlembicConfig(str(PROJECT_ROOT / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", self.db_url)
        await asyncio.to_thread(command.upgrade, cfg, "head")

    async def rollback_migration(self) -> None:
        """回滚一步迁移（kairos db migrate rollback 语义）。"""
        from alembic import command
        from alembic.config import Config as AlembicConfig

        from src.paths import PROJECT_ROOT

        cfg = AlembicConfig(str(PROJECT_ROOT / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", self.db_url)
        await asyncio.to_thread(command.downgrade, cfg, "-1")

    async def verify_schema(self) -> dict[str, object]:
        """迁移后校验（schema-slice.sql 后置校验断言）。

        返回校验结果；任一断言失败抛 RuntimeError（失败关闭）。
        """
        async with self.engine.connect() as conn:
            # 1. 用户表计数（15 张物理/虚拟表；FTS 内部表 memories_fts_* 不计入）
            table_rows = await conn.execute(
                text(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'memories_fts_%' "
                    "AND name != 'alembic_version'"
                )
            )
            table_count = table_rows.scalar_one()
            if table_count != _EXPECTED_USER_TABLES:
                raise RuntimeError(
                    f"schema 校验失败: 表数 {table_count} != 期望 {_EXPECTED_USER_TABLES}"
                )

            # 2. 外键完整性（PRAGMA foreign_key_check 期望空结果集）
            fk_rows = await conn.execute(text("PRAGMA foreign_key_check"))
            violations = fk_rows.fetchall()
            if violations:
                raise RuntimeError(f"schema 校验失败: 外键违规 {len(violations)} 条")

            # 3. 整体完整性（PRAGMA integrity_check 期望 'ok'）
            ok_rows = await conn.execute(text("PRAGMA integrity_check"))
            if ok_rows.scalar_one() != "ok":
                raise RuntimeError("schema 校验失败: integrity_check 未通过")

            # 4. FTS 虚拟表存在
            fts_rows = await conn.execute(
                text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=:n"),
                {"n": FTS_TABLE},
            )
            if fts_rows.scalar_one() != 1:
                raise RuntimeError(f"schema 校验失败: FTS 虚拟表 {FTS_TABLE} 缺失")

        return {"tables": table_count, "foreign_keys": 0, "integrity": "ok"}


async def bootstrap(db: Database) -> None:
    """启动就绪：迁移 + 校验（kairos serve 启动路径）。"""
    await db.run_migrations()
    await db.verify_schema()
