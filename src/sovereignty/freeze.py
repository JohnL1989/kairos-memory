"""强制冻结/解冻（竖切组件 8）——POST /v1/freeze / POST /v1/unfreeze（CAL-03）。

权威规格：
- 架构 §1.2 强制冻结机制（冻结所有内部环，到期自动解冻）
- 架构 §10.9 安全休眠态执行路径（冻结为宪法主权面至高权限）
- api-spec §1.7（duration_seconds + scope；冻结/解冻事件写入审计日志）
- 冻结优先级高于记忆级锁定（api-spec §1.3：冻结期间所有写操作一律拒绝）

实现：冻结状态记录于 config 表（scope=override，重启可恢复）；
冻结期间 MemoryStore 写路径经 FreezeGuard 检查拒绝。
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

from sqlalchemy import text

from src.errors import AdminRequiredError, SecurityRedlineError
from src.storage.db import Database
from src.storage.models import utc_now
from src.supervision.audit_tribunal import AuditTribunal

# config 表键（scope=override）
FREEZE_KEY = "kairos.sovereignty.freeze_until"


class FreezeGuard:
    """强制冻结守卫（写操作前置检查；冻结期间所有写操作一律拒绝）。"""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def is_frozen(self) -> bool:
        """冻结中（freeze_until > now）。"""
        async with self.db.session() as session:
            row = (
                await session.execute(
                    text("SELECT value FROM config WHERE key = :k"), {"k": FREEZE_KEY}
                )
            ).fetchone()
        if row is None or not row[0]:
            return False
        try:
            from datetime import datetime

            frozen_until = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            return frozen_until > datetime.now(UTC)
        except ValueError:
            return False

    async def check(self) -> None:
        """写操作前检查（S 级：冻结期间拒绝，SecurityRedlineError）。"""
        if await self.is_frozen():
            raise SecurityRedlineError("系统处于强制冻结状态，所有写操作拒绝（CAL-03）")


class FreezePort:
    """强制冻结/解冻端口（CAL-03，admin Key）。"""

    def __init__(self, db: Database, tribunal: AuditTribunal) -> None:
        self.db = db
        self.tribunal = tribunal
        self.guard = FreezeGuard(db)

    async def freeze(self, duration_seconds: int, *, operator: str = "admin") -> dict[str, Any]:
        """强制冻结（到期自动解冻）。"""
        if operator != "admin":
            raise AdminRequiredError("强制冻结需 admin Key（CAL-03）")
        if duration_seconds <= 0:
            raise SecurityRedlineError(f"冻结时长必须为正: {duration_seconds}")
        from datetime import datetime, timedelta

        frozen_until = (datetime.now(UTC) + timedelta(seconds=duration_seconds)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"
        async with self.db.session() as session:
            await session.execute(
                text(
                    "INSERT OR REPLACE INTO config (key, value, scope, updated_at, updated_by) "
                    "VALUES (:k, :v, 'override', :ts, :by)"
                ),
                {"k": FREEZE_KEY, "v": frozen_until, "ts": utc_now(), "by": operator},
            )
            await session.commit()
        await self.tribunal.record(
            operator=operator,
            action="freeze",
            target_type="config",
            target_id=FREEZE_KEY,
            details={"duration_seconds": duration_seconds, "frozen_until": frozen_until},
            redline_id="S-16",
        )
        return {"status": "frozen", "frozen_until": frozen_until}

    async def unfreeze(self, *, operator: str = "admin") -> dict[str, Any]:
        """解冻（清除冻结标记）。"""
        if operator != "admin":
            raise AdminRequiredError("解冻需 admin Key（CAL-03）")
        async with self.db.session() as session:
            await session.execute(text("DELETE FROM config WHERE key = :k"), {"k": FREEZE_KEY})
            await session.commit()
        await self.tribunal.record(
            operator=operator,
            action="unfreeze",
            target_type="config",
            target_id=FREEZE_KEY,
            details={},
            redline_id="S-16",
        )
        return {"status": "unfrozen"}
