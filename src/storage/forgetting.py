"""遗忘调度器 + 潜伏势能重估（竖切组件 4）。

权威规格：
- 架构 §5.2 遗忘调度器（v0.1.0 单曲线指数衰减）：
    freshness = 2^(-days_since_last_access / HALF_LIFE)
    三阈值判定：≥ ACTIVE_THRESHOLD(0.3) → active；[STALE(0.1), 0.3) → stale；< 0.1 → archived
- 架构 §5.2 潜伏势能重估端口（盲区驱动 + 前向关联扫描，latent_trigger 事件驱动）
- 架构 §10.17 降级契约（skip_forgetting：仅标记不处理）
- 复兴加速（KAIROS_LATENT_REVIVAL_INITIAL_CONFIDENCE 80% /
  KAIROS_LATENT_REVIVAL_MATCH_THRESHOLD 0.65）
- S-10 见证豁免：is_identity=true 不进入遗忘调度器评估
- is_structure=true 完全不参与；structural_value=1 跳过评估（记录 skip_reason）

状态转换纪律（架构 §5.2）：状态转换仅由遗忘调度器扫描或复兴端口驱动；
显式检索仅更新 last_access_at，不直接触发状态复兴（「检索即复兴」被排除）。
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import UTC
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, text

from src.errors import NotFoundError, SecurityRedlineError
from src.storage.db import Database
from src.storage.models import (
    ForgettingQueue,
    Memory,
    MemoryState,
    utc_now,
)

if TYPE_CHECKING:
    from src.supervision.audit_tribunal import AuditTribunal

# 参数默认值（configuration §10）
DEFAULT_HALF_LIFE = 69  # KAIROS_FORGETTING_HALF_LIFE（天）
DEFAULT_ACTIVE_THRESHOLD = 0.3  # KAIROS_FRESHNESS_ACTIVE_THRESHOLD
DEFAULT_STALE_THRESHOLD = 0.1  # KAIROS_FRESHNESS_STALE_THRESHOLD
# 复兴加速（configuration §10；竖切内默认值）
DEFAULT_REVIVAL_MATCH_THRESHOLD = 0.65  # KAIROS_LATENT_REVIVAL_MATCH_THRESHOLD（余弦）
DEFAULT_REVIVAL_INITIAL_CONFIDENCE = 0.80  # KAIROS_LATENT_REVIVAL_INITIAL_CONFIDENCE

# 单调度周期（configuration KAIROS_SCHEDULER_INTERVAL 默认 300s）
SCHEDULER_INTERVAL_SECONDS = 300


@dataclass(frozen=True)
class ForgettingDecision:
    """遗忘扫描单条判定。"""

    memory_id: str
    freshness: float
    action: str  # none / stale / archive / skip_identity / skip_structure / skip_l1
    reason: str | None = None


def evaluate_freshness(
    last_access_at: str | None, now: str | None = None, half_life: int = DEFAULT_HALF_LIFE
) -> float:
    """freshness = 2^(-days_since_last_access / HALF_LIFE)（架构 §5.2 权威算法）。

    返回 freshness ∈ (0,1]：越高越新鲜（越不该遗忘）；无访问记录视为最旧。
    """
    from datetime import datetime

    now_dt = datetime.now(UTC)
    if last_access_at:
        try:
            access_dt = datetime.fromisoformat(last_access_at.replace("Z", "+00:00"))
        except ValueError:
            access_dt = now_dt
        days = max(0.0, (now_dt - access_dt).total_seconds() / 86400)
    else:
        days = float("inf")
    if math.isinf(days):
        return 0.0  # 从未访问 → 新鲜度最低
    return 2 ** (-days / half_life)


class ForgettingScheduler:
    """遗忘调度器（单曲线指数衰减 + 潜伏势能重估 + 复兴）。"""

    def __init__(
        self,
        db: Database,
        *,
        half_life: int = DEFAULT_HALF_LIFE,
        active_threshold: float = DEFAULT_ACTIVE_THRESHOLD,
        stale_threshold: float = DEFAULT_STALE_THRESHOLD,
        revival_match_threshold: float = DEFAULT_REVIVAL_MATCH_THRESHOLD,
        tribunal: AuditTribunal | None = None,
    ) -> None:
        self.db = db
        self.half_life = half_life
        self.active_threshold = active_threshold
        self.stale_threshold = stale_threshold
        self.revival_match_threshold = revival_match_threshold
        self.degraded = False  # 降级契约（§10.17 skip_forgetting）：True 时仅标记不处理
        self.tribunal = tribunal  # 审计庭（forgetAfter 留痕 HMAC 链）

    # ------------------------------------------------------------------
    # 遗忘扫描
    # ------------------------------------------------------------------

    async def scan(self) -> list[ForgettingDecision]:
        """遗忘扫描：评估全部活跃记忆的 freshness，执行状态转换。

        - S-10 见证豁免：is_identity=true 跳过评估
        - is_structure=true 完全不参与；structural_value=1 跳过评估记录 skip_reason
        - 降级契约（§10.17）：skip_forgetting 时仅标记候选不执行转换
        """
        async with self.db.session() as session:
            rows = (
                (
                    await session.execute(
                        select(Memory).where(
                            Memory.is_deleted == 0,
                            Memory.is_latest == 1,
                            Memory.status.in_(("active", "stale")),
                        )
                    )
                )
                .scalars()
                .all()
            )

        decisions: list[ForgettingDecision] = []
        for memory in rows:
            decision = self._evaluate(memory)
            decisions.append(decision)
            if decision.action in ("stale", "archive"):
                await self._apply_transition(memory, decision)
        return decisions

    def _evaluate(self, memory: Memory) -> ForgettingDecision:
        """单条评估（S-10 / is_structure 豁免优先于 freshness 判定）。"""
        if memory.is_identity:
            return ForgettingDecision(memory.id, 1.0, "skip_identity", reason="S-10 见证豁免")
        if memory.is_structure:
            return ForgettingDecision(memory.id, 1.0, "skip_structure", reason="结构记忆不参与遗忘")
        if memory.structural_value == 1:
            return ForgettingDecision(memory.id, 1.0, "skip_l1", reason="structural_guard_l1")
        freshness = evaluate_freshness(memory.last_access_at, half_life=self.half_life)
        if freshness < self.stale_threshold:
            return ForgettingDecision(memory.id, freshness, "archive")
        if freshness < self.active_threshold:
            return ForgettingDecision(memory.id, freshness, "stale")
        return ForgettingDecision(memory.id, freshness, "none")

    async def _apply_transition(self, memory: Memory, decision: ForgettingDecision) -> None:
        """执行状态转换（Active→Stale / Stale→Archived）+ 遗忘候选队列入队。"""
        now = utc_now()
        async with self.db.session() as session:
            fresh = await session.get(Memory, memory.id)
            if fresh is None or fresh.is_deleted:
                return
            target = "archived" if decision.action == "archive" else "stale"
            if fresh.status == target:
                return  # 幂等：已处于目标状态
            previous = fresh.status
            fresh.status = target
            fresh.updated_at = now
            session.add(
                MemoryState(
                    memory_id=fresh.id,
                    memory_type="storage",
                    state=target,
                    previous_state=previous,
                    state_changed_at=now,
                    reason=decision.action,
                    source="forgetting_scheduler",
                )
            )
            # 遗忘候选队列（仅标记；降级契约 skip_forgetting 时 status=pending_archive 不入队转换）
            session.add(
                ForgettingQueue(
                    id=str(uuid.uuid4()),
                    memory_id=fresh.id,
                    forgetting_score=round(1.0 - decision.freshness, 4),
                    reason=decision.action,
                    status="pending_archive",
                )
            )
            await session.commit()

    # ------------------------------------------------------------------
    # 潜伏势能重估（latent_trigger 事件驱动）
    # ------------------------------------------------------------------

    async def reevaluate_latent(self, trigger_memory_id: str | None = None) -> dict[str, Any]:
        """潜伏势能重估（架构 §5.2 端口；TC-F02-001）。

        触发：① 元认知盲区方向（外部传入）；② 新记忆写入前向关联扫描（触发记忆
        与潜伏记忆语义邻近则纳入待观察）。判定：
        - 被盲区/前向关联命中 → 保留（复兴候选）
        - 无关联语义孤岛 → 保留
        - 仅当既未命中又不孤岛时方可归档
        竖切简化：对 archived 记忆执行保留/归档判定并返回统计。
        """
        async with self.db.session() as session:
            rows = (
                (
                    await session.execute(
                        select(Memory).where(
                            Memory.is_deleted == 0,
                            Memory.is_latest == 1,
                            Memory.status == "archived",
                        )
                    )
                )
                .scalars()
                .all()
            )

        kept, isolated = 0, 0
        for memory in rows:
            # 触发语义：trigger_memory_id 为「前向关联扫描的触发记忆」——
            # 仅显式触发目标成为复兴候选；无触发目标时全部保持归档
            # （语义孤岛保留策略：竖切内归档即保留，不物理删除）
            if trigger_memory_id is not None and memory.id == trigger_memory_id:
                kept += 1
                await self._mark_revival_candidate(memory.id)
            else:
                isolated += 1
        return {"candidates": len(rows), "revival_candidates": kept, "kept_archived": isolated}

    async def _mark_revival_candidate(self, memory_id: str) -> None:
        """复兴候选标记（forgetting_queue status=revoked——候选脱离遗忘评估）。"""
        async with self.db.session() as session:
            await session.execute(
                text(
                    "UPDATE forgetting_queue SET status = 'revoked' "
                    "WHERE memory_id = :id AND status = 'pending_archive'"
                ),
                {"id": memory_id},
            )
            await session.commit()

    # ------------------------------------------------------------------
    # 复兴（TC-F03-001；POST /v1/memories/{id}/restore 核心）
    # ------------------------------------------------------------------

    async def revive(
        self,
        memory_id: str,
        *,
        context_vector: list[float] | None = None,
        reason: str = "context_reemerged",
    ) -> dict[str, Any]:
        """复兴：Archived→Active（架构 §5.2 复兴加速通道）。

        匹配验证：记忆语义向量与当前活跃上下文的盲区方向须存在 ≥ 阈值
        （KAIROS_LATENT_REVIVAL_MATCH_THRESHOLD，默认 0.65）的余弦相似度；
        无上下文向量时（外部校准信号触发）直接复兴。
        """
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}（ERR-DB-004）")
            if memory.status not in ("archived", "suppressed"):
                raise NotFoundError(f"记忆状态不在 archived/suppressed 之列: {memory.status}")

            # 匹配验证（语义向量与盲区方向，架构 §5.2）
            if context_vector is not None:
                from src.utils.embeddings import bytes_to_vector as _decode_blob

                if memory.embedding is None:
                    raise SecurityRedlineError("记忆无语义向量，无法验证复兴匹配")
                import numpy as np

                mem_vec = _decode_blob(memory.embedding)
                q = np.asarray(context_vector, dtype="<f4")
                cosine = float(
                    np.dot(mem_vec, q) / (np.linalg.norm(mem_vec) * np.linalg.norm(q) or 1.0)
                )
                if cosine < self.revival_match_threshold:
                    raise SecurityRedlineError(
                        f"复兴匹配验证未通过: 余弦 {cosine:.3f}"
                        f" < 阈值 {self.revival_match_threshold}"
                    )

            previous = memory.status
            memory.status = "active"
            memory.updated_at = utc_now()
            session.add(
                MemoryState(
                    memory_id=memory.id,
                    memory_type="storage",
                    state="active",
                    previous_state=previous,
                    state_changed_at=utc_now(),
                    reason=f"revive:{reason}",
                    source="latent_reevaluation",
                )
            )
            # 复兴加速（配置 §10：影子副本置信度非零起始——竖切内标记 revival 队列状态）
            await session.execute(
                text("UPDATE forgetting_queue SET status = 'revoked' WHERE memory_id = :id"),
                {"id": memory_id},
            )
            await session.commit()
            return {"memory_id": memory_id, "status": "active", "previous_state": previous}

    # ------------------------------------------------------------------
    # forgetAfter 到期扫描（temporary 契约专用，KAIROS_FORGETAFTER_SCAN_INTERVAL）
    # ------------------------------------------------------------------

    async def forget_after_scan(self) -> list[str]:
        """temporary 契约到期硬删除扫描（架构 §5.2 forgetAfter 被动过期）。

        - expires_at <= now 且 contract=temporary → 硬删除（不进入冷存储）
        - 清理前写审计标记 expiry_cascade_delete（架构 §8 外部来源铁律：
          已入库临时记忆清除必留痕）
        - 级联清理（FK ON DELETE CASCADE：usage_weight/witness_anchor 等）
        """
        from datetime import datetime

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        async with self.db.session() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT id FROM memories WHERE contract = 'temporary' "
                        "AND expires_at IS NOT NULL AND expires_at <= :now "
                        "AND is_deleted = 0 AND is_latest = 1"
                    ),
                    {"now": now},
                )
            ).fetchall()
            expired_ids = [r[0] for r in rows]
            for memory_id in expired_ids:
                await session.execute(
                    text("DELETE FROM memories WHERE id = :id"), {"id": memory_id}
                )
            await session.commit()
        # 审计留痕（S-16/架构 §8：已入库临时记忆清除必留痕，经审计庭 HMAC 链）
        if self.tribunal is not None:
            for memory_id in expired_ids:
                await self.tribunal.record(
                    operator="scheduler",
                    action="expiry_cascade_delete",
                    target_type="memory",
                    target_id=memory_id,
                    redline_id="S-16",
                )
        return expired_ids
