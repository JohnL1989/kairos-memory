"""记忆 CRUD（竖切组件 1）——写入/读取/更新/软删除。

权威规格：
- 架构 §5.1-5.2（双副本/差异检验）、§7.3 摄取验证门禁（捕获门控）
- detailed-design §2 写入管线设计②（幂等 + 乐观锁事务提交）
- api-spec §1.1/1.3/1.5（端点契约：幂等键 / If-Match 乐观锁 / 契约分支删除）
- error-reference（ERR-* 错误码语义）

写入流程（竖切简化——无 WM 沙箱验证环，WM 不在竖切）：
  门禁（IngestionGate 捕获门控五层）→ 幂等键去重 → 单事务三分提交：
  事实源（memories 主记录）+ 状态轨迹（memory_states）+ 幂等记录（journal_buffer 承载）
  → 双副本初始化（witness_anchor 主副本 + usage_weight 影子副本，S-14 隔离）
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.access.ingestion import IngestionGate
from src.errors import (
    IdempotencyConflictError,
    IntentionNotClosedError,
    InvalidPathError,
    LockedMemoryError,
    MissingFieldError,
    NotFoundError,
    PathDepthError,
    SecurityRedlineError,
    VersionConflictError,
)
from src.events.types import PRIORITY_USE_EVENT, USE_EVENT
from src.storage.db import Database
from src.storage.models import (
    CONTRACTS,
    PROVENANCES,
    Memory,
    MemoryState,
    MemoryVersion,
    UsageWeight,
    WitnessAnchor,
    utc_now,
)
from src.utils.embeddings import Embedder

logger = logging.getLogger("kairos.memory_store")

if TYPE_CHECKING:
    from src.events.bus import EventBus
    from src.sovereignty.freeze import FreezeGuard

# 路径深度上限（error-reference ERR-INPUT-003：超过 10 层）
MAX_PATH_DEPTH = 10
# 幂等键记录保留语义：journal_buffer.digest_status='completed' 表示已处理
IDEMPOTENCY_DONE = "completed"


@dataclass(frozen=True)
class MemoryCreated:
    id: str
    path: str
    version: int


@dataclass(frozen=True)
class MemoryWriteInput:
    """POST /v1/memories 请求体（api-spec §1.1）。"""

    path: str
    content: str
    provenance: str
    contract: str = "ondemand"
    memory_types: list[str] = field(default_factory=lambda: ["semantic"])
    vad: dict[str, float] | None = None
    relations: list[dict[str, Any]] | None = None
    encoding_context: dict[str, Any] | None = None
    occurred_at: str | None = None


def _validate_path(path: str) -> None:
    """路径格式校验（ERR-INPUT-002/003）。"""
    if not path.startswith("kairos://"):
        raise InvalidPathError(f"路径必须以 kairos:// 开头: {path!r}")
    # 路径深度：kairos://_user/{id}/memories/ → 段数（按 / 分割计非空段）
    segments = [s for s in path.split("/") if s]
    if len(segments) > MAX_PATH_DEPTH:
        raise PathDepthError(f"路径深度超限（>10 层）: {path!r}")


def _validate_input(data: MemoryWriteInput) -> None:
    """字段校验（ERR-INPUT-004 / S-15 来源必填 / 契约枚举）。"""
    if not data.path:
        raise MissingFieldError("缺少必填字段: path")
    if not data.content:
        raise MissingFieldError("缺少必填字段: content")
    if not data.provenance:
        raise MissingFieldError("缺少必填字段: provenance（S-15 来源可鉴别，缺失返回 422）")
    if data.provenance not in PROVENANCES:
        raise MissingFieldError(f"非法 provenance: {data.provenance!r}")
    if data.contract not in CONTRACTS:
        raise MissingFieldError(f"非法 contract: {data.contract!r}（五值枚举）")
    _validate_path(data.path)
    if data.memory_types:
        for mt in data.memory_types:
            if mt not in ("episodic", "semantic", "procedural"):
                raise MissingFieldError(f"非法 memory_type: {mt!r}")
    if data.vad is not None:
        for axis, value in data.vad.items():
            if axis not in ("v", "a", "d") or not -1 <= value <= 1:
                raise MissingFieldError(f"非法 VAD 坐标: {axis}={value}")


def _content_hash(content: str) -> str:
    """content_hash = SHA-256(content)（data-model §1 memories）。"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _now() -> str:
    return utc_now()


def _to_memory_dict(m: Memory) -> dict[str, Any]:
    """ORM → API 响应对象（MemoryDetail 子集）。"""
    return {
        "id": m.id,
        "path": m.path,
        "version": m.version,
        "content": m.content,
        "content_summary": m.content_summary,
        "contract": m.contract,
        "memory_types": json.loads(m.memory_types),
        "provenance": m.provenance,
        "status": m.status,
        "is_identity": bool(m.is_identity),
        "identity_confidence": m.identity_confidence,
        "is_sensitive": bool(m.is_sensitive),
        "vad": {"v": m.vad_v, "a": m.vad_a, "d": m.vad_d},
        "heat_score": m.heat_score,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "last_access_at": m.last_access_at,
        "occurred_at": m.occurred_at,
    }


class MemoryStore:
    """记忆 CRUD（竖切组件 1）。"""

    def __init__(
        self,
        db: Database,
        gate: IngestionGate | None = None,
        embedder: Embedder | None = None,
        freeze_guard: FreezeGuard | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self.db = db
        self.gate = gate or IngestionGate()
        self.embedder = embedder  # W5 起注入；嵌入为派生视图（可重建，失败不阻断写入）
        self.freeze_guard = freeze_guard  # CAL-03 冻结守卫（W9 组装注入）
        self.bus = bus  # 事件总线（use_event 发布；首迭代接线）

    async def _publish_use_event(
        self, memory_id: str, *, action: str, extra: dict[str, Any] | None = None
    ) -> None:
        """发布 use_event（Outbox 语义；发布失败不阻断主操作——事件为派生信号可重放）。"""
        if self.bus is None:
            return
        try:
            payload = {"action": action}
            if extra:
                payload.update(extra)
            await self.bus.publish(
                USE_EVENT,
                "storage",
                payload=payload,
                priority=PRIORITY_USE_EVENT,
                memory_id=memory_id,
            )
        except Exception:
            # 事件发布失败仅留痕（影子副本可经维护重放，不阻断主写入）
            pass

    async def _check_frozen(self) -> None:
        """写操作前置检查：强制冻结期间所有写操作一律拒绝（api-spec §1.3 优先级）。"""
        if self.freeze_guard is not None:
            await self.freeze_guard.check()

    async def _embed_after_write(self, memory_id: str, content: str) -> None:
        """写入后异步生成嵌入（派生视图；失败仅记录，不阻断写入事务）。

        detailed-design §2 写入管线③：索引为派生视图可重建——嵌入损坏仅触发
        重建，禁止索引侧数据反写主记录。
        """
        if self.embedder is None:
            return
        try:
            vector = await self.embedder.embed(content)
            from src.storage.vector_index import VectorIndex

            await VectorIndex(self.db).upsert_embedding(memory_id, vector)
        except Exception:
            # 嵌入失败不阻断主写入（fail-open 留痕；重试/重建由维护引擎承载）
            pass

    # ------------------------------------------------------------------
    # 写入（POST /v1/memories）
    # ------------------------------------------------------------------

    async def create(
        self,
        data: MemoryWriteInput,
        *,
        idempotency_key: str | None = None,
        skip_capture_reason: str | None = None,
        operator: str = "api",
    ) -> MemoryCreated:
        """创建记忆（幂等键去重 + 捕获门控 + 单事务三分提交）。

        幂等（detailed-design §2 ②）：同键重复提交返回首次结果；
        键冲突且载荷不一致 → 409 ERR-CTR-005。幂等记录由 journal_buffer
        表承载（竖切表清单内，digest_status='completed' 语义复用）。
        """
        _validate_input(data)
        await self._check_frozen()

        # 捕获门控（S-07 秘密文本 / S-03 超长 → 异常；琐碎/维护提示 → 拒绝返回）
        verdict = self.gate.check(
            data.content, skip_reason=skip_capture_reason, contract=data.contract
        )
        if not verdict.accepted:
            raise MissingFieldError(
                f"捕获门控拒绝写入: {verdict.reason}（架构 §7.3 捕获门控）",
                details={"gate_reason": verdict.reason},
            )
        content = verdict.cleaned_content or data.content

        memory_id = str(uuid.uuid4())
        # 存储路径 = 输入路径 + 记忆 uuid 尾段（api-spec §1.1 响应形态
        # kairos://_user/{id}/memories/{uuid}；UNIQUE(path, version) 约束下
        # 每条记忆路径唯一，目录前缀经前缀匹配浏览）
        stored_path = f"{data.path.rstrip('/')}/{memory_id}"
        now = _now()
        payload_hash = _content_hash(json.dumps(data.__dict__, ensure_ascii=False))

        async with self.db.session() as session:
            # 幂等键去重（同事务内查询 + 写入，防竞态）
            if idempotency_key:
                existing = await self._lookup_idempotency(session, idempotency_key)
                if existing is not None:
                    if existing.get("payload_hash") != payload_hash:
                        raise IdempotencyConflictError(
                            f"幂等键冲突: {idempotency_key}"
                            "（同键重复提交且载荷不一致，ERR-CTR-005）"
                        )
                    # 同键同载荷：返回首次写入结果
                    return MemoryCreated(id=existing["memory_id"], path=data.path, version=1)

            memory = Memory(
                id=memory_id,
                path=stored_path,
                version=1,
                content=content,
                content_hash=_content_hash(content),
                memory_types=json.dumps(data.memory_types, ensure_ascii=False),
                contract=data.contract,
                provenance=data.provenance,
                vad_v=(data.vad or {}).get("v", 0),
                vad_a=(data.vad or {}).get("a", 0),
                vad_d=(data.vad or {}).get("d", 0),
                encoding_context=(
                    json.dumps(data.encoding_context, ensure_ascii=False)
                    if data.encoding_context
                    else None
                ),
                occurred_at=data.occurred_at,
                created_at=now,
                updated_at=now,
                last_access_at=now,  # 新记忆视为刚访问（freshness=1，防遗忘调度器 10s 内归档）
                root_memory_id=memory_id,  # 版本链根节点（首次写入指向自身）
                hall="canonical",  # 竖切无 WM 验证环，门禁通过直接 canonical
            )
            session.add(memory)

            # 双副本初始化（S-14：两副本单向隔离，见 dual_copy）
            session.add(
                WitnessAnchor(memory_id=memory_id, narrative_coherence_score=0.0, anchor_version=1)
            )
            session.add(UsageWeight(memory_id=memory_id))

            # 状态轨迹（初始 active）
            session.add(
                MemoryState(
                    memory_id=memory_id,
                    memory_type="storage",
                    state="active",
                    previous_state="",
                    reason="initial_write",
                    source=operator,
                )
            )

            # 幂等记录（journal_buffer 承载）
            if idempotency_key:
                from src.storage.models import JournalBuffer

                session.add(
                    JournalBuffer(
                        id=idempotency_key,
                        session_id="idempotency",
                        raw_content=json.dumps({"payload_hash": payload_hash}),
                        digest_status=IDEMPOTENCY_DONE,
                        digest_result=memory_id,
                        processed_at=now,
                    )
                )

            await session.commit()

        # 嵌入生成（派生视图；W5 起注入 embedder 时启用）
        await self._embed_after_write(memory_id, content)
        # use_event 发布（影子副本/审计依赖；首迭代接线）
        await self._publish_use_event(memory_id, action="memory_written")
        # 写入侧实体提取（竖切组件 3 实体加成数据源：slice-guide 组件 3 / 架构 §7.3h）
        await self._store_entities(memory_id, content, stored_path)
        return MemoryCreated(id=memory_id, path=stored_path, version=1)

    async def _store_entities(self, memory_id: str, content: str, path: str) -> None:
        """写入侧规则法实体提取 → entities 去重入库 → memory_entities 关联。

        设计依据：slice-guide 组件 3（三信号融合 α_e=0.15，实体词典为检索侧
        _entity_recall 的数据源——词典空则实体加成恒 0，本方法为激活点）；
        architecture §7.3h（竖切取关键字降级侧，无 LLM 依赖）。

        失败不阻断主写入：实体为检索增强信号，非记忆本体（异常仅告警日志）。
        实现复用公共函数 store_entities_for_memory（与 backfill 同源）。
        """
        from src.storage.entity_extractor import store_entities_for_memory

        try:
            await store_entities_for_memory(self.db, memory_id, content, path)
        except Exception:
            logger.warning(
                "entity extraction skipped for %s (non-blocking)", memory_id, exc_info=True
            )

    async def _lookup_idempotency(self, session: AsyncSession, key: str) -> dict[str, str] | None:
        """按幂等键查询已处理记录。"""
        from sqlalchemy import text

        row = (
            await session.execute(
                text(
                    "SELECT raw_content, digest_result FROM journal_buffer "
                    "WHERE id = :k AND digest_status = 'completed'"
                ),
                {"k": key},
            )
        ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(row[0] or "{}")
        except json.JSONDecodeError:
            payload = {}
        return {"payload_hash": payload.get("payload_hash", ""), "memory_id": row[1] or ""}

    # ------------------------------------------------------------------
    # 读取（GET /v1/memories/{id}）
    # ------------------------------------------------------------------

    async def get(self, memory_id: str) -> dict[str, Any]:
        """读取记忆（404 ERR-DB-004 若不存在或已软删除）。"""
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}（ERR-DB-004）")
            return _to_memory_dict(memory)

    # ------------------------------------------------------------------
    # 更新（PATCH /v1/memories/{id}，乐观锁 + 版本链追加）
    # ------------------------------------------------------------------

    async def update(
        self,
        memory_id: str,
        *,
        if_match_version: int | None,
        content: str | None = None,
        content_summary: str | None = None,
        vad: dict[str, float] | None = None,
        memory_types: list[str] | None = None,
        occurred_at: str | None = None,
        operator: str = "api",
    ) -> dict[str, Any]:
        """更新记忆（api-spec §1.3）。

        - If-Match 乐观锁必需（detailed-design §2 ②：v0.1.0 一律经 version
          乐观锁裁决，无「最后写入胜出」路径）；冲突 → 409 ERR-DB-005
        - 版本链追加而非覆盖（data-model §1：superseded_by 链 + memory_versions 快照）
        - locked_until 未到期 → 403 ERR-CTR-003
        """
        await self._check_frozen()
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}（ERR-DB-004）")

            self._check_locked(memory)

            if if_match_version is None:
                raise VersionConflictError(
                    "缺少 If-Match 请求头（乐观锁必需，无「最后写入胜出」路径）"
                )
            if memory.version != if_match_version:
                raise VersionConflictError(
                    f"版本冲突: 当前 v{memory.version} != If-Match v{if_match_version}"
                    "（ERR-DB-005）"
                )

            # 捕获门控（更新内容同样过门禁；更新不改变契约/来源）
            if content is not None:
                verdict = self.gate.check(content, contract=memory.contract)
                if not verdict.accepted:
                    raise MissingFieldError(
                        f"捕获门控拒绝更新: {verdict.reason}",
                        details={"gate_reason": verdict.reason},
                    )
                content = verdict.cleaned_content or content

            now = _now()
            new_version = memory.version + 1

            # 版本快照（memory_versions；回滚依据）
            session.add(
                MemoryVersion(
                    id=str(uuid.uuid4()),
                    memory_id=memory_id,
                    snapshot=json.dumps(_to_memory_dict(memory), ensure_ascii=False),
                    version_number=memory.version,
                    reason="update",
                    created_at=now,
                )
            )

            # 版本链：旧版本降级 is_latest，新记录追加
            memory.is_latest = 0
            new_memory_id = str(uuid.uuid4())
            new_memory = Memory(
                id=new_memory_id,
                path=memory.path,
                version=new_version,
                content=content if content is not None else memory.content,
                content_summary=content_summary
                if content_summary is not None
                else memory.content_summary,
                content_hash=_content_hash(content if content is not None else memory.content),
                memory_types=(
                    json.dumps(memory_types, ensure_ascii=False)
                    if memory_types is not None
                    else memory.memory_types
                ),
                contract=memory.contract,
                provenance=memory.provenance,
                vad_v=(vad or {}).get("v", memory.vad_v),
                vad_a=(vad or {}).get("a", memory.vad_a),
                vad_d=(vad or {}).get("d", memory.vad_d),
                encoding_context=memory.encoding_context,
                occurred_at=occurred_at if occurred_at is not None else memory.occurred_at,
                created_at=memory.created_at,
                updated_at=now,
                parent_memory_id=memory_id,
                root_memory_id=memory.root_memory_id or memory_id,
                is_latest=1,
                status=memory.status,
                is_identity=memory.is_identity,
                identity_confidence=memory.identity_confidence,
                identity_reviewed_at=memory.identity_reviewed_at,
                identity_review_count=memory.identity_review_count,
                heat_score=memory.heat_score,
                hall=memory.hall,
                expires_at=memory.expires_at,
                locked_until=memory.locked_until,
                calibration_confidence=memory.calibration_confidence,
                last_access_at=memory.last_access_at,
                sync_version=memory.sync_version,
                distill_level=memory.distill_level,
                extinction_status=memory.extinction_status,
                decontextualization_level=memory.decontextualization_level,
                domain=memory.domain,
                quality_tier=memory.quality_tier,
                compacted=memory.compacted,
                compacted_at=memory.compacted_at,
                compression_trail=memory.compression_trail,
                is_sensitive=memory.is_sensitive,
                identity_relevance=memory.identity_relevance,
                solution_branch_id=memory.solution_branch_id,
                structural_value=memory.structural_value,
                structural_value_reasons=memory.structural_value_reasons,
                structural_value_updated_at=memory.structural_value_updated_at,
                is_structure=memory.is_structure,
                valid_until=memory.valid_until,
                expiration_date=memory.expiration_date,
            )
            session.add(new_memory)
            # 先 flush 新行再回链旧行（next_version_id/superseded_by 的 FK
            # 指向新行——同一 flush 批次内后插行导致 FK 失败，须显式分步）
            await session.flush()
            memory.next_version_id = new_memory_id
            memory.superseded_by = new_memory_id  # 语义：被替代后的替代者（新版本）

            # 双副本随版本推进（见证锚定 anchor_version 递增）
            witness = await session.get(WitnessAnchor, memory_id)
            if witness is not None:
                witness.anchor_version += 1

            await session.commit()
            # 嵌入重算（更新内容后语义向量须同步；派生视图，失败不阻断）
            await self._embed_after_write(new_memory.id, new_memory.content)
            await self._publish_use_event(new_memory.id, action="memory_updated")
            return _to_memory_dict(new_memory)

    # ------------------------------------------------------------------
    # 删除（DELETE /v1/memories/{id}，契约分支）
    # ------------------------------------------------------------------

    async def delete(self, memory_id: str, *, operator: str = "api") -> None:
        """按契约删除（api-spec §1.5 契约分支）：

        - permanent  → 403 拒绝（常驻记忆不可经常规删除路径移除）
        - intention  → 409 ERR-CTR-004（须先经意图关闭裁定降级为 ondemand）
        - temporary  → 硬删除（直接清除，清理前审计标记 expiry_cascade_delete）
        - ondemand / environmental → 软删除（is_deleted=true，保留审计痕迹）
        - locked_until 未到期 → 403 ERR-CTR-003（优先于契约分支判定）
        """
        await self._check_frozen()
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}（ERR-DB-004）")

            self._check_locked(memory)

            now = _now()
            if memory.contract == "permanent":
                raise SecurityRedlineError(
                    "permanent 契约拒绝删除（常驻记忆仅可经宪法修订端口降级后删除）"
                )
            if memory.contract == "intention":
                raise IntentionNotClosedError(
                    "intention 契约未关闭，禁止直接删除（须先经意图关闭裁定降级为 ondemand）"
                )

            if memory.contract == "temporary":
                # 硬删除（架构 §8 外部来源铁律：已入库临时记忆清除必留痕）
                await self._record_state(
                    session, memory, reason="hard_delete_expiry", operator=operator, now=now
                )
                # 级联清理（FK ON DELETE CASCADE 自动处理 witness_anchor/usage_weight 等）
                await session.delete(memory)
            else:
                # 软删除（保留审计痕迹）
                memory.is_deleted = 1
                memory.updated_at = now
                await self._record_state(
                    session, memory, reason="soft_delete", operator=operator, now=now
                )

            await session.commit()
            await self._publish_use_event(memory_id, action="memory_deleted")

    async def _record_state(
        self,
        session: AsyncSession,
        memory: Memory,
        *,
        reason: str,
        operator: str,
        now: str,
    ) -> None:
        """状态轨迹留痕。

        state 列受 CHECK 约束（五值枚举 active/stale/archived/suppressed/superseded，
        data-model §11）——删除/锁定时保留当前状态，删除语义由 reason 标记承载。
        """
        session.add(
            MemoryState(
                memory_id=memory.id,
                memory_type="storage",
                state=memory.status,
                previous_state=memory.status,
                state_changed_at=now,
                reason=reason,
                source=operator,
            )
        )

    # ------------------------------------------------------------------
    # 归档（POST /v1/memories/{id}/archive，M-05）
    # ------------------------------------------------------------------

    async def archive(self, memory_id: str, *, reason: str | None = None) -> dict[str, Any]:
        """归档记忆（M-05；api-spec §1.5）。

        - 幂等：已归档重复归档返回成功不重复操作
        - permanent 契约拒绝（403）；temporary 契约不进入归档
        - 身份守卫（S-10 见证豁免）：is_identity=true 不可归档（ERR-SEC-001）
        - locked_until 未到期拒绝（ERR-CTR-003）
        """
        await self._check_frozen()
        async with self.db.session() as session:
            memory = await session.get(Memory, memory_id)
            if memory is None or memory.is_deleted:
                raise NotFoundError(f"记忆不存在: {memory_id}（ERR-DB-004）")
            self._check_locked(memory)
            if memory.is_identity:
                raise SecurityRedlineError(
                    f"身份记忆不可归档（S-10 见证豁免，ERR-SEC-001）: {memory_id}"
                )
            if memory.contract == "permanent":
                raise SecurityRedlineError("permanent 契约拒绝归档（须先经宪法修订端口降级）")
            if memory.contract == "temporary":
                raise SecurityRedlineError("temporary 契约不进入归档（到期由 forgetAfter 硬删除）")
            if memory.status == "archived":
                return {"memory_id": memory_id, "status": "archived", "idempotent": True}
            now = utc_now()
            memory.status = "archived"
            memory.updated_at = now
            await self._record_state(session, memory, reason="archive", operator="api", now=now)
            await session.commit()
            await self._publish_use_event(memory_id, action="memory_archived")
            return {"memory_id": memory_id, "status": "archived", "idempotent": False}

    # ------------------------------------------------------------------
    # 列表（GET /v1/memories?path=&limit=&offset=）
    # ------------------------------------------------------------------

    async def list(
        self,
        *,
        path_prefix: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """路径前缀列出（api-spec §1.2；排除软删除与失效版本）。"""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        async with self.db.session() as session:
            base_where = [Memory.is_deleted == 0, Memory.is_latest == 1]
            if path_prefix:
                # 路径前缀（GLOB 语义：kairos://x/* 匹配直接子级；kairos://x/ 匹配自身）
                base_where.append(
                    Memory.path.like(f"{path_prefix}%")
                    | (Memory.path == path_prefix.rstrip("/") + "/")
                )
            total = (
                await session.execute(select(func.count(Memory.id)).where(*base_where))
            ).scalar_one()
            rows = (
                await session.execute(
                    select(Memory)
                    .where(*base_where)
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).scalars()
            items = [_to_memory_dict(m) for m in rows]
            return items, total

    # ------------------------------------------------------------------
    # 锁定检查（ERR-CTR-003）
    # ------------------------------------------------------------------

    @staticmethod
    def _check_locked(memory: Memory) -> None:
        if memory.locked_until is not None and memory.locked_until > _now():
            raise LockedMemoryError(
                f"记忆已锁定至 {memory.locked_until}（locked_until 未到期，ERR-CTR-003）"
            )
