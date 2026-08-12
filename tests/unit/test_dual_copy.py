"""双副本与 S-14 隔离防线单元测试。

覆盖：
- S-14 语境自指禁令：使用权重永远不能反向写回 witness_anchor /
  narrative_coherence_score（update_usage 无写主副本路径）
- update_witness 仅接受外部校准/宪法端口（operator 校验）
- 差异检验基础版（方向背离 → suspect_flag）
- E2E-09 语义（竖切内 S-14 单测，E2E-09 本体不在竖切 7/9 范围）
"""

from __future__ import annotations

import pytest

from src.errors import NotFoundError, SecurityRedlineError
from src.storage.dual_copy import DualCopyManager, UsageDelta
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.models import UsageWeight, WitnessAnchor

pytestmark = pytest.mark.unit


@pytest.fixture
async def setup(memory_db) -> tuple[MemoryStore, DualCopyManager, str]:
    store = MemoryStore(memory_db)
    copies = DualCopyManager(memory_db)
    created = await store.create(
        MemoryWriteInput(
            path="kairos://_user/u1/memories/",
            content="S-14 隔离防线测试记忆内容。",
            provenance="user_input",
        )
    )
    return store, copies, created.id


class TestS14Isolation:
    async def test_usage_never_writes_witness(self, setup) -> None:
        """S-14 核心：使用权重更新后见证锚定保持不变。"""
        _store, copies, memory_id = setup
        async with copies.db.session() as session:
            before = await session.get(WitnessAnchor, memory_id)
            assert before is not None
            before_score = before.narrative_coherence_score

        # 大量使用事件（影子副本侧升温）
        for _ in range(10):
            await copies.update_usage(
                memory_id,
                UsageDelta(usage_count=5, activation_weight=0.3, use_load_retrieval=0.8),
            )

        async with copies.db.session() as session:
            weight = await session.get(UsageWeight, memory_id)
            anchor = await session.get(WitnessAnchor, memory_id)
            assert weight is not None and weight.usage_count == 50
            assert anchor is not None
            assert anchor.narrative_coherence_score == before_score  # 见证分未被动

    async def test_usage_api_has_no_witness_write_path(self, setup) -> None:
        """S-14 实现级断言：update_usage 函数体（排除 docstring）无写 witness 语句。"""
        import inspect

        from src.storage import dual_copy

        source = inspect.getsource(dual_copy.DualCopyManager.update_usage)
        # 剥离 docstring（首个三引号到匹配结尾）
        if '"""' in source:
            start = source.index('"""') + 3
            end = source.index('"""', start)
            body = source[: source.index('"""')] + source[end + 3 :]
        else:
            body = source
        assert "WitnessAnchor" not in body
        assert "narrative_coherence_score" not in body

    async def test_witness_update_requires_external_operator(self, setup) -> None:
        """S-14 防线：内部组件调用 update_witness 被拒绝。"""
        _store, copies, memory_id = setup
        with pytest.raises(SecurityRedlineError, match="S-14"):
            await copies.update_witness(
                memory_id,
                narrative_coherence_score=0.9,
                operator="internal_usage",  # 内部信号伪装
            )

    async def test_witness_update_by_calibration_allowed(self, setup) -> None:
        """外部校准（operator=calibration）可更新见证锚定。"""
        _store, copies, memory_id = setup
        result = await copies.update_witness(
            memory_id, narrative_coherence_score=0.85, operator="calibration"
        )
        assert result["narrative_coherence_score"] == 0.85
        assert result["calibration_count"] == 1


class TestDualCopy:
    async def test_usage_accumulates(self, setup) -> None:
        _store, copies, memory_id = setup
        await copies.update_usage(memory_id, UsageDelta(usage_count=2, activation_weight=0.1))
        snap = await copies.read_usage(memory_id)
        assert snap["usage_count"] == 2
        assert snap["activation_weight"] == pytest.approx(0.1)

    async def test_usage_404(self, setup) -> None:
        _store, copies, _memory_id = setup
        with pytest.raises(NotFoundError):
            await copies.read_usage("missing")

    async def test_differential_check_divergence(self, setup) -> None:
        """差异检验：权重升 + 见证分低 → suspect_flag 挂起合并。"""
        _store, copies, memory_id = setup
        # 低见证分（narrative_coherence_score=0.1）+ 高使用
        await copies.update_witness(
            memory_id, narrative_coherence_score=0.1, operator="calibration"
        )
        await copies.update_usage(memory_id, UsageDelta(usage_count=10))
        result = await copies.differential_check(memory_id)
        assert result["blocked"] is True
        assert result["reason"] == "direction_divergence"
        snap = await copies.read_usage(memory_id)
        assert snap["suspect_flag"] is True
