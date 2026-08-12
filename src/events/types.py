"""事件类型定义（竖切 4 类）。

权威源：架构 §10.10 事件枚举与流控（全量 10 类，竖切首迭代 4 类）。
其余 6 类（intention_activate / intention_resolve / affective_boost /
exploration_budget / attention_allocation / sublimation_tick）待对应组件
启用时按 §10.6 注册门禁实现。

事件标准格式（架构 §10.10）：
  event_id: uuid, event_type, source_layer, target, payload, trace_id: uuid,
  timestamp: int64 纳秒, priority: 0-9（0=最高校准信号，9=最低升华探针）

优先级语义（竖切 4 类）：
  0 = calibration_signal / degradation_switch（不被背压阻塞，直接插入队列头部）
  3 = use_event（常规使用事件）
  6 = latent_trigger（空闲驱动）
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

# 竖切首迭代事件类型（架构 §10.10；usage_events.event_type 应用层校验枚举）
USE_EVENT = "use_event"
CALIBRATION_SIGNAL = "calibration_signal"
DEGRADATION_SWITCH = "degradation_switch"
LATENT_TRIGGER = "latent_trigger"

SLICE_EVENT_TYPES: tuple[str, ...] = (
    USE_EVENT,
    CALIBRATION_SIGNAL,
    DEGRADATION_SWITCH,
    LATENT_TRIGGER,
)

# 优先级（0-9；0=最高校准信号，9=最低升华探针）
PRIORITY_CALIBRATION = 0
PRIORITY_DEGRADATION = 0
PRIORITY_USE_EVENT = 3
PRIORITY_LATENT_TRIGGER = 6

# 背压豁免线：优先级 ≤ 2 的事件不被背压阻塞（架构 §10.10）
BACKPRESSURE_EXEMPT_MAX = 2

# 背压丢弃线：优先级 ≥ 7 的事件超限时优先丢弃（架构 §10.10）
BACKPRESSURE_DROP_MIN = 7


@dataclass(frozen=True)
class Event:
    """总线事件（标准格式，架构 §10.10）。"""

    event_type: str
    source_layer: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = PRIORITY_USE_EVENT
    memory_id: str | None = None
    trace_id: str | None = None
    target: str = "broadcast"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def with_trace(self, trace_id: str | None) -> Event:
        """注入 trace_id（全链路可审计）。"""
        return Event(
            event_type=self.event_type,
            source_layer=self.source_layer,
            payload=self.payload,
            priority=self.priority,
            memory_id=self.memory_id,
            trace_id=trace_id or self.trace_id,
            target=self.target,
            event_id=self.event_id,
        )


# 订阅者处理器：async (Event) -> None
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]
