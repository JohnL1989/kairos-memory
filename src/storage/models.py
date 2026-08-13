"""数据模型定义（竖切 15 张物理表 ORM；FTS5 虚拟表 memories_fts 不经 ORM，由 db.py 直接建）。

权威来源：docs/specification/schema-slice.sql（DDL 唯一承载）+ data-model.md（字段语义）。
类型映射（schema-slice §约定）：
  UUID        -> TEXT（RFC 4122 小写带连字符）
  TIMESTAMPTZ -> TEXT（ISO-8601 UTC 定长 'YYYY-MM-DDTHH:MM:SS.sssZ'）
  BOOLEAN     -> INTEGER（0/1）
  JSONB       -> TEXT（JSON 序列化）
  VECTOR(n)   -> BLOB（n × float32 小端，1536 维 = 6144 字节）
  INTERVAL    -> INTEGER（整数秒）
  BIGSERIAL   -> INTEGER PRIMARY KEY AUTOINCREMENT（sqlite_autoincrement=True）

memories_fts（FTS5 虚拟表）与 FTS 同步触发器不经 ORM 定义，
由迁移脚本 op.execute() 原生 SQL 创建（ADR-011），此处仅登记常量。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------------------------
# 通用常量
# ---------------------------------------------------------------------------

# 状态五值枚举（memories.status / memory_states.state 同口径，架构 §5.2）
MEMORY_STATUSES = ("active", "stale", "archived", "suppressed", "superseded")
# 契约五值枚举（架构 §5.2 四类契约 + intention 前瞻）
CONTRACTS = ("permanent", "ondemand", "environmental", "temporary", "intention")
# 来源五值（S-15 来源可鉴别）
PROVENANCES = (
    "external_calibration",
    "internal_inference",
    "user_input",
    "system_generated",
    "exploration",
)
# 事件类型（架构 §10.10；竖切首迭代 4 类）
EVENT_TYPES = ("use_event", "calibration_signal", "degradation_switch", "latent_trigger")
# 审计目标类型
AUDIT_TARGET_TYPES = ("memory", "config", "user", "redline")

# FTS5 虚拟表名（不经 ORM，由迁移 op.execute 创建，ADR-011）
FTS_TABLE = "memories_fts"

# 竖切表清单（16 张；口径见 slice-implementation-guide §二——memory_relations 为
# MCP 关系管理三工具数据层（§6.8 link/unlink/relations），0002 迁移补齐）
SLICE_TABLES = (
    "memories",
    "memory_versions",
    "witness_anchor",
    "usage_weight",
    "journal_buffer",
    "usage_events",
    "forgetting_queue",
    "audit_log",
    "config",
    "seeds",
    "memory_states",
    "entities",
    "memory_entities",
    "memory_relations",
    "memories_fts",
    "schema_version",
)


def utc_now() -> str:
    """ISO-8601 UTC 定长时间戳（24 字符，schema-slice §约定）。"""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class Base(DeclarativeBase):
    """ORM 基类（SQLAlchemy 2.0 声明式）。"""


# ---------------------------------------------------------------------------
# 1. memories — 主记忆表（服务组件 1/2/3/4/5）
# ---------------------------------------------------------------------------


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint("is_sensitive IN (0,1)", name="ck_memories_is_sensitive"),
        CheckConstraint(
            "identity_relevance BETWEEN 0 AND 1", name="ck_memories_identity_relevance"
        ),
        CheckConstraint(
            "contract IN ('permanent','ondemand','environmental','temporary','intention')",
            name="ck_memories_contract",
        ),
        CheckConstraint("hall IN ('processing','validation','canonical')", name="ck_memories_hall"),
        CheckConstraint("distill_level BETWEEN 0 AND 4", name="ck_memories_distill_level"),
        CheckConstraint(
            "extinction_status IN ('active','extinct','fossilized')",
            name="ck_memories_extinction_status",
        ),
        CheckConstraint(
            "provenance IN ('external_calibration','internal_inference','user_input',"
            "'system_generated','exploration')",
            name="ck_memories_provenance",
        ),
        CheckConstraint(
            "status IN ('active','stale','archived','suppressed','superseded')",
            name="ck_memories_status",
        ),
        CheckConstraint("is_identity IN (0,1)", name="ck_memories_is_identity"),
        CheckConstraint(
            "identity_confidence BETWEEN 0 AND 1", name="ck_memories_identity_confidence"
        ),
        CheckConstraint("is_structure IN (0,1)", name="ck_memories_is_structure"),
        CheckConstraint("structural_value IN (0,1,2)", name="ck_memories_structural_value"),
        CheckConstraint("is_deleted IN (0,1)", name="ck_memories_is_deleted"),
        CheckConstraint(
            "calibration_confidence BETWEEN 0 AND 1", name="ck_memories_calibration_confidence"
        ),
        CheckConstraint("vad_v BETWEEN -1 AND 1", name="ck_memories_vad_v"),
        CheckConstraint("vad_a BETWEEN -1 AND 1", name="ck_memories_vad_a"),
        CheckConstraint("vad_d BETWEEN -1 AND 1", name="ck_memories_vad_d"),
        CheckConstraint("decontextualization_level BETWEEN 0 AND 1", name="ck_memories_decontext"),
        CheckConstraint("heat_score BETWEEN 0 AND 1", name="ck_memories_heat_score"),
        CheckConstraint("is_latest IN (0,1)", name="ck_memories_is_latest"),
        CheckConstraint(
            "quality_tier IN ('mental_models','observation','experience','world')",
            name="ck_memories_quality_tier",
        ),
        CheckConstraint("compacted IN (0,1)", name="ck_memories_compacted"),
        # is_structure ↔ structural_value 双向同步（data-model 0.0.16）
        CheckConstraint(
            "(is_structure = 0 AND structural_value != 2) "
            "OR (is_structure = 1 AND structural_value = 2)",
            name="ck_memories_structure_sync",
        ),
        UniqueConstraint("path", "version", name="uq_memories_path_version"),
        Index("idx_memories_path", "path"),
        Index("idx_memories_contract", "contract"),
        Index("idx_memories_created", "created_at"),
        Index("idx_memories_status", "status"),
        Index("idx_memories_last_access", "last_access_at"),
        Index("idx_memories_hall_status", "hall", "status"),
        Index("idx_memories_identity", "is_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_summary: Mapped[str | None] = mapped_column(Text)
    is_sensitive: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[bytes | None] = mapped_column(Text)  # VECTOR(1536) BLOB；NULL 跳过检索
    memory_types: Mapped[str] = mapped_column(String, nullable=False)  # JSON 数组
    identity_relevance: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    contract: Mapped[str] = mapped_column(String, nullable=False, default="ondemand")
    hall: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    solution_branch_id: Mapped[str | None] = mapped_column(String(36))
    distill_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extinction_status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    extinct_at: Mapped[str | None] = mapped_column(String)
    extinct_reason: Mapped[str | None] = mapped_column(String)
    lma_urn: Mapped[str | None] = mapped_column(String)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provenance: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    is_identity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    identity_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    identity_reviewed_at: Mapped[str | None] = mapped_column(String)
    identity_review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_structure: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    structural_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    structural_value_reasons: Mapped[str] = mapped_column(String, nullable=False, default="[]")
    structural_value_updated_at: Mapped[str | None] = mapped_column(String)
    is_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calibration_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    vad_v: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    vad_a: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    vad_d: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    decontextualization_level: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    heat_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    expires_at: Mapped[str | None] = mapped_column(String)
    valid_until: Mapped[str | None] = mapped_column(String)
    expiration_date: Mapped[str | None] = mapped_column(String)
    locked_until: Mapped[str | None] = mapped_column(String)
    encoding_context: Mapped[str | None] = mapped_column(Text)  # JSONB
    occurred_at: Mapped[str | None] = mapped_column(String)  # 双时态事件时间（可空）
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    superseded_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="SET NULL")
    )
    parent_memory_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("memories.id"))
    root_memory_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("memories.id"))
    next_version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("memories.id"))
    is_latest: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_access_at: Mapped[str | None] = mapped_column(String)
    domain: Mapped[str] = mapped_column(String, nullable=False, default="general")
    quality_tier: Mapped[str] = mapped_column(String, nullable=False, default="world")
    compacted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compacted_at: Mapped[str | None] = mapped_column(String)
    compression_trail: Mapped[str] = mapped_column(String, nullable=False, default="{}")


# ---------------------------------------------------------------------------
# 2. memory_versions — 版本快照表（组件 1）
# ---------------------------------------------------------------------------


class MemoryVersion(Base):
    __tablename__ = "memory_versions"
    __table_args__ = (
        CheckConstraint(
            "reason IS NULL OR reason IN ('update','rollback_prep','manual')",
            name="ck_memory_versions_reason",
        ),
        UniqueConstraint("memory_id", "version_number", name="uq_mv_memory_version"),
        Index("idx_memory_versions_memory", "memory_id", "version_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    memory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # JSONB 完整记忆快照
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)


# ---------------------------------------------------------------------------
# 3. witness_anchor — 见证锚定主副本（组件 1，强一致）
# ---------------------------------------------------------------------------


class WitnessAnchor(Base):
    __tablename__ = "witness_anchor"

    memory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), primary_key=True
    )
    narrative_coherence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    last_calibrated_at: Mapped[str | None] = mapped_column(String)
    calibration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    anchor_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    overridden_by_external: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# 4. usage_weight — 使用权重影子副本（组件 1，最终一致）
# ---------------------------------------------------------------------------


class UsageWeight(Base):
    __tablename__ = "usage_weight"
    __table_args__ = (
        CheckConstraint("activation_weight BETWEEN 0 AND 1", name="ck_uw_activation"),
        CheckConstraint("exploration_confidence BETWEEN 0 AND 1", name="ck_uw_exploration"),
        CheckConstraint("suspect_flag IN (0,1)", name="ck_uw_suspect"),
    )

    memory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), primary_key=True
    )
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[str | None] = mapped_column(String)
    activation_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    use_load_retrieval: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    use_load_verification: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    use_load_contribution: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    use_load_simulation: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    use_load_implicit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    exploration_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    suspect_flag: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# 5. journal_buffer — 写入暂存区（组件 1）
# ---------------------------------------------------------------------------


class JournalBuffer(Base):
    __tablename__ = "journal_buffer"
    __table_args__ = (
        CheckConstraint(
            "digest_status IN ('pending','processing','completed','failed')",
            name="ck_journal_status",
        ),
        Index("idx_journal_session", "session_id"),
        Index("idx_journal_status", "digest_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)  # JSONB role + content
    digest_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    digest_result: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    processed_at: Mapped[str | None] = mapped_column(String)


# ---------------------------------------------------------------------------
# 6. usage_events — 事件总线持久化（组件 7）
# ---------------------------------------------------------------------------
# 无 CHECK 约束：枚举随架构演进扩展，由应用层校验（schema-slice 注记）。


class UsageEvent(Base):
    __tablename__ = "usage_events"
    __table_args__ = (
        CheckConstraint("severity BETWEEN 0 AND 9", name="ck_usage_events_severity"),
        Index("idx_usage_events_memory_time", "memory_id", "created_at"),
        Index("idx_usage_events_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    source_layer: Mapped[str] = mapped_column(String, nullable=False)
    memory_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="SET NULL")
    )
    context: Mapped[str | None] = mapped_column(Text)  # JSONB
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    ttl: Mapped[int | None] = mapped_column(Integer)  # INTERVAL → 整数秒


# ---------------------------------------------------------------------------
# 7. forgetting_queue — 遗忘候选队列（组件 4）
# ---------------------------------------------------------------------------


class ForgettingQueue(Base):
    __tablename__ = "forgetting_queue"
    __table_args__ = (
        CheckConstraint("forgetting_score BETWEEN 0 AND 1", name="ck_fq_score"),
        CheckConstraint("status IN ('pending_archive','archived','revoked')", name="ck_fq_status"),
        Index("idx_forgetting_status", "status", "forgetting_score"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    memory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    forgetting_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)


# ---------------------------------------------------------------------------
# 8. audit_log — 审计日志 HMAC 链（组件 6）
# ---------------------------------------------------------------------------
# AUTOINCREMENT 必需：保证 id 单调不复用，维持 HMAC 链时序假设。


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint(
            "target_type IS NULL OR target_type IN ('memory','config','user','redline')",
            name="ck_audit_target_type",
        ),
        Index("idx_audit_time", "timestamp"),
        Index("idx_audit_target", "target_type", "target_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[str] = mapped_column("timestamp", String, nullable=False)
    operator: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String)
    target_id: Mapped[str | None] = mapped_column(String)
    content_hash: Mapped[str | None] = mapped_column(String)  # SHA-256(操作内容)
    previous_hash: Mapped[str | None] = mapped_column(String)  # 上一条的 HMAC
    hmac: Mapped[str] = mapped_column(String, nullable=False)  # HMAC-SHA256 签名
    details: Mapped[str | None] = mapped_column(Text)  # JSONB
    redline_id: Mapped[str | None] = mapped_column(String)


# ---------------------------------------------------------------------------
# 9. config — 运行时配置（组件 9）
# ---------------------------------------------------------------------------


class ConfigEntry(Base):
    __tablename__ = "config"
    __table_args__ = (
        CheckConstraint("scope IN ('static','dynamic','override')", name="ck_config_scope"),
    )

    key: Mapped[str] = mapped_column("key", String, primary_key=True)
    value: Mapped[str] = mapped_column("value", String, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False, default="static")
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    updated_by: Mapped[str | None] = mapped_column(String)


# ---------------------------------------------------------------------------
# 10. seeds — 冷启动种子锚点（组件 9）
# ---------------------------------------------------------------------------


class Seed(Base):
    __tablename__ = "seeds"
    __table_args__ = (
        CheckConstraint("seed_type IN ('config','identity','calibration')", name="ck_seeds_type"),
        CheckConstraint("initial_confidence BETWEEN 0 AND 1", name="ck_seeds_initial"),
        CheckConstraint("current_confidence BETWEEN 0 AND 1", name="ck_seeds_current"),
        CheckConstraint("degradation_level BETWEEN 0 AND 1", name="ck_seeds_degradation"),
        CheckConstraint("status IN ('active','degrading','retired')", name="ck_seeds_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    seed_type: Mapped[str] = mapped_column(String, nullable=False)
    initial_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    current_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    degradation_level: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    last_reviewed_at: Mapped[str | None] = mapped_column(String)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bias_reset_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_snapshot: Mapped[str | None] = mapped_column(Text)  # JSONB


# ---------------------------------------------------------------------------
# 11. memory_states — 状态变更审计轨迹（组件 1/4）
# ---------------------------------------------------------------------------
# 无 UNIQUE：支持同一记忆多次状态转换；不建 FK（硬删除后仍可追溯）。


class MemoryState(Base):
    __tablename__ = "memory_states"
    __table_args__ = (
        CheckConstraint(
            "memory_type IN ('storage','knowledge','experience','task')",
            name="ck_ms_memory_type",
        ),
        CheckConstraint(
            "state IN ('active','stale','archived','suppressed','superseded')",
            name="ck_ms_state",
        ),
        Index("idx_memory_states_history", "memory_id", "state_changed_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    memory_id: Mapped[str] = mapped_column(String, nullable=False)
    memory_type: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    previous_state: Mapped[str] = mapped_column(String, nullable=False, default="")
    state_changed_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    reason: Mapped[str] = mapped_column(String, nullable=False, default="")
    source: Mapped[str] = mapped_column(String, nullable=False, default="system")


# ---------------------------------------------------------------------------
# 12. entities — 实体表（组件 3，实体加成信号）
# ---------------------------------------------------------------------------


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        CheckConstraint("type IN ('project','people','concept','tool')", name="ck_entities_type"),
        UniqueConstraint("user_id", "name", name="uq_entities_user_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False, default="concept")
    description: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[bytes | None] = mapped_column(Text)  # VECTOR(1536)
    # 属性名避让 SQLAlchemy 保留名，列名仍为 metadata
    metadata_col: Mapped[str | None] = mapped_column("metadata", Text)  # JSONB
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)


# ---------------------------------------------------------------------------
# 13. memory_entities — 记忆-实体关联（组件 3）
# ---------------------------------------------------------------------------


class MemoryEntity(Base):
    __tablename__ = "memory_entities"
    __table_args__ = (
        UniqueConstraint("memory_id", "entity_id", "valid_from", name="uq_me_memory_entity"),
        Index("idx_memory_entities_entity", "entity_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    memory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relation: Mapped[str] = mapped_column(String, nullable=False, default="mentions")
    valid_from: Mapped[str | None] = mapped_column(String)
    valid_to: Mapped[str | None] = mapped_column(String)
    superseded_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("memory_entities.id", ondelete="SET NULL")
    )


class MemoryRelation(Base):
    """记忆关系索引表（data-model §1 memory_relations 契约；kairos_link/unlink/relations 数据层）。

    - relation_type 基础六值 + 语义标记扩展（TEXT 无 CHECK；六值与扩展不互斥）
    - UNIQUE(source_id, target_id, relation_type) 防同类型重复边
    - deleted_at 软删除（kairos_unlink 标记而非物理删除，检索过滤 deleted_at IS NULL）
    """

    __tablename__ = "memory_relations"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "relation_type", name="uq_relations_triplet"),
        Index("idx_memory_relations_target", "target_id"),
        Index("idx_memory_relations_type", "relation_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String, nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    reason: Mapped[str | None] = mapped_column(String)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    deleted_at: Mapped[str | None] = mapped_column(String)


# ---------------------------------------------------------------------------
# 15. schema_version — Schema 版本管理（组件 9）
# ---------------------------------------------------------------------------


class SchemaVersion(Base):
    __tablename__ = "schema_version"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    applied_at: Mapped[str] = mapped_column(String, nullable=False, default=utc_now)
    migration_name: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)


# 竖切 ORM 表注册（供迁移与测试引用）
ALL_MODELS: tuple[type[Any], ...] = (
    Memory,
    MemoryVersion,
    WitnessAnchor,
    UsageWeight,
    JournalBuffer,
    UsageEvent,
    ForgettingQueue,
    AuditLog,
    ConfigEntry,
    Seed,
    MemoryState,
    Entity,
    MemoryEntity,
    SchemaVersion,
)
