"""事件订阅者（首迭代接线）——use_event → 影子副本更新 + 访问刷新。

架构 §10.10：use_event 提交（影子副本、权重、审计依赖）——订阅者将
使用事件应用到 usage_weight 影子副本（最终一致，S-14：永不写回见证锚定）；
并同步刷新 memories.last_access_at（forgetting.py 声明「显式检索仅更新
last_access_at，不直接触发状态复兴」的实现落点）。
"""

from __future__ import annotations

from sqlalchemy import update

from src.events.types import Event
from src.storage.db import Database
from src.storage.dual_copy import DualCopyManager, UsageDelta
from src.storage.models import Memory


class UsageEventSubscriber:
    """use_event 订阅者：应用使用事件增量到影子副本。"""

    def __init__(self, db: Database) -> None:
        self.db = db
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
        # 访问刷新：显式检索/写入刷新 last_access_at（遗忘调度器 freshness
        # 依据；forgetting.py 声明语义落点，防记忆只减不增）
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        async with self.db.session() as session:
            await session.execute(
                update(Memory)
                .where(Memory.id == event.memory_id)
                .values(last_access_at=now)
            )
            await session.commit()  # 缺 commit 则 async with 退出回滚，刷新不落库
