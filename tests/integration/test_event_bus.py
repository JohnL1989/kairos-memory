"""事件总线集成测试（组件 7）——发布/订阅/持久化/背压/优先级/trace_id。

覆盖（slice-implementation-guide 组件 7 验收）：
- 4 类事件发布/订阅/ACK
- usage_events 表持久化（ADR-002 数据库表而非消息队列）
- 背压：优先级 0-2 不被背压阻塞；优先级 7-9 超限丢弃
- trace_id 全链路可审计（query_by_trace）
- 未知事件类型拒绝（类型注册门禁简化，§10.6）
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from src.events.bus import EventBus
from src.events.types import Event
from src.storage.models import UsageEvent

pytestmark = pytest.mark.integration


@pytest.fixture
async def bus(memory_db) -> EventBus:
    return EventBus(memory_db, queue_capacity=4)


class TestPublishSubscribe:
    async def test_publish_subscribe_ack(self, bus: EventBus) -> None:
        """4 类事件全链路：发布 → 订阅者收到（ACK）。"""
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        for event_type in (
            "use_event",
            "calibration_signal",
            "degradation_switch",
            "latent_trigger",
        ):
            bus.subscribe(event_type, handler)

        await bus.publish("use_event", "wm", payload={"usage": 1}, priority=3)
        await bus.publish("calibration_signal", "sovereignty", priority=0)
        await bus.publish("degradation_switch", "sovereignty", priority=0)
        await bus.publish("latent_trigger", "metacognition", priority=6)

        processed = await bus.drain()
        assert processed == 4
        assert [e.event_type for e in received] == [
            "calibration_signal",
            "degradation_switch",
            "use_event",
            "latent_trigger",
        ]  # 高优通道优先

    async def test_publish_persists_to_table(self, bus: EventBus) -> None:
        """usage_events 表持久化（ADR-002）。"""
        await bus.publish("use_event", "storage", priority=3)
        async with bus.db.session() as session:
            count = (await session.execute(select(func.count(UsageEvent.id)))).scalar_one()
            assert count == 1
            event = (await session.execute(select(UsageEvent))).scalars().first()
            assert event is not None
            assert event.event_type == "use_event"
            assert event.source_layer == "storage"
            assert event.memory_id is None
            assert event.severity == 3  # severity 承载优先级

    async def test_unknown_event_type_rejected(self, bus: EventBus) -> None:
        """类型注册门禁（§10.6 简化）：未知事件类型拒绝。"""
        with pytest.raises(ValueError, match="未知事件类型"):
            await bus.publish("exploration_budget", "metacognition")  # 竖切外类型

    async def test_subscriber_error_isolation(self, bus: EventBus) -> None:
        """订阅者异常不阻断总线（错误隔离，层间传播纪律）。"""

        async def bad_handler(event: Event) -> None:
            raise RuntimeError("handler bug")

        bus.subscribe("use_event", bad_handler)
        await bus.publish("use_event", "storage")
        processed = await bus.drain()
        assert processed == 1  # 总线继续工作


class TestBackpressure:
    async def test_low_priority_dropped_when_full(self, bus: EventBus) -> None:
        """背压：队列满时优先级 7-9 事件被丢弃。"""
        # 填满队列（4 条 use_event，priority=3）
        for _ in range(4):
            await bus.publish("use_event", "storage", priority=3)
        # 队列已满，再发一条高优先级（≥7 丢弃）
        await bus.publish("use_event", "storage", priority=9)
        assert bus.dropped_count == 1
        processed = await bus.drain()
        assert processed == 4  # 只处理了 4 条

    async def test_high_priority_never_blocked(self, bus: EventBus) -> None:
        """背压豁免：队列满时优先级 0-2 仍可发布并优先分发。"""
        for _ in range(4):
            await bus.publish("use_event", "storage", priority=3)
        # 校准信号（priority=0）在满队列时仍被受理
        await bus.publish("calibration_signal", "sovereignty", priority=0)
        await bus.publish("calibration_signal", "sovereignty", priority=0)
        processed = await bus.drain()
        assert processed == 6  # 4 常规 + 2 豁免
        assert bus.dropped_count == 0


class TestTraceId:
    async def test_trace_id_auditable(self, bus: EventBus) -> None:
        """trace_id 全链路可审计：跨层事件经同一 trace_id 可查询。"""
        event1 = await bus.publish("calibration_signal", "sovereignty", priority=0)
        await bus.publish(
            "use_event",
            "storage",
            priority=3,
            trace_id=event1.trace_id,  # 同一链路
        )
        events = await bus.query_by_trace(event1.trace_id or "")
        assert len(events) == 2
        assert {e["event_type"] for e in events} == {"calibration_signal", "use_event"}

    async def test_auto_trace_generation(self, bus: EventBus) -> None:
        """未携带 trace_id 时自动生成（全链路可审计底线）。"""
        event = await bus.publish("use_event", "storage")
        assert event.trace_id is not None
        events = await bus.query_by_trace(event.trace_id or "")
        assert len(events) == 1
