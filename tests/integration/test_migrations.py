"""迁移集成测试（W2 验收：迁移可回滚；后置校验三断言）。

对应 TC-A07-001~003（test-plan §3.9）：迁移执行 / 后置校验 / 回滚。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest_asyncio
from sqlalchemy import text

from src.storage.db import _EXPECTED_USER_TABLES, Database


@pytest_asyncio.fixture
async def file_db() -> Database:
    """临时文件数据库（回滚测试需要真实文件持久化）。"""
    tmp = tempfile.mkdtemp(prefix="kairos-mig-")
    db = Database(f"sqlite:///{Path(tmp) / 'test.db'}")
    yield db
    await db.close()


class TestMigrationApply:
    async def test_migrate_head_then_verify(self, file_db: Database) -> None:
        await file_db.run_migrations()
        result = await file_db.verify_schema()
        assert result["tables"] == _EXPECTED_USER_TABLES
        assert result["integrity"] == "ok"

    async def test_user_table_count_after_migrate(self, file_db: Database) -> None:
        await file_db.run_migrations()
        async with file_db.engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'memories_fts_%' "
                    "AND name != 'alembic_version' ORDER BY name"
                )
            )
            names = {r[0] for r in rows}
        expected = {
            "audit_log",
            "config",
            "entities",
            "forgetting_queue",
            "journal_buffer",
            "memory_entities",
            "memory_states",
            "memory_versions",
            "memories",
            "memories_fts",
            "schema_version",
            "seeds",
            "usage_events",
            "usage_weight",
            "witness_anchor",
        }
        assert names == expected

    async def test_fts_triggers_created(self, file_db: Database) -> None:
        """FTS 同步触发器（ADR-011 手写 op.execute 生效）。"""
        await file_db.run_migrations()
        async with file_db.engine.connect() as conn:
            rows = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")
            )
            triggers = {r[0] for r in rows}
        assert {"memories_fts_ai", "memories_fts_ad", "memories_fts_au"} <= triggers

    async def test_fts_insert_sync(self, file_db: Database) -> None:
        """写入 memories 触发 FTS 同步（external content 模式自动同步，schema-slice §14）。"""
        await file_db.run_migrations()
        async with file_db.engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO memories (id, path, version, content, content_hash, "
                    "memory_types, provenance) "
                    "VALUES (:id, :path, 1, :content, :hash, '[\"semantic\"]', 'user_input')"
                ),
                {
                    "id": "m1",
                    "path": "kairos://_user/t/memories/",
                    "content": "测试内容",
                    "hash": "h1",
                },
            )
        async with file_db.engine.connect() as conn:
            rows = await conn.execute(text("SELECT rowid, content FROM memories_fts"))
            assert rows.fetchone() is not None


class TestMigrationRollback:
    """迁移可回滚（project-plan W2 验收；TC-A07-003）。"""

    async def test_downgrade_drops_all_tables(self, file_db: Database) -> None:
        await file_db.run_migrations()
        await file_db.rollback_migration()
        async with file_db.engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'"
                )
            )
            assert rows.scalar_one() == 0

    async def test_migrate_again_after_rollback(self, file_db: Database) -> None:
        """回滚后可重新迁移（幂等链路）。"""
        await file_db.run_migrations()
        await file_db.rollback_migration()
        await file_db.run_migrations()
        await file_db.verify_schema()
