"""存储后端抽象层测试（D-449 前置，acceptance-criteria「存储后端」判据）。

覆盖：
- StorageBackend 五方法契约（write/path_retrieve/vector_search/update_witness/update_usage）
- SQLiteBackend 实现（委托现有组件，行为与竖切一致）
- MockPGBackend 接口可替换性（同一契约、业务无感切换）
"""

from __future__ import annotations

import pytest

from src.app import build_app
from src.storage.backend import (
    MemoryRecord,
    MockPGBackend,
    SQLiteBackend,
    StorageBackend,
    UsageDelta,
    WitnessUpdate,
)

pytestmark = pytest.mark.unit


def _settings():
    return type(
        "S",
        (),
        {
            "get": lambda self, k, d=None: {
                "KAIROS_AUDIT_HMAC_KEY": "22" * 32,
                "KAIROS_FORGETTING_HALF_LIFE": 69,
                "KAIROS_FRESHNESS_ACTIVE_THRESHOLD": 0.3,
                "KAIROS_FRESHNESS_STALE_THRESHOLD": 0.1,
                "KAIROS_DEGRADATION_PERIOD_N": 50,
                "KAIROS_DEGRADATION_PERIOD_M": 200,
                "KAIROS_HOST": "127.0.0.1",
                "KAIROS_PORT": 8010,
            }.get(k, d),
        },
    )()


@pytest.fixture
async def sqlite_backend(memory_db):
    """SQLiteBackend（委托竖切组件）。"""
    kairos = build_app(_settings(), db=memory_db)
    backend = SQLiteBackend(
        memory_db, store=kairos.store, copies=kairos.dual_copy, vectors=kairos.search.vector_index
    )
    yield backend, kairos
    await kairos.close()


class TestStorageBackendContract:
    async def test_contract_methods(self) -> None:
        """五方法契约齐备（抽象完整性）。"""
        for method in ("write", "path_retrieve", "vector_search", "update_witness", "update_usage"):
            assert hasattr(StorageBackend, method)
            assert getattr(StorageBackend, method).__isabstractmethod__ is True


class TestSQLiteBackend:
    async def test_write_and_retrieve(self, sqlite_backend) -> None:
        backend, _kairos = sqlite_backend
        mid = await backend.write(
            MemoryRecord(
                id="b1",
                path="kairos://_user/u1/memories/b1",
                content="后端写入记忆内容，长度足够用于门禁校验。",
                metadata={"provenance": "user_input"},
            )
        )
        assert mid  # 存储层生成 uuid（路径 uuid 化，api-spec §1.1 响应形态）
        hits = await backend.path_retrieve("kairos://_user/u1/")
        assert any(h.id == mid for h in hits)

    async def test_witness_and_usage(self, sqlite_backend) -> None:
        backend, kairos = sqlite_backend
        mid = await backend.write(
            MemoryRecord(
                id="b2",
                path="kairos://_user/u1/memories/b2",
                content="后端见证测试内容，长度足够用于门禁校验。",
                metadata={"provenance": "user_input"},
            )
        )
        await backend.update_witness(mid, WitnessUpdate(narrative_coherence_score=0.9))
        witness = await kairos.dual_copy.read_witness(mid)
        assert witness["narrative_coherence_score"] == 0.9
        await backend.update_usage(mid, UsageDelta(usage_count=3, activation_weight=0.1))
        usage = await kairos.dual_copy.read_usage(mid)
        assert usage["usage_count"] == 3

    async def test_vector_search(self, sqlite_backend) -> None:
        backend, kairos = sqlite_backend
        mid = await backend.write(
            MemoryRecord(
                id="b3",
                path="kairos://_user/u1/memories/b3",
                content="后端向量检索测试内容，长度足够用于门禁校验。",
                metadata={"provenance": "user_input"},
            )
        )
        hits = await backend.vector_search([0.1] * 1536, top_k=10)
        assert any(h.id == mid for h in hits)


class TestMockPGInterchangeability:
    """接口可替换性：Mock PG 后端与 SQLite 后端满足同一契约（业务无感切换）。"""

    async def test_mock_pg_implements_contract(self) -> None:
        backend: StorageBackend = MockPGBackend()
        mid = await backend.write(
            MemoryRecord(
                id="p1",
                path="kairos://_user/u1/memories/p1",
                content="mock pg 记忆内容，长度足够用于门禁校验。",
            )
        )
        assert mid == "p1"
        hits = await backend.path_retrieve("kairos://_user/u1/")
        assert len(hits) == 1
        await backend.update_witness("p1", WitnessUpdate(narrative_coherence_score=0.8))
        await backend.update_usage("p1", UsageDelta(usage_count=2))
        vectors = await backend.vector_search([0.0] * 1536, top_k=5)
        assert len(vectors) >= 1

    async def test_contract_driven_usage(self, sqlite_backend) -> None:
        """业务层仅依赖抽象契约（SQLite 与 Mock 可互换）。"""
        _backend, kairos = sqlite_backend
        # 以抽象类型操作（业务层视角）
        backend: StorageBackend = MockPGBackend()
        await backend.write(
            MemoryRecord(
                id="px", path="kairos://_project/x/", content="契约驱动内容，长度足够用于门禁校验。"
            )
        )
        assert len(await backend.path_retrieve("kairos://_project/")) == 1
        # SQLite 后端同契约操作
        sqlite: StorageBackend = SQLiteBackend(
            kairos.db,
            store=kairos.store,
            copies=kairos.dual_copy,
            vectors=kairos.search.vector_index,
        )
        mid = await sqlite.write(
            MemoryRecord(
                id="py",
                path="kairos://_project/y/",
                content="契约驱动内容，长度足够用于门禁校验。",
                metadata={"provenance": "user_input"},
            )
        )
        assert len(await sqlite.path_retrieve("kairos://_project/")) >= 1
        assert mid  # 存储层生成 uuid
