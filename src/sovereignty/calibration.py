"""外部校准端口（竖切组件 8）——POST /v1/calibrate（CAL-01）。

权威规格：
- 架构 §1.2 外部校准端口（宪法修订唯一入口，S-11：元认知自校准不可修改
  宪法级偏好）
- 架构 §5.2 见证锚定（narrative_coherence_score 仅由外部校准/再巩固环更新，
  S-14 语境自指禁令）
- api-spec §1.7 POST /v1/calibrate（memory_id + narrative_coherence_score + source）

校准事件写入事件总线（calibration_signal，priority=0）——降级状态机据此
感知校准恢复（校准时延驱动）。
"""

from __future__ import annotations

from typing import Any

from src.errors import SecurityRedlineError
from src.events.types import CALIBRATION_SIGNAL, PRIORITY_CALIBRATION
from src.storage.db import Database
from src.storage.dual_copy import DualCopyManager
from src.supervision.audit_tribunal import AuditTribunal


class CalibrationPort:
    """外部校准端口（S-11 宪法修订唯一入口）。"""

    def __init__(
        self,
        db: Database,
        tribunal: AuditTribunal,
        bus: Any | None = None,
    ) -> None:
        self.db = db
        self.tribunal = tribunal
        self.bus = bus  # 事件总线（calibration_signal 发布；W9 组装注入）

    async def calibrate(
        self,
        *,
        memory_id: str,
        narrative_coherence_score: float,
        source: str,
        operator: str = "admin",
    ) -> dict[str, Any]:
        """接收外部校准信号（CAL-01）。

        - 分数域校验 [0,1]（非法拒绝 422 语义）
        - 写入见证锚定主副本（S-14：仅外部校准可写）
        - 审计留痕（校准为宪法级操作）
        - 发布 calibration_signal（priority=0，降级状态机消费）
        """
        if not 0 <= narrative_coherence_score <= 1:
            raise SecurityRedlineError(
                f"narrative_coherence_score 必须在 [0,1] 区间: {narrative_coherence_score}"
            )
        if not memory_id or not source:
            raise SecurityRedlineError("缺少必填字段: memory_id / source（CAL-01）")

        copies = DualCopyManager(self.db)
        result = await copies.update_witness(
            memory_id,
            narrative_coherence_score=narrative_coherence_score,
            operator="calibration",
        )

        # 审计留痕（校准操作）
        await self.tribunal.record(
            operator=operator,
            action="external_calibration",
            target_type="memory",
            target_id=memory_id,
            details={"score": narrative_coherence_score, "source": source},
            redline_id="S-11",
        )

        # 事件总线通知（降级状态机据此复位校准时延）
        if self.bus is not None:
            await self.bus.publish(
                CALIBRATION_SIGNAL,
                "sovereignty",
                payload={"memory_id": memory_id, "score": narrative_coherence_score},
                priority=PRIORITY_CALIBRATION,
            )

        return {
            "status": "accepted",
            "memory_id": memory_id,
            "previous_score": result["narrative_coherence_score"],
            "new_score": narrative_coherence_score,
        }

    async def last_calibration_at(self) -> str | None:
        """最近一次外部校准时间（降级状态机校准时延依据）。"""
        async with self.db.session() as session:
            from sqlalchemy import text

            row = (
                await session.execute(text("SELECT MAX(last_calibrated_at) FROM witness_anchor"))
            ).fetchone()
        return row[0] if row and row[0] else None
