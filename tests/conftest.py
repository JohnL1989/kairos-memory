"""测试共享 fixtures。

- memory_db：内存 SQLite + 迁移 + 校验（每个测试函数独立，StaticPool）
- settings：最小完整配置（含必填密钥；测试环境密钥为固定测试值，非真实密钥）
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

# 测试环境：全部密钥注入固定测试值（非真实密钥；S 级红线测试数据除外）
_TEST_ENV = {
    "KAIROS_SALT": "00" * 16,
    "KAIROS_SECRET_KEY": "11" * 32,
    "KAIROS_AUDIT_HMAC_KEY": "22" * 32,
    "KAIROS_DB_URL": "sqlite:///:memory:",
    "KAIROS_DATA_DIR": str(Path(tempfile.gettempdir()) / "kairos-test-data"),
}


@pytest.fixture(scope="session", autouse=True)
def _test_env() -> None:
    for key, value in _TEST_ENV.items():
        os.environ.setdefault(key, value)


@pytest.fixture
def test_env() -> dict[str, str]:
    return dict(_TEST_ENV)


@pytest_asyncio.fixture
async def memory_db(tmp_path):
    """临时文件数据库：迁移至 head + 后置校验（每个测试独立）。

    注：SQLite 内存库（:memory:）每连接独立，Alembic 迁移引擎与测试引擎
    非同连接——故用临时文件库承载「内存库」语义（迁移连接共享同一 DB 文件）。
    """
    from src.storage.db import Database

    db = Database(f"sqlite:///{tmp_path / 'test.db'}")
    try:
        await db.run_migrations()
        await db.verify_schema()
        yield db
    finally:
        await db.close()
