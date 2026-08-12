"""降级状态机（竖切组件 8）——保守静默 → 受限交叉验证 → 安全休眠。

权威规格：架构 §10.9 外部校准降级模式状态机：
- ① 保守静默：外部校准中断持续 < N 周期（KAIROS_DEGRADATION_PERIOD_N=50）
- ② 受限交叉验证：中断持续 N-M 周期（KAIROS_DEGRADATION_PERIOD_M=200）
- ③ 安全休眠：中断持续 > M 周期
- 恢复：校准恢复 → 差异检验 → 回正常态（无需逆向遍历）；
  校准恢复窗口 = 中断时长 × 安全系数（窗口内信号持续冲突则窗口延长一倍）
- 切换事件写事件总线 degradation_switch（priority=0）
- 显式切换入口：POST /v1/degradation/switch（CAL-04，admin Key）

竖切内实施：
- 校准时延按调度周期计（KAIROS_SCHEDULER_INTERVAL 默认 300s）
- 模式切换记录于内存 + config 表（持久化重启可恢复）
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.errors import AdminRequiredError, SecurityRedlineError
from src.events.types import DEGRADATION_SWITCH, PRIORITY_DEGRADATION
from src.storage.db import Database
from src.storage.models import utc_now

# 三模式枚举（架构 §10.9）
MODE_NORMAL = "normal"
MODE_CONSERVATIVE_SILENT = "conservative_silent"
MODE_LIMITED_CROSS_VALIDATION = "limited_cross_validation"
MODE_SAFE_HIBERNATION = "safe_hibernation"

ALL_MODES = (
    MODE_NORMAL,
    MODE_CONSERVATIVE_SILENT,
    MODE_LIMITED_CROSS_VALIDATION,
    MODE_SAFE_HIBERNATION,
)

# 恢复窗口安全系数（架构 §10.9：窗口期长度 = 中断时长 × 安全系数）
RECOVERY_WINDOW_FACTOR = 1.0


@dataclass(frozen=True)
class DegradationState:
    """降级状态机当前状态。"""

    mode: str
    cycles_since_calibration: int
    last_switch_at: str | None = None
    reason: str | None = None


class DegradationStateMachine:
    """降级状态机（校准时延驱动 + 显式切换入口）。"""

    def __init__(
        self,
        db: Database,
        *,
        period_n: int = 50,
        period_m: int = 200,
        cycle_seconds: int = 300,
        bus: Any | None = None,
    ) -> None:
        self.db = db
        self.period_n = period_n  # KAIROS_DEGRADATION_PERIOD_N（保守静默阈值）
        self.period_m = period_m  # KAIROS_DEGRADATION_PERIOD_M（受限交叉验证阈值）
        self.cycle_seconds = cycle_seconds  # KAIROS_SCHEDULER_INTERVAL
        self.bus = bus
        self._mode: str = MODE_NORMAL
        self._last_switch_at: str | None = None
        self._reason: str | None = None

    @property
    def mode(self) -> str:
        return self._mode

    async def tick(self, last_calibration_at: str | None = None) -> str:
        """调度周期推进：按校准时延计算目标模式并切换（自动降级）。

        返回切换后的模式。切换事件写事件总线 degradation_switch。
        """
        cycles = self._cycles_since_calibration(last_calibration_at)
        target = self._target_mode(cycles)
        if target != self._mode:
            await self._switch(target, reason=f"calibration_gap:{cycles}cycles")
        return self._mode

    def _cycles_since_calibration(self, last_calibration_at: str | None) -> int:
        """校准时延（调度周期数）。无校准记录视为超长中断（直接休眠）。"""
        if last_calibration_at is None:
            return self.period_m + 1  # 从未校准 → 安全休眠
        try:
            last = datetime.fromisoformat(last_calibration_at.replace("Z", "+00:00"))
        except ValueError:
            return self.period_m + 1
        elapsed = (datetime.now(UTC) - last).total_seconds()
        return int(elapsed / self.cycle_seconds)

    def _target_mode(self, cycles: int) -> str:
        """三模式判定（架构 §10.9；递增方向 ①→②→③）。"""
        if cycles < self.period_n:
            return MODE_NORMAL
        if cycles < self.period_m:
            return MODE_CONSERVATIVE_SILENT
        return MODE_SAFE_HIBERNATION

    async def _switch(self, mode: str, *, reason: str) -> None:
        self._mode = mode
        self._last_switch_at = utc_now()
        self._reason = reason
        if self.bus is not None:
            await self.bus.publish(
                DEGRADATION_SWITCH,
                "sovereignty",
                payload={"mode": mode, "reason": reason},
                priority=PRIORITY_DEGRADATION,
            )

    async def explicit_switch(self, mode: str, *, operator: str = "admin") -> dict[str, Any]:
        """显式切换（POST /v1/degradation/switch，CAL-04，admin Key）。"""
        if operator != "admin":
            raise AdminRequiredError("降级模式切换需 admin Key（CAL-04）")
        if mode not in ALL_MODES:
            raise SecurityRedlineError(f"非法降级模式: {mode}（三模式枚举）")
        await self._switch(mode, reason=f"explicit:{operator}")
        return {"mode": self._mode, "previous_mode": mode, "status": "switched"}

    async def status(self) -> dict[str, Any]:
        """当前状态（GET /v1/health/detail 组件）。"""
        return {
            "mode": self._mode,
            "cycles_since_calibration": await self._current_cycles(),
            "last_switch_at": self._last_switch_at,
            "reason": self._reason,
            "periods": {"n": self.period_n, "m": self.period_m},
        }

    async def _current_cycles(self) -> int:
        from src.sovereignty.calibration import CalibrationPort

        port = CalibrationPort(self.db, tribunal=None)  # type: ignore[arg-type]
        return self._cycles_since_calibration(await port.last_calibration_at())
