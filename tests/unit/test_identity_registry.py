"""身份注册表单元测试（竖切组件 5）——构造论初始赋予 + 双向更新 + 否决权。

覆盖：
- 初始赋予（见证锚定写入触发语义 + 幂等）
- 双向更新：strengthen 提升置信度（可观测）；未赋予记忆拒绝加强
- 降级门槛：无判例拒绝（403 ERR-SEC-001）；有判例执行降级
- S-16 审计留痕（identity_demotion 可追溯，G-03 v0.1.0 判据）
- 使用权重永远无法将 is_identity 置为 false（S-14 一致性）
- S-10 见证豁免数据源（身份记忆清单）
- 否决裁决器（§1.8）：veto_event 阻断写入检查
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from src.errors import NotFoundError, SecurityRedlineError
from src.storage.dual_copy import DualCopyManager, UsageDelta
from src.storage.identity_registry import IdentityRegistry, VetoAdjudicator
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.models import Memory

pytestmark = pytest.mark.unit


@pytest.fixture
async def setup(memory_db) -> tuple[MemoryStore, IdentityRegistry]:
    from src.supervision.audit_tribunal import AuditTribunal

    store = MemoryStore(memory_db)
    # 测试环境审计 HMAC 密钥（conftest 注入固定测试值）
    tribunal = AuditTribunal(memory_db, hmac_key="22" * 32)
    registry = IdentityRegistry(memory_db, tribunal=tribunal)
    return store, registry


async def _write(store: MemoryStore, **kw) -> str:
    result = await store.create(
        MemoryWriteInput(
            path="kairos://_user/u1/core/",
            content="身份测试记忆内容，长度足够用于评估。",
            provenance="user_input",
            **kw,
        )
    )
    return result.id


class TestInitialGrant:
    async def test_grant_sets_identity(self, setup) -> None:
        """初始赋予：is_identity=1 + 置信度 + 审查计数。"""
        store, registry = setup
        mid = await _write(store)
        result = await registry.grant_initial_identity(mid)
        assert result["is_identity"] is True
        snap = await registry.get_identity(mid)
        assert snap["is_identity"] is True
        assert snap["identity_confidence"] == 0.6
        assert snap["identity_review_count"] == 1

    async def test_grant_idempotent(self, setup) -> None:
        """重复赋予幂等：置信度取最大值钳制，不重置。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid, confidence=0.6)
        await registry.grant_initial_identity(mid, confidence=0.9)
        snap = await registry.get_identity(mid)
        assert snap["identity_confidence"] == 0.9
        await registry.grant_initial_identity(mid, confidence=0.5)
        snap = await registry.get_identity(mid)
        assert snap["identity_confidence"] == 0.9  # 不降（max 钳制）

    async def test_grant_404(self, setup) -> None:
        _store, registry = setup
        with pytest.raises(NotFoundError):
            await registry.grant_initial_identity("missing")


class TestBidirectionalUpdate:
    async def test_strengthen_raises_confidence(self, setup) -> None:
        """双向更新（加强）：自洽度结构性上升 → 置信度提升（G-03 可观测）。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid, confidence=0.6)
        for _ in range(3):
            await registry.strengthen(mid)
        snap = await registry.get_identity(mid)
        assert snap["identity_confidence"] == pytest.approx(0.9)

    async def test_strengthen_requires_identity(self, setup) -> None:
        """未赋予身份的记忆拒绝加强（身份仅经见证锚定初始赋予）。"""
        store, registry = setup
        mid = await _write(store)
        with pytest.raises(SecurityRedlineError):
            await registry.strengthen(mid)

    async def test_usage_never_resets_identity(self, setup) -> None:
        """使用权重永远无法将 is_identity 置为 false（S-14 一致性）。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid)
        copies = DualCopyManager(store.db)
        for _ in range(5):
            await copies.update_usage(mid, UsageDelta(usage_count=10, activation_weight=0.5))
        snap = await registry.get_identity(mid)
        assert snap["is_identity"] is True  # 影子副本升温不影响身份标志


class TestDemotion:
    async def test_demotion_requires_case(self, setup) -> None:
        """降级门槛：无判例（case_id）→ 403 ERR-SEC-001。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid)
        with pytest.raises(SecurityRedlineError, match="判例"):
            await registry.demote(mid, case_id="")

    async def test_demotion_with_case_and_audit(self, setup) -> None:
        """有判例降级：移除标志 + 审计 identity_demotion 留痕（G-03 审计可追溯）。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid, confidence=0.8)
        result = await registry.demote(mid, case_id="case-001", narrative_trend="declining")
        assert result["is_identity"] is False
        snap = await registry.get_identity(mid)
        assert snap["is_identity"] is False
        assert snap["identity_confidence"] == 0.5  # 复位
        # 审计可追溯（S-16：未留痕的降级视为未执行）
        async with store.db.session() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT action, redline_id, details FROM audit_log "
                        "WHERE target_id = :id AND action = 'identity_demotion'"
                    ),
                    {"id": mid},
                )
            ).fetchone()
            assert row is not None
            assert row[0] == "identity_demotion"
            assert row[1] == "S-16"
            assert "case-001" in row[2]

    async def test_demote_does_not_delete_memory(self, setup) -> None:
        """降级不删除记忆（架构 §5.2：降级仅移除标志）。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid)
        await registry.demote(mid, case_id="case-002")
        async with store.db.session() as session:
            memory = await session.get(Memory, mid)
            assert memory is not None and memory.is_deleted == 0


class TestWitnessExemption:
    async def test_identity_list(self, setup) -> None:
        """S-10 见证豁免数据源：身份记忆清单（遗忘调度器评估用）。"""
        store, registry = setup
        mid = await _write(store)
        await registry.grant_initial_identity(mid)
        identities = await registry.list_identity_memories()
        assert any(i["id"] == mid for i in identities)


class TestVetoAdjudicator:
    async def test_veto_blocks_write(self, setup) -> None:
        """§1.8：veto_event 命中 → 写入阻断（存储层写入路径最后检查点）。"""
        _store, _registry = setup
        adjudicator = VetoAdjudicator()
        adjudicator.inject_veto("commit-1", reason="威胁身份记忆叙事连续性")
        veto = adjudicator.check("commit-1")
        assert veto is not None
        assert veto["source"] == "identity_listener"
        assert veto["severity"] == "block"

    async def test_no_veto_allows_write(self, setup) -> None:
        _store, _registry = setup
        adjudicator = VetoAdjudicator()
        assert adjudicator.check("commit-2") is None  # 放行

    async def test_resolve_clears_event(self, setup) -> None:
        _store, _registry = setup
        adjudicator = VetoAdjudicator()
        adjudicator.inject_veto("commit-3", reason="r")
        adjudicator.resolve("commit-3")
        assert adjudicator.check("commit-3") is None
