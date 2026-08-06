#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kairos 文档一致性审计脚本 —— documentation-governance §2/§3 的执行工具。

用法:
    python scripts/doc-audit.py            # 审计仓库根目录 docs/
    python scripts/doc-audit.py <子目录>   # 指定相对目录

退出码: 0 = 全部通过（可作里程碑门禁）；1 = 存在失败项。
仅依赖标准库，可在 CI 或本地直接运行。

0.0.12 门禁扩展（开发就绪度审计遗留项闭环）:
  - 编号连续性（14）扩展至 G-xx/CJ-xxx/RSK-xxx/MRK-xxx 五个命名空间（条目定义行口径）
  - 新增决策编号标注检查（14a）：决策 D-xx 两位数的正文引用行内无决策语境词时 warn
  - 债务闭环真实性（10）改正文口径：版本记录中的历史提及不算落地证据，区分
    「仅版本记录可见」与「完全不可见」两档
  - 陈旧数值（6.6）集中为显式清单 + 权威数值历史值邻近检查（负向后瞻排除
    「原」「「」引述与勘误语境）

0.0.34 门禁扩展（round14 审计防复发建议落地）:
  - 新增治理面计数一致性（6.17）：架构 §0 图题/统一口径/结构原则三处
    治理面计数必须同为「两个」+ 身份面不入计数声明（R14-01 防复发）
  - 新增检索权重公式唯一性（6.18）：§5.2 三链路历史配比必须带
    「历史配比」注记，四链路配比必须存在（R14-03 防复发）
  - 新增 §10.24 关联债索引完整性（6.19）：debt-collection §四 摘要表
    D-0xx 活跃债编号 ⊆ §10.24 第一组收录集合（R14-06 防复发）
"""
from __future__ import annotations

import pathlib
import re
import sys

SECTION_MARK = "\u00a7"  # §
ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TOKEN = r"[A-Za-z0-9_+./\-]+\.md"

# 审计产物目录不参与文档一致性校验——评审报告需引用原文（含陈旧值样本）
EXCLUDE_DIRS = {"reviews"}

FAILS: list[str] = []
WARNS: list[str] = []


def md_files():
    """遍历受治理的 Markdown 文档，跳过审计产物目录。"""
    for p in DOCS.rglob("*.md"):
        if EXCLUDE_DIRS & set(p.relative_to(DOCS).parts):
            continue
        yield p


def fail(msg: str) -> None:
    FAILS.append(msg)


def warn(msg: str) -> None:
    WARNS.append(msg)


def heading_ids(text: str) -> set[str]:
    """提取 Markdown 标题中的编号（0.1 / 7.3.1 / A.5 / 一 等）。"""
    ids: set[str] = set()
    for line in text.splitlines():
        m = re.match(
            r"^ {0,3}#{2,4}\s+(?:%s)?([0-9A-Z一二三四五六七八九十]+(?:\.[0-9]+)*)"
            % SECTION_MARK,
            line.strip(),
        )
        if m:
            ids.add(m.group(1))
    return ids


def section_exists(cit: str, ids: set[str]) -> bool:
    """章节号存在性：先精确匹配，再回退到父级章节。"""
    parts = cit.split(".")
    for i in range(len(parts), 0, -1):
        if ".".join(parts[:i]) in ids:
            return True
    return False


def check_links() -> None:
    """1) 所有指向 .md 的 Markdown 链接目标必须存在。"""
    total = 0
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = m.group(1).split("#")[0].strip()
            if not target or target.startswith("http") or "://" in target:
                continue
            if not target.endswith(".md"):
                continue
            total += 1
            if not (p.parent / target).resolve().is_file():
                fail(f"链接目标不存在: {p.relative_to(DOCS)} -> {target}")
    print(f"[1/18] Markdown 链接检查: {total} 个链接")


def check_sections() -> None:
    """2) [文档](路径) §X 形式的跨文档章节引用必须指向存在的章节。"""
    heads: dict[str, set[str]] = {}
    for p in md_files():
        heads[p.name] = heading_ids(p.read_text(encoding="utf-8"))
    checked = 0
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(
            r"\[[^\]]*\]\(([^)]+\.md)\)\s*%s([0-9A-Z一二三四五六七八九十]+(?:\.[0-9]+)*)"
            % SECTION_MARK,
            text,
        ):
            tgt = m.group(1).split("#")[0]
            name = pathlib.Path(tgt).name
            if name not in heads:
                continue
            checked += 1
            if not section_exists(m.group(2), heads[name]):
                fail(
                    f"章节引用不存在: {p.relative_to(DOCS)} -> {tgt} §{m.group(2)}"
                )
    print(f"[2/18] 章节引用检查: {checked} 处引用")


def check_format() -> None:
    """3) 交叉引用必须使用 [文档名](相对路径) §X 格式，禁止裸文件名。"""
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        in_code = False
        for i, line in enumerate(text.splitlines()):
            s = line.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code or s.startswith("<!--"):
                continue
            stripped = re.sub(r"\[[^\]]*\]\([^)]*\)", "", line)
            stripped = re.sub(r"`[^`]*`", "", stripped)
            for m in re.finditer(
                r"(?<![A-Za-z0-9_+./\-])(" + TOKEN + r")(?![A-Za-z0-9_+./\-])",
                stripped,
            ):
                if m.group(1) != "SOUL.md":
                    fail(
                        f"裸文件名引用（应为链接格式）: {p.relative_to(DOCS)}:{i+1} {m.group(1)}"
                    )
    print("[3/18] 交叉引用格式检查")


def check_version_records() -> None:
    """4) 每份文档恰有一条 0.0.1 版本记录，且无旧版本行/旧版本标题。"""
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        # 0.0.16 起允许 0.0.1 行日期等于文档 created（新建文档不必伪造 2026-07-31）
        row_pat = re.compile(r"^\| 0\.0\.1 \| 2026-\d{2}-\d{2} \|", re.M)
        n = len(row_pat.findall(text))
        if n != 1:
            fail(f"版本记录异常（应恰有 1 条 0.0.1，实际 {n}）: {p.relative_to(DOCS)}")
        if not re.search(r"^#{1,6}\s*.*版本记录", text, re.M):
            fail(f"缺少版本记录章节: {p.relative_to(DOCS)}")
        for m in re.finditer(
            r"^\| (?:v?0\.1\.[1-9][0-9.]*|v1\.0\.0|v0\.1\.0-rc[0-9.]*) \|", text, re.M
        ):
            fail(f"旧版本行残留: {p.relative_to(DOCS)} -> {m.group(1)}")
        for m in re.finditer(r"^## (?:v?0\.1\.[1-9]|v1\.0\.0|v0\.1\.0-rc)", text, re.M):
            fail(f"旧版本标题残留: {p.relative_to(DOCS)} -> {m.group(0)}")
    print("[4/18] 版本记录检查")


def check_mislabels() -> None:
    """5) 无「认知基础 architecture-v0.1.0.md」类归属错位。"""
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        if "认知基础 architecture-v0.1.0.md" in text:
            fail(f"认知来源归属错位: {p.relative_to(DOCS)}")
    print("[5/18] 认知来源归属检查")


def _declared(text: str, pattern: str, label: str):
    """从文档中解析声明值。找不到返回 None 并记 fail。"""
    m = re.search(pattern, text)
    if not m:
        fail(f"未找到声明值: {label}（正则 {pattern}）")
        return None
    return int(m.group(1))


def _declared_pair(text: str, pattern: str, label: str):
    """解析声明中的两个数值（如 md/yaml 份数）。找不到返回 (None, None) 并记 fail。"""
    m = re.search(pattern, text)
    if not m:
        fail(f"未找到声明值: {label}（正则 {pattern}）")
        return None, None
    return int(m.group(1)), int(m.group(2))


def _assert_eq(actual: int, declared, label: str) -> None:
    if declared is None:
        return
    if actual != declared:
        fail(f"计数不一致 [{label}]: 实际统计 {actual}，文档声明 {declared}")


def count_data_model_tables(dm: str) -> int:
    """### 标题后 8 行内出现「| 列名」表头者，才算一张物理表。"""
    lines = dm.split("\n")
    n = 0
    for i, l in enumerate(lines):
        if l.startswith("### "):
            for j in range(i + 1, min(i + 8, len(lines))):
                if lines[j].startswith("| 列名"):
                    n += 1
                    break
    return n


def count_config_params(cfg: str):
    """返回 (正文参数数, 附录 A 参数数)。口径：表格行首单元格为 `KAIROS_*`。"""
    pat = r"^\|\s*`(KAIROS_[A-Z0-9_]+)`"
    idx = cfg.find("## 附录 A")
    if idx < 0:
        return len(set(re.findall(pat, cfg, re.M))), 0
    return (
        len(set(re.findall(pat, cfg[:idx], re.M))),
        len(set(re.findall(pat, cfg[idx:], re.M))),
    )


def count_glossary_terms(gl: str) -> int:
    """术语表术语数：4 列数据行去掉表头行（首列「术语」）与分隔行（首列 `:----`）。"""
    n = 0
    for line in gl.splitlines():
        if not line.startswith("|"):
            continue
        first = line.strip("|").split("|")[0].strip()
        if _ncells(line) == 4 and first not in ("术语", "") and not first.startswith(":"):
            n += 1
    return n


def check_numeric() -> None:
    """6) 关键数值：**实际统计**与文档声明双向比对（非字符串存在性检查）。"""
    dm = (DOCS / "specification" / "data-model.md").read_text(encoding="utf-8")
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    cfg = (DOCS / "ops" / "configuration.md").read_text(encoding="utf-8")
    err = (DOCS / "references" / "error-reference.md").read_text(encoding="utf-8")
    imp = (DOCS / "specification" / "implementation-map.md").read_text(encoding="utf-8")

    # 6.1 data-model 物理表数（README 声明 ↔ 实际统计）
    tables = count_data_model_tables(dm)
    _assert_eq(
        tables,
        _declared(readme, r"\*\*数据模型\*\* — (\d+) 张表", "README data-model 表数"),
        "data-model 物理表数",
    )
    _assert_eq(
        tables,
        _declared(imp, r"表数 \*\*(\d+)\*\*", "implementation-map 表数"),
        "implementation-map 表数",
    )

    # 6.2 配置参数（正文 / 附录 A / 合计）
    main_n, apx_n = count_config_params(cfg)
    _assert_eq(
        main_n,
        _declared(readme, r"\*\*配置参数参考\*\* — (\d+) 项参数", "README 参数数"),
        "configuration 正文参数数",
    )
    _assert_eq(
        apx_n,
        _declared(cfg, r"全库另有 \*\*(\d+) 项\*\*", "configuration 附录声明数"),
        "configuration 附录 A 参数数",
    )
    _assert_eq(
        main_n + apx_n,
        _declared(cfg, r"全库参数总数 = \d+ \+ \d+ = (\d+) 项", "configuration 总数"),
        "configuration 参数总数",
    )

    # 6.3 错误码
    codes = set(re.findall(r"^\|\s*`(ERR-[A-Z]+-\d+)`", err, re.M))
    _assert_eq(
        len(codes),
        _declared(readme, r"\*\*错误参考\*\* — \d+ 类 (\d+) 个错误码", "README 错误码数"),
        "error-reference 错误码数",
    )
    ts = (DOCS / "ops" / "troubleshooting.md").read_text(encoding="utf-8")
    missing = sorted(c for c in codes if c not in ts)
    if missing:
        fail(f"troubleshooting 错误码速查缺失 {len(missing)} 项: {missing[:5]}…")

    # 6.4 文档份数（0.0.16 起支持多 yaml：README 声明模式 `**N 份 md + M 份 yaml**`）
    md_n = sum(1 for _ in md_files())
    yaml_n = len([p for p in DOCS.rglob("*.yaml") if not (EXCLUDE_DIRS & set(p.relative_to(DOCS).parts))])
    md_decl, yaml_decl = _declared_pair(
        readme, r"\*\*(\d+) 份 md \+ (\d+) 份 yaml\*\*", "README 文档份数"
    )
    if md_decl is not None and md_n != md_decl:
        fail(f"docs/ 下 md 份数 {md_n} != README 声明 {md_decl}")
    if yaml_decl is not None and yaml_n != yaml_decl:
        fail(f"docs/ 下 yaml 份数 {yaml_n} != README 声明 {yaml_decl}")

    # 6.5 安全红线 S-01~S-19 完整
    sec = (DOCS / "security" / "security-specification.md").read_text(encoding="utf-8")
    redlines = set(re.findall(r"(?<![A-Za-z0-9])S-(\d\d)", sec))
    want = {f"{i:02d}" for i in range(1, 20)}
    if redlines != want:
        fail(f"安全红线编号异常: 缺 {sorted(want - redlines)} / 多 {sorted(redlines - want)}")

    if "10 类事件枚举" not in imp:
        fail("implementation-map 事件类型应为 10 类")

    # 6.7 术语表术语数（README 声明 ↔ 实际统计 ↔ 架构 §11 引用；0.0.20 增补架构侧，
    # 闭环第五轮审计 1-06 门禁盲区）
    gl = (DOCS / "references" / "glossary.md").read_text(encoding="utf-8")
    terms = count_glossary_terms(gl)
    _assert_eq(
        terms,
        _declared(readme, r"\*\*术语表\*\* — (\d+) 条中英文术语对照", "README 术语数"),
        "glossary 术语数",
    )
    arch = (DOCS / "foundation" / "architecture-v0.1.0.md").read_text(encoding="utf-8")
    _assert_eq(
        terms,
        _declared(arch, r"（(\d+) 条中英文对照）", "架构 §11 术语数"),
        "架构 §11 术语数（应等于 glossary 实际）",
    )

    # 6.8 ADR 数（README 声明 ↔ adr.md 实际标题数）
    adr = (DOCS / "governance" / "adr.md").read_text(encoding="utf-8")
    adr_n = len(re.findall(r"^## ADR-\d{3}", adr, re.M))
    _assert_eq(
        adr_n,
        _declared(readme, r"架构决策记录\*\* — (\d+) 项已采纳 ADR", "README ADR 数"),
        "adr.md ADR 数",
    )

    # 6.8a 操作目录 OP 数（README 声明 ↔ operation-catalog 实际 OP 行数；0.0.31 补盲区，
    # 闭环第十一轮审计 2.1-02）
    opc = (DOCS / "specification" / "operation-catalog.md").read_text(encoding="utf-8")
    op_n = len(re.findall(r"^\|\s*OP-\d{3}", opc, re.M))
    _assert_eq(
        op_n,
        _declared(readme, r"操作目录\*\* — (\d+) 项标准操作", "README 操作数"),
        "operation-catalog OP 数",
    )

    # 6.9 implementation-map 组件路径数 ↔ 实际统计 ↔ test-plan 单元下界
    comp_rows = len(re.findall(r"^\|\s*[^|]+\|\s*`src/", imp, re.M))
    _assert_eq(
        comp_rows,
        _declared(imp, r"登记 \*\*(\d+)\*\* 个组件代码路径", "implementation-map 组件数"),
        "implementation-map 组件路径数",
    )
    tp = (DOCS / "quality" / "test-plan.md").read_text(encoding="utf-8")
    _assert_eq(
        comp_rows,
        _declared(tp, r"下界 ≥ (\d+)", "test-plan 单元下界"),
        "test-plan 单元下界（应等于 implementation-map 组件数）",
    )

    # 6.10 E2E 计数：implementation-map 声明 ↔ test-plan 实际 E2E 行数
    e2e_n = len(re.findall(r"^\| E2E-\d+ \|", tp, re.M))
    _assert_eq(
        e2e_n,
        _declared(imp, r"(\d+) 条关键用户路径", "implementation-map E2E 数"),
        "implementation-map E2E 数（应等于 test-plan E2E 用例数）",
    )

    # 6.11 implementation-map 参数总数声明 ↔ configuration 实际统计
    _assert_eq(
        main_n + apx_n,
        _declared(imp, r"(\d+) 项参数（configuration 正文 \d+ \+ 附录 A \d+", "implementation-map 参数总数"),
        "implementation-map 参数总数（应等于 configuration 正文+附录）",
    )

    # 6.12 API 端点计数（api-spec 定义行 ↔ 口径注记声明；0.0.25 补盲区，闭环第八轮审计 1-1）
    # 定义行两种格式：`**METHOD /path**`（§一~§七 内联）与 `### METHOD /path`（§6.5+ 锚点式）
    api = (DOCS / "specification" / "api-spec.md").read_text(encoding="utf-8")
    api_ends = set()
    for m in re.finditer(
        r"^(?:\*{2}|###\s*)(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s*]+)",
        api,
        re.M,
    ):
        api_ends.add((m.group(1), m.group(2).split("?")[0]))
    v1_n = sum(1 for _m, p in api_ends if p.startswith("/v1/"))
    _assert_eq(
        v1_n,
        _declared(api, r"全库声明的 \*\*(\d+)\*\* 指 \*\*`/v1` 前缀", "api-spec 业务端点声明"),
        "api-spec /v1 业务端点数",
    )
    _assert_eq(
        len(api_ends),
        _declared(api, r"物理总数为 \*\*(\d+)\*\*", "api-spec 物理总数声明"),
        "api-spec 物理端点数",
    )

    # 6.6 陈旧数值残留
    # 陈旧值扫描：跳过「版本记录」历史条目行（历史摘要允许保留旧口径）。
    # 0.0.12 改进（门禁盲区 3）：硬编码清单集中为 STALE_EXACT（显式全文串）与
    # STALE_NEIGHBOR（权威数值的已知历史值，随量词匹配）——历史值随数值变更
    # 登记于此，避免清单遗忘；匹配加负向后瞻排除「原」「「」前缀（勘误注记与
    # 引述历史计数为合法语境）。
    all_text = "".join(_scannable(p.read_text(encoding="utf-8")) for p in md_files())
    for stale in [
        "169 项",
        "127 项扩展",
        "126 项扩展",
        "17 类事件",
        "端点数 79",
        "80 个 `/v1` 业务端点",
        "物理总数为 **81**",
        "共 81 端点",
        "55 张表",
        "176 项参数",
        "episodic/narrative",
        "narrative/semantic/procedural",
    ]:
        if stale in all_text:
            fail(f"陈旧数值残留: {stale}")
    # 权威数值的已知历史值（0.0.12 登记——数值变更时把旧值追加到对应列表）
    stale_neighbor: list[tuple[str, list[str]]] = [
        ("物理表数", ["56 张表", "55 张表"]),
        ("参数总数", ["334 项", "339 项", "341 项", "342 项", "347 项", "358 项"]),
        ("术语条数", ["53 条"]),
        ("组件路径数", ["64 个", "67 个"]),
        ("E2E 用例数", ["6 条"]),
        ("ADR 数", ["10 项已采纳 ADR", "11 项已采纳 ADR"]),
    ]
    for label, pats in stale_neighbor:
        for s in pats:
            if re.search(r"(?<![0-9原「])" + re.escape(s), all_text):
                fail(f"陈旧数值残留[{label}]: {s}")
    print(
        f"[6/18] 数值一致性检查（表 {tables} / 参数 {main_n}+{apx_n} / "
        f"错误码 {len(codes)} / 术语 {terms} / ADR {adr_n} / 组件 {comp_rows} / "
        f"E2E {e2e_n} / 文档 {md_n} md + {yaml_n} yaml）"
    )


def check_ddl_fields() -> None:
    """6.13 DDL<->data-model 字段集比对（0.0.26 补盲区，闭环第九轮审计 H-03/M-13）。

    schema-slice.sql 各表列名集合须与 data-model 同名表字段表一致——防
    data-model 新增字段后 schema-slice 未回填（H-03 类漏修）。
    """
    sql = (DOCS / "specification" / "schema-slice.sql").read_text(encoding="utf-8")
    dm = (DOCS / "specification" / "data-model.md").read_text(encoding="utf-8")

    sql_tables: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE VIRTUAL TABLE (\w+) \((.*?)\n\);|CREATE TABLE (\w+) \((.*?)\n\);", sql, re.S):
        name = m.group(1) or m.group(3)
        body = m.group(2) or m.group(4)
        cols: set[str] = set()
        for line in body.split("\n"):
            cm = re.match(r'\s*"([a-z_]+)"\s+\w+|^\s*([a-z_]+)\s+\w+|^\s*([a-z_]+),$', line.strip())
            if cm:
                cols.add(next(c for c in cm.groups() if c))
        sql_tables[name] = cols

    dm_tables: dict[str, set[str]] = {}
    cur = None
    for line in dm.split("\n"):
        hm = re.match(r"^### (?:[\d.]+ )?(\w+)", line)
        if hm:
            cur = hm.group(1)
            dm_tables[cur] = set()
            continue
        cm = re.match(r"^\| `([a-z_]+)` \|", line)
        if cm and cur is not None:
            dm_tables[cur].add(cm.group(1))

    bad = 0
    for tname in sorted(sql_tables):
        sc = sql_tables[tname]
        dc = dm_tables.get(tname)
        if dc is None:
            fail(f"DDL 表 {tname} 在 data-model 无同名字段表（6.13）")
            bad += 1
            continue
        only_dm = dc - sc
        only_sql = sc - dc
        if only_dm:
            fail(f"DDL<->data-model 字段集不一致[{tname}]: data-model 有、schema-slice 缺 {sorted(only_dm)}（6.13）")
            bad += 1
        if only_sql:
            fail(f"DDL<->data-model 字段集不一致[{tname}]: schema-slice 有、data-model 缺 {sorted(only_sql)}（6.13）")
            bad += 1
    print(f"[6.13] DDL<->data-model 字段集比对: {len(sql_tables)} 表，{bad} 项差异")


MECH_SECTIONS: list[tuple[str, str]] = [
    # 机制名 → 权威章节号（0.0.26 登记，闭环第九轮审计 H-01/M-01/M-05/M-06）
    # 注：「预测器」未收录——其定位横跨 §3.1（定位节）与 §3.2（核心组件），单值映射会误报
    ("价值上下文管理器", "3.3"),
    ("保守倾向闸门", "3.3"),
    ("辞典式裁决器", "3.3"),
    ("帕累托约束集", "3.3"),
    ("帕累托前沿", "3.3"),
    ("候选生成器", "3.3"),
    ("使用负载计量器", "3.3"),
    ("负载计量", "3.3"),
    ("结构注入器", "3.3"),
    ("序数压制幅度记录", "3.3"),
    ("排列漂移审计", "3.3"),
    ("全局合规声明", "3.3"),
    ("跨层三环不变量", "10.3"),
    ("MCP Bridge", "7.1a"),
    ("检索深度分级", "3.9"),
    ("汇聚式多路径融合", "4.2"),
    ("汇聚式融合", "4.2"),
    ("真理路由器", "3.2.1"),
    ("情感基线提升", "3.2"),
    ("组合寄存器", "3.2"),
    ("前瞻保持", "3.2"),
    ("校准信号冲突消解", "3.2"),
    ("意图契约", "3.2"),
    ("调节器", "3.2"),
]

_SECT_REF = re.compile(r"§(\d+(?:\.\d+)*[a-z]?)")


def check_mechanism_sections() -> None:
    """6.14 机制名→权威章节映射抽检（0.0.26 补盲区，闭环第九轮审计 H-01/M-13）。

    高频核心机制建立「机制名 → 权威章节」映射，扫描全库正文：引用行同时出现
    机制名与 §X 时，§X 必须命中该机制的权威章节（含父级回退）——拦截
    「§3.2 辞典式裁决器」类语义落点漂移。历史记录（版本记录区/changelog）
    不参与判定。
    """
    bad = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS))
        if rel == "governance/changelog.md":
            continue
        for line in _scannable(p.read_text(encoding="utf-8")):
            hit = next((m for m, _sec in MECH_SECTIONS if m in line), None)
            if hit is None:
                continue
            canonical = next(sec for m, sec in MECH_SECTIONS if m == hit)
            refs = _SECT_REF.findall(line)
            if not refs:
                continue
            # 权威章节命中（含父级回退，如 3.2 的权威 3.2.1）即视为正确
            ok = any(
                ref == canonical or canonical.startswith(ref + ".")
                for ref in refs
            )
            if not ok:
                fail(f"机制「{hit}」权威章节 §{canonical}，但 {rel} 引用 {sorted(set(refs))}（6.14）")
                bad += 1
    print(f"[6.14] 机制名→权威章节抽检: {len(MECH_SECTIONS)} 条映射，{bad} 项漂移")


def check_hard_line_refs() -> None:
    r"""6.15 硬行号引用禁令（0.0.28 补盲区，闭环第十轮审计 C-03/F-01）。

    语义化交叉引用是 documentation-governance §2 的规范（文档名+章节）；
    `path.md:行号` 引用随编辑必漂移（configuration 附录 A 曾 135/136 漂移），
    整体废除。匹配 `[\w.\-/]+\.md:\d+` 即报错；reviews/ 为审计产物（证据需
    引用原文行号）不在扫描范围（EXCLUDE_DIRS）。
    """
    bad = 0
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        hits = re.findall(r"[\w.\-/]+\.md:\d+(?:-\d+)?", text)
        for h in hits:
            fail(f"硬行号引用禁令（6.15）: {p.relative_to(DOCS)} -> {h}（改「文档 §章节」语义引用）")
            bad += 1
    print(f"[6.15] 硬行号引用禁令: {bad} 处残留")


def check_line_endings() -> None:
    """6.16 行尾一致性检查（0.0.31 补，闭环第十一轮审计 2.4-01）。

    全库 md 统一 LF 行尾（.gitattributes: * text=auto eol=lf）——CRLF 残留
    会产生跨平台行尾噪声 diff。
    """
    bad = 0
    for p in md_files():
        if b"\r\n" in p.read_bytes():
            fail(f"CRLF 行尾残留（6.16）: {p.relative_to(DOCS)}（统一 LF，见 .gitattributes）")
            bad += 1
    print(f"[6.16] 行尾一致性检查: {bad} 份 CRLF 残留")


def check_governance_count() -> None:
    """6.17 治理面计数一致性（0.0.34 补盲区，闭环 round14 R14-01）。

    §0 三处治理面计数必须同为「两个」：① §0.4.1 图题（骨架视图行）
    ② §0.4 统一口径行 ③ 结构原则对应行（须声明「身份面不入治理面计数」）。
    三处任一处漂移即 fail——防「三个/两个正交治理面」新旧口径并存复发。
    """
    p = DOCS / "foundation" / "architecture-v0.1.0.md"
    text = p.read_text(encoding="utf-8")
    bad = 0

    m = re.search(r"骨架视图[^\n]*?六层功能栈 \+ (两个|2 ?个)正交治理面", text)
    if not m:
        fail("§0.4.1 图题治理面计数非「两个」（6.17）")
        bad += 1

    m = re.search(r"\*\*统一口径\*\*[^\n]*?(两个|2 ?个)正交治理面", text)
    if not m:
        fail("§0.4 统一口径治理面计数非「两个」（6.17）")
        bad += 1

    m = re.search(r"\*\*结构原则对应\*\*[^\n]*", text)
    if not m or "不入治理面计数" not in m.group(0):
        fail("§0.4 结构原则未声明「身份面不入治理面计数」（6.17）")
        bad += 1

    print(f"[6.17] 治理面计数一致性: §0 三处口径，{bad} 项漂移")


def check_retrieval_weights() -> None:
    """6.18 检索权重公式唯一性（0.0.34 补盲区，闭环 round14 R14-03）。

    §5.2 检索得分默认权重以四链路配比（0.50/0.20/0.10/0.20）为唯一权威；
    三链路历史配比（0.55/0.30/0.15）出现时必须带「历史配比」注记——
    防两套权重数字并存未标注（实现者无从确认现行默认值）。
    """
    p = DOCS / "foundation" / "architecture-v0.1.0.md"
    text = p.read_text(encoding="utf-8")
    start = text.find("### 5.2 组件")
    end = text.find("#### v1.1+ 蓝图组件摘要")
    seg = text[start:end] if start != -1 and end > start else text
    bad = 0

    m = re.search(r"最终检索得分 = 语义相似度", seg)
    if m:
        ctx = seg[m.start() : m.start() + 300]
        if "历史配比" not in ctx:
            fail("§5.2 三链路配比（0.55/0.30/0.15）未标注「历史配比」（6.18）")
            bad += 1
    else:
        fail("§5.2 三链路历史配比公式未找到（检查口径失配，6.18）")
        bad += 1

    # 四链路公式跨两行（「语义 0.50 +」行尾换行续「实体共现 0.20 …」）
    m = re.search(r"最终得分 = 语义 0\.50 [\s\S]{0,80}?因果 0\.20", seg)
    if not m:
        fail("§5.2 四链路配比公式（0.50/0.20/0.10/0.20）未找到（6.18）")
        bad += 1

    print(f"[6.18] 检索权重公式唯一性: 三/四链路配比，{bad} 项问题")


def check_debt_index() -> None:
    """6.19 §10.24 关联债索引完整性（0.0.34 补盲区，闭环 round14 R14-06）。

    debt-collection §四 摘要表 D-0xx 活跃债编号 ⊆ 架构 §10.24 第一组
    「架构设计间隙」收录集合——防「债已有架构落点但 §10.24 无索引」的
    跨文档追溯链断裂复发（round14 缺 D-006/008/016/019 四条教训）。
    口径注记：仅比对 D-0xx 段——§10.24 第二/三组与摘要表非一一映射
    （D-201~204 等仅收录于 §10.24 侧；D-1xx+ 债以蓝图/debt 正文为落点）。
    """
    debt = (DOCS / "governance" / "debt-collection.md").read_text(encoding="utf-8")
    arch = (DOCS / "foundation" / "architecture-v0.1.0.md").read_text(encoding="utf-8")
    m = re.search(r"## 四、已归档：认知-工程差距摘要[\s\S]*?(?=\n## 五、)", debt)
    active = set(re.findall(r"^\| (D-0\d{2}) \|", m.group(0), re.M)) if m else set()
    m = re.search(r"#### 一、架构设计间隙[\s\S]*?(?=\n#### 二、)", arch)
    indexed = set(re.findall(r"\[(D-0\d{2})\]", m.group(0))) if m else set()
    missing = sorted(active - indexed)
    for d in missing:
        fail(f"§10.24 关联债索引缺 {d}（摘要表活跃债无架构落点，6.19）")
    print(f"[6.19] §10.24 关联债索引完整性: 活跃 D-0xx {len(active)} 条，缺失 {len(missing)} 条")


def check_mcp_tool_rows() -> None:
    """6.12a MCP 工具表行数比对（0.0.28 补盲区，闭环第十轮审计 C-01）。

    MCP Bridge 工具集权威口径 15 个（0.0.14 裁决）——api-spec §6.8 注册表与
    架构 §7.1a 概览表的 `kairos_` 工具行数须相等且为 15，两表工具名集合须一致。
    """
    bad = 0
    api = (DOCS / "specification" / "api-spec.md").read_text(encoding="utf-8")
    arch = (DOCS / "foundation" / "architecture-v0.1.0.md").read_text(encoding="utf-8")
    sec68 = api[api.index("### 6.8"):api.index("### 6.9")]
    sec71a = arch[arch.index("### 7.1a"):arch.index("### 7.3")]
    api_tools = set(re.findall(r"^\|\s*`(kairos_[a-z_]+)`", sec68, re.M))
    arch_tools = set(re.findall(r"^\|\s*`(kairos_[a-z_]+)`", sec71a, re.M))
    if len(api_tools) != 15:
        fail(f"MCP 工具表行数（6.12a）: api-spec §6.8 实为 {len(api_tools)} 行，权威口径 15")
        bad += 1
    if len(arch_tools) != 15:
        fail(f"MCP 工具表行数（6.12a）: 架构 §7.1a 实为 {len(arch_tools)} 行，权威口径 15")
        bad += 1
    if api_tools != arch_tools:
        fail(f"MCP 工具表一致性（6.12a）: api-spec §6.8 与架构 §7.1a 工具名集合不一致——"
             f"仅 api-spec 有 {sorted(api_tools - arch_tools)} / 仅架构有 {sorted(arch_tools - api_tools)}")
        bad += 1
    print(f"[6.12a] MCP 工具表比对: api-spec {len(api_tools)} 行 / 架构 {len(arch_tools)} 行，{bad} 项差异")


def check_config_index() -> None:
    """7) 全库引用的 KAIROS_* 参数必须在 configuration.md 中有定义或索引。"""
    cfg = (DOCS / "ops" / "configuration.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"^\|\s*`(KAIROS_[A-Z0-9_]+)`", cfg, re.M))
    refs: dict[str, str] = {}
    for p in md_files():
        for i, line in enumerate(p.read_text(encoding="utf-8").split("\n")):
            for t in re.findall(r"KAIROS_[A-Z0-9_]*", line):
                if t.endswith("_"):          # KAIROS_FEATURE_* 之类通配前缀
                    continue
                refs.setdefault(t, f"{p.relative_to(DOCS)}:{i+1}")
    dangling = sorted(set(refs) - defined)
    for t in dangling[:10]:
        fail(f"悬空配置引用（未在 configuration.md 定义或索引）: {t} @ {refs[t]}")
    if len(dangling) > 10:
        fail(f"…另有 {len(dangling)-10} 项悬空配置引用")
    print(f"[7/18] 配置参数索引完整性: 引用 {len(refs)} 项，已索引 {len(refs)-len(dangling)} 项")


_CODE_SPAN = re.compile(r"`[^`]*`")


def _scannable(txt: str) -> str:
    """剔除「版本记录」章节的表格行——历史摘要允许保留旧口径，陈旧值扫描不计入。

    0.0.12 提升为模块级（原为 check_numeric 局部函数），供债务闭环检查与
    决策编号检查复用同一「正文口径」。
    """
    out, in_ver = [], False
    for line in txt.splitlines():
        if re.match(r"^#{1,6}\s*.*版本记录", line):
            in_ver = True
        elif line.startswith("#"):
            in_ver = False
        if not (in_ver and line.startswith("|")):
            out.append(line)
    return "\n".join(out)

def _ncells(row: str) -> int:
    """统计表格行的列数。正确处理：代码span内的 `|` 与转义 `\\|` 均不计为分隔符。"""
    masked = _CODE_SPAN.sub("", row)
    return masked.replace("\\|", "\x00").strip("|").count("|") + 1


def check_fences() -> None:
    """8) 代码围栏必须成对闭合。

    围栏失衡会让解析器把大段正文当作代码跳过——既破坏渲染，也使后续
    所有基于 in_code 的检查（交叉引用格式、表格渲染）对该区段完全失效。
    历史教训：一处游离/缺失围栏曾同时掩盖 80+ 项缺陷。
    """
    for p in md_files():
        lines = p.read_text(encoding="utf-8").split("\n")
        fences = [
            (i + 1, ln.strip())
            for i, ln in enumerate(lines)
            if ln.strip().startswith("```") or ln.strip().startswith("~~~")
        ]
        if len(fences) % 2:
            fail(
                f"代码围栏未成对（共 {len(fences)} 个，应为偶数）: "
                f"{p.relative_to(DOCS)} 围栏行号 {[n for n, _ in fences][-6:]}"
            )
            continue
        # 闭合围栏不应带语言标签——带标签说明此前有围栏缺失/多余
        for idx, (n, ln) in enumerate(fences):
            if idx % 2 == 1 and ln[3:].strip():
                fail(
                    f"闭合围栏带语言标签（提示此前存在缺失/多余围栏）: "
                    f"{p.relative_to(DOCS)}:{n} -> {ln}"
                )
    print("[8/18] 代码围栏配对检查")


def check_table_render() -> None:
    """9) 表格渲染：列数一致、数据行首尾管道齐全、无 `|` 开头的伪表格段落。"""
    for p in md_files():
        lines = p.read_text(encoding="utf-8").split("\n")
        in_code = False
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_code = not in_code
                i += 1
                continue
            if in_code:
                i += 1
                continue
            # 分隔行 → 定位一张表
            if re.match(r"^\|[\s\-:|]+\|$", s) and i > 0 and lines[i - 1].lstrip().startswith("|"):
                ncol = _ncells(s)
                hcol = _ncells(lines[i - 1].strip())
                if hcol != ncol:
                    fail(f"表头/分隔列数不符（{hcol} vs {ncol}）: {p.relative_to(DOCS)}:{i}")
                j = i + 1
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    row = lines[j].strip()
                    if not row.endswith("|"):
                        fail(f"表格数据行缺行尾管道符: {p.relative_to(DOCS)}:{j+1}")
                    else:
                        c = _ncells(row)
                        if c != ncol:
                            fail(f"表格列数不符（{c} vs {ncol}）: {p.relative_to(DOCS)}:{j+1}")
                    j += 1
                i = j
                continue
            # 伪表格：以 | 开头但既非表格行也非分隔行（前后无分隔行）
            if s.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", s):
                prev = lines[i - 1].strip() if i > 0 else ""
                nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if not prev.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", nxt):
                    fail(f"疑似误用 `|` 开头的段落（将被解析为单列表格）: {p.relative_to(DOCS)}:{i+1}")
            i += 1
    print("[9/18] 表格渲染检查")


def _version_rows(text: str) -> list[tuple[str, str]]:
    """提取「版本记录」章节中的 (版本号, 日期) 序列，按出现顺序返回。"""
    rows: list[tuple[str, str]] = []
    in_ver = False
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s*.*版本记录", line):
            in_ver = True
            continue
        if in_ver and line.startswith("#"):
            break
        if in_ver:
            m = re.match(
                r"^\|\s*v?(\d+\.\d+\.\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|", line
            )
            if m:
                rows.append((m.group(1), m.group(2)))
    return rows


def check_metadata_dates() -> None:
    """11) frontmatter `updated` 不得早于版本记录中的最新日期。

    改正文却不更新 frontmatter 是高频疏漏（复审时 28/51 份倒挂），
    人工评审无法发现，必须由门禁兜住。
    """
    n = 0
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^updated:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
        rows = _version_rows(text)
        if not m or not rows:
            continue
        n += 1
        newest = max(d for _, d in rows)
        if m.group(1) < newest:
            fail(
                f"元数据日期倒挂: {p.relative_to(DOCS)} "
                f"frontmatter updated={m.group(1)} < 版本记录最新 {newest}"
            )
    print(f"[11/18] 元数据日期一致性: 检查 {n} 份")


def check_version_monotonic() -> None:
    """12) 版本记录首条为 0.0.1，其后版本号严格递增、日期不倒退。"""
    for p in md_files():
        rows = _version_rows(p.read_text(encoding="utf-8"))
        if not rows:
            continue
        if rows[0][0] != "0.0.1":
            fail(f"版本记录首条应为 0.0.1: {p.relative_to(DOCS)} 实际 {rows[0][0]}")
        key = lambda v: tuple(int(x) for x in v.split("."))
        for a, b in zip(rows, rows[1:]):
            if key(b[0]) <= key(a[0]):
                fail(f"版本号未递增: {p.relative_to(DOCS)} {a[0]} -> {b[0]}")
            if b[1] < a[1]:
                fail(f"版本记录日期倒退: {p.relative_to(DOCS)} {a[1]} -> {b[1]}")
    print("[12/18] 版本记录单调性检查")


# D-01 决策：辞典式排序的定位从「兜底裁决」改为「在帕累托不可支配集上
# 标记默认推荐项」。旧语义一旦残留，会实质性推翻 P6 铁律的合规论证。
#
# 匹配需精确到「肯定式使用」——以下三类不算违规，必须放行：
#   (a) 否定式修订表述：「非兜底裁决」「不是兜底裁决」
#   (b) 引号内引述旧词：「由『兜底裁决』改为…」「不再表述为『兜底裁决』」
#   (c) 「最终裁决」中的「终裁」子串，以及身份面/宪法面否决权的正当终裁
# 行内添加 <!-- allow-deprecated --> 可额外豁免。
DEPRECATED_PATTERNS: list[tuple[str, str]] = [
    (r"(?<![非「])辞典式排序兜底", "D-01：应表述为「在不可支配集上标记默认推荐项」"),
    (r"(?<![非「])值优先兜底", "D-01：应表述为「值优先默认指针」"),
    (r"(?<![非「])(?<!不是)(?<!不做)兜底裁决", "D-01：辞典式排序不做兜底裁决"),
    (r"链本身\s*[=＝]\s*终裁", "D-01：链只在不可支配集上标记默认推荐项，不做终裁"),
    (r"辞典式[^。；\n]{0,20}(?<![非不])终裁", "D-01：辞典式排序不构成终裁"),
    # 2026-08-04 扩展（全库深度审计）：同义表述「六级链…兜底」「跨域兜底」
    # 为 D-01 修订前的语义残留；前导断言排除引号内引述（版本记录/勘误说明）
    (r"(?<![非「/])六级链[^。；\n]{0,12}兜底", "D-01：应表述为「在不可支配集上标记默认推荐项」"),
    (r"(?<![非「/])跨域兜底", "D-01：应表述为「跨域默认项选择」"),
    # 2026-08-04 扩展（第二轮全库深度审计）：版本记录模板残留（RC-09 修订后旧文案）
    (r"版本号固定为 0\.0\.1", "RC-09：草稿阶段从 0.0.1 起、实质变更按 0.0.2 → 递增，模板文案须同步"),
]


def check_deprecated_terms() -> None:
    """13) 裁决语境废弃术语残留（D-01 决策）。"""
    hits = 0
    for p in md_files():
        for i, line in enumerate(p.read_text(encoding="utf-8").split("\n")):
            if "allow-deprecated" in line:
                continue
            for pat, why in DEPRECATED_PATTERNS:
                m = re.search(pat, line)
                if m:
                    hits += 1
                    fail(
                        f"废弃术语残留: {p.relative_to(DOCS)}:{i+1} "
                        f"「{m.group(0)}」—— {why}"
                    )
    print(f"[13/18] 废弃术语检查（D-01 裁决模型）: {hits} 处命中")


def check_numbering_continuity() -> None:
    """14) 编号命名空间按段检查，段内不得断号。

    断号无法区分「从未分配」与「曾存在但被移除」。补墓碑条目占位后，
    编号自然连续，检查即通过。0.0.12 扩展：覆盖债务 D-xxx、差距 G-xx（含
    G-09a 子编号）、认知关节 CJ-xxx、架构风险 RSK-xxx、方法论风险 MRK-xxx
    五个命名空间——各命名空间以其「条目定义行」为分配证据（债务沿用全文
    匹配以捕获正文引用），避免把预留区间声明（如 RSK-008~019）误判为断号。
    """
    targets = [
        ("债务", DOCS / "governance" / "debt-collection.md",
         r"(?<![A-Za-z0-9])D-(\d{3})(?![0-9])", "text", "D-"),
        ("差距", DOCS / "governance" / "cognitive-architecture-gap.md",
         r"^\|\s*G-(\d{2}[a-z]?)\s*\|", "line", "G-"),
        ("认知关节", DOCS / "foundation" / "architecture-v0.1.0.md",
         r"^\|\s*CJ-(\d{3})\s*\|", "line", "CJ-"),
        ("架构风险", DOCS / "governance" / "risks.md",
         r"^###\s*RSK-(\d{3})", "line", "RSK-"),
        ("方法论风险", DOCS / "governance" / "risks.md",
         r"^###\s*MRK-(\d{3})", "line", "MRK-"),
    ]
    for label, path, pat, mode, prefix in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if mode == "line":
            # 子编号（如 G-09a）与主编号（G-09）归并——主编号连续性为准
            found = sorted({int(re.sub(r"[a-z]$", "", x)) for x in re.findall(pat, text, re.M)})
        else:
            found = sorted({int(x) for x in re.findall(pat, text)})
        if not found:
            continue
        buckets: dict[int, list[int]] = {}
        for n in found:
            buckets.setdefault(n // 100, []).append(n)
        for b, ns in sorted(buckets.items()):
            gaps = [i for i in range(min(ns), max(ns) + 1) if i not in ns]
            if gaps:
                fail(
                    f"{label}编号断号（须补墓碑条目占位或预留区间声明）: {path.name} "
                    f"{b}xx 段缺 {[prefix + '%03d' % g for g in gaps]}"
                )
    print("[14/18] 编号连续性检查")


def check_decision_numbering() -> None:
    """14a) 决策编号（D-xx 两位数）引用须可辨识——行内无决策语境词时 warn。

    决策编号（D-01~D-15，定义于 reviews fix-report）与债务编号（D-xxx 三位数）
    同前缀并存，仅靠位数区分。0.0.11 起 documentation-governance §5 将「显式
    标注体系」强化为强制规则；本检查兜住「决策 D-xx」引用在无决策语境行内
    的漏标（如「D-05 已迁入」）。行内含「决策|裁决|修订|裁定」等语境词的
    引用视为已可辨识，不 warn。
    """
    ctx_words = ("决策", "裁决", "修订", "裁定", "批准", "方案")
    hits = 0
    for p in md_files():
        if p.name in ("debt-collection.md", "changelog.md"):
            continue
        text = p.read_text(encoding="utf-8")
        scannable = _scannable(text)
        for i, line in enumerate(scannable.splitlines(), 1):
            for m in re.finditer(r"(?<![A-Za-z0-9])D-(\d{2})(?![0-9])", line):
                if any(w in line for w in ctx_words):
                    continue
                hits += 1
                warn(
                    f"决策编号引用建议标注「决策」前缀（区分债务 D-xxx 三位数）: "
                    f"{p.relative_to(DOCS)}:{i} 「{m.group(0)}」 {line.strip()[:60]}"
                )
    print(f"[14a/18] 决策编号标注检查: {hits} 处未标注")


def check_anchors() -> None:
    """15) Markdown 锚点链接（`路径#锚点` 与 `#锚点`）必须存在于目标标题 slug。"""
    def slugify(heading: str) -> str:
        s = re.sub(r"[^\w\u4e00-\u9fff\- ]", "", heading).strip().lower()
        return s.replace(" ", "-")

    slugs: dict[str, set[str]] = {}
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        found: set[str] = set()
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^ {0,3}#{1,6}\s+(.*)$", line)
            if m:
                found.add(slugify(m.group(1)))
        slugs[rel] = found

    checked = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"\[[^\]]*\]\(([^)#\s]+\.md)?#([^)\s]+)\)", text):
            target = m.group(1) or ""
            anchor = m.group(2).lower()
            if not anchor:
                continue
            if target:
                tgt = (p.parent / target).resolve()
                try:
                    trel = str(tgt.relative_to(DOCS)).replace("\\", "/")
                except ValueError:
                    continue
            else:
                trel = rel
            checked += 1
            if trel in slugs and anchor not in slugs[trel]:
                fail(f"锚点不存在: {rel} -> {target}#{m.group(2)}")
    print(f"[15/18] 锚点链接检查: {checked} 处")


def check_frontmatter() -> None:
    """16) frontmatter 必填字段：title / created / updated / last_reviewed / status。"""
    required = ["title", "created", "updated", "last_reviewed", "status"]
    n = 0
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---"):
            fail(f"frontmatter 缺失: {p.relative_to(DOCS)}")
            continue
        m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not m:
            fail(f"frontmatter 格式异常: {p.relative_to(DOCS)}")
            continue
        n += 1
        fields = set(re.findall(r"^([a-zA-Z_]+):", m.group(1), re.M))
        miss = [k for k in required if k not in fields]
        if miss:
            fail(f"frontmatter 缺字段 {miss}: {p.relative_to(DOCS)}")
    print(f"[16/18] frontmatter 必填字段: 检查 {n} 份")


def check_changelog_sync() -> None:
    """17) changelog 最新条目日期不得早于任何文档的版本记录最新日期。

    治理链条最容易在改动最大的那天断掉——正是最需要它生效的时候。
    """
    cl_path = DOCS / "governance" / "changelog.md"
    if not cl_path.is_file():
        return
    dates = re.findall(r"(\d{4}-\d{2}-\d{2})", cl_path.read_text(encoding="utf-8"))
    if not dates:
        fail("changelog.md 无任何日期条目")
        return
    newest = max(dates)
    stale: list[tuple[str, str]] = []
    for p in md_files():
        if p.name == "changelog.md":
            continue
        rows = _version_rows(p.read_text(encoding="utf-8"))
        if rows:
            d = max(x[1] for x in rows)
            if d > newest:
                stale.append((str(p.relative_to(DOCS)), d))
    for name, d in stale[:8]:
        fail(f"变更未登记 changelog: {name} 版本记录 {d} > changelog 最新 {newest}")
    if len(stale) > 8:
        fail(f"…另有 {len(stale)-8} 份文档的变更未登记 changelog")
    print(f"[17/18] changelog 同步检查: changelog 最新条目 {newest}")


def check_debt_closure() -> None:
    """10) 已闭环债务（§四 状态表标 ✅ 已实施/已决策）的落地必须他处可检索。

    墓碑占位（RC-15 编号连续性）与未闭环条目（设计锁定/新登记/路线图）零引用是
    正常状态——未实施条目在实现前不会被他处引用，不参与检查。
    0.0.12 改进（门禁盲区 1）：落地统计口径按「正文」而非「全文」——版本记录中的
    历史提及（如 changelog 批次说明）不算落地证据；区分「仅版本记录可见」与
    「完全不可见」两档，提高人工确认的信息质量。
    """
    dc_path = DOCS / "governance" / "debt-collection.md"
    if not dc_path.is_file():
        return
    dc = dc_path.read_text(encoding="utf-8")
    others = [p for p in md_files() if p.name != "debt-collection.md"]
    corpus_all = "".join(p.read_text(encoding="utf-8") for p in others)
    corpus_body = "".join(_scannable(p.read_text(encoding="utf-8")) for p in others)
    # §四 状态表行: | D-XXX | 差距 | Phase | 状态 |；状态含 ✅（已实施/已决策）视为已闭环
    closed = {
        cells[0]
        for line in dc.splitlines()
        if line.startswith("| D-")
        for cells in [[c.strip() for c in line.strip("|").split("|")]]
        if len(cells) == 4 and "✅" in cells[3]
    }
    landed_body = set(re.findall(r"(?<![A-Za-z0-9])(D-\d{3})", corpus_body))
    landed_ver_only = set(re.findall(r"(?<![A-Za-z0-9])(D-\d{3})", corpus_all)) - landed_body
    ghosts_body = sorted(closed - landed_body)
    if ghosts_body:
        ver_only = [g for g in ghosts_body if g in landed_ver_only]
        invisible = [g for g in ghosts_body if g not in landed_ver_only]
        detail = ""
        if ver_only:
            detail += f"仅版本记录可见 {ver_only[:5]}{'…' if len(ver_only) > 5 else ''}；"
        if invisible:
            detail += f"完全不可见 {invisible[:5]}{'…' if len(invisible) > 5 else ''}；"
        warn(
            f"已闭环债务正文零命中（落地不可检索，需人工确认）: "
            f"{detail}共 {len(ghosts_body)} 项"
        )
    print(
    f"[10/18] 债务闭环真实性抽查: 已闭环 {len(closed)} 项，正文可见 {len(closed)-len(ghosts_body)} 项"
    )


def main() -> int:
    global DOCS
    if len(sys.argv) > 1:
        DOCS = ROOT / sys.argv[1]
    if not DOCS.is_dir():
        print(f"文档目录不存在: {DOCS}")
        return 1

    print("=" * 60)
    print("Kairos 文档一致性审计（documentation-governance §2/§3）")
    print(f"审计目录: {DOCS}")
    print("=" * 60)
    check_links()
    check_sections()
    check_format()
    check_version_records()
    check_mislabels()
    check_numeric()
    check_ddl_fields()
    check_mechanism_sections()
    check_hard_line_refs()
    check_mcp_tool_rows()
    check_line_endings()
    check_governance_count()
    check_retrieval_weights()
    check_debt_index()
    check_config_index()
    check_fences()
    check_table_render()
    check_debt_closure()
    check_metadata_dates()
    check_version_monotonic()
    check_deprecated_terms()
    check_numbering_continuity()
    check_decision_numbering()
    check_changelog_sync()
    check_anchors()
    check_frontmatter()
    print("-" * 60)
    for w in WARNS:
        print("[WARN]", w)
    if not FAILS:
        print("全部检查通过。")
        return 0
    for f in FAILS:
        print("[FAIL]", f)
    print(f"\n共 {len(FAILS)} 项失败。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
