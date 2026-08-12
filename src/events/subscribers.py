"""事件订阅者（首迭代接线）——use_event → 影子副本更新。

架构 §10.10：use_event 提交（影子副本、权重、审计依赖）——订阅者将
使用事件应用到 usage_weight 影子副本（最终一致，S-14：永不写回见证锚定）。
"""

from __future__ import annotations

from src.events.types import Event
from src.storage.db import Database
from src.storage.dual_copy import DualCopyManager, UsageDelta


class UsageEventSubscriber:
    """use_event 订阅者：应用使用事件增量到影子副本。"""

    def __init__(self, db: Database) -> None:
        self.copies = DualCopyManager(db)

    async def handle(self, event: Event) -> None:
        """处理 use_event（memory_id 为空时跳过；未知记忆跳过不阻断总线）。"""
        if event.event_type != "use_event" or not event.memory_id:
            return
        # 影子副本增量：检索/写入各计一次使用（竖切基础口径）
        await self.copies.update_usage(
            event.memory_id,
            UsageDelta(usage_count=1, activation_weight=0.05),
        )
