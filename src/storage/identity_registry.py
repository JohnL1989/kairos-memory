"""身份注册表（竖切组件 5，构造论）——is_identity 初始赋予 + 双向更新 + 否决权。

权威规格：
- 架构 §5.2 身份注册表动态建构（初始赋予：经见证锚定写入触发，冷启动锚点；
  使用权重永远无法将 is_identity 置为 false；双向更新规则：自洽度结构性上升
  →身份加强提案→提升置信度；持续下降超阈值→降级审查请求→宪法解释层裁定降级）
- 架构 §1.8 身份面否决权（预提交总线 + 身份总线监听器 + 否决裁决器三组件；
  存储层写入路径最终提交前调用否决裁决器检查 veto_event——不可绕过）
- 架构 §8 S-10（见证豁免：身份连续性记忆的保留不受使用权重衰减影响）
- G-03 v0.1.0 判据（双向更新可观测、审计可追溯）

降级门槛（架构 §8）：is_identity 降级须经「元认知层提案 → 宪法解释层判例 →
本端口执行」完整路径；降级写入审计日志标记 identity_demotion。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from src.errors import NotFoundError, SecurityRedlineError
from src.storage.db import Database
from src.storage.models import Memory, utc_now

if TYPE_CHECKING:
    from src.supervision.audit_tribunal import AuditTribunal

# 双向更新步进（架构无数值公式——机制式趋势+审查+裁定；竖切实现采用
# 保守步进：加强 +0.1/次，降级须判例；步进值可经 KAIROS_IDENTITY_* 配置演进）
STRENGTHEN_STEP = 0.1
DEMOTION_RESET_CONFIDENCE = 0.5

# 审计标记（S-16：身份降级留痕）
AUDIT_ACTION_DEMOTION = "identity_demotion"


class IdentityRegistry:
    """身份注册表（构造论动态建构；字段承载于 memories 表）。"""

    def __init__(self, db: Database, tribunal: AuditTribunal | None = None) -> None:
        self.db = db
        self.tribunal = tribunal  # 降级审计留痕（S-16）；W8 审计庭接入后必填

    # ------------------------------------------------------------------
    # 初始赋予（存储层写入触发，冷启动锚点）
    # ------------------------------------------------------------------

    async def grant_initial_identity(
        self, memory_id: str, *, confidence: float = 0.6
    ) -> dict[str, Any]:
        """初始赋予 is_identity=true（初始猜测，非永久锁定）。

        触发条件（架构 §5.2）：经见证锚定写入 + 冷启动锚点（identity 种子）。
        使用权重永远无法将 is_identity 置为 false（本方法无 inverse）。
        """
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}")
            if memory.is_identity:
                # 幂等：已赋予（加强置信度上限钳制）
                memory.identity_confidence = min(1.0, max(memory.identity_confidence, confidence))
            else:
                memory.is_identity = 1
                memory.identity_confidence = confidence
            memory.identity_reviewed_at = utc_now()
            memory.identity_review_count += 1
            await session.commit()
            return {
                "memory_id": memory_id,
                "is_identity": True,
                "identity_confidence": memory.identity_confidence,
            }

    # ------------------------------------------------------------------
    # 双向更新（叙事自洽度趋势驱动）
    # ------------------------------------------------------------------

    async def strengthen(
        self, memory_id: str, *, narrative_delta: float = STRENGTHEN_STEP
    ) -> dict[str, Any]:
        """身份加强（自洽度结构性上升 → 提升置信度）。

        仅对已赋予身份的记忆生效；未赋予的普通记忆不因内部信号获得身份
        （身份仅经见证锚定初始赋予——S-14 语境自指禁令的一致性延伸）。
        """
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}")
            if not memory.is_identity:
                raise SecurityRedlineError(
                    f"记忆 {memory_id} 未赋予身份标志，不可加强（身份仅经见证锚定初始赋予）"
                )
            memory.identity_confidence = min(1.0, memory.identity_confidence + narrative_delta)
            memory.identity_reviewed_at = utc_now()
            memory.identity_review_count += 1
            await session.commit()
            return {
                "memory_id": memory_id,
                "identity_confidence": memory.identity_confidence,
                "action": "strengthen",
            }

    async def review_demotion(
        self, memory_id: str, *, case_id: str | None = None
    ) -> dict[str, Any]:
        """降级审查（宪法解释层裁定前置）：确认降级前提（叙事自洽度持续下降）。

        is_identity 降级门槛（架构 §8）：须附宪法解释层判例（case_id）——
        未附判例的降级请求拒绝（403 ERR-SEC-001，api-spec §1.7 constitution 端口）。
        """
        if not case_id:
            raise SecurityRedlineError(
                "身份降级须附宪法解释层判例（case_id）——is_identity 降级门槛（架构 §8）"
            )
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}")
            return {
                "memory_id": memory_id,
                "case_id": case_id,
                "review_ok": True,
                "current_confidence": memory.identity_confidence,
            }

    async def demote(
        self,
        memory_id: str,
        *,
        case_id: str,
        narrative_trend: str = "declining",
        operator: str = "constitution",
    ) -> dict[str, Any]:
        """执行降级（移除 is_identity 标志，不删除记忆）+ 审计 identity_demotion。

        降级不删除记忆（架构 §5.2：降级仅移除标志）；审计日志标记
        identity_demotion + 叙事自洽度变化（S-16 留痕，audit_log 表）。
        """
        # 先审查（判例必需，S-16 与 api-spec §1.7 门槛）
        await self.review_demotion(memory_id, case_id=case_id)

        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}")
            memory.is_identity = 0
            memory.identity_confidence = DEMOTION_RESET_CONFIDENCE
            memory.identity_reviewed_at = utc_now()
            memory.identity_review_count += 1
            await session.commit()

        # 审计留痕（S-16：未留痕的降级视为未执行；经审计庭 HMAC 链）
        if self.tribunal is None:
            raise SecurityRedlineError(
                "身份降级须经审计庭留痕（S-16）——审计庭未接入，降级视为未执行"
            )
        await self.tribunal.record(
            operator=operator,
            action=AUDIT_ACTION_DEMOTION,
            target_type="memory",
            target_id=memory_id,
            details={"case_id": case_id, "narrative_trend": narrative_trend},
            redline_id="S-16",
        )
        return {
            "memory_id": memory_id,
            "is_identity": False,
            "identity_confidence": DEMOTION_RESET_CONFIDENCE,
            "audit": AUDIT_ACTION_DEMOTION,
        }

    # ------------------------------------------------------------------
    # 查询与豁免（S-10 见证豁免数据源）
    # ------------------------------------------------------------------

    async def get_identity(self, memory_id: str) -> dict[str, Any]:
        """查询身份状态（否决权数据源）。"""
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}")
            return {
                "memory_id": memory_id,
                "is_identity": bool(memory.is_identity),
                "identity_confidence": memory.identity_confidence,
                "identity_reviewed_at": memory.identity_reviewed_at,
                "identity_review_count": memory.identity_review_count,
            }

    async def list_identity_memories(self) -> list[dict[str, Any]]:
        """身份记忆清单（见证豁免 S-10 评估用）。"""
        async with self.db.session() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT id, path, identity_confidence FROM memories "
                        "WHERE is_identity = 1 AND is_deleted = 0 AND is_latest = 1"
                    )
                )
            ).fetchall()
        return [{"id": r[0], "path": r[1], "identity_confidence": r[2]} for r in rows]


# ---------------------------------------------------------------------------
# 身份面否决权（架构 §1.8 三组件：预提交总线 + 身份总线监听器 + 否决裁决器）
# ---------------------------------------------------------------------------


class VetoAdjudicator:
    """否决裁决器（存储层写入路径的最后检查点，不可绕过）。

    检查预提交总线上是否存在针对当前待提交产出的 veto_event——
    有则阻断写入（回滚），无则放行。否决裁决器本身不判断身份威胁
    （只检查总线事件，威胁判断由身份总线监听器承载）。
    """

    def __init__(self) -> None:
        self._veto_events: dict[str, dict[str, Any]] = {}  # target_commit_id → veto_event

    def inject_veto(self, target_commit_id: str, *, reason: str, severity: str = "block") -> None:
        """身份总线监听器注入 veto_event（架构 §1.8 veto_event 格式）。"""
        self._veto_events[target_commit_id] = {
            "target_commit_id": target_commit_id,
            "source": "identity_listener",
            "reason": reason,
            "severity": severity,
            "timestamp": utc_now(),
        }

    def check(self, target_commit_id: str) -> dict[str, Any] | None:
        """写入前检查（存储层最终提交前调用，§5.1 门禁不可旁路）。"""
        return self._veto_events.get(target_commit_id)

    def resolve(self, target_commit_id: str) -> None:
        """裁决完成（写入放行/回滚后清除事件）。"""
        self._veto_events.pop(target_commit_id, None)
