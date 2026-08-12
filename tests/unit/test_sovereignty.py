"""宪法主权面单元测试（TC-CAL01-001 / TC-CAL03-001 / TC-CAL04-001）。

覆盖：
- 外部校准（CAL-01）：写入见证锚定 + S-11 审计 + 分数域校验
- 强制冻结/解冻（CAL-03）：admin 鉴权、到期自动解冻语义、写操作拒绝
- 降级状态机（CAL-04）：三模式自动切换（校准时延驱动）+ 显式切换
- 校准恢复 → 正常态（E2E-04 语义）
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.errors import AdminRequiredError, SecurityRedlineError
from src.sovereignty.calibration import CalibrationPort
from src.sovereignty.degradation import (
    MODE_CONSERVATIVE_SILENT,
    MODE_NORMAL,
    MODE_SAFE_HIBERNATION,
    DegradationStateMachine,
)
from src.sovereignty.freeze import FreezePort
from src.storage.dual_copy import DualCopyManager
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.models import utc_now
from src.supervision.audit_tribunal import AuditTribunal

pytestmark = pytest.mark.unit

HMAC_KEY = "22" * 32


@pytest.fixture
async def setup(memory_db) -> tuple[MemoryStore, AuditTribunal]:
    store = MemoryStore(memory_db)
    tribunal = AuditTribunal(memory_db, hmac_key=HMAC_KEY)
    return store, tribunal


async def _seed(store: MemoryStore) -> str:
    result = await store.create(
        MemoryWriteInput(
            path="kairos://_user/u1/memories/",
            content="主权面测试记忆内容，长度足够用于评估。",
            provenance="user_input",
        )
    )
    return result.id


class TestCalibration:
    async def test_calibrate_updates_witness(self, setup) -> None:
        """TC-CAL01-001：外部校准 → 见证锚定分数更新 + 审计留痕。"""
        store, tribunal = setup
        mid = await _seed(store)
        port = CalibrationPort(store.db, tribunal)
        result = await port.calibrate(
            memory_id=mid, narrative_coherence_score=0.85, source="user_review"
        )
        assert result["status"] == "accepted"
        copies = DualCopyManager(store.db)
        witness = await copies.read_witness(mid)
        assert witness["narrative_coherence_score"] == 0.85
        # S-11 审计留痕
        verify = await tribunal.verify_chain()
        assert verify["chain_valid"] is True

    async def test_calibrate_score_range(self, setup) -> None:
        store, tribunal = setup
        mid = await _seed(store)
        port = CalibrationPort(store.db, tribunal)
        with pytest.raises(SecurityRedlineError):
            await port.calibrate(memory_id=mid, narrative_coherence_score=1.5, source="x")

    async def test_calibrate_missing_fields(self, setup) -> None:
        _store, tribunal = setup
        port = CalibrationPort(_store.db, tribunal)
        with pytest.raises(SecurityRedlineError):
            await port.calibrate(memory_id="", narrative_coherence_score=0.5, source="")


class TestFreeze:
    async def test_freeze_blocks_writes(self, setup) -> None:
        """TC-CAL03-001：冻结期间写操作一律拒绝（FreezeGuard）。"""
        store, tribunal = setup
        port = FreezePort(store.db, tribunal)
        await port.freeze(duration_seconds=300)
        assert await port.guard.is_frozen() is True
        with pytest.raises(SecurityRedlineError, match="冻结"):
            await port.guard.check()

    async def test_unfreeze_allows_writes(self, setup) -> None:
        store, tribunal = setup
        port = FreezePort(store.db, tribunal)
        await port.freeze(duration_seconds=300)
        await port.unfreeze()
        assert await port.guard.is_frozen() is False
        await port.guard.check()  # 不抛异常

    async def test_freeze_expires_automatically(self, setup) -> None:
        """到期自动解冻语义（freeze_until 过期 → is_frozen=False）。"""
        store, tribunal = setup
        port = FreezePort(store.db, tribunal)
        # 写一个已过期的冻结标记
        from sqlalchemy import text

        past = (datetime.now(UTC) - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[
            :-3
        ] + "Z"
        async with store.db.session() as session:
            await session.execute(
                text(
                    "INSERT OR REPLACE INTO config (key, value, scope) "
                    "VALUES ('kairos.sovereignty.freeze_until', :v, 'override')"
                ),
                {"v": past},
            )
            await session.commit()
        assert await port.guard.is_frozen() is False

    async def test_freeze_requires_admin(self, setup) -> None:
        store, tribunal = setup
        port = FreezePort(store.db, tribunal)
        with pytest.raises(AdminRequiredError):
            await port.freeze(duration_seconds=300, operator="read")


class TestDegradationMachine:
    async def test_normal_with_recent_calibration(self, setup) -> None:
        """校准恢复 → 正常态（E2E-04 语义）。"""
        _store, _tribunal = setup
        machine = DegradationStateMachine(_store.db, period_n=50, period_m=200, cycle_seconds=300)
        mode = await machine.tick(last_calibration_at=utc_now())
        assert mode == MODE_NORMAL

    async def test_conservative_silent_after_n_cycles(self, setup) -> None:
        """中断 ≥N 周期 → 保守静默。"""
        _store, _tribunal = setup
        machine = DegradationStateMachine(_store.db, period_n=5, period_m=10, cycle_seconds=1)
        past = (datetime.now(UTC) - timedelta(seconds=7)).strftime("%Y-%m-%dT%H:%M:%S.%f")[
            :-3
        ] + "Z"
        mode = await machine.tick(last_calibration_at=past)
        assert mode == MODE_CONSERVATIVE_SILENT

    async def test_safe_hibernation_after_m_cycles(self, setup) -> None:
        """中断 ≥M 周期 → 安全休眠。"""
        _store, _tribunal = setup
        machine = DegradationStateMachine(_store.db, period_n=5, period_m=10, cycle_seconds=1)
        past = (datetime.now(UTC) - timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%S.%f")[
            :-3
        ] + "Z"
        mode = await machine.tick(last_calibration_at=past)
        assert mode == MODE_SAFE_HIBERNATION

    async def test_no_calibration_ever_hibernates(self, setup) -> None:
        """从未校准 → 安全休眠（降级安全侧）。"""
        _store, _tribunal = setup
        machine = DegradationStateMachine(_store.db, period_n=5, period_m=10, cycle_seconds=1)
        mode = await machine.tick(last_calibration_at=None)
        assert mode == MODE_SAFE_HIBERNATION

    async def test_explicit_switch(self, setup) -> None:
        """TC-CAL04-001：显式切换（admin）+ 非法模式拒绝 + 非 admin 拒绝。"""
        _store, _tribunal = setup
        machine = DegradationStateMachine(_store.db)
        result = await machine.explicit_switch(MODE_SAFE_HIBERNATION)
        assert result["status"] == "switched"
        assert machine.mode == MODE_SAFE_HIBERNATION
        with pytest.raises(SecurityRedlineError):
            await machine.explicit_switch("illegal_mode")
        with pytest.raises(AdminRequiredError):
            await machine.explicit_switch(MODE_NORMAL, operator="read")

    async def test_recovery_after_calibration(self, setup) -> None:
        """校准恢复 → 状态机回正常态（无需逆向遍历）。"""
        _store, _tribunal = setup
        machine = DegradationStateMachine(_store.db, period_n=5, period_m=10, cycle_seconds=1)
        past = (datetime.now(UTC) - timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%S.%f")[
            :-3
        ] + "Z"
        assert await machine.tick(last_calibration_at=past) == MODE_SAFE_HIBERNATION
        # 校准恢复（最近校准）
        assert await machine.tick(last_calibration_at=utc_now()) == MODE_NORMAL
