-- =============================================================================
-- Kairos v0.1.0 竖切 Schema — SQLite 可执行 DDL
-- =============================================================================
-- 权威来源 : docs/specification/data-model.md（字段语义）
-- 类型映射 : docs/specification/data-model.md §13.1 / §13.2
-- 表清单   : docs/development/slice-implementation-guide.md §二（15 张表）
-- 里程碑   : W2「schema 迁移」的直接输入
--
-- 范围声明 : 仅覆盖竖切 15 张表，非 v0.1.0 全量 57 张表。
-- 冲突处置 : 本文件与 data-model.md 不一致时，以 data-model.md 为准并修订本文件。
--
-- 依赖扩展 : sqlite-vec（向量距离函数）、FTS5（编译期内置）
-- 生成日期 : 2026-08-04（0.0.11 批次重建——对齐 data-model v0.0.10）
-- 变更记录 : 2026-08-04 补 occurred_at（双时态）、parent/root/next_version_id/is_latest
--            （版本链）、contract 增 intention 枚举；schema_version 去 singleton 列对齐 data-model
-- 0.0.14 复核 : 15 张表与 data-model v0.0.12 逐列比对无残余差异（0.0.11/0.0.12 批次修改不涉本 15 表）；
--            data-model 0.0.14 对 memory_relations 的 relation_type 语义标记扩展不涉及本文件（关系索引表非竖切范围）
-- 0.0.26 复核 : 15 张表与 data-model v0.0.25 逐列比对（0.0.16 批次新增 memories.structural_value/
--            structural_value_reasons/structural_value_updated_at/compression_trail 4 字段已回填；
--            is_structure ↔ structural_value 双向同步 CHECK 已补；其余 14 张表无残余差异）
-- =============================================================================

PRAGMA foreign_keys = ON;      -- 必须：SQLite 默认不强制外键，未开启则所有 FK 静默失效
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

BEGIN;

-- -----------------------------------------------------------------------------
-- 约定（见 data-model.md §13.1 / §13.3）
--   UUID        -> TEXT，RFC 4122 小写带连字符 36 字符
--   TIMESTAMPTZ -> TEXT，ISO-8601 UTC 定长 'YYYY-MM-DDTHH:MM:SS.sssZ'（24 字符）
--   BOOLEAN     -> INTEGER，仅 0/1
--   JSONB       -> TEXT，JSON 序列化字符串（JSON1 扩展查询）
--   VECTOR(n)   -> BLOB，n × float32 小端紧凑排列（1536 维 = 6144 字节）
--   INTERVAL    -> INTEGER，整数秒
--   BIGSERIAL   -> INTEGER PRIMARY KEY AUTOINCREMENT
--   过期/锁定判定一律在应用层用 tz-aware datetime 比较，不依赖 DB 侧时钟
-- -----------------------------------------------------------------------------

-- =============================================================================
-- 1. memories — 主记忆表（服务组件 1/2/3/4/5）
-- =============================================================================
CREATE TABLE memories (
  id                        TEXT    PRIMARY KEY,                         -- UUID
  path                      TEXT    NOT NULL,                            -- kairos:// 路径
  version                   INTEGER NOT NULL DEFAULT 1,
  content                   TEXT    NOT NULL,
  content_summary           TEXT,
  is_sensitive              INTEGER NOT NULL DEFAULT 0 CHECK (is_sensitive IN (0,1)),
  content_hash              TEXT    NOT NULL,                            -- SHA-256(content)
  embedding                 BLOB,                                        -- VECTOR(1536)；NULL 记录向量检索时跳过
  memory_types              TEXT    NOT NULL,                            -- JSON 数组 ["episodic","semantic","procedural"]
  identity_relevance        REAL    NOT NULL DEFAULT 0   CHECK (identity_relevance BETWEEN 0 AND 1),
  contract                  TEXT    NOT NULL DEFAULT 'ondemand'
                                    CHECK (contract IN ('permanent','ondemand','environmental','temporary','intention')),
  hall                      TEXT    NOT NULL DEFAULT 'processing'
                                    CHECK (hall IN ('processing','validation','canonical')),
  solution_branch_id        TEXT,                                        -- UUID
  distill_level             INTEGER NOT NULL DEFAULT 0   CHECK (distill_level BETWEEN 0 AND 4),
  extinction_status         TEXT    NOT NULL DEFAULT 'active'
                                    CHECK (extinction_status IN ('active','extinct','fossilized')),
  extinct_at                TEXT,
  extinct_reason            TEXT,
  lma_urn                   TEXT,                                        -- urn:kairos:lma:<uuid>
  sync_version              INTEGER NOT NULL DEFAULT 0,
  provenance                TEXT    NOT NULL
                                    CHECK (provenance IN ('external_calibration','internal_inference',
                                                          'user_input','system_generated','exploration')),
  status                    TEXT    NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active','stale','archived','suppressed','superseded')),
  is_identity               INTEGER NOT NULL DEFAULT 0 CHECK (is_identity IN (0,1)),
  identity_confidence       REAL    NOT NULL DEFAULT 0.5 CHECK (identity_confidence BETWEEN 0 AND 1),
  identity_reviewed_at      TEXT,
  identity_review_count     INTEGER NOT NULL DEFAULT 0,
  is_structure              INTEGER NOT NULL DEFAULT 0 CHECK (is_structure IN (0,1)),
  structural_value          INTEGER NOT NULL DEFAULT 0   CHECK (structural_value IN (0,1,2)),  -- 半定量结构标记：0 非结构 / 1 疑似 / 2 确认（新增）
  structural_value_reasons  TEXT    NOT NULL DEFAULT '[]',   -- JSON 数组：升档原因列表（新增）
  structural_value_updated_at TEXT,                           -- 最近一次升/降档时间 ISO-8601（新增）
  is_deleted                INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0,1)),
  calibration_confidence    REAL    NOT NULL DEFAULT 0.5 CHECK (calibration_confidence BETWEEN 0 AND 1),
  vad_v                     REAL    NOT NULL DEFAULT 0   CHECK (vad_v BETWEEN -1 AND 1),
  vad_a                     REAL    NOT NULL DEFAULT 0   CHECK (vad_a BETWEEN -1 AND 1),
  vad_d                     REAL    NOT NULL DEFAULT 0   CHECK (vad_d BETWEEN -1 AND 1),
  decontextualization_level REAL    NOT NULL DEFAULT 0   CHECK (decontextualization_level BETWEEN 0 AND 1),
  heat_score                REAL    NOT NULL DEFAULT 1.0 CHECK (heat_score BETWEEN 0 AND 1),
  expires_at                TEXT,                                        -- 仅 temporary 契约；到期硬删除
  locked_until              TEXT,
  encoding_context          TEXT,                                        -- JSONB
  occurred_at               TEXT,                                        -- 事件时间（双时态，可空——无法判定时不填；轻量级时间戳后处理回填）
  created_at                TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at                TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  superseded_by             TEXT    REFERENCES memories(id) ON DELETE SET NULL,
  parent_memory_id          TEXT    REFERENCES memories(id),            -- 版本链前驱（首次写入 NULL）
  root_memory_id            TEXT    REFERENCES memories(id),            -- 版本链根节点（首次写入指向自身）
  next_version_id           TEXT    REFERENCES memories(id),            -- 版本链后继（最新版本 NULL）
  is_latest                 INTEGER NOT NULL DEFAULT 1 CHECK (is_latest IN (0,1)),
  last_access_at            TEXT,
  domain                    TEXT    NOT NULL DEFAULT 'general',
  quality_tier              TEXT    NOT NULL DEFAULT 'world'
                                    CHECK (quality_tier IN ('mental_models','observation','experience','world')),
  compacted                INTEGER NOT NULL DEFAULT 0 CHECK (compacted IN (0,1)),   -- 压缩标记（RC-07）
  compacted_at             TEXT,                                                     -- 压缩时间 ISO8601；30 天回滚窗口判定
  compression_trail        TEXT    NOT NULL DEFAULT '{}',   -- JSON 对象：逐记忆压缩审计日志（新增，P6 逐记忆粒度）
  -- is_structure ↔ structural_value 双向同步（data-model 0.0.16）：is_structure=1 ↔ structural_value=2
  CHECK ((is_structure = 0 AND structural_value != 2) OR (is_structure = 1 AND structural_value = 2)),
  UNIQUE (path, version)
);

CREATE INDEX idx_memories_path        ON memories(path);                 -- 前缀查询：WHERE path GLOB 'kairos://x/*'
CREATE INDEX idx_memories_contract    ON memories(contract);
CREATE INDEX idx_memories_created     ON memories(created_at);
CREATE INDEX idx_memories_status      ON memories(status);
CREATE INDEX idx_memories_last_access ON memories(last_access_at);
CREATE INDEX idx_memories_hall_status ON memories(hall, status);
CREATE INDEX idx_memories_identity    ON memories(is_identity) WHERE is_identity = 1;

-- idx_memories_types：PG 为 JSONB GIN 索引，SQLite 无等价物（data-model §13.2）。
-- v0.1.0 降级为全表 json_each 扫描；1 万条量级可接受，规模化后拆 memory_types 关联表。
--
-- idx_memories_embedding：PG 为 pgvector HNSW（近似）。SQLite 侧 v0.1.0 不建向量索引，
-- 使用 sqlite-vec 的 vec_distance_cosine(embedding, :q) 精确扫描（brute-force）。
-- 两模式召回集合可能不同，三信号权重需分模式标定（架构 §7.3a）。

-- =============================================================================
-- 2. memory_versions — 版本快照表（组件 1，显式回滚依据）
-- =============================================================================
CREATE TABLE memory_versions (
  id             TEXT    PRIMARY KEY,                                    -- UUID
  memory_id      TEXT    NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  snapshot       TEXT    NOT NULL,                                       -- JSONB：完整记忆快照
  version_number INTEGER NOT NULL,                                       -- 对应 memories.version
  reason         TEXT    CHECK (reason IS NULL OR reason IN ('update','rollback_prep','manual')),
  created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE (memory_id, version_number)
);

CREATE INDEX idx_memory_versions_memory ON memory_versions(memory_id, version_number DESC);

-- =============================================================================
-- 3. witness_anchor — 见证锚定主副本（组件 1，强一致）
-- =============================================================================
CREATE TABLE witness_anchor (
  memory_id                 TEXT    PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,
  narrative_coherence_score REAL    NOT NULL DEFAULT 0 CHECK (narrative_coherence_score BETWEEN 0 AND 1),
  last_calibrated_at        TEXT,
  calibration_count         INTEGER NOT NULL DEFAULT 0,
  anchor_version            INTEGER NOT NULL DEFAULT 1,
  overridden_by_external    INTEGER NOT NULL DEFAULT 0 CHECK (overridden_by_external IN (0,1))
);

-- =============================================================================
-- 4. usage_weight — 使用权重影子副本（组件 1，最终一致）
-- =============================================================================
CREATE TABLE usage_weight (
  memory_id              TEXT    PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,
  usage_count            INTEGER NOT NULL DEFAULT 0,
  last_used_at           TEXT,
  activation_weight      REAL    NOT NULL DEFAULT 0 CHECK (activation_weight BETWEEN 0 AND 1),
  use_load_retrieval     REAL    NOT NULL DEFAULT 0,
  use_load_verification  REAL    NOT NULL DEFAULT 0,
  use_load_contribution  REAL    NOT NULL DEFAULT 0,
  use_load_simulation    REAL    NOT NULL DEFAULT 0,
  use_load_implicit      REAL    NOT NULL DEFAULT 0,
  exploration_confidence REAL    NOT NULL DEFAULT 0 CHECK (exploration_confidence BETWEEN 0 AND 1),
  suspect_flag           INTEGER NOT NULL DEFAULT 0 CHECK (suspect_flag IN (0,1))
);

-- =============================================================================
-- 5. journal_buffer — 写入暂存区（组件 1）
-- =============================================================================
CREATE TABLE journal_buffer (
  id            TEXT    PRIMARY KEY,                                     -- UUID
  session_id    TEXT    NOT NULL,
  raw_content   TEXT    NOT NULL,                                        -- JSONB：原始轮次 role + content
  digest_status TEXT    NOT NULL DEFAULT 'pending'
                        CHECK (digest_status IN ('pending','processing','completed','failed')),
  digest_result TEXT,
  retry_count   INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  processed_at  TEXT
);

CREATE INDEX idx_journal_session ON journal_buffer(session_id);
CREATE INDEX idx_journal_status  ON journal_buffer(digest_status);

-- =============================================================================
-- 6. usage_events — 事件总线持久化（组件 7）
-- =============================================================================
-- event_type 取值见架构 architecture-v0.1.0.md §10.10；竖切范围内为 4 类：
--   use_event / calibration_signal / degradation_switch / latent_trigger
-- 不加 CHECK 约束——枚举随架构演进扩展，由应用层校验。
CREATE TABLE usage_events (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,                        -- BIGSERIAL
  event_type   TEXT    NOT NULL,
  source_layer TEXT    NOT NULL,
  memory_id    TEXT    REFERENCES memories(id) ON DELETE SET NULL,
  context      TEXT,                                                     -- JSONB
  severity     INTEGER NOT NULL DEFAULT 0 CHECK (severity BETWEEN 0 AND 9),
  created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ttl          INTEGER                                                   -- INTERVAL → 整数秒
);

-- PG 侧按 created_at 时间分区；SQLite 无分区（data-model §13.2）。
-- 降级方案：单表 + 下列索引，维护引擎按 created_at 批量 DELETE + VACUUM 实现等效归档。
CREATE INDEX idx_usage_events_memory_time ON usage_events(memory_id, created_at);
CREATE INDEX idx_usage_events_created     ON usage_events(created_at);

-- =============================================================================
-- 7. forgetting_queue — 遗忘候选队列（组件 4）
-- =============================================================================
CREATE TABLE forgetting_queue (
  id              TEXT PRIMARY KEY,                                      -- UUID
  memory_id       TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  forgetting_score REAL NOT NULL CHECK (forgetting_score BETWEEN 0 AND 1),
  reason          TEXT,
  status          TEXT NOT NULL
                       CHECK (status IN ('pending_archive','archived','revoked')),
  created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_forgetting_status ON forgetting_queue(status, forgetting_score DESC);

-- =============================================================================
-- 8. audit_log — 审计日志 HMAC 链（组件 6）
-- =============================================================================
-- AUTOINCREMENT 必需：保证 id 单调不复用，删除后不回绕，维持 HMAC 链的时序假设。
CREATE TABLE audit_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,                       -- BIGSERIAL
  "timestamp"   TEXT NOT NULL,
  operator      TEXT NOT NULL,
  action        TEXT NOT NULL,
  target_type   TEXT CHECK (target_type IS NULL OR target_type IN ('memory','config','user','redline')),
  target_id     TEXT,
  content_hash  TEXT,                                                    -- SHA-256(操作内容)
  previous_hash TEXT,                                                    -- 上一条的 HMAC
  hmac          TEXT NOT NULL,                                           -- HMAC-SHA256 签名
  details       TEXT,                                                    -- JSONB
  redline_id    TEXT
);

CREATE INDEX idx_audit_time   ON audit_log("timestamp");
CREATE INDEX idx_audit_target ON audit_log(target_type, target_id);

-- =============================================================================
-- 9. config — 运行时配置（组件 9）
-- =============================================================================
CREATE TABLE config (
  "key"      TEXT PRIMARY KEY,
  "value"    TEXT NOT NULL,
  scope      TEXT NOT NULL DEFAULT 'static'
                  CHECK (scope IN ('static','dynamic','override')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_by TEXT
);

-- =============================================================================
-- 10. seeds — 冷启动种子锚点（组件 9）
-- =============================================================================
CREATE TABLE seeds (
  id                 TEXT    PRIMARY KEY,                                -- UUID
  path               TEXT    NOT NULL UNIQUE,                            -- kairos://_system/seeds/{name}
  seed_type          TEXT    NOT NULL CHECK (seed_type IN ('config','identity','calibration')),
  initial_confidence REAL    NOT NULL CHECK (initial_confidence BETWEEN 0 AND 1),
  current_confidence REAL    NOT NULL CHECK (current_confidence BETWEEN 0 AND 1),
  degradation_level  REAL    NOT NULL DEFAULT 0 CHECK (degradation_level BETWEEN 0 AND 1),
  status             TEXT    NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active','degrading','retired')),
  created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  last_reviewed_at   TEXT,
  review_count       INTEGER NOT NULL DEFAULT 0,
  bias_reset_count   INTEGER NOT NULL DEFAULT 0,
  content_snapshot   TEXT                                                -- JSONB
);

-- =============================================================================
-- 11. memory_states — 状态变更审计轨迹（组件 1/4）
-- =============================================================================
-- 无 UNIQUE 约束：支持同一记忆多次状态转换，保留完整历史。
-- data-model 未对 memory_id 声明 FK（历史轨迹需在记忆硬删除后仍可追溯），此处保持一致不建 FK。
CREATE TABLE memory_states (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,                    -- BIGSERIAL
  memory_id        TEXT    NOT NULL,                                     -- 关联 memories.id（不建 FK）
  memory_type      TEXT    NOT NULL
                           CHECK (memory_type IN ('storage','knowledge','experience','task')),
  state            TEXT    NOT NULL
                           CHECK (state IN ('active','stale','archived','suppressed','superseded')),
  previous_state   TEXT    NOT NULL DEFAULT '',
  state_changed_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  reason           TEXT    NOT NULL DEFAULT '',
  source           TEXT    NOT NULL DEFAULT 'system'
);

CREATE INDEX idx_memory_states_history ON memory_states(memory_id, state_changed_at);

-- =============================================================================
-- 12. entities — 实体表（组件 3，实体加成信号）
-- =============================================================================
CREATE TABLE entities (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,                         -- BIGSERIAL
  user_id     TEXT    NOT NULL,
  name        TEXT    NOT NULL,
  type        TEXT    NOT NULL DEFAULT 'concept'
                      CHECK (type IN ('project','people','concept','tool')),
  description TEXT,
  embedding   BLOB,                                                      -- VECTOR(1536)
  metadata    TEXT,                                                      -- JSONB
  created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE (user_id, name)
);

-- =============================================================================
-- 13. memory_entities — 记忆-实体关联（组件 3）
-- =============================================================================
-- superseded_by：data-model §八 RC-04 修正为 BIGINT（此前误标 UUID，与自引用目标类型不符）。
-- UNIQUE(memory_id, entity_id, valid_from)：valid_from 为 NULL 时 SQLite 视各 NULL 互不相等
-- （与 PostgreSQL 行为一致），即"当前有效"关系可重复插入——由应用层保证唯一。
CREATE TABLE memory_entities (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,                       -- BIGSERIAL
  memory_id     TEXT    NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  entity_id     INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  relation      TEXT    NOT NULL DEFAULT 'mentions',
  valid_from    TEXT,
  valid_to      TEXT,
  superseded_by INTEGER REFERENCES memory_entities(id) ON DELETE SET NULL,
  UNIQUE (memory_id, entity_id, valid_from)
);

CREATE INDEX idx_memory_entities_entity ON memory_entities(entity_id);

-- =============================================================================
-- 14. memories_fts — FTS5 全文索引（组件 3，BM25 信号）
-- =============================================================================
-- contentless-external 模式：仅存倒排索引，原文通过 rowid 关联 memories。
-- 中文分词：v0.1.0 使用 unicode61；jieba tokenizer 需编译扩展后改为 tokenize='jieba'。
CREATE VIRTUAL TABLE memories_fts USING fts5(
  content,
  content_summary,
  path,
  content='memories',
  content_rowid='rowid',
  tokenize='unicode61'
);

-- 同步触发器：SQLite 的 external content 模式**不会**自动同步索引，
-- 必须显式建立下列三个触发器（SQLite 官方 FTS5 §4.4.3）。
CREATE TRIGGER memories_fts_ai AFTER INSERT ON memories BEGIN
  INSERT INTO memories_fts(rowid, content, content_summary, path)
  VALUES (new.rowid, new.content, new.content_summary, new.path);
END;

CREATE TRIGGER memories_fts_ad AFTER DELETE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, content, content_summary, path)
  VALUES ('delete', old.rowid, old.content, old.content_summary, old.path);
END;

CREATE TRIGGER memories_fts_au AFTER UPDATE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, content, content_summary, path)
  VALUES ('delete', old.rowid, old.content, old.content_summary, old.path);
  INSERT INTO memories_fts(rowid, content, content_summary, path)
  VALUES (new.rowid, new.content, new.content_summary, new.path);
END;

-- 索引优化：每 KAIROS_FTS5_OPTIMIZE_INTERVAL 秒执行一次
--   INSERT INTO memories_fts(memories_fts) VALUES('optimize');

-- =============================================================================
-- 15. schema_version — Schema 版本管理（组件 9）
-- =============================================================================
-- 单行表：始终只有一条记录。单行语义由应用层保证（INSERT OR REPLACE 以 version 为主键
-- 替换旧记录），与 data-model §十一 定义一致（无 singleton 列——对齐 data-model v0.0.10）。
CREATE TABLE schema_version (
  version        INTEGER PRIMARY KEY,
  applied_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  migration_name TEXT    NOT NULL,
  checksum       TEXT    NOT NULL
);

COMMIT;

-- =============================================================================
-- 后置校验（迁移脚本执行后由 W2 验收断言）
--   SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
--     AND name NOT LIKE 'memories_fts_%';        -- 期望 15（含 memories_fts 虚拟表）
--   PRAGMA foreign_key_check;                    -- 期望空结果集
--   PRAGMA integrity_check;                      -- 期望 'ok'
-- =============================================================================
