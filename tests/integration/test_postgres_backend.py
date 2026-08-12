"""PostgresBackend 集成测试（D-449 闭合，ADR-001 竖切验收后 PG 适配）。

依赖：Docker pgvector 容器（kairos-pg，55432 端口）。
覆盖：StorageBackend 契约五方法在真实 PostgreSQL + pgvector 上全链路验证
（write / path_retrieve / vector_search（pgvector <=> 余弦）/ update_witness /
update_usage + upsert_embedding）。

环境变量 KAIROS_PG_TEST_SKIP=1 可跳过（无 Docker 环境 CI 回退）。
"""

from __future__ import annotations

import os

import pytest

from src.storage.backend import MemoryRecord, UsageDelta, WitnessUpdate
from src.storage.postgres_backend import DEFAULT_DSN, PostgresBackend

pytestmark = pytest.mark.integration

PG_AVAILABLE = os.environ.get("KAIROS_PG_TEST_SKIP", "0") != "1"


@pytest.fixture
async def backend():
    if not PG_AVAILABLE:
        pytest.skip("KAIROS_PG_TEST_SKIP=1（无 Docker PG 环境）")
    b = PostgresBackend(DEFAULT_DSN)
    await b.connect()
    # 测试库专用：清空三表（避免历史数据跨轮累积影响断言）
    pool = b._pool
    assert pool is not None
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE usage_weight, witness_anchor, memories")
    yield b
    await b.close()


@pytest.fixture
async def seeded(backend):
    """写入两条种子记忆（含向量）。"""
    import uuid

    rng = __import__("numpy").random.default_rng(1)
    uid = uuid.uuid4().hex[:8]  # 每次运行唯一（PG 状态持久，避免跨轮累计）
    m1 = MemoryRecord(
        id=f"pg-{uid}-1",
        path=f"kairos://_user/u1/memories/pg-{uid}-1",
        content="PostgreSQL 后端测试记忆甲。",
    )
    m2 = MemoryRecord(
        id=f"pg-{uid}-2",
        path=f"kairos://_user/u2/memories/pg-{uid}-2",
        content="PostgreSQL 后端测试记忆乙。",
    )
    await backend.write(m1)
    await backend.write(m2)
    await backend.upsert_embedding("pg-1", rng.standard_normal(1536).tolist())
    await backend.upsert_embedding("pg-2", rng.standard_normal(1536).tolist())
    return backend, m1, m2


class TestPostgresBackendContract:
    async def test_write_and_path_retrieve(self, seeded) -> None:
        backend, m1, m2 = seeded
        hits = await backend.path_retrieve("kairos://_user/u1/")
        assert len(hits) == 1
        assert hits[0].id == m1.id
        all_hits = await backend.path_retrieve("kairos://", limit=10)
        assert len(all_hits) == 2

    async def test_vector_search_pgvector(self, seeded) -> None:
        """pgvector <=> 余弦距离检索（真实 PG + pgvector 扩展）。"""
        backend, m1, _m2 = seeded
        query = [0.0] * 1536
        query[0] = 1.0
        await backend.upsert_embedding(m1.id, query)  # 与查询同向量 → 余弦 1.0
        hits = await backend.vector_search(query, top_k=5)
        assert hits  # 至少一条
        top = hits[0]
        assert top.id == m1.id  # 精确命中（余弦 1.0 最高）
        assert 0.99 < top.score <= 1.0

    async def test_witness_and_usage(self, seeded) -> None:
        backend, m1, _m2 = seeded
        await backend.update_witness(m1.id, WitnessUpdate(narrative_coherence_score=0.9))
        await backend.update_usage(m1.id, UsageDelta(usage_count=3))
        # PG 侧状态验证

        pool = backend._pool
        assert pool is not None
        async with pool.acquire() as conn:
            witness = await conn.fetchrow(
                "SELECT narrative_coherence_score, calibration_count FROM witness_anchor WHERE memory_id = $1",
                m1.id,
            )
            usage = await conn.fetchrow(
                "SELECT usage_count FROM usage_weight WHERE memory_id = $1", m1.id
            )
        assert witness["narrative_coherence_score"] == pytest.approx(0.9, abs=1e-6)
        assert witness["calibration_count"] >= 1  # 幂等（重复运行累计）
        assert usage["usage_count"] == 3

    async def test_unconnected_raises(self) -> None:
        b = PostgresBackend("postgresql://x:y@127.0.0.1:1/nope")
        with pytest.raises(RuntimeError, match="未连接"):
            await b.write(MemoryRecord(id="x", path="kairos://x/", content="x"))
