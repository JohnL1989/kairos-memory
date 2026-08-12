"""Alembic 迁移环境（async 模式，aiosqlite 方言）。

- 迁移 DDL 唯一承载：docs/specification/schema-slice.sql
  （迁移执行其 CREATE 语句；DRY——ORM models 与 DDL 的一致性由测试校验）
- URL：alembic.ini 占位，运行时由 src/storage/db.py 覆盖
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.storage import models  # noqa: F401  # 注册 metadata
from src.storage.db import _async_sqlite_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = models.Base.metadata


def _effective_url() -> str:
    """db.py 传入的 sqlite:/// 转 async 形态（aiosqlite 方言）。"""
    url = config.get_main_option("sqlalchemy.url") or ""
    return _async_sqlite_url(url)


def run_migrations_offline() -> None:
    """离线模式（生成 SQL 脚本，不连接 DB）。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    section = dict(config.get_section(config.config_ini_section, {}))
    section["sqlalchemy.url"] = _effective_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
