"""ORM models ↔ schema-slice.sql 权威 DDL 一致性校验（竖切 15 张表）。

防漂移：migrations 从 schema-slice.sql 执行 DDL（单一事实源），
本测试断言 ORM metadata 与权威 DDL 的表/列/约束集合一致——
models.py 改动若与 DDL 偏离即失败（data-model §13.4 对齐纪律）。
"""

from __future__ import annotations

import re

from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable

from src.paths import SCHEMA_SLICE_SQL
from src.storage.models import SLICE_TABLES, Base

# DDL 中表名（CREATE TABLE / CREATE VIRTUAL TABLE / CREATE INDEX 目标）
_TABLE_RE = re.compile(r"CREATE (?:VIRTUAL )?TABLE ([a-z_]+)\b")
_INDEX_TARGET_RE = re.compile(r"CREATE INDEX \w+ ON ([a-z_]+)\(")
_TRIGGER_RE = re.compile(r"CREATE TRIGGER (\w+)")


def _ddl_tables() -> set[str]:
    sql = SCHEMA_SLICE_SQL.read_text(encoding="utf-8")
    return set(_TABLE_RE.findall(sql))


def _ddl_indexed_tables() -> set[str]:
    sql = SCHEMA_SLICE_SQL.read_text(encoding="utf-8")
    return set(_INDEX_TARGET_RE.findall(sql))


def _metadata_table_names() -> set[str]:
    names = set(Base.metadata.tables.keys())
    # FTS 虚拟表不经 ORM（ADR-011），从 DDL 侧校验
    names.discard("memories_fts")
    return names


class TestTableCoverage:
    def test_slice_table_count_is_15(self) -> None:
        assert len(SLICE_TABLES) == 16
        assert len(_ddl_tables()) == 16

    def test_ddl_tables_match_slice_manifest(self) -> None:
        ddl = _ddl_tables()
        manifest = set(SLICE_TABLES)
        assert ddl == manifest

    def test_orm_tables_match_ddl(self) -> None:
        ddl = _ddl_tables()
        orm = _metadata_table_names()
        # ORM 应覆盖除 FTS 外全部 DDL 表，且无多余表（FTS 经迁移 op.execute 创建，ADR-011）
        assert orm == ddl - {"memories_fts"}

    def test_fts_sync_triggers_present(self) -> None:
        """memories_fts 三个同步触发器（schema-slice.sql §14）。"""
        sql = SCHEMA_SLICE_SQL.read_text(encoding="utf-8")
        triggers = set(_TRIGGER_RE.findall(sql))
        assert {"memories_fts_ai", "memories_fts_ad", "memories_fts_au"} <= triggers


class TestColumnAlignment:
    """逐表列集合一致性（ORM ↔ DDL）。"""

    @staticmethod
    def _ddl_create_statements() -> dict[str, str]:
        sql = SCHEMA_SLICE_SQL.read_text(encoding="utf-8")
        tables: dict[str, str] = {}
        for match in _TABLE_RE.finditer(sql):
            name = match.group(1)
            start = match.start()
            # 语句结尾 = 下一个 ";"（schema-slice.sql 内无内嵌分号）
            end = sql.find(";", start)
            tables[name] = sql[start : end if end != -1 else len(sql)]
        return tables

    @staticmethod
    def _ddl_columns(create_stmt: str) -> set[str]:
        header_end = create_stmt.find("(")
        body = create_stmt[header_end + 1 :]
        columns: set[str] = set()
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("--"):
                continue
            # 表级约束行（CHECK/UNIQUE/INDEX/PRIMARY KEY 等）跳过；
            # 注意 \b 防止 CHECKSUM 误判为 CHECK 约束
            if re.match(r"^(CHECK\b|UNIQUE|INDEX|PRIMARY|FOREIGN|CONSTRAINT)", line, re.IGNORECASE):
                continue
            col_match = re.match(r'^"?([a-z_]+)"?\s', line)
            if col_match:
                columns.add(col_match.group(1))
        return columns

    @staticmethod
    def _orm_columns(table_name: str) -> set[str]:
        # 用 SQLite 内存引擎编译 ORM DDL 提取列名
        engine = create_engine("sqlite:///:memory:")
        stmt = str(CreateTable(Base.metadata.tables[table_name]).compile(engine))
        engine.dispose()
        columns: set[str] = set()
        for line in stmt.splitlines():
            line = line.strip().rstrip(",")
            if not line or line.startswith(
                ("--", "CREATE", "CONSTRAINT", "UNIQUE", "CHECK", "PRIMARY", "FOREIGN")
            ):
                continue
            col_match = re.match(r'^"?([a-z_]+)"?\s', line)
            if col_match:
                columns.add(col_match.group(1))
        return columns

    def test_all_tables_column_alignment(self) -> None:
        ddl_tables = self._ddl_create_statements()
        for name in sorted(set(SLICE_TABLES) - {"memories_fts"}):
            ddl_cols = self._ddl_columns(ddl_tables[name])
            orm_cols = self._orm_columns(name)
            assert ddl_cols == orm_cols, (
                f"表 {name} 列不一致: DDL-only={ddl_cols - orm_cols} ORM-only={orm_cols - ddl_cols}"
            )
