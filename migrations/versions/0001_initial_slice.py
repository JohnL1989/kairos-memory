"""竖切初始迁移：15 张表（schema-slice.sql 权威 DDL）

Revision ID: 0001
Revises:
Create Date: 2026-08-11

DDL 唯一承载：docs/specification/schema-slice.sql（data-model §13.4）。
本迁移解析并执行其 CREATE 语句（跳过 PRAGMA/BEGIN/COMMIT——由 Alembic
连接层与应用启动配置承载），保证迁移结果与权威 DDL 逐字一致；
ORM models.py 与 DDL 的一致性由 tests/unit/test_schema_alignment.py 校验。
FTS5 虚拟表与同步触发器随 schema-slice.sql 一并创建（ADR-011 手写 op.execute）。
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# schema-slice.sql 中的 CREATE 语句前缀（执行白名单）
_EXECUTABLE_PREFIXES = ("CREATE TABLE", "CREATE INDEX", "CREATE VIRTUAL TABLE", "CREATE TRIGGER")
# 跳过语句（连接层/启动配置承载）
_SKIP_PREFIXES = ("PRAGMA", "BEGIN", "COMMIT")

# 触发器清单（downgrade 显式删除；SQLite DROP TABLE 不级联删触发器）
_FTS_TRIGGERS = ("memories_fts_ai", "memories_fts_ad", "memories_fts_au")

# 建表语句顺序（依赖关系）：引用方在后
_DDL_SOURCE = Path(__file__).resolve().parents[2] / "docs" / "specification" / "schema-slice.sql"


def _ddl_statements() -> list[str]:
    """解析 schema-slice.sql，返回可执行 CREATE 语句列表（保持原顺序）。

    行扫描 + 触发器块感知（CREATE TRIGGER ... BEGIN ... END 内含分号，
    不能按分号简单分割）；语句以分号或 END 收尾。
    """
    sql = _DDL_SOURCE.read_text(encoding="utf-8")
    statements: list[str] = []
    buf: list[str] = []
    in_trigger = False
    for raw_line in sql.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        upper = stripped.upper()
        if upper.startswith("--"):
            # 语句前注释并入缓存（执行时 SQLite 可解析），独立注释块丢弃
            if not buf:
                continue
            buf.append(raw_line)
            continue
        if upper.startswith("PRAGMA") or upper.rstrip(";") in ("BEGIN", "COMMIT"):
            # 连接级配置/事务控制由 Alembic 与应用启动承载，跳过
            continue
        buf.append(raw_line)
        if upper.startswith("CREATE TRIGGER"):
            in_trigger = True
            continue
        if in_trigger:
            if upper.rstrip(";") == "END":
                in_trigger = False
                statements.append("\n".join(buf))
                buf = []
            continue
        # 语句结束判定：剥离行尾注释后以分号收尾（行内可含多条语句）
        code_part = stripped.split("--")[0].rstrip()
        if code_part.endswith(";"):
            statements.append("\n".join(buf))
            buf = []
    return statements


def upgrade() -> None:
    for stmt in _ddl_statements():
        op.execute(stmt)


def downgrade() -> None:
    for trigger in _FTS_TRIGGERS:
        op.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    # 显式清单逆序 DROP（schema-slice.sql 15 张表；引用方在前，被引用方在后）
    tables: list[str] = [
        "memory_versions",
        "usage_weight",
        "witness_anchor",
        "journal_buffer",
        "usage_events",
        "forgetting_queue",
        "audit_log",
        "config",
        "seeds",
        "memory_states",
        "memory_entities",
        "entities",
        "memories_fts",
        "schema_version",
        "memories",  # 最后（自引用 FK + 被引用最多）
    ]
    for name in tables:
        op.execute(f"DROP TABLE IF EXISTS {name}")
