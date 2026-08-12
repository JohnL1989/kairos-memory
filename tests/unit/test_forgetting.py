"""遗忘调度器 + 潜伏势能重估单元测试（TC-F01-001 / TC-F02-001 / TC-F03-001）。

覆盖：
- freshness 单曲线公式（2^(-days/HALF_LIFE)，默认 69 天）
- 三阈值状态转换（Active→Stale / Stale→Archived）
- S-10 见证豁免（is_identity 不进入评估）
- is_structure 豁免（=2 完全不参与 / =1 跳过记录）
- 遗忘候选队列入队
- 潜伏势能重估（TC-F02-001：重估保留或归档）
- 复兴（TC-F03-001：Archived→Active，含匹配验证）
- 降级契约 skip_forgetting（§10.17）
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from src.errors import NotFoundError, SecurityRedlineError
from src.storage.forgetting import ForgettingScheduler, evaluate_freshness
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.models import Memory, utc_now

pytestmark = pytest.mark.unit


@pytest.fixture
async def setup(memory_db) -> tuple[MemoryStore, ForgettingScheduler]:
    store = MemoryStore(memory_db)
    scheduler = ForgettingScheduler(memory_db)
    return store, scheduler


def _past_iso(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


async def _write_aged(store: MemoryStore, days_ago: float, **kw) -> str:
    """写入记忆并回拨 last_access_at（模拟长期未访问）。"""
    result = await store.create(
        MemoryWriteInput(
            path="kairos://_user/u1/memories/",
            content="遗忘测试记忆内容，长度足够用于评估。",
            provenance="user_input",
            **kw,
        )
    )
    async with store.db.session() as session:
        memory = await session.get(Memory, result.id)
        assert memory is not None
        memory.last_access_at = _past_iso(days_ago)
        await session.commit()
    return result.id


class TestFreshnessFormula:
    def test_zero_days_freshness_one(self) -> None:
        assert evaluate_freshness(utc_now()) == pytest.approx(1.0)

    def test_half_life_days_freshness_half(self) -> None:
        """69 天 → freshness = 0.5（半衰期定义）。"""
        assert evaluate_freshness(_past_iso(69)) == pytest.approx(0.5, abs=0.01)

    def test_ten_days_above_active(self) -> None:
        assert evaluate_freshness(_past_iso(10)) > 0.3  # active 区间

    def test_never_accessed_zero(self) -> None:
        assert evaluate_freshness(None) == 0.0


class TestScanTransitions:
    async def test_stale_transition(self, setup) -> None:
        """Active→Stale：freshness 落入 [0.1, 0.3)（约 120-229 天）。"""
        store, scheduler = setup
        await _write_aged(store, 150)
        decisions = await scheduler.scan()
        stale = [d for d in decisions if d.action == "stale"]
        assert len(stale) == 1
        async with store.db.session() as session:
            from sqlalchemy import select

            memory = (await session.execute(select(Memory))).scalars().first()
            assert memory is not None and memory.status == "stale"

    async def test_archive_transition(self, setup) -> None:
        """Stale→Archived：freshness < 0.1（约 >229 天）。"""
        store, scheduler = setup
        await _write_aged(store, 365)
        decisions = await scheduler.scan()
        archived = [d for d in decisions if d.action == "archive"]
        assert len(archived) == 1
        async with store.db.session() as session:
            from sqlalchemy import select

            memory = (await session.execute(select(Memory))).scalars().first()
            assert memory is not None and memory.status == "archived"

    async def test_fresh_memory_untouched(self, setup) -> None:
        store, scheduler = setup
        await _write_aged(store, 1)
        decisions = await scheduler.scan()
        assert all(d.action == "none" for d in decisions)
        async with store.db.session() as session:
            from sqlalchemy import select

            memory = (await session.execute(select(Memory))).scalars().first()
            assert memory is not None and memory.status == "active"

    async def test_identity_exempt_from_forgetting(self, setup) -> None:
        """S-10 见证豁免：is_identity=true 记忆不进入遗忘评估。"""
        store, scheduler = setup
        mid = await _write_aged(store, 400)
        async with store.db.session() as session:
            memory = await session.get(Memory, mid)
            assert memory is not None
            memory.is_identity = 1
            memory.identity_confidence = 0.9
            await session.commit()
        decisions = await scheduler.scan()
        exempt = [d for d in decisions if d.memory_id == mid]
        assert len(exempt) == 1 and exempt[0].action == "skip_identity"

    async def test_structure_exempt(self, setup) -> None:
        """is_structure=true 完全不参与；structural_value=1 跳过评估留痕。"""
        store, scheduler = setup
        mid = await _write_aged(store, 400)
        async with store.db.session() as session:
            memory = await session.get(Memory, mid)
            assert memory is not None
            memory.is_structure = 1
            memory.structural_value = 2
            await session.commit()
        decisions = await scheduler.scan()
        assert [d for d in decisions if d.memory_id == mid][0].action == "skip_structure"

    async def test_forgetting_queue_recorded(self, setup) -> None:
        """遗忘候选进入 forgetting_queue（pending_archive）。"""
        store, scheduler = setup
        await _write_aged(store, 365)
        await scheduler.scan()
        async with store.db.session() as session:
            from src.storage.models import ForgettingQueue

            rows = (await session.execute(select(ForgettingQueue))).scalars().all()
            assert len(rows) == 1
            assert rows[0].status == "pending_archive"


class TestLatentReevaluation:
    async def test_trigger_keeps_candidate(self, setup) -> None:
        """TC-F02-001：潜伏重估——命中触发目标 → 保留（复兴候选）。"""
        store, scheduler = setup
        mid = await _write_aged(store, 400)
        await scheduler.scan()  # 先归档
        result = await scheduler.reevaluate_latent(trigger_memory_id=mid)
        assert result["revival_candidates"] >= 1

    async def test_untouched_stays_archived(self, setup) -> None:
        """非触发目标保持归档（语义孤岛保留策略——竖切内不物理删除）。"""
        store, scheduler = setup
        await _write_aged(store, 400)
        await scheduler.scan()
        result = await scheduler.reevaluate_latent(trigger_memory_id=None)
        assert result["revival_candidates"] == 0  # 无触发目标


class TestRevival:
    async def test_revive_archived_to_active(self, setup) -> None:
        """TC-F03-001：复兴（Archived→Active），回归可用状态。"""
        store, scheduler = setup
        mid = await _write_aged(store, 400)
        await scheduler.scan()
        result = await scheduler.revive(mid)
        assert result["status"] == "active"
        async with store.db.session() as session:
            memory = await session.get(Memory, mid)
            assert memory is not None and memory.status == "active"

    async def test_revive_rejects_non_archived(self, setup) -> None:
        store, scheduler = setup
        mid = await _write_aged(store, 1)
        with pytest.raises(NotFoundError):
            await scheduler.revive(mid)  # active 状态不可复兴

    async def test_revive_match_validation(self, setup) -> None:
        """复兴匹配验证：语义向量与盲区方向余弦 < 阈值 → 拒绝。"""
        store, scheduler = setup
        mid = await _write_aged(store, 400)
        await scheduler.scan()
        # 无嵌入的记忆复兴带上下文向量 → 拒绝（无语义向量）
        with pytest.raises(SecurityRedlineError):
            await scheduler.revive(mid, context_vector=[0.0] * 1536)
