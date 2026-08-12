"""记忆 CRUD 单元测试（TC-W01-001~003 / TC-W04-001 / TC-W07-001 语义）。

覆盖：写入（路径/来源/契约校验、捕获门控、幂等键）、读取、更新（乐观锁+
版本链）、删除（契约分支）、列表、锁定拒绝（ERR-CTR-003）。
"""

from __future__ import annotations

from datetime import UTC

import pytest

from src.access.ingestion import IngestionGate
from src.errors import (
    IdempotencyConflictError,
    IntentionNotClosedError,
    InvalidPathError,
    LockedMemoryError,
    MissingFieldError,
    NotFoundError,
    PathDepthError,
    SecurityRedlineError,
    VersionConflictError,
)
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.models import Memory, MemoryState, UsageWeight, WitnessAnchor, utc_now

pytestmark = pytest.mark.unit


@pytest.fixture
async def store(memory_db) -> MemoryStore:
    return MemoryStore(memory_db, gate=IngestionGate())


def _input(**overrides) -> MemoryWriteInput:
    base: dict = {
        "path": "kairos://_user/u1/memories/",
        "content": "这是一个正常的记忆内容，用于单元测试。",
        "provenance": "user_input",
    }
    base.update(overrides)
    return MemoryWriteInput(**base)


class TestWrite:
    async def test_create_success(self, store: MemoryStore) -> None:
        """TC-W01-001 语义：路径+内容 → 返回 id/path/version=1。"""
        result = await store.create(_input())
        assert result.version == 1
        assert result.path.startswith("kairos://")
        assert result.id

    async def test_create_initializes_dual_copies(self, store: MemoryStore) -> None:
        """双副本初始化：witness_anchor + usage_weight 随写入创建。"""
        result = await store.create(_input())
        async with store.db.session() as session:
            anchor = await session.get(WitnessAnchor, result.id)
            weight = await session.get(UsageWeight, result.id)
            assert anchor is not None and anchor.narrative_coherence_score == 0.0
            assert weight is not None and weight.usage_count == 0

    async def test_create_records_state_trace(self, store: MemoryStore) -> None:
        """状态轨迹：initial_write 留痕（memory_states）。"""
        result = await store.create(_input())
        async with store.db.session() as session:
            from sqlalchemy import select

            states = (
                (
                    await session.execute(
                        select(MemoryState).where(MemoryState.memory_id == result.id)
                    )
                )
                .scalars()
                .all()
            )
            assert any(s.reason == "initial_write" and s.state == "active" for s in states)

    async def test_path_must_be_kairos(self, store: MemoryStore) -> None:
        """ERR-INPUT-002：路径非 kairos:// 开头。"""
        with pytest.raises(InvalidPathError):
            await store.create(_input(path="http://example.com/x"))

    async def test_path_depth_limit(self, store: MemoryStore) -> None:
        """ERR-INPUT-003：路径深度 >10 层。"""
        deep = "kairos://" + "/".join(["seg"] * 12) + "/"
        with pytest.raises(PathDepthError):
            await store.create(_input(path=deep))

    async def test_provenance_required(self, store: MemoryStore) -> None:
        """S-15：provenance 缺失 → 422 MissingFieldError。"""
        with pytest.raises(MissingFieldError):
            await store.create(_input(provenance=""))

    async def test_contract_enum(self, store: MemoryStore) -> None:
        with pytest.raises(MissingFieldError):
            await store.create(_input(contract="illegal_contract"))

    async def test_vad_validation(self, store: MemoryStore) -> None:
        """TC-W04-001 前置：非法 VAD 拒绝。"""
        with pytest.raises(MissingFieldError):
            await store.create(_input(vad={"v": 5.0}))
        # 合法 VAD 写入并读取回显
        result = await store.create(_input(vad={"v": 0.5, "a": 0.3, "d": 0.8}))
        detail = await store.get(result.id)
        assert detail["vad"] == {"v": 0.5, "a": 0.3, "d": 0.8}

    async def test_trivial_content_rejected(self, store: MemoryStore) -> None:
        """捕获门控层 1：琐碎文本拒绝写入。"""
        with pytest.raises(MissingFieldError, match="捕获门控"):
            await store.create(_input(content="好的"))

    async def test_secret_content_rejected(self, store: MemoryStore) -> None:
        """TC-W07-001 语义（S-07）：含 api_key= 模式的内容被门禁拒绝。"""
        with pytest.raises(SecurityRedlineError):
            await store.create(_input(content="服务器配置 api_key=sk-abc1234567 请记录"))

    async def test_maintenance_prompt_rejected(self, store: MemoryStore) -> None:
        """捕获门控层 4：维护提示过滤。"""
        with pytest.raises(MissingFieldError, match="捕获门控"):
            await store.create(
                _input(content="Please review the conversation above and reply with ok")
            )

    async def test_content_length_limit(self, store: MemoryStore) -> None:
        """S-03：超过 64KB → ContentTooLongError（413 语义）。"""
        from src.errors import ContentTooLongError

        with pytest.raises(ContentTooLongError):
            await store.create(_input(content="x" * 70000))


class TestIdempotency:
    async def test_same_key_same_payload_returns_first(self, store: MemoryStore) -> None:
        """同键重复提交：不产生新记录，返回首次结果。"""
        first = await store.create(_input(), idempotency_key="key-1")
        second = await store.create(_input(), idempotency_key="key-1")
        assert first.id == second.id
        async with store.db.session() as session:
            from sqlalchemy import select

            count = (
                (await session.execute(select(Memory.id).where(Memory.path == first.path)))
                .scalars()
                .all()
            )
            assert len(count) == 1

    async def test_same_key_diff_payload_conflict(self, store: MemoryStore) -> None:
        """同键异载荷 → 409 ERR-CTR-005。"""
        await store.create(_input(), idempotency_key="key-2")
        with pytest.raises(IdempotencyConflictError):
            await store.create(_input(content="不同内容的记忆内容测试。"), idempotency_key="key-2")


class TestRead:
    async def test_get_success(self, store: MemoryStore) -> None:
        result = await store.create(_input())
        detail = await store.get(result.id)
        assert detail["id"] == result.id
        assert detail["status"] == "active"
        assert detail["contract"] == "ondemand"

    async def test_get_404(self, store: MemoryStore) -> None:
        with pytest.raises(NotFoundError):
            await store.get("no-such-id")

    async def test_get_soft_deleted_404(self, store: MemoryStore) -> None:
        result = await store.create(_input())
        await store.delete(result.id)
        with pytest.raises(NotFoundError):
            await store.get(result.id)


class TestUpdate:
    async def test_update_with_optimistic_lock(self, store: MemoryStore) -> None:
        """TC-W07 语义：If-Match 匹配 → 新版本；版本链追加。"""
        result = await store.create(_input())
        updated = await store.update(
            result.id, if_match_version=1, content="更新后的记忆内容，测试版本链。"
        )
        assert updated["version"] == 2
        assert updated["content"] == "更新后的记忆内容，测试版本链。"
        # 版本链：旧版本 is_latest=0 且 superseded_by 指向新版本
        async with store.db.session() as session:
            old = await session.get(Memory, result.id)
            assert old is not None
            assert old.is_latest == 0
            assert old.next_version_id == updated["id"]

    async def test_update_requires_if_match(self, store: MemoryStore) -> None:
        """乐观锁强制：缺 If-Match → ERR-DB-005。"""
        result = await store.create(_input())
        with pytest.raises(VersionConflictError):
            await store.update(result.id, if_match_version=None, content="x" * 30)

    async def test_update_version_conflict(self, store: MemoryStore) -> None:
        """If-Match 与当前版本不一致 → 409 ERR-DB-005。"""
        result = await store.create(_input())
        with pytest.raises(VersionConflictError):
            await store.update(result.id, if_match_version=99, content="x" * 30)

    async def test_update_locked_rejected(self, store: MemoryStore) -> None:
        """locked_until 未到期 → 403 ERR-CTR-003。"""
        result = await store.create(_input())
        async with store.db.session() as session:
            memory = await session.get(Memory, result.id)
            assert memory is not None
            memory.locked_until = utc_now()  # 立即锁定（now 之后 0 秒仍 > now？用未来时间）

            # 未来 1 小时
            from datetime import datetime, timedelta

            memory.locked_until = (datetime.now(UTC) + timedelta(hours=1)).strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )[:-3] + "Z"
            await session.commit()
        with pytest.raises(LockedMemoryError):
            await store.update(result.id, if_match_version=1, content="x" * 30)


class TestDelete:
    async def test_permanent_rejected(self, store: MemoryStore) -> None:
        """permanent 契约拒删（403 SecurityRedlineError）。"""
        result = await store.create(_input(contract="permanent"))
        with pytest.raises(SecurityRedlineError):
            await store.delete(result.id)

    async def test_intention_rejected(self, store: MemoryStore) -> None:
        """intention 契约未关闭 → 409 ERR-CTR-004。"""
        result = await store.create(_input(contract="intention"))
        with pytest.raises(IntentionNotClosedError):
            await store.delete(result.id)

    async def test_ondemand_soft_delete(self, store: MemoryStore) -> None:
        """ondemand 契约软删除：is_deleted=1，记录保留。"""
        result = await store.create(_input())
        await store.delete(result.id)
        async with store.db.session() as session:
            memory = await session.get(Memory, result.id)
            assert memory is not None and memory.is_deleted == 1

    async def test_temporary_hard_delete(self, store: MemoryStore) -> None:
        """temporary 契约硬删除：记录清除（级联影子副本）。"""
        result = await store.create(_input(contract="temporary"))
        await store.delete(result.id)
        async with store.db.session() as session:
            memory = await session.get(Memory, result.id)
            weight = await session.get(UsageWeight, result.id)
            assert memory is None
            assert weight is None

    async def test_delete_locked_rejected(self, store: MemoryStore) -> None:
        """锁定态拒绝删除（优先于契约分支）。"""
        result = await store.create(_input())
        from datetime import datetime, timedelta

        async with store.db.session() as session:
            memory = await session.get(Memory, result.id)
            assert memory is not None
            memory.locked_until = (datetime.now(UTC) + timedelta(hours=1)).strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )[:-3] + "Z"
            await session.commit()
        with pytest.raises(LockedMemoryError):
            await store.delete(result.id)


class TestList:
    async def test_list_by_path_prefix(self, store: MemoryStore) -> None:
        await store.create(
            _input(path="kairos://_user/u1/memories/", content="记忆甲内容用于测试。")
        )
        await store.create(
            _input(path="kairos://_user/u2/memories/", content="记忆乙内容用于测试。")
        )
        items, total = await store.list(path_prefix="kairos://_user/u1/")
        assert total == 1
        assert items[0]["path"].startswith("kairos://_user/u1/memories/")

    async def test_list_excludes_soft_deleted(self, store: MemoryStore) -> None:
        result = await store.create(_input())
        await store.delete(result.id)
        _items, total = await store.list(path_prefix="kairos://")
        assert total == 0
