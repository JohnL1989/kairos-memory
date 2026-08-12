"""项目路径常量（避免各模块重复推导项目根）。"""

from __future__ import annotations

from pathlib import Path

# 项目根（src/paths.py 的上上级 = 仓库根）
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 竖切权威 DDL（W2 迁移的权威对照；data-model §13.4）
SCHEMA_SLICE_SQL = PROJECT_ROOT / "docs" / "specification" / "schema-slice.sql"

# 迁移目录（Alembic）
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"

# 审计脚本（CI 门禁）
DOC_AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "doc-audit.py"
DEEP_AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "deep-audit.py"
