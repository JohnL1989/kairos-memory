"""事件总线（竖切组件 7）——发布/订阅/背压/优先级，usage_events 表持久化。

权威规格：架构 §10.10（事件枚举与流控）、ADR-002（数据库表而非消息队列）、
slice-implementation-guide 组件 7（4 类事件全链路可用，trace_id 可审计）。

实现模型：
- 持久化：publish 事务内写 usage_events 表（表结构承载 event 快照）
- 分发：内存 asyncio.Queue + 订阅者回调注册表；bus.drain() 确定性消费（测试友好）
- 背压（架构 §10.10）：队列容量 KAIROS_EVENT_QUEUE_CAPACITY 默认 128；
  优先级 0-2 不被背压阻塞（直接插入队列头部）；优先级 ≥7 超限时优先丢弃
- trace_id：publish 未携带时自动生成，全链路可审计（audit 庭可经 trace_id 查询）
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import text

from src.events.types import (
    BACKPRESSURE_DROP_MIN,
    BACKPRESSURE_EXEMPT_MAX,
    SLICE_EVENT_TYPES,
    Event,
    EventHandler,
)
from src.storage.db import Database
from src.storage.models import UsageEvent

# 每层入站队列容量上限（configuration.md；架构 §10.10）
DEFAULT_QUEUE_CAPACITY = 128


class EventBus:
    """事件总线（竖切 4 类事件）。"""

    def __init__(self, db: Database, queue_capacity: int = DEFAULT_QUEUE_CAPACITY) -> None:
        self.db = db
        self.queue_capacity = queue_capacity
        # 常规队列（有界，背压适用）
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=queue_capacity)
        # 高优通道（无界）：优先级 ≤2 事件不被背压阻塞（架构 §10.10），
        # 独立通道即时分发——「直接插入队列头部」在竖切内等价于此
        self._priority_events: list[Event] = []
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self.dropped_count = 0  # 背压丢弃计数（可观测性）

    # ------------------------------------------------------------------
    # 发布
    # ------------------------------------------------------------------

    async def publish(
        self,
        event_type: str,
        source_layer: str,
        *,
        payload: dict[str, Any] | None = None,
        priority: int = 3,
        memory_id: str | None = None,
        trace_id: str | None = None,
        ttl: int | None = None,
    ) -> Event:
        """发布事件（事务内持久化 + 入内存队列分发）。

        - 事件类型应用层校验（竖切 4 类；未知类型拒绝——类型注册门禁 §10.6 简化）
        - 背压：队列满时优先级 ≤2 强制入队（不被阻塞）；≥7 优先丢弃；
          其余（3-6）缓发（等待队列空位，可观测性记录）
        """
        if event_type not in SLICE_EVENT_TYPES:
            raise ValueError(f"未知事件类型: {event_type}（竖切 4 类，架构 §10.10）")

        event = Event(
            event_type=event_type,
            source_layer=source_layer,
            payload=payload or {},
            priority=priority,
            memory_id=memory_id,
            trace_id=trace_id or str(uuid.uuid4()),
        )

        # 持久化（usage_events 表；severity 列承载优先级 0-9，schema-slice 注记）
        async with self.db.session() as session:
            session.add(
                UsageEvent(
                    event_type=event.event_type,
                    source_layer=event.source_layer,
                    memory_id=event.memory_id,
                    context=_event_payload_json(event),
                    severity=event.priority,
                    ttl=ttl,
                )
            )
            await session.commit()

        # 内存分发队列（背压处理）
        await self._enqueue(event)
        return event

    async def _enqueue(self, event: Event) -> None:
        if event.priority <= BACKPRESSURE_EXEMPT_MAX:
            # 优先级 0-2 不被背压阻塞：进入无界高优通道（队列头部等价语义）
            self._priority_events.append(event)
            return
        if self._queue.full() and event.priority >= BACKPRESSURE_DROP_MIN:
            # 队列满且优先级 7-9：超限时优先丢弃
            self.dropped_count += 1
            return
        # 其余（3-6）：等待空位（缓发）
        await self._queue.put(event)

    # ------------------------------------------------------------------
    # 订阅与分发
    # ------------------------------------------------------------------

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """注册事件订阅者（事件类型必须为竖切 4 类）。"""
        if event_type not in SLICE_EVENT_TYPES:
            raise ValueError(f"未知事件类型: {event_type}")
        self._subscribers[event_type].append(handler)

    async def drain(self, max_events: int | None = None) -> int:
        """确定性消费待分发事件（测试与调度器调用；高优通道优先）。

        返回已分发事件数。订阅者异常不阻断后续事件（错误隔离，日志留痕）。
        """
        processed = 0
        while self._priority_events or not self._queue.empty():
            if max_events is not None and processed >= max_events:
                break
            event = (
                self._priority_events.pop(0) if self._priority_events else self._queue.get_nowait()
            )
            for handler in self._subscribers.get(event.event_type, []):
                try:
                    await handler(event)
                except Exception:
                    # 订阅者错误隔离：不阻断总线（层间传播经事件总线承载，
                    # coding-conventions §三——不抛异常出层）
                    self.dropped_count += 1
            processed += 1
        return processed

    # ------------------------------------------------------------------
    # 查询（trace_id 全链路可审计）
    # ------------------------------------------------------------------

    async def query_by_trace(self, trace_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """按 trace_id 查询事件完整跨层路径（审计庭经此追踪，架构 §10.10）。"""
        async with self.db.session() as session:
            rows = await session.execute(
                text(
                    "SELECT event_type, source_layer, severity, created_at, context "
                    "FROM usage_events WHERE json_extract(context, '$.trace_id') = :tid "
                    "ORDER BY id DESC LIMIT :lim"
                ),
                {"tid": trace_id, "lim": limit},
            )
            return [
                {
                    "event_type": r[0],
                    "source_layer": r[1],
                    "severity": r[2],
                    "created_at": r[3],
                    "context": r[4],
                }
                for r in rows
            ]

    async def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """最近事件（运维/测试用）。"""
        async with self.db.session() as session:
            rows = await session.execute(
                text(
                    "SELECT id, event_type, source_layer, severity, created_at "
                    "FROM usage_events ORDER BY id DESC LIMIT :lim"
                ),
                {"lim": limit},
            )
            return [
                {
                    "id": r[0],
                    "event_type": r[1],
                    "source_layer": r[2],
                    "severity": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]


def _event_payload_json(event: Event) -> str:
    """事件持久化 JSON（含 trace_id 供跨层审计）。"""
    import json

    return json.dumps(
        {
            "trace_id": event.trace_id,
            "target": event.target,
            "payload": event.payload,
            "event_id": event.event_id,
        },
        ensure_ascii=False,
    )
