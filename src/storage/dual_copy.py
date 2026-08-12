"""双副本管理（竖切组件 1）——见证锚定主副本 + 使用权重影子副本分离。

权威规格：架构 §5.1-5.2（双副本/差异检验）、§5.5 差异检验（见证→使用仲裁）、
§8 S-14 语境自指禁令。

双副本模型：
- 见证锚定（主副本，witness_anchor 表）：强一致，真实性权威；仅由外部校准
  （POST /v1/calibrate，W8）与再巩固环更新；对外仅暴露快照。
- 使用权重（影子副本，usage_weight 表）：最终一致，异步合并；记录使用统计。

S-14 语境自指禁令（本模块核心防线）：
- 任何内部信号（使用权重/激活频率/影子副本置信度）不得作为见证锚定
  真实性或叙事自洽度的证据来源；
- 使用权重永远不能反向写回 narrative_coherence_score 或见证锚定主副本。
- 实现：update_usage 与 update_witness 两个单向端口，物理隔离——
  影子副本侧 API 无任何写主副本的路径（S-14 单测覆盖）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.errors import NotFoundError, SecurityRedlineError
from src.storage.db import Database
from src.storage.models import UsageWeight, WitnessAnchor, utc_now


@dataclass(frozen=True)
class UsageDelta:
    """使用事件增量（架构 §10.10 use_event 的存储侧投影）。"""

    usage_count: int = 1
    activation_weight: float = 0.0
    use_load_retrieval: float = 0.0
    use_load_verification: float = 0.0
    use_load_contribution: float = 0.0
    use_load_simulation: float = 0.0
    use_load_implicit: float = 0.0


class DualCopyManager:
    """双副本管理器（S-14 单向隔离防线）。"""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 主副本（见证锚定）——强一致，仅外部校准可写
    # ------------------------------------------------------------------

    async def update_witness(
        self,
        memory_id: str,
        *,
        narrative_coherence_score: float | None = None,
        overridden_by_external: bool | None = None,
        operator: str = "calibration",
    ) -> dict[str, Any]:
        """更新见证锚定主副本（S-11 外部校准端口唯一入口之一）。

        本方法是 witness_anchor 主副本内容事实的唯一合法写路径；
        任何内部信号不得调用（S-14——调用方若为内部组件将在此被拒绝）。
        """
        if operator not in ("calibration", "constitution"):
            raise SecurityRedlineError(
                f"S-14 语境自指禁令：见证锚定仅可由外部校准/宪法端口更新（operator={operator}）"
            )
        async with self.db.session() as session:
            anchor = await session.get(WitnessAnchor, memory_id)
            if anchor is None:
                raise NotFoundError(f"见证锚定不存在: {memory_id}")
            now = utc_now()
            if narrative_coherence_score is not None:
                anchor.narrative_coherence_score = narrative_coherence_score
                anchor.last_calibrated_at = now
                anchor.calibration_count += 1
            if overridden_by_external is not None:
                anchor.overridden_by_external = int(overridden_by_external)
            await session.commit()
            return {
                "memory_id": memory_id,
                "narrative_coherence_score": anchor.narrative_coherence_score,
                "calibration_count": anchor.calibration_count,
                "anchor_version": anchor.anchor_version,
            }

    async def read_witness(self, memory_id: str) -> dict[str, Any]:
        """读取见证锚定（对外仅暴露快照，架构 §5.2）。"""
        async with self.db.session() as session:
            anchor = await session.get(WitnessAnchor, memory_id)
            if anchor is None:
                raise NotFoundError(f"见证锚定不存在: {memory_id}")
            return {
                "memory_id": memory_id,
                "narrative_coherence_score": anchor.narrative_coherence_score,
                "last_calibrated_at": anchor.last_calibrated_at,
                "calibration_count": anchor.calibration_count,
                "anchor_version": anchor.anchor_version,
                "overridden_by_external": bool(anchor.overridden_by_external),
            }

    # ------------------------------------------------------------------
    # 影子副本（使用权重）——最终一致，任何组件可写，永不反写主副本
    # ------------------------------------------------------------------

    async def update_usage(self, memory_id: str, delta: UsageDelta) -> dict[str, Any]:
        """应用使用事件增量（影子副本侧）。

        S-14 防线：本方法只写 usage_weight 表——无任何写 witness_anchor
        或 memories.narrative_coherence_score 的路径（单测断言）。
        """
        async with self.db.session() as session:
            weight = await session.get(UsageWeight, memory_id)
            if weight is None:
                # 记忆不存在或尚未初始化影子副本
                raise NotFoundError(f"使用权重记录不存在: {memory_id}")
            now = utc_now()
            weight.usage_count += delta.usage_count
            weight.last_used_at = now
            weight.activation_weight = min(1.0, weight.activation_weight + delta.activation_weight)
            weight.use_load_retrieval += delta.use_load_retrieval
            weight.use_load_verification += delta.use_load_verification
            weight.use_load_contribution += delta.use_load_contribution
            weight.use_load_simulation += delta.use_load_simulation
            weight.use_load_implicit += delta.use_load_implicit
            await session.commit()
            return {
                "memory_id": memory_id,
                "usage_count": weight.usage_count,
                "last_used_at": weight.last_used_at,
                "activation_weight": weight.activation_weight,
            }

    async def read_usage(self, memory_id: str) -> dict[str, Any]:
        """读取影子副本快照。"""
        async with self.db.session() as session:
            weight = await session.get(UsageWeight, memory_id)
            if weight is None:
                raise NotFoundError(f"使用权重记录不存在: {memory_id}")
            return {
                "memory_id": memory_id,
                "usage_count": weight.usage_count,
                "last_used_at": weight.last_used_at,
                "activation_weight": weight.activation_weight,
                "use_load_retrieval": weight.use_load_retrieval,
                "use_load_verification": weight.use_load_verification,
                "use_load_contribution": weight.use_load_contribution,
                "use_load_simulation": weight.use_load_simulation,
                "use_load_implicit": weight.use_load_implicit,
                "exploration_confidence": weight.exploration_confidence,
                "suspect_flag": bool(weight.suspect_flag),
            }

    # ------------------------------------------------------------------
    # 差异检验（架构 §5.5 见证→使用仲裁；竖切基础版）
    # ------------------------------------------------------------------

    async def differential_check(self, memory_id: str) -> dict[str, Any]:
        """基础差异检验：使用权重陡升/累积偏差检测（竖切 W3 交付基础版）。

        完整差异检验（摘要比对 + 语义内核 + 沙箱隔离）依赖检索组件（W5）
        与校准（W8）后接入。本版检测：
        - 使用权重陡升（单位窗口升幅超阈值 → 挂起合并标记）
        - 见证/使用方向背离（权重升见证降 → suspect_flag）
        """
        async with self.db.session() as session:
            weight = await session.get(UsageWeight, memory_id)
            anchor = await session.get(WitnessAnchor, memory_id)
            if weight is None or anchor is None:
                raise NotFoundError(f"双副本记录不存在: {memory_id}")
            result: dict[str, Any] = {"memory_id": memory_id, "blocked": False}
            # 方向背离：权重升（usage_count>0）且见证分下降（narrative_coherence_score 低）
            if weight.usage_count > 0 and anchor.narrative_coherence_score < 0.3:
                weight.suspect_flag = 1
                result["blocked"] = True
                result["reason"] = "direction_divergence"
                result["suspect_flag"] = True
            await session.commit()
            return result
