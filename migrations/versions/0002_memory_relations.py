"""memory_relations 关系索引表迁移（kairos_link/unlink/relations 数据层）

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13

DDL 唯一承载：docs/specification/schema-slice.sql（data-model §13.4）。
本迁移执行 memory_relations 表 + 索引的 CREATE 语句（契约：data-model §1；
MCP 关系管理三工具 kairos_link/unlink/relations 数据层，架构 §7.1a）。

本表是 0001 初始迁移的增量（竖切交付时遗漏），遵循同一 DDL 承载原则。
"""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_CREATE_TABLE = """
CREATE TABLE memory_relations (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id     TEXT    NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  target_id     TEXT    NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  relation_type TEXT    NOT NULL,
  strength      REAL    NOT NULL DEFAULT 1.0,
  reason        TEXT,
  confidence    REAL,
  created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  deleted_at    TEXT,
  UNIQUE (source_id, target_id, relation_type)
);
"""

_CREATE_INDEXES = """
CREATE INDEX idx_memory_relations_target ON memory_relations(target_id);
CREATE INDEX idx_memory_relations_type ON memory_relations(relation_type);
"""


def upgrade() -> None:
    # IF NOT EXISTS 幂等防御（schema-slice.sql 为当前权威含本表，0001 已跳过——
    # 防其他建库路径重复执行）
    op.execute(
        _CREATE_TABLE.replace("CREATE TABLE memory_relations", "CREATE TABLE IF NOT EXISTS memory_relations")
    )
    # SQLAlchemy op.execute 单语句限制：索引逐条执行
    op.execute("CREATE INDEX IF NOT EXISTS idx_memory_relations_target ON memory_relations(target_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_memory_relations_type ON memory_relations(relation_type);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memory_relations")
