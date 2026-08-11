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

0.0.54 门禁扩展（round23 结构性建议 S23-1 落地）:
  - 新增单一事实源反查（6.23）：架构/技术选型等权威文档正文引用的
    HTTP 端点必须已在 api-spec 登记（api-spec 为端点单一事实源），
    防 R23-01/R23-01b 类「端点漏 /v1 前缀、引用未登记端点」事实错误
    复发（豁免：版本记录行、changelog、blueprint-v1.1 未来规划、
    debt-collection 债务账目、analysis/ 外部对照产物、父路径引用、
    多方法简写 GET/POST）

0.0.56 门禁扩展（round24 结构性建议 S24-1/S24-2 落地）:
  - 新增端点→章节锚点一致性（6.24）：权威文档同一行内「api-spec §X」
    引用与已登记端点比对，章节号须与实际登记章节一致（或互为父子级），
    防 R24-02/R24-03 类「端点正确但章节引用错位」事实错误复发
    （豁免：api-spec/changelog/blueprint-v1.1/debt-collection/analysis、
    版本记录行、未登记端点）
  - 新增认知基础去版本化（6.25）：cognitive-foundation.md 正文不得散布
    v0.1.0/v1.1 版本绑定声明（豁免：文件名链接、版本记录表行、
    债务元数据版本槽位 D-xxx vX.Y 协议槽位），防 R24-01 类治理缺口复发

0.0.58 门禁扩展（round25 结构性建议 S25-1/S25-2 落地）:
  - 新增通用章节引用存在性与标题语义（6.26）：扫描全文「文档名 §X」
    裸引用（无链接格式）与「§X『标题名』」引号标题引用，校验目标
    文档存在对应章节（含中文数字↔阿拉伯数字双向映射、父级回退、
    中文标题名匹配），防 R25-02/R25-07/R25-19 类「章节号错位」
    事实错误复发（豁免：changelog/blueprint-v1.1/debt-collection/
    analysis、版本记录行、§X.Y 占位符、编号迁移注记行）
  - 新增 api-spec 章节版本标注完备性（6.27）：api-spec §11~§17 各节
    标题或定位段必须声明版本边界（v0.1.0 交付 / v1.1 预留 / 端点预留 /
    P3，v1.1+），防 R25-22 类「版本边界裸奔」治理缺口复发

0.0.60 门禁扩展（round26 结构性建议 S26-1/S26-2/S26-3 落地）:
  - 新增机器可读契约 ↔ api-spec 一致性反查（6.28）：openapi paths 的
    (方法,路径) 集合 ≡ api-spec 登记端点（单一事实源，0.0.54 已立）；
    servers 端口 ≡ 全库默认 8010；securitySchemes ≡ 单一 bearerAuth
    (type http, scheme bearer)；mcp-tools.json 各 mapsTo ⊆ 登记端点
    （MCP-only 工具豁免），防 R26 类「机器可读契约/索引与事实源漂移」
    复发（响应码逐项⊇声明值为骨架近似，deferred，债务 D-428 追踪）
  - 新增跨文档错误码集合一致性（6.29）：error-reference ≡ troubleshooting
    全集合相等 + api-spec §7 ⊆ error-reference 子集（§7 为 HTTP 子集、
    非全量，全量以 error-reference 为准），防 ERR-XXX 增删后三处表体
    不同步复发
  - 新增示例代码纪律（6.30）：围栏代码块内 `kairos write` 真实调用须含
    `--source`（S-15 provenance 必填，api-spec §3）；`calibration_status`
    赋值字面量须为规范四值（healthy/degraded/virtual/dormant，api-spec
    §6.5），防「示例参数/枚举写错」事实错误复发（豁免：行内命令名列举、
    blockquote 草稿声明、表格单元格示例）

0.0.71 门禁扩展（round35 门禁建议落实，R35-01 防复发）:
  - 新增治理执行记录覆盖性（6.32）：documentation-governance §3
    「执行记录（设计阶段）」为自引用快照，须覆盖至 changelog 最新批次
    （round33 立「含自身批次」纪律、round35 重演捕获——执行记录滞后于
    最新 changelog 批次即 FAIL），防「治理执行记录过时」类治理缺口复发
    （豁免：changelog 无版本记录行的异常态；执行记录引用块缺失本身即
    FAIL——自引用快照不存在）

0.0.74 门禁扩展（round38 门禁建议落实，round37 建议落地）:
  - 新增 feature-list「对应架构组件」列引用落点全量校验（6.33）：
    解析该列 `[文档](路径) §X 机制名`，校验目标文档存在、章节号存在
    （含父级回退/中文数字/P3-21）、机制名关键词出现在目标文档该章节
    文本块内（子串匹配）——拦截 R37-04~R37-09 类「章节号存在但所指
    机制不在该章节」的悬空引用（round37 发现 feature-list 引用列 12 处
    悬空/错位，根因为门禁 6.14 仅抽检 24 条映射、6.26 仅查章节号存在性）
  - 扩展 6.26 档 4：链接格式「[文档](路径) §X 机制名」的机制名存在性
    校验（候选词全文痕迹校验，WARN 级软提示不阻断 exit 0——全库存在
    大量「§X 后接章节结构描述/自然语言」引用，无法可靠区分机制名与
    描述语；真实悬空由 6.33 FAIL 级精准捕获，本档供人工审计辅助）
0.0.76 门禁优化（round39 门禁补盲区建议落地）:
  - 6.26 档 4 候选词提取优化：新增动词/描述性前缀剥离（「定义了跨层
    三环不变量」→「跨层三环不变量」、「详述生效规则」→「生效规则」、
    「只覆盖检索」→「检索」、「约束认知质量指标」→「认知质量指标」
    等——round39 教训：WARN 噪声主要来自「§X 后接动词短语」，剥离
    动词前缀后仅以名词短语作为机制名候选）；尾部后缀扩展（参数/状态机/
    验收/确定/路径/过程/流程）；括号内 a-d 类字母段标注（「种子生命
    周期追踪（a-d）」）回退取括号前文本。    效果：WARN 23→12 条（26→23
    为 round39 修复 4 条真实问题）。突变测试验证：悬空引用「存储层
    量子纠缠索引」仍可被精确捕获（标题行匹配恢复「整段连续中文段」
    严格逻辑——曾尝试「任意 3+ 字子串滑动窗口」导致误放行：子串
    「存储层」恰好命中 §5 标题，削弱捕获能力，已回退）。
0.0.78 门禁优化（round40 改进建议落地）:
  - 6.26 档 4 新增「3-6 字尾缀标题匹配」判定（zh_tails）：候选词
    3-6 字**尾部窗口**在目标文档标题行出现即通过——收敛「修饰语+子节
    标题」类 WARN（「特征标志编码纪律」尾缀「编码纪律」命中架构 §0.8
    「#### 编码纪律」子节、「各条推论」尾缀「条推论」命中架构 §0.3
    「### 0.3 五条推论」，WARN 12→10 条）。仅取尾部窗口非任意子串——
    反例「存储层量子纠缠索引」尾缀不含「存储层」（前缀）不误放行；
    3 字下限防「指标/纪律」类泛化误报。突变测试双验证：悬空捕获 +
    描述放过。保守决策：「权重」未入尾部后缀剥离表（「三信号混合
    检索权重参数」保留 WARN，措辞等价可忽略，避免误放行风险）。
0.0.82 门禁扩展（round44 门禁建议落实，R43-3/S43-1 落地）:
  - 新增 changelog 结构纪律（6.34）：叙述节版本号单调升序 + `## 版本记录`
    标题紧邻版本表体（防 R43-09/10 类回归）。
  - 新增红线语义互斥词对检查（6.35，S-14 试点）：维护「红线禁止短语 ↔
    违例措辞」词对表，否定行跳过避免误报。
0.0.84 门禁扩展（round46 结构性建议 S45-1/S45-2/S45-3 落地）:
  - 新增版本归属互斥检查（6.36）：自举式倒排索引，实体（端点/契约值/事件
    类型/表字段）跨文档/跨章节同时被标「已落地」与「未落地」即 WARN（首轮
    软门禁，不阻断 exit 0）。
  - 新增表格内容与引言范围词一致性（6.37）：仅对排他性「仅列/仅含 N 类/项」
    触发，比对紧邻表格数据行数（首轮软门禁）。
  - 新增阈值型监控规则自洽性（6.38）：「指标/阈值/触发动作」三列监控表当前
    值越阈即 WARN（防交付态恒触发自毁，首轮软门禁）。
"""
from __future__ import annotations

import pathlib
import re
import sys

# 0.0.92 修复：Windows GBK 控制台下输出含 ⊇ 等字符时 UnicodeEncodeError 崩溃
# （对齐 deep-audit.py 0.0.6 同类修复先例），门禁逻辑不变。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SECTION_MARK = "\u00a7"  # §
# 中文数字 ↔ 阿拉伯数字（章节引用双向映射，6.26 用）
CN2AR = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
         "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}
AR2CN = {v: k for k, v in CN2AR.items()}
# 中文文档名/别名 → 文件名（裸引用解析，6.26 用）
DOC_NAME_MAP = {
    "架构": "architecture-v0.1.0.md",
    "认知基础": "cognitive-foundation.md",
    "api-spec": "api-spec.md",
    "configuration": "configuration.md",
    "data-model": "data-model.md",
    "technology-stack": "technology-stack.md",
    "glossary": "glossary.md",
    "蓝图": "architecture-blueprint-v1.1.md",
    "test-strategy": "test-strategy.md",
    "test-plan": "test-plan.md",
    "acceptance-criteria": "acceptance-criteria.md",
    "detailed-design": "detailed-design.md",
    "deployment": "deployment.md",
    "feature-list": "feature-list.md",
    "security-specification": "security-specification.md",
    "threat-model": "threat-model.md",
    "runbook": "runbook.md",
    "benchmark-plan": "benchmark-plan.md",
    "quick-start": "quick-start.md",
    "user-guide": "user-guide.md",
    "observability": "observability.md",
    "reliability": "reliability.md",
    "troubleshooting": "troubleshooting.md",
    "operation-catalog": "operation-catalog.md",
    "rl-weight-spec": "rl-weight-spec.md",
    "use-cases": "use-cases.md",
    "system-context": "system-context.md",
    "requirements-baseline": "requirements-baseline.md",
    "nfr-specification": "nfr-specification.md",
    "feature-list": "feature-list.md",
    "claim-implementation-matrix": "claim-implementation-matrix.md",
    "schema-slice.sql": "schema-slice.sql",
    "implementation-map": "implementation-map.md",
}
# 6.26 豁免文档：历史叙述/未来规划/债务账目/外部对照产物
SECTION_EXEMPT = {"changelog.md", "architecture-blueprint-v1.1.md", "debt-collection.md"}
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


def _section_blocks(text: str) -> dict[str, str]:
    """构建目标文档「章节号 → 章节文本块」映射。

    每个标题（`## §5 存储层` / `### 5.2 ...` / `### P3-21 ...` / `### 一、...`）
    到下一个同/上级标题之间的全部文本（含标题行）归为该章节文本块。
    父级回退：章节 X 的文本块包含其后所有子章节内容（无独立子标题的
    合并章节如架构 §5.2 亦然）。用于 6.33 机制名落点存在性校验。
    """
    lines = text.splitlines()
    blocks: dict[str, list[str]] = {}
    order: list[str] = []
    stack: list[tuple[int, str]] = []  # (标题层级, 章节号)

    for line in lines:
        m = re.match(
            r"^ {0,3}(#{2,6})\s+(?:%s)?([0-9A-Z一二三四五六七八九十]+(?:\.[0-9A-Za-z]+)*(?:-[0-9]+)?[a-z]?)[\s·：:]*(.*)$"
            % SECTION_MARK,
            line.strip(),
        )
        if m:
            level, num = len(m.group(1)), m.group(2)
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, num))
            if num not in blocks:
                blocks[num] = []
                order.append(num)
            blocks[num].append(line)
            continue
        if not stack:
            continue
        # 当前最深层章节追加内容行（父级同时享有——合并章节内容）
        for _lvl, _num in stack:
            blocks[_num].append(line)
    return {k: "\n".join(v) for k, v in blocks.items()}


def check_feature_list_refs() -> None:
    """6.33 feature-list「对应架构组件」列引用落点全量校验（round37 建议落地）。

    round37（0.0.73）发现 feature-list「对应架构组件」列 12 处引用落点
    悬空/错位（R-05 时间索引、M-12 社区检测、M-13/A-16 事实新鲜度、
    M-16 MemCube 等指向架构 §5.2 不存在的节点；W-09 语义错配）——根因
    为门禁 6.14 仅抽检 24 条映射、6.26 仅查章节号存在性，未校验「引用
    文本所指机制名是否真的在该章节内」。本检查将该列**全量**纳入机器
    校验：

      - 解析 feature-list 每行「对应架构组件」列 `[文档](路径) §X 机制名`
      - 目标文档存在性（链接目标文件存在）
      - 章节号存在性（§X 在目标文档标题中，含父级回退、中文数字映射、
        P3-21 类带连字符章节号）
      - 机制名关键词存在性：§X 后的关键词（中文/英文/混合，去括号与
        修饰语）须出现在目标文档该章节的**文本块**中（子串匹配）——
        拦截「章节号存在但所指机制不在该章节」的悬空引用

    豁免：版本记录表行；引用列无「§X 关键词」形态（仅链接无章节号、
    或章节号后无关键词、或关键词为通用措辞）。
    """
    fl = DOCS / "specification" / "feature-list.md"
    if not fl.exists():
        return
    # 预构建目标文档章节文本块
    blocks: dict[str, dict[str, str]] = {}
    for p in md_files():
        blocks[p.name] = _section_blocks(p.read_text(encoding="utf-8"))
    bad = 0
    sec_pat = re.compile(
        r"§([0-9A-Z一二三四五六七八九十]+(?:\.[0-9A-Za-z]+)*(?:-[0-9]+)?[a-z]?)"
    )
    for ln_no, line in enumerate(fl.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^\| *0\.0\.", line.lstrip()):
            continue  # 版本记录表行
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        ref_cell = cells[-1]
        # 解析 `[标题](路径) §X 关键词`（可能多个，用 / 或 + 分隔）
        for m in re.finditer(
            r"\[([^\]]*)\]\(([^)]+\.md)\)(?=[^\)]*\s*§)\s*([^|/+,]*§[^|/+,]*)",
            ref_cell,
        ):
            tgt = m.group(2).split("#")[0]
            name = pathlib.Path(tgt).name
            if name not in blocks:
                fail(f"6.33 引用目标文档不存在：feature-list L{ln_no} -> {tgt}")
                bad += 1
                continue
            after = m.group(3).strip()
            sec_m = sec_pat.search(after)
            if not sec_m:
                continue
            sec = sec_m.group(1)
            # 章节号存在性（含父级回退、中文↔阿拉伯、P3-21）
            ids = set(blocks[name].keys())
            ok_sec = False
            sec_parts = sec.split(".")
            for i in range(len(sec_parts), 0, -1):
                key = ".".join(sec_parts[:i])
                if key in ids:
                    ok_sec = True
                    break
                if key in CN2AR and CN2AR[key] in ids:
                    ok_sec = True
                    break
                if key in AR2CN and AR2CN[key] in ids:
                    ok_sec = True
                    break
            if not ok_sec:
                fail(f"6.33 章节引用不存在：feature-list L{ln_no} -> {tgt} §{sec}")
                bad += 1
                continue
            # 关键词：§X 之后的文字（去括号内容、去英文参数/命令名、去通用措辞）
            tail = after[sec_m.end():].strip()
            kw_raw = tail.split("（")[0].split("(")[0].strip()
            kw_raw = re.sub(r"[`*\[\]]", "", kw_raw)
            kw = kw_raw.strip()
            if not kw:
                continue
            # 通用措辞豁免（非机制名的修饰语/动词短语）
            if kw in ("的", "中", "等", "见", "如", "后", "处", "相关", "机制", "组件",
                      "结构", "定义", "说明", "一节", "本章", "条目", "部分", "边界",
                      "版本", "与", "及", "或", "并", "且", "（", "）"):
                continue
            if len(kw) < 2:
                continue
            block = blocks[name].get(sec, "")
            # 去除 block 中的链接/代码形态后子串匹配
            block_clean = re.sub(r"\[[^\]]*\]\([^)]*\)", "", block)
            block_clean = re.sub(r"`[^`]*`", "", block_clean)
            if kw not in block_clean:
                fail(
                    f"6.33 机制名「{kw}」不在 {tgt} §{sec} 章节内（feature-list L{ln_no}，引用「{ref_cell[:50]}…」）"
                )
                bad += 1
    print(f"[6.33] feature-list 引用列全量校验: {bad} 项落点漂移")


def _section_content_map(text: str) -> dict[str, list[str]]:
    """构建目标文档「章节号 → 该章节下的机制名关键词」映射。

    用于 6.33 机制名落点存在性校验：取每个标题（含 `### 5.2` 形态与
    无编号子标题）的标题行与后续内容行，抽出其中的加粗机制名、列表项
    首个名词与中文短语作为「该章节存在的机制名」候选。返回
    {章节号(含父级回退): [关键词, ...]}。
    """
    lines = text.splitlines()
    # 标题栈：记录 (层级, 章节号) —— 父级回退时子章节归属父级
    stack: list[tuple[int, str]] = []
    section_words: dict[str, set[str]] = {}

    def _current() -> str | None:
        return stack[-1][1] if stack else None

    for line in lines:
        m = re.match(
            r"^ {0,3}(#{2,6})\s+(?:%s)?([0-9A-Z一二三四五六七八九十]+(?:\.[0-9]+)*[a-z]?)[\s·：:]*(.*)$"
            % SECTION_MARK,
            line.strip(),
        )
        if m:
            level, num, title = len(m.group(1)), m.group(2), m.group(3).strip()
            # 维护标题栈（相同或更高层级标题弹出栈顶）
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, num))
            cur = _current()
            if cur is None:
                continue
            # 标题行中的机制名（括号前主名、加粗名、后续中文短语）
            words = set()
            for part in re.split(r"[（(]|[）)]|·|、|：", title):
                part = part.strip().strip("*").strip()
                if re.fullmatch(r"[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_\-（）()· ]{1,18}", part):
                    words.add(part)
            for w in re.findall(r"\*\*([^*]{2,20})\*\*", title):
                words.add(w.strip())
            section_words.setdefault(cur, set()).update(w for w in words if len(w) >= 2)
            continue
        # 非标题行：加粗机制名与列表项首词
        cur = _current()
        if cur is None:
            continue
        for w in re.findall(r"\*\*([^*]{2,20})\*\*", line):
            section_words.setdefault(cur, set()).add(w.strip())
        lm = re.match(r"^\s*[|└├│ ]*[\-*]\s+\*\*?([\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_\-（）()· ]{1,18})\*\*?", line)
        if lm:
            section_words.setdefault(cur, set()).add(lm.group(1).strip())
    # 父级回退：子章节关键词并入父级
    flat: dict[str, set[str]] = {}
    for num, words in section_words.items():
        parts = num.split(".")
        for i in range(1, len(parts) + 1):
            key = ".".join(parts[:i])
            flat.setdefault(key, set()).update(words)
    return {k: sorted(v) for k, v in flat.items()}


def check_feature_list_refs() -> None:
    """6.33 feature-list「对应架构组件」列引用落点全量校验（round37 建议落地）。

    round37（0.0.73）发现 feature-list「对应架构组件」列 12 处引用落点
    悬空/错位（R-05 时间索引、M-12 社区检测、M-13/A-16 事实新鲜度、
    M-16 MemCube 等指向架构 §5.2 不存在的节点；W-09 语义错配）——根因
    为门禁 6.14 仅抽检 24 条映射、6.26 仅查章节号存在性，未校验「引用
    文本所指机制名是否真的在该章节内」。本检查将该列**全量**纳入机器
    校验：

      - 解析 feature-list 每行「对应架构组件」列 `[文档](路径) §X 机制名`
      - 目标文档存在性（链接目标文件存在）
      - 章节号存在性（§X 在目标文档标题中，含父级回退）
      - 机制名关键词存在性（机制名核心词须出现在目标文档该章节的
        标题/正文机制名池中；空白机制名跳过）

    豁免：版本记录表行；无「§X 机制名」形态的引用（仅链接无章节号、
    或章节号后无关键词）。
    """
    fl = DOCS / "specification" / "feature-list.md"
    if not fl.exists():
        return
    # 预构建目标文档章节机制名池
    pool: dict[str, dict[str, list[str]]] = {}
    for p in md_files():
        pool[p.name] = _section_content_map(p.read_text(encoding="utf-8"))
    bad = 0
    for ln_no, line in enumerate(fl.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^\| *0\.0\.", line.lstrip()):
            continue  # 版本记录表行
        if "|" not in line:
            continue
        # 提取「对应架构组件」列（最后一列）
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        ref_cell = cells[-1]
        # 解析 `[标题](路径) §X 关键词`（可能多个，用 / 或 + 分隔）
        for m in re.finditer(
            r"\[([^\]]*)\]\(([^)]+\.md)\)\s*%s([0-9A-Z一二三四五六七八九十]+(?:\.[0-9]+)*[a-z]?)[\s·：:]*(.*?)(?=$|/|\+|\||\[|,|，)"
            % SECTION_MARK,
            ref_cell,
        ):
            tgt = m.group(2).split("#")[0]
            name = pathlib.Path(tgt).name
            if name not in pool:
                fail(f"6.33 引用目标文档不存在：feature-list L{ln_no} -> {tgt}")
                bad += 1
                continue
            sec = m.group(3)
            # 章节号存在性（含中文数字↔阿拉伯、父级回退）
            ids = set(pool[name].keys())
            ok_sec = False
            for i in range(len(sec.split(".")), 0, -1):
                key = ".".join(sec.split(".")[:i])
                if key in ids:
                    ok_sec = True
                    break
                if key in CN2AR and CN2AR[key] in ids:
                    ok_sec = True
                    break
                if key in AR2CN and AR2CN[key] in ids:
                    ok_sec = True
                    break
            if not ok_sec:
                fail(f"6.33 章节引用不存在：feature-list L{ln_no} -> {tgt} §{sec}")
                bad += 1
                continue
            # 机制名关键词存在性：取 §X 后关键词（去括号/加粗/空格）
            kw_raw = m.group(4).strip().strip("*").strip()
            kw = re.split(r"[（(]", kw_raw)[0].strip()
            kw = re.sub(r"[\u4e00-\u9fa5A-Za-z0-9_\-（）()· ]", "", kw)
            if not kw:
                continue
            words = pool[name].get(sec, [])
            if not any(kw in w or w in kw for w in words):
                fail(
                    f"6.33 机制名「{kw}」不在 {tgt} §{sec} 章节内（feature-list L{ln_no}）"
                )
                bad += 1
    print(f"[6.33] feature-list 引用列全量校验: {bad} 项落点漂移")


def check_hard_line_refs() -> None:
    r"""6.15 硬行号引用禁令（0.0.28 补盲区，闭环第十轮审计 C-03/F-01；
        0.0.69 扩展捕获 Lxx 缩写行号形态，闭环 round34 门禁建议 R34-04/R34-06）。

    语义化交叉引用是 documentation-governance §2 的规范（文档名+章节）；
    `path.md:行号` 引用随编辑必漂移（configuration 附录 A 曾 135/136 漂移），
    整体废除。0.0.69 起同时捕获 `L\d{2,4}` 缩写行号形态（如「§1.1 L94」、
    「L64/D.10」——0.0.68 round34 审计捕获此类漏网残留，原正则仅匹配
    `[\w.\-/]+\.md:\d+` 全格式）。豁免范围：
    - reviews/ 为审计产物（证据需引用原文行号）不在扫描范围（EXCLUDE_DIRS）；
    - changelog.md 为历史批次记录（叙述节 52 处 Lxx 均为历史修复描述）；
    - 版本记录表格行由 _scannable 剔除（历史摘要允许保留旧口径）；
    - 测试用例编号 `TC-CAL01-001` 等（Lxx 前为字母 CAL，正则
      `(?<![A-Za-z0-9])` 天然排除，非行号引用）。
    """
    bad = 0
    lxx_re = re.compile(r"(?<![A-Za-z0-9])L\d{2,4}(?![A-Za-z0-9])")
    for p in md_files():
        text = p.read_text(encoding="utf-8")
        # A. 全格式 file.md:行号（全库扫描）
        hits = re.findall(r"[\w.\-/]+\.md:\d+(?:-\d+)?", text)
        for h in hits:
            fail(f"硬行号引用禁令（6.15）: {p.relative_to(DOCS)} -> {h}（改「文档 §章节」语义引用）")
            bad += 1
        # B. Lxx 缩写形态（豁免 changelog 历史记录 + 版本记录表格行）
        if p.name == "changelog.md":
            continue
        body = _scannable(text)
        for m in lxx_re.finditer(body):
            fail(f"硬行号引用禁令（6.15）: {p.relative_to(DOCS)} -> {m.group(0)}（改「文档 §章节」语义引用）")
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
    """16) frontmatter 必填字段：title / created / updated / last_reviewed / status。

    0.0.95 扩展（round55 盲区修复）：原非贪婪正则 `\\A---\\n(.*?)\\n---\\n`
    在 frontmatter 缺少立即闭合 `---` 时会误匹配正文中的 `---` 分隔线，
    将正文引用块/表格卷入 frontmatter 区而不报错（Obsidian 显示为
    「无效属性」——adr/risks/slice-implementation-guide/acceptance-criteria/
    benchmark-plan/test-strategy 六份文档实测复现）。现于字段检查前
    增加 frontmatter 区内容合法性校验：闭合 `---` 之前的行只允许
    YAML 形态（`key:` / 缩进 / `- 列表` / `# 注释` / 空行），出现
    `>` 引用块、`|` 表格、普通文本行即 FAIL。
    """
    required = ["title", "created", "updated", "last_reviewed", "status"]
    legal_line = re.compile(
        r"^(?:[a-zA-Z_][\w.-]*:\s*.*$|^\s+[^\s>|].*$|^\s*-\s+.*$|^\s*#.*$|^\s*$)",
        re.M,
    )
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
        fm = m.group(1)
        # 盲区校验：frontmatter 区不得含正文形态行（引用块/表格/普通文本）
        bad_lines = [
            ln for ln in fm.split("\n")
            if ln.strip() and not legal_line.match(ln)
        ]
        if bad_lines:
            fail(
                f"frontmatter 区含正文行（缺立即闭合 ---，Obsidian 无效属性）："
                f"{p.relative_to(DOCS)} 首处 {bad_lines[0].strip()[:50]!r}"
            )
            continue
        fields = set(re.findall(r"^([a-zA-Z_]+):", fm, re.M))
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


def check_feature_flag_count() -> None:
    """6.20 特征标志计数一致性（round22 R22-09 补盲区）。

    架构 §0.8 标志表行数 N 须与 configuration §11 一致；正文「N 个特征标志的
    组合空间为 2^N 种」两数与表一致（2^N = 组合空间）；默认 OFF 计数两表一致，
    且正文「M 个默认 OFF」与表内默认值统计一致。防「标志表增删未全库同步」
    导致计数漂移（round22 R22-09）。
    """
    arch = (DOCS / "foundation" / "architecture-v0.1.0.md").read_text(encoding="utf-8")
    cfg = (DOCS / "ops" / "configuration.md").read_text(encoding="utf-8")
    bad = 0

    # 架构 §0.8 标志默认表（介于表头与「所有特征标志的状态」说明之间）
    i = arch.find("| 特征标志 | 默认 | 所涉组件 |")
    if i == -1:
        fail("6.20 架构 §0.8 特征标志表头未找到")
        bad += 1
        n_arch = off_arch = 0
    else:
        seg = arch[i: arch.find("\n所有特征标志的状态", i)]
        arch_rows = re.findall(r"^\| *`(KAIROS_FEATURE_[A-Z0-9_]+)` *\| *(\w+)", seg, re.M)
        n_arch = len(arch_rows)
        off_arch = sum(1 for _, d in arch_rows if d.upper().startswith("OFF"))

    # configuration §11 标志表
    j = cfg.find("## §11")
    if j == -1:
        fail("6.20 configuration §11 特征标志节未找到")
        bad += 1
        n_cfg = off_cfg = 0
    else:
        seg_cfg = cfg[j: cfg.find("\n## ", j + 4)]
        cfg_rows = re.findall(r"^\| *`(KAIROS_FEATURE_[A-Z0-9_]+)` *\| *(\w+)", seg_cfg, re.M)
        n_cfg = len(cfg_rows)
        off_cfg = sum(1 for _, d in cfg_rows if d.upper().startswith("OFF"))

    if n_arch:
        if f"{n_arch} 个特征标志" not in arch:
            fail(f"6.20 架构 §0.8 未声明「{n_arch} 个特征标志」（与标志表行数不一致）")
            bad += 1
        space = 2 ** n_arch
        if f"{space} 种" not in arch:
            fail(f"6.20 架构 §0.8 未声明组合空间「{space} 种」（应为 2^{n_arch}）")
            bad += 1
        if f"{off_arch} 个默认 OFF" not in arch:
            fail(f"6.20 架构 §0.8 未声明「{off_arch} 个默认 OFF」（与表内默认值统计不一致）")
            bad += 1

    if n_arch and n_cfg and n_arch != n_cfg:
        fail(f"6.20 特征标志计数分歧：架构 {n_arch} 行 ≠ configuration §11 {n_cfg} 行")
        bad += 1
    elif n_cfg == 0:
        fail("6.20 configuration §11 特征标志表未解析到行")
        bad += 1
    if n_arch and n_cfg and off_arch != off_cfg:
        fail(f"6.20 默认 OFF 计数分歧：架构 {off_arch} ≠ configuration {off_cfg}")
        bad += 1

    print(f"[6.20] 特征标志计数一致性: 架构 {n_arch} 行/默认OFF {off_arch}，"
          f"configuration {n_cfg} 行/默认OFF {off_cfg}，{bad} 项问题")


def check_falsification_carry() -> None:
    """6.21 证伪纪律与配置集承载一致性（round22 S21-1 补盲区）。

    架构 §0.8 对质量层下达强制性约束：① 证伪测试以 `[FALSIFICATION]` 标记、
    「无证伪测试的特征标志不应合入主分支」；② 测试矩阵只对三种命名配置集
    （kairos-minimal / kairos-slice / kairos-full）负责。防 R22-01/R22-02 类
    「上游下达约束、下游零承载」脱节复发。
    """
    q = DOCS / "quality"
    bad = 0
    # ① 证伪标记承载：test-plan / test-strategy 必须含 [FALSIFICATION]
    for name in ("test-plan.md", "test-strategy.md"):
        p = q / name
        if not p.is_file() or "[FALSIFICATION]" not in p.read_text(encoding="utf-8"):
            fail(f"6.21 质量层缺失 `[FALSIFICATION]` 承载：{name}（架构 §0.8 编码纪律）")
            bad += 1
    # ② 三配置集关键词在质量层至少出现（test-plan / test-strategy / acceptance-criteria）
    text = ""
    for name in ("test-plan.md", "test-strategy.md", "acceptance-criteria.md"):
        p = q / name
        if p.is_file():
            text += p.read_text(encoding="utf-8")
    for token in ("kairos-minimal", "kairos-slice", "kairos-full"):
        if token not in text:
            fail(f"6.21 质量层缺失命名配置集承载：未出现 `{token}`（架构 §0.8 命名配置集约束）")
            bad += 1
    print(f"[6.21] 证伪纪律与配置集承载一致性: {'全部承载' if bad == 0 else f'{bad} 项缺失'}")


def check_self_imposed_gate_debt() -> None:
    """6.22 自设硬门禁的债务追缴一致性（round22 S22-2 补盲区）。

    扫描全库「X 前 + 须/必须」自设硬门禁句式（编码启动前 / 上线前 / 定稿前 /
    发布前 / 合入主分支前等），校验每处有对应 debt-collection 条目——防 R22-04
    类「文档自设硬门禁但无追缴」脱节复发。changelog 为历史叙述、debt-collection
    为追缴登记本体，二者内句式不计入活动门禁。
    """
    pattern = re.compile(
        r"(编码启动前|上线前|定稿前|发布前|合入主分支前|合入前|投产前)"
        r"[^。；\n]{0,60}?(须|必须|必须于)"
    )
    debt = (DOCS / "governance" / "debt-collection.md").read_text(encoding="utf-8")
    debt_bodies = [
        b for _, b in re.findall(r"### (D-\d{3})[^\n]*\n((?:.|\n)*?)(?=\n### |\n## )", debt)
    ]
    bad = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        if rel in ("governance/changelog.md", "governance/debt-collection.md"):
            continue
        text = p.read_text(encoding="utf-8")
        for m in pattern.finditer(text):
            ctx = text[max(0, m.start() - 80): m.end() + 20]
            if re.search(r"D-\d{3}", ctx):
                continue  # 行内已挂债务，已追缴
            num = re.search(r"\d+\s*[项条个]", ctx)
            if num:
                tok = num.group(0)
                if any(tok in b for b in debt_bodies):
                    continue  # debt-collection 有对应条目
                fail(f"6.22 自设硬门禁无对应债务追缴：{rel} 「…{ctx.strip()[:36]}…」含「{tok}」但 debt-collection 无对应条目")
                bad += 1
            elif not re.search(r"D-\d{3}", text):
                fail(f"6.22 自设硬门禁无债务追缴体系：{rel} 「…{ctx.strip()[:36]}…」文档零债务引用")
                bad += 1
            else:
                warn(f"6.22 自设硬门禁未挂精确债务（文档级参与）：{rel}")
    print(f"[6.22] 自设硬门禁债务追缴一致性: {bad} 项未追缴")


def check_endpoint_source() -> None:
    """6.23 单一事实源反查（端点登记一致性；round23 S23-1 落地）。

    api-spec.md 为 HTTP 端点的单一事实源。权威文档（架构/技术选型/质量/
    运维等）正文引用的 `METHOD /path` 端点必须已在 api-spec 登记，且
    `/v1` 前缀不得遗漏——防 R23-01/R23-01b 类「端点漏 /v1 前缀、引用
    未登记端点」事实错误复发。

    豁免（不计入引用集合）：
      - 文档级：api-spec 自身、changelog（历史叙述）、blueprint-v1.1
        （未来规划端点）、debt-collection（债务账目）、analysis/（外部
        对照产物）、reviews/（审计产物）
      - 行级：版本记录表行（`| 0.0.x |`）
      - 匹配级：父路径引用（`POST /v1/admin/compaction/rollback` ⊆
        登记的 `POST /v1/admin/compaction/rollback/{snapshot_id}`）、
        多方法简写（`GET/POST /v1/skills` 只取首个 GET）。
      注：架构组件树（├─ │ 围栏）为正文描述而非代码示例，不豁免。
    """
    api_path = DOCS / "specification" / "api-spec.md"
    if not api_path.is_file():
        fail("6.23 api-spec.md 不存在，无法反查端点登记")
        return
    api = api_path.read_text(encoding="utf-8")
    registered: set[tuple[str, str]] = set()
    for m in re.finditer(
        r"^(?:\*{2}|###\s*)(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s*]+)",
        api,
        re.M,
    ):
        registered.add((m.group(1), m.group(2).split("?")[0].rstrip("/")))

    # 文档级豁免：单一事实源自身 / 历史叙述 / 未来规划 / 债务账目 / 外部对照产物
    skip_files = {"api-spec.md", "changelog.md", "architecture-blueprint-v1.1.md", "debt-collection.md"}
    ref_pat = re.compile(
        r"(?<![A-Za-z/])(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+"
        r"(/[A-Za-z0-9_{}?=&.\-/]+)"
    )
    bad = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in skip_files or "analysis" in parts:
            continue
        text = p.read_text(encoding="utf-8")
        for ln_no, line in enumerate(text.splitlines(), 1):
            s = line.lstrip()
            if re.match(r"^\| *0\.0\.", s):  # 版本记录表行（历史叙述）
                continue
            for m in ref_pat.finditer(line):
                meth, ref = m.group(1), m.group(2).split("?")[0].rstrip("/")
                if (meth, ref) in registered:
                    continue
                # 父路径引用：同 METHOD 下存在登记端点以 ref + '/' 开头
                if ref.count("/") >= 2 and any(
                    mth == meth and rp.startswith(ref + "/") for mth, rp in registered
                ):
                    continue
                # 缺 /v1 前缀：'/v1' + ref 已登记（R23-01 类）
                if not ref.startswith("/v1/") and (meth, "/v1" + ref) in registered:
                    fail(f"6.23 端点缺 /v1 前缀：{rel} L{ln_no} `{meth} {ref}`（api-spec 登记为 `{meth} /v1{ref}`）")
                    bad += 1
                    continue
                fail(f"6.23 引用未登记端点：{rel} L{ln_no} `{meth} {ref}`（api-spec 无对应登记，见单一事实源）")
                bad += 1
    print(f"[6.23] 单一事实源反查（端点登记一致性）: {bad} 项未登记/前缀错误")


def check_endpoint_section() -> None:
    """6.24 端点→章节锚点一致性（round24 S24-1 落地）。

    6.23 只校验 `METHOD /path` 端点是否登记，不校验正文给出的
    「api-spec §X」章节引用是否正确——R24-02/R24-03 类「端点路径
    正确但章节引用错位」事实错误因此漏网。本检查对权威文档同一行
    内同时出现的「api-spec §X」引用与已登记端点做比对，要求引用
    章节号与端点在 api-spec 的实际登记章节一致（或互为父子级）。

    豁免（不计入比对）：
      - 文档级：api-spec 自身、changelog（历史叙述）、blueprint-v1.1
        （未来规划端点）、debt-collection（债务账目）、analysis/（外部
        对照产物）、reviews/（审计产物）
      - 行级：版本记录表行（`| 0.0.x |`）
      - 匹配级：端点未在 api-spec 登记（待定义端点，如 /metrics）、
        行内无「api-spec §数字」引用（软引用「见 §健康检查」不含
        数字章节号，跳过）、「以 … 为准」句式（operation-catalog 中
        「MCP 工具注册以 [api-spec.md](api-spec.md) §6.8 为准」指工具
        注册表位置而非端点定义位置，跳过）
    """
    api_path = DOCS / "specification" / "api-spec.md"
    if not api_path.is_file():
        fail("6.24 api-spec.md 不存在，无法反查端点章节锚点")
        return
    api = api_path.read_text(encoding="utf-8")

    # 1) 建立端点 → 实际登记章节号映射：维护当前大章（## §N）与当前小节（### N.x）
    endpoint_section: dict[tuple[str, str], str] = {}
    cur_big, cur_sub = "", ""
    for line in api.splitlines():
        m = re.match(r"^##\s*%s(\d+)\s+" % SECTION_MARK, line)
        if m:
            cur_big = m.group(1)
            cur_sub = ""
            continue
        m = re.match(r"^###\s*(\d+(?:\.\d+)*)\s+", line)
        if m:
            cur_sub = m.group(1)
            continue
        m = re.match(r"^\*{2}(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s*]+)", line)
        if m:
            section = cur_sub or cur_big
            if section:
                endpoint_section[(m.group(1), m.group(2).split("?")[0].rstrip("/"))] = section

    # 2) 扫描权威文档同一行「api-spec §X」引用 + 已登记端点
    skip_files = {"api-spec.md", "changelog.md", "architecture-blueprint-v1.1.md", "debt-collection.md"}
    ref_pat = re.compile(
        r"(?<![A-Za-z/])(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+"
        r"(/[A-Za-z0-9_{}?=&.\-/]+)"
    )
    sect_pat = re.compile(r"api-spec[^%s\n]{0,60}?%s(\d+(?:\.\d+)*)" % (SECTION_MARK, SECTION_MARK))
    bad = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in skip_files or "analysis" in parts:
            continue
        text = p.read_text(encoding="utf-8")
        for ln_no, line in enumerate(text.splitlines(), 1):
            s = line.lstrip()
            if re.match(r"^\| *0\.0\.", s):  # 版本记录表行（历史叙述）
                continue
            sect_m = sect_pat.search(line)
            if not sect_m:
                continue
            # 「以 … 为准」句式豁免：指工具注册表/权威清单位置，非端点定义位置
            if "为准" in line:
                continue
            ref_section = sect_m.group(1)
            for m in ref_pat.finditer(line):
                meth, ref = m.group(1), m.group(2).split("?")[0].rstrip("/")
                key = (meth, ref)
                if key not in endpoint_section:
                    continue  # 待定义/未登记端点不比对
                actual = endpoint_section[key]
                # 一致：章节号相等，或引用为实际的父级（§6 ⊆ §6.5），或实际为引用的父级
                if (
                    ref_section == actual
                    or actual.startswith(ref_section + ".")
                    or ref_section.startswith(actual + ".")
                ):
                    continue
                fail(
                    f"6.24 端点章节引用错位：{rel} L{ln_no} `{meth} {ref}` "
                    f"引用 api-spec §{ref_section}，实际登记于 §{actual}"
                )
                bad += 1
    print(f"[6.24] 端点→章节锚点一致性: {bad} 项章节引用错位")


def check_cognitive_deprovision() -> None:
    """6.25 认知基础去版本化（round24 S24-2 落地）。

    认知基础定位为「版本无关的认知理论模型」（架构 §0.9）——正文不得
    散布 v0.1.0/v1.1 版本绑定声明（R24-01 类治理缺口）。R21-07 曾人工
    清理一轮仍有残留，本检查将其纳入机器可检测范围。

    豁免（不计入命中）：
      - 文件名链接：`architecture-v0.1.0.md` / `architecture-blueprint-v1.1.md`
        （链接目标文件名中的版本号，非版本绑定声明）
      - 版本记录表行：`| 0.0.x |`（历史记录）
      - 债务元数据版本槽位：`D-xxx，v1.1 协议槽位`（债务定义的一部分）
    """
    path = DOCS / "foundation" / "cognitive-foundation.md"
    if not path.is_file():
        fail("6.25 cognitive-foundation.md 不存在")
        return
    text = path.read_text(encoding="utf-8")
    version_pat = re.compile(r"v(?:0\.1\.0|1\.1)(?!\.md)")
    # 债务元数据版本槽位豁免：D-328，v1.1 协议槽位 / **D-328**，v1.1 协议槽位（加粗）
    debt_slot = re.compile(r"D-\d+\*{0,2}[^，。]*?，v(?:0\.1\.0|1\.1)\s*协议槽位")
    bad = 0
    for ln_no, line in enumerate(text.splitlines(), 1):
        s = line.lstrip()
        if re.match(r"^\| *0\.0\.", s):  # 版本记录表行
            continue
        for m in version_pat.finditer(line):
            ctx = line[max(0, m.start() - 40): m.end() + 30]
            if debt_slot.search(ctx):  # 债务元数据版本槽位豁免
                continue
            fail(f"6.25 认知基础版本绑定声明残留：L{ln_no} `…{ctx.strip()[:60]}…`")
            bad += 1
    print(f"[6.25] 认知基础去版本化: {bad} 处版本绑定声明残留")


def check_section_refs() -> None:
    """6.26 通用章节引用存在性与标题语义（round25 S25-1 落地）。

    [2/18] 章节引用检查只覆盖「链接格式」`[文档](路径.md) §X`；对
    **裸引用**（无链接的「架构 §X」「认知基础 §X」等中文文档名 + §数字）
    与「§X『标题名』」引号标题引用不做存在性校验——R25-02（认知基础引
    「架构 §0.6」实际机制在 §3.3）、R25-07（troubleshooting 引「架构
    §7 安全红线」实际在 §8）、R25-19（认知基础引「架构 §监督平面」用
    中文标题）类「章节号错位」事实错误因此漏网。本检查将其纳入机器
    可检测范围。

    三档校验：
      - 档 1 裸数字引用存在性：`架构 §X` / `认知基础 §X`（无链接格式）
        → 目标文档标题必须含 X（含中文数字↔阿拉伯数字双向映射、父级回退）
      - 档 2 中文标题引用存在性：`架构 §监督平面` / `认知基础 §引论`
        （§ 后为纯中文标题名）→ 目标文档标题行必须含该词
      - 档 3 引号标题语义：`§X『标题名』` / `§X「标题名」` → 引号文字
        必须出现在引用章节或其父级章节的标题行中（R25-07 类防复发）

    豁免（不计入命中）：
      - 文档级：changelog（历史叙述）、architecture-blueprint-v1.1
        （未来规划）、debt-collection（债务账目）、analysis/（外部
        对照产物）、reviews/（审计产物）
      - 行级：版本记录表行（`| 0.0.x |`）、编号迁移注记行（含
        「编号迁移」「并入」「保留编号空缺」——认知基础 §1.5/1.6 迁移
        注记自述编号空缺）
      - 匹配级：`§X.Y` 占位符（implementation-map「架构 §X.Y」指
        引用约定示例）、已链接格式引用（由 [2/18] 覆盖）
    """
    # 1) 构建全库标题索引：文件名 → {编号 → 标题行}
    heads: dict[str, dict[str, str]] = {}
    for p in md_files():
        num2title: dict[str, str] = {}
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(
                r"^ {0,3}#{2,4}\s+(?:%s)?([0-9A-Z一二三四五六七八九十]+(?:\.[0-9]+)*[a-z]?)[\s·]*(.*)$"
                % SECTION_MARK,
                line.strip(),
            )
            if m:
                num2title.setdefault(m.group(1), m.group(2).strip())
                continue
            # 纯中文标题（无编号前缀，如「## 引论」「## 持久化」）→ 以标题本身为 key
            m2 = re.match(r"^ {0,3}#{2,4}\s+([\u4e00-\u9fa5]{2,20})$", line.strip())
            if m2:
                num2title.setdefault(m2.group(1), m2.group(1))
                continue
            # 无编号子标题（#### 命名配置集与组合约束）→ 归入父级章节的标题池
            m3 = re.match(r"^ {0,3}#{4,6}\s+([\u4e00-\u9fa5A-Za-z（）()·\-]{2,20})$", line.strip())
            if m3:
                num2title.setdefault(m3.group(1), m3.group(1))
        heads[p.name] = num2title

    def _num_in_ids(num: str, ids: set[str]) -> bool:
        """数字章节号存在性（含中文↔阿拉伯双向映射与父级回退）。"""
        parts = num.split(".")
        for i in range(len(parts), 0, -1):
            key = ".".join(parts[:i])
            if key in ids:
                return True
            # 中文数字 → 阿拉伯（目标标题为「三」时引用「3」）
            if key in CN2AR and CN2AR[key] in ids:
                return True
            # 阿拉伯 → 中文（目标标题为「3」时引用「三」）
            if key in AR2CN and AR2CN[key] in ids:
                return True
        return False

    # 2) 预构建目标文档的编号集合（含中文数字别名与字母后缀归一）
    ids_map: dict[str, set[str]] = {}
    for name, num2title in heads.items():
        ids = set(num2title.keys())
        for t in list(num2title.keys()):
            if t in CN2AR:
                ids.add(CN2AR[t])
            if len(t) > 1 and t[0] in CN2AR:  # 一a → 1a
                ids.add(CN2AR[t[0]] + t[1:])
        ids_map[name] = ids

    # 3) 扫描全文
    bad = 0
    doc_alt = "|".join(re.escape(k) for k in DOC_NAME_MAP)
    # 编号引用：数字/中文数字 + 可选点号层级 + 可选字母后缀（一a/二b/3.1/三）
    bare_num_pat = re.compile(
        r"(?<!\[)(%s)\s*%s([0-9A-Z一二三四五六七八九十]+(?:\.[0-9]+)*[a-z]?)"
        % (doc_alt, SECTION_MARK)
    )
    # 中文标题引用：§ 后 2+ 汉字（排除编号分支已吃的数字）
    bare_cn_pat = re.compile(
        r"(?<!\[)(%s)\s*%s([\u4e00-\u9fa5]{2,14})" % (doc_alt, SECTION_MARK)
    )
    quote_pat = re.compile(
        r"\[[^\]]*\]\(([^)]+\.md)\)[\s]*%s(\d+(?:\.\d+)*)[\s]*[「『]\s*([^」』]{1,16})[\s」』]"
        % SECTION_MARK
    )
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in SECTION_EXEMPT or "analysis" in parts:
            continue
        text = p.read_text(encoding="utf-8")
        for ln_no, line in enumerate(text.splitlines(), 1):
            s = line.lstrip()
            if re.match(r"^\| *0\.0\.", s):  # 版本记录表行
                continue
            if "编号迁移" in line or "并入" in line or "保留编号空缺" in line:
                continue  # 编号迁移注记行（认知基础 §1.5/1.6 空缺自述）
            # 档 1：裸数字引用（含中文数字/字母后缀）
            for m in bare_num_pat.finditer(line):
                name_cn, cit = m.group(1), m.group(2)
                # 排除已链接格式（链接内由 [2/18] 覆盖）
                before = line[: m.start()]
                if before.rstrip().endswith(("](", "](")):
                    continue
                if cit in ("X", "X.Y") or cit.startswith("X."):
                    continue  # §X.Y 占位符（implementation-map 引用约定示例）
                fname = DOC_NAME_MAP[name_cn]
                if not _num_in_ids(cit, ids_map.get(fname, set())):
                    fail(
                        f"6.26 裸章节引用不存在：{rel} L{ln_no} "
                        f"`{name_cn} §{cit}`（{fname} 无此章节）"
                    )
                    bad += 1
            # 档 2：中文标题引用（§ 后为纯中文标题词）
            for m in bare_cn_pat.finditer(line):
                name_cn, title = m.group(1), m.group(2)
                before = line[: m.start()]
                if before.rstrip().endswith(("](", "](")):
                    continue
                if title in ("一致", "声明", "为准", "依赖", "界定", "布局", "架构方向"):
                    continue  # 非标题引用的粘连词
                fname = DOC_NAME_MAP[name_cn]
                # 粘连词排除：§三的 / §三） 等（「三」为数字由档 1 捕获，档 2 只处理纯中文标题词）
                if title[0] in CN2AR:
                    continue
                titles = list(heads.get(fname, {}).values())
                # 双向前缀/包含匹配：标题行以引用词开头（引论方法论声明 → 引论）
                # 或引用词是标题行子串（持久化 ⊆ ## 持久化）
                if not any(
                    t.startswith(title) or title in t or t in title
                    for t in titles
                ):
                    fail(
                        f"6.26 裸中文标题引用不存在：{rel} L{ln_no} "
                        f"`{name_cn} §{title}`（{fname} 无含该词的标题行）"
                    )
                    bad += 1
            # 档 3：引号标题语义（链接格式 §X「标题名」）
            for m in quote_pat.finditer(line):
                fname = pathlib.Path(m.group(1).split("#")[0]).name
                if fname not in heads:
                    continue
                cit, quote = m.group(2), m.group(3)
                num2title = heads.get(fname, {})
                # 引号文字在目标文档全文出现（标题行、加粗机制名、列表项机制名等
                # 均视为存在）——只报「章节号与标题名错位」类，不报「悬空」类
                # （悬空判定易与节内机制名形式冲突，留人工）
                cur = {n: t for n, t in num2title.items()
                       if n == cit or n.startswith(cit + ".") or cit.startswith(n + ".")}
                if not any(quote in t for t in cur.values()):
                    hit_other = [
                        n for n, t in num2title.items()
                        if quote in t and not (n == cit or n.startswith(cit + ".") or cit.startswith(n + "."))
                        # 排除无编号中文标题 key（#### 子标题归父章节，非独立章节）
                        and not re.match(r"^[\u4e00-\u9fa5]{2,20}$", n)
                    ]
                    if hit_other:
                        fail(
                            f"6.26 引号标题章节错位：{rel} L{ln_no} "
                            f"`{fname} §{cit}「{quote}」`（该标题位于 §{hit_other[0]}）"
                        )
                        bad += 1
    # 档 4：链接格式「[文档](路径) §X 机制名」的机制名存在性兜底
    # （round37 建议落地：6.26 扩展为「引用文本所指机制名在该章节内的
    # 关键字存在性」校验——防 R37-04~R37-09 类「章节号存在但所指机制
    # 不在该章节」的悬空引用复发；feature-list「对应架构组件」列由 6.33
    # 全量覆盖，此处排除该文档并覆盖其余文档的链接格式引用）
    #
    # 判定策略（防误报收敛版，多级痕迹校验）：
    #   1) 候选词（§X 后首个机制名词：连续中文段/英文词，遇「与及或和
    #      的等为后中」等虚词截断，尾部虚词剥离）在目标文档全文出现 →
    #      通过（机制存在于文档；「双副本」vs「见证锚定（主副本）与使用
    #      权重（影子副本）分离」类措辞差异不误报）
    #   2) 候选词去常用后缀（表/声明/结构/机制/组件/定义/说明/器/化/性/
    #      注记/协议）的核心词在全文出现 → 通过
    #   3) 候选词任意连续 3+ 字中文子串出现在目标文档标题行 → 通过
    #      （「各条推论」→ 架构 §0.3 标题「五条推论」含「推论」）
    #   4) 以上皆否 → 引用了一个目标文档中无任何痕迹的机制名
    #      （FAIL——真实悬空，需人工修复引用）
    sec_blocks: dict[str, dict[str, str]] = {}
    sec_fulltext: dict[str, str] = {}
    sec_heads: dict[str, str] = {}
    for _p in md_files():
        _text = _p.read_text(encoding="utf-8")
        sec_blocks[_p.name] = _section_blocks(_text)
        sec_fulltext[_p.name] = re.sub(r"\[[^\]\n]*\]\([^)\n]*\)", "", _text)  # [^\]]* 限行内（防跨行吞噬代码块内容，round48 修复）
        sec_heads[_p.name] = "\n".join(
            l for l in _text.splitlines()
            if re.match(r"^ {0,3}#{2,6}\s+", l)
        )
    link_kw_pat = re.compile(
        r"\[[^\]]*\]\(([^)]+\.md)\)[\s]*%s([0-9A-Z一二三四五六七八九十]+(?:\.[0-9A-Za-z]+)*(?:-[0-9]+)?[a-z]?)[\s]*([\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_\-（）()· ]{1,20})"
        % SECTION_MARK
    )
    # 候选词提取：§X 后首个机制名词（round39 收敛优化）
    #   1) 括号截断（「§一（社区检测）」→「社区检测」；「§X 机制名）…」→
    #      「机制名」；括号内为 a-d 类字母段标注（「种子生命周期追踪
    #      （a-d）」）时忽略括号，回退取括号前文本）
    #   2) 动词/描述性前缀剥离（「定义了跨层三环不变量」→「跨层三环
    #      不变量」；「详述生效规则」→「生效规则」；「只覆盖检索」→
    #      「检索」；「登记契约」→「契约」；「保持规范一致」→「规范
    #      一致」；「约束认知质量指标」→「认知质量指标」）——round39
    #      教训：WARN 噪声主要来自「§X 后接动词短语」，剥离动词前缀后
    #      仅以名词短语作为机制名候选
    #   3) 虚词截断（「各条推论的认知层定义源」→「各条推论」；「三信号
    #      混合检索经复审」→「三信号混合检索」）
    #   4) 尾部虚词/后缀剥离（「配置集矩阵与」→「配置集矩阵」；
    #      「三信号混合检索权重参数」→「三信号混合检索」；
    #      「事件类型枚举表确定」→「事件类型枚举表」）
    _kw_bracket_pat = re.compile(r"[（(]([^（）()]{2,16})[）)]")
    _vword_split_pat = re.compile(r"(与|及|或|和|的|等|为|后|中|处|并|且|其|经|至|前|内|上|下|以|于|按|依|据)(?=[\u4e00-\u9fa5])")
    _vword_tail_pat = re.compile(r"(与|及|或|和|的|等|为|后|中|处|并|且|其|经|至|前|内|上|下|以|于|按|依|据|表|声明|结构|机制|组件|定义|说明|器|化|性|注记|协议|参数|状态机|验收|确定|路径|过程|流程|为准)$")
    # round39：动词/描述性前缀（§X 后常见「动词 + 名词短语」描述语）
    _verb_prefix_pat = re.compile(
        r"^(定义了|定义|详述|描述了|描述|登记|保持|约束|只覆盖|仅覆盖|覆盖|新增|预留|已修正|已修复|提供|给出|列出|规定|限制|确保|维持|遵循|符合|设置|实现|承载|指出|提及|记录|说明|负责|承担|描述性|涵盖|包含|涉及|影响|约束了|规定了|给出了|描述了|详述了|明确了|明确了|列出|展示)"
    )

    def _extract_kw(raw: str) -> str:
        s = raw.strip()
        # 0) 取括号内内容（「§一（社区检测）」→「社区检测」）；
        #    括号内为 a-d 类字母段标注时忽略括号，回退取括号前文本
        bm = _kw_bracket_pat.search(s)
        if bm:
            b_inner = bm.group(1)
            if re.match(r"^[a-z]-[a-z]$", b_inner):
                s = s[: bm.start()].strip()
            else:
                s = b_inner
        # 1) 动词/描述性前缀剥离（仅剥离，剥离后剩余须 ≥2 字）
        pm = _verb_prefix_pat.match(s)
        if pm:
            rest = s[pm.end():].strip()
            if len(rest) >= 2 and re.match(r"[\u4e00-\u9fa5A-Za-z]", rest):
                s = rest
        # 2) 虚词截断（取首个虚词前）
        parts = _vword_split_pat.split(s, 1)
        if len(parts) == 3:
            s = parts[0]
        # 3) 取首个 token（中文连续段或英文词，允许中文·连字符）
        tm = re.match(r"[\u4e00-\u9fa5·（）()A-Za-z0-9_-]+", s)
        if not tm:
            return ""
        kw = tm.group(0).strip("（）()·")
        # 4) 尾部虚词/后缀剥离
        while len(kw) > 2 and _vword_tail_pat.search(kw):
            kw = _vword_tail_pat.sub("", kw)
        kw = kw.strip("（）()·")
        # 5) 残留括号过滤（「g）追加（relation_type」→ 无效候选，返回空）
        if re.search(r"[（）()]", kw):
            return ""
        return kw

    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in SECTION_EXEMPT or p.name == "feature-list.md" or "analysis" in parts:
            continue
        text = p.read_text(encoding="utf-8")
        for ln_no, line in enumerate(text.splitlines(), 1):
            if re.match(r"^\| *0\.0\.", line.lstrip()):
                continue
            for m in link_kw_pat.finditer(line):
                tgt = m.group(1).split("#")[0]
                fname = pathlib.Path(tgt).name
                if fname not in sec_blocks:
                    continue
                cit, kw_raw = m.group(2), m.group(3).strip()
                cand = _extract_kw(kw_raw)
                if len(cand) < 2:
                    continue
                fulltext = sec_fulltext.get(fname, "")
                # 1) 原文全文出现 → 通过
                if cand in fulltext:
                    continue
                # 2) 去常用后缀核心词 → 通过
                core = re.sub(r"(表|声明|结构|机制|组件|定义|说明|器|化|性|注记|协议)$", "", cand).strip()
                if len(core) >= 2 and core in fulltext:
                    continue
                # 3) 候选词连续中文段出现在目标文档标题行 → 通过
                #    （round39 复核：曾改为「任意 3+ 字子串滑动窗口」——
                #    引入误放行风险——「存储层量子纠缠索引」因含子串
                #    「存储层」（恰好是 §5 标题）被放行，而「量子纠缠
                #    索引」完全悬空；恢复「整段连续中文段匹配标题」的
                #    严格逻辑，避免削弱审计捕获能力）
                zh_segs = [s for s in re.findall(r"[\u4e00-\u9fa5]{2,}", cand) if len(s) >= 2]
                heads = sec_heads.get(fname, "")
                if any(seg in heads for seg in zh_segs):
                    continue
                # 3b) 候选词 3-6 字尾缀在目标文档标题行出现 → 通过
                #    （round40 建议：收敛「修饰语+子节标题」类 WARN——
                #    「特征标志编码纪律」→ 尾缀「编码纪律」命中「#### 编码
                #    纪律」（架构 §0.8 L613）；「各条推论」→「条推论」命中
                #    「### 0.3 五条推论」；「认知质量指标」→「量指标」命中
                #    「### 10.5 量化指标」。仅取**尾部窗口**非任意子串——
                #    反例「存储层量子纠缠索引」尾缀不含「存储层」（前缀），
                #    不误放行；3 字下限防「指标/纪律」类泛化误报）
                zh_tails = set()
                for seg in re.findall(r"[\u4e00-\u9fa5]{3,}", cand):
                    for L in range(3, min(len(seg), 7) + 1):
                        zh_tails.add(seg[-L:])
                if any(t in heads for t in zh_tails):
                    continue
                # 4) 无任何痕迹 → WARN（软提示，不阻断 exit 0）
                #    注：全库存在大量「§X 后接章节结构描述/自然语言」的
                #    链接引用（如「§一 竖切组件列按功能域记」「§10.3
                #    定义了跨层三环不变量」），候选词提取无法可靠区分
                #    「机制名」与「描述语」；R37 类真实悬空已由 6.33
                #    （feature-list 全量，FAIL 级）精准捕获，本检查定位
                #    为软提示供人工审计，避免误报破坏门禁。
                warn(
                    f"6.26 候选机制名「{cand}」未在 {fname} 找到痕迹（{rel} L{ln_no}，§{cit}；若为章节结构描述可忽略）"
                )
                bad += 1
    print(f"[6.26] 通用章节引用存在性与标题语义: {bad} 处引用错位/不存在")


def check_section_version_marks() -> None:
    """6.27 api-spec 章节版本标注完备性（round25 S25-2 落地）。

    api-spec §11~§17 混排 v1.1 预留端点（facts/edge-types/skills/
    graph-render 等）与 v0.1.0 交付端点（Connectors/Profile/管理导入
    导出），版本边界全靠各节自行标注——R25-22 中 §13~§17 缺失标注导致
    「技能管理 API 被误读为 v0.1.0 交付」「graph/render 无承载」歧义。
    本检查要求 §11~§17 各节标题或定位段（标题后 3 行内）必须出现
    版本边界关键词之一：`v0.1.0 交付` / `v1.1 预留` / `端点预留` /
    `P3，v1.1+` / `P3 前瞻` / `v0.1.0 不交付`，缺失即 FAIL。
    """
    api_path = DOCS / "specification" / "api-spec.md"
    if not api_path.is_file():
        fail("6.27 api-spec.md 不存在")
        return
    api = api_path.read_text(encoding="utf-8")
    lines = api.splitlines()
    marks = ("v0.1.0 交付", "v1.1 预留", "端点预留", "P3，v1.1+", "P3 前瞻", "v0.1.0 不交付")
    bad = 0
    for i, line in enumerate(lines, 1):
        m = re.match(r"^##\s*%s(\d{2})\s+" % SECTION_MARK, line)
        if not m:
            continue
        sec = m.group(1)
        if not (11 <= int(sec) <= 17):
            continue
        window = "\n".join(lines[i - 1: i + 3])  # 标题 + 后续 3 行（定位段）
        if not any(mk in window for mk in marks):
            fail(f"6.27 api-spec §{sec} 缺版本边界标注（标题/定位段须含 "
                 f"「v0.1.0 交付」/「v1.1 预留」/「端点预留」/「P3，v1.1+」之一）")
            bad += 1
    print(f"[6.27] api-spec 章节版本标注完备性: {bad} 节缺标注")


def check_contract_consistency() -> None:
    """6.28 机器可读契约 ↔ api-spec 一致性反查（round26 S26-1 落地）。

    openapi.yaml（AUTO-GENERATED from api-spec.md）与 mcp-tools.json 是
    api-spec 的机器可读索引，必须与 api-spec 单一事实源对齐；错位会令
    代码生成 / MCP 注册基于错误契约。逐项反查：
      ① openapi `paths` 的 (方法, 路径) 集合 ≡ api-spec 登记端点集合
        （api-spec 为端点单一事实源，见 6.23）；
      ② 每个 operation 成功响应码 ⊇ api-spec 声明值——骨架近似，
        deferred（债务 D-428 追踪逐端点收敛），本检查仅 informational
        注记，不 FAIL；
      ③ `servers` 端口 ≡ 全库默认端口 8010（ops/deployment.md、
        user/quick-start.md 口径）；
      ④ `securitySchemes` ≡ 单一 bearerAuth（type http, scheme bearer），
        与 api-spec §1 认证方式一致。
    另：mcp-tools.json 各 `mapsTo` 端点 ⊆ api-spec 登记端点（MCP-only
    工具豁免——无 REST 端点映射）。
    """
    api_path = DOCS / "specification" / "api-spec.md"
    oa_path = DOCS / "specification" / "api-contract" / "openapi.yaml"
    mcp_path = DOCS / "specification" / "api-contract" / "mcp-tools.json"
    if not api_path.is_file():
        fail("6.28 api-spec.md 不存在，无法反查契约一致性")
        return
    api = api_path.read_text(encoding="utf-8")
    registered: set[tuple[str, str]] = set()
    for m in re.finditer(
        r"^(?:\*{2}|###\s*)(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s*]+)",
        api, re.M,
    ):
        registered.add((m.group(1), m.group(2).split("?")[0].rstrip("/")))

    oa_ops: set[tuple[str, str]] = set()
    if not oa_path.is_file():
        fail("6.28 openapi.yaml 不存在，无法反查契约一致性")
    else:
        oa = oa_path.read_text(encoding="utf-8")
        cur_path = ""
        in_paths = False
        for line in oa.splitlines():
            if re.match(r"^[a-zA-Z_]+:", line):  # 顶层键
                in_paths = line.startswith("paths:")
                continue
            if not in_paths:
                continue
            mp = re.match(r"^  (/[^:\s][^:]*):\s*$", line)
            if mp:
                cur_path = mp.group(1).rstrip("/")
                continue
            mm = re.match(r"^    (get|post|put|patch|delete|head|options):", line, re.I)
            if mm and cur_path:
                oa_ops.add((mm.group(1).upper(), cur_path))
        if oa_ops != registered:
            for op in sorted(registered - oa_ops):
                fail(f"6.28 openapi 缺 api-spec 登记端点：{op[0]} {op[1]}")
            for op in sorted(oa_ops - registered):
                fail(f"6.28 openapi 含未登记端点（api-spec 无对应）：{op[0]} {op[1]}")
        # ③ servers 端口
        port_m = re.search(r"url:\s*https?://[^:\s]+:(\d+)", oa)
        if port_m:
            if port_m.group(1) != "8010":
                fail(f"6.28 openapi servers 端口 {port_m.group(1)} ≠ 全库默认 8010")
        else:
            fail("6.28 openapi servers 未声明端口（默认 8010）")
        # ④ securitySchemes ≡ 单一 bearerAuth
        sm = re.search(r"securitySchemes:(.*?)(?=^[a-zA-Z_]+:|\Z)", oa, re.S | re.M)
        if not sm:
            fail("6.28 openapi 缺 securitySchemes 段")
        else:
            block = sm.group(1)
            if not re.search(r"^\s+bearerAuth:\s*$", block, re.M):
                fail("6.28 openapi securitySchemes 缺 bearerAuth（须与 api-spec §1 单一 bearerAuth 一致）")
            elif "type: http" not in block or "scheme: bearer" not in block:
                fail("6.28 openapi bearerAuth 须 type: http + scheme: bearer（与 api-spec §1 一致）")
        # ② deferred 注记（D-428）
        if "SkeletonResponse" in oa:
            print("[6.28] 响应码逐项⊇声明值：deferred（骨架近似，债务 D-428 追踪逐端点收敛，本检查不 FAIL）")

    # mcp-tools.json mapsTo ⊆ registered
    if mcp_path.is_file():
        import json
        mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
        for t in mcp.get("tools", []):
            if "mapsTo" not in t:
                continue  # MCP-only 工具豁免
            mm = re.match(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)", t["mapsTo"])
            if not mm:
                if str(t["mapsTo"]).strip().lower().startswith("mcp-only"):
                    continue  # 显式 MCP-only 豁免标记（无独立公开 REST 端点）
                warn(f"6.28 mcp 工具 {t.get('name')} mapsTo 格式异常：{t['mapsTo']}")
                continue
            key = (mm.group(1), mm.group(2).rstrip("/"))
            if key not in registered:
                fail(f"6.28 mcp 工具 {t.get('name')} mapsTo 端点未登记于 api-spec：{key[0]} {key[1]}")
    print(f"[6.28] 机器可读契约 ↔ api-spec 一致性反查: api-spec 端点={len(registered)} openapi 操作={len(oa_ops)}")


def check_error_code_sets() -> None:
    """6.29 跨文档错误码集合一致性（round26 S26-2 落地）。

    错误码全集权威在 references/error-reference.md（42 个，11 类）。
    ops/troubleshooting.md §三 错误码速查为同一全集的运维视图；
    api-spec §7 声明为 HTTP 子集（非全量，全量以 error-reference 为准）。
    故采用：error-reference ≡ troubleshooting 全集合相等 + api-spec §7 ⊆
    error-reference 子集。任一差集非空即 FAIL（防 ERR-XXX 增删后三处表体
    不同步的复发）。
    """
    err_ref_path = DOCS / "references" / "error-reference.md"
    ts_path = DOCS / "ops" / "troubleshooting.md"
    api_path = DOCS / "specification" / "api-spec.md"
    if not (err_ref_path.is_file() and ts_path.is_file() and api_path.is_file()):
        fail("6.29 错误码源文件缺失（error-reference/troubleshooting/api-spec）")
        return
    err_ref = err_ref_path.read_text(encoding="utf-8")
    ts = ts_path.read_text(encoding="utf-8")
    api = api_path.read_text(encoding="utf-8")
    code_pat = r"ERR-[A-Z]{2,5}-\d{3}"
    E = set(re.findall(code_pat, err_ref))
    T = set(re.findall(code_pat, ts))
    i7 = api.find("## " + SECTION_MARK + "7")
    if i7 >= 0:
        rest = api[i7:]
        i8 = rest.find("## " + SECTION_MARK + "8")
        sec7 = rest[:i8] if i8 >= 0 else rest
    else:
        sec7 = ""
    S = set(re.findall(code_pat, sec7))
    bad = 0
    if E != T:
        for c in sorted(E - T):
            fail(f"6.29 错误码 {c} 在 error-reference 但不在 troubleshooting（两处全集须一致）")
            bad += 1
        for c in sorted(T - E):
            fail(f"6.29 错误码 {c} 在 troubleshooting 但不在 error-reference（两处全集须一致）")
            bad += 1
    if not S <= E:
        for c in sorted(S - E):
            fail(f"6.29 错误码 {c} 在 api-spec §7 但不在 error-reference 全集（§7 须为子集）")
            bad += 1
    print(f"[6.29] 跨文档错误码集合一致性: error-reference={len(E)} troubleshooting={len(T)} api-spec§7={len(S)} 差集={bad}")


def check_example_discipline() -> None:
    """6.30 示例代码纪律（round26 S26-3 落地）。

    文档纪律须覆盖示例代码（CLI/SDK）：示例命令的参数与枚举值须可追溯
    api-spec，防「示例写错参数/枚举」类事实错误复发。
      ① 围栏代码块内 `kairos write` 真实调用（write 后接非选项参数）须在同
        一块内含 `--source`（S-15 provenance 必填，缺失返回 422；api-spec §3
        CLI 表）——缺则 FAIL；
      ② 围栏代码块内 `calibration_status` 字段赋值字面量须为规范四值
        {healthy, degraded, virtual, dormant}（api-spec §6.5 / user-guide
        枚举注记）——非规范值 FAIL。
    豁免：行内命令名列举（如 `kairos write` 裸名）、blockquote 草稿声明、
    表格单元格示例（非围栏块）不计入；围栏块外的提及不视为调用示例。
    """
    fence_re = re.compile(r"^\s*(```|~~~)")
    cal_canon = {"healthy", "degraded", "virtual", "dormant"}
    bad = 0
    for p in md_files():
        lines = p.read_text(encoding="utf-8").splitlines()
        in_fence = False
        buf = []
        for line in lines:
            m = fence_re.match(line)
            if m:
                if not in_fence:
                    in_fence = True
                    buf = []
                else:
                    txt = "\n".join(buf)
                    if "kairos write" in txt and "--source" not in txt:
                        for bl in buf:
                            if re.search(r"kairos write\s+\S", bl) and not re.search(r"kairos write\s+--", bl):
                                fail(f"6.30 围栏示例缺 --source：{p.name} `kairos write` 调用须含 --source（S-15 必填，api-spec §3）")
                                bad += 1
                                break
                    for mm in re.finditer(r"calibration_status\s*[:=]\s*['\"]?([a-zA-Z_]+)['\"]?", txt):
                        if mm.group(1) not in cal_canon:
                            fail(f"6.30 围栏示例 calibration_status 非规范值：{p.name} `{mm.group(1)}`（须为 healthy/degraded/virtual/dormant，api-spec §6.5）")
                            bad += 1
                    in_fence = False
            elif in_fence:
                buf.append(line)
    print(f"[6.30] 示例代码纪律: {bad} 处示例参数/枚举违规")


def check_punctuation_discipline() -> None:
    """6.31 中文正文半角标点纪律（round30 落地）。

    中文正文须使用全角标点。检测紧邻中文字符的半角标点
    （`, ; ! ?`），即 CJK[,;!?]CJK 形态，归一为全角。
    排除（防误报）：
      ① 围栏代码块（``` / ~~~）内不扫描；
      ② 行内代码（`...`）相邻处不计入；
      ③ ASCII 括号表达式内（如 `(100ms)`、元组/区间记法）不计入。
    例外目录：analysis/（外部理念对照产物，含视频原文引号，非权威正文）。
    """
    CJK = "\u4e00-\u9fff"
    MAP = {",": "，", ";": "；", "!": "！", "?": "？"}
    PAT = re.compile(rf"(?<=[{CJK}])([,;!?])(?=[{CJK}])")
    bad = 0
    for p in md_files():
        if "analysis" in p.relative_to(DOCS).parts:
            continue
        lines = p.read_text(encoding="utf-8").splitlines()
        in_fence = False
        for i, raw in enumerate(lines):
            s = raw.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            # 行内代码哨兵：替换为非空白 \x00，避免与中文相邻误判
            masked = []
            in_code = False
            for ch in raw:
                if ch == "`":
                    in_code = not in_code
                    masked.append("\x00")
                else:
                    masked.append("\x00" if in_code else ch)
            masked = "".join(masked)
            for m in PAT.finditer(masked):
                depth = 0
                for ch in masked[: m.start()]:
                    if ch in "([":
                        depth += 1
                    elif ch in ")]":
                        depth = max(0, depth - 1)
                if depth > 0:
                    continue
                fail(
                    f"6.31 中文正文半角标点：{p.relative_to(DOCS)} 第 {i+1} 行 "
                    f"含半角 {m.group(1)}（应全角 {MAP[m.group(1)]}）：{raw.strip()[:60]}"
                )
                bad += 1
    print(f"[6.31] 中文正文半角标点纪律: {bad} 处违规")


def check_gov_exec_record() -> None:
    """6.32 治理执行记录覆盖性（0.0.71 补盲区，round35 R35-01 防复发）。

    自引用快照纪律：documentation-governance §3「执行记录（设计阶段）」
    是审计轮次的自引用快照，必须在每次 changelog 新批次后补记含最新批次
    （round33 立「含自身批次」纪律、round35 重演捕获——执行记录滞后于
    最新 changelog 批次即判 FAIL）。检查逻辑：
      ① 取 changelog 版本记录表最新版本号（| 0.0.NN | 行最大值）；
      ② 验证 documentation-governance 执行记录引用块包含该版本号。
    豁免边界（防误报）：
      - changelog 无版本记录行（异常态）时不判；
      - 执行记录引用块缺失本身即 FAIL（自引用快照不存在）；
      - 版本号以字符串包含匹配（0.0.NN 形态不会与更大版本号前缀混淆）。
    """
    changelog = DOCS / "governance" / "changelog.md"
    gov = DOCS / "governance" / "documentation-governance.md"
    cl_text = changelog.read_text(encoding="utf-8")
    gv_text = gov.read_text(encoding="utf-8")
    vers = re.findall(r"^\| (0\.0\.\d+) \|", cl_text, re.M)
    if not vers:
        print("[6.32] 治理执行记录覆盖性: changelog 无版本记录（跳过）")
        return
    latest = max(vers, key=lambda v: [int(x) for x in v.split(".")])
    m = re.search(r"> \*\*执行记录（设计阶段）\*\*[^\n]*", gv_text)
    if not m:
        fail("6.32 治理执行记录缺失（documentation-governance §3 应含「执行记录（设计阶段）」自引用快照）")
        print("[6.32] 治理执行记录覆盖性: 执行记录引用块缺失（FAIL）")
        return
    rec = m.group(0)
    if latest not in rec:
        fail(f"6.32 治理执行记录未覆盖最新 changelog 批次 {latest}（自引用快照须含最新批次，round35 R35-01 防复发）")
    print(f"[6.32] 治理执行记录覆盖性: 最新批次 {latest}，执行记录{'已覆盖' if latest in rec else '滞后'}")


def check_changelog_structure() -> None:
    """6.34 changelog 结构纪律（0.0.82 落 round43 §四 4.4 S43-3，防 R43-09/10 复发）。

    检查逻辑：
      ① 叙述节版本号单调升序：changelog 正文 `## 0.0.N（...）` 按出现顺序提取 N，
         必须严格递增（倒置即 FAIL）；
      ② `## 版本记录` 标题须紧邻其表体——标题与首条 `| 版本 |` 表头之间
         不得插入其它 `## X.Y.Z` 节（中间只允许空白行）。
    豁免：changelog 无叙述节时不判。
    """
    cl = DOCS / "governance" / "changelog.md"
    text = cl.read_text(encoding="utf-8")
    nar = re.findall(r"^## (0\.0\.\d+)[（(]", text, re.M)
    bad = 0
    for i in range(1, len(nar)):
        a = [int(x) for x in nar[i - 1].split(".")]
        b = [int(x) for x in nar[i].split(".")]
        if b < a:
            fail(f"6.34 changelog 叙述节顺序倒置：{nar[i-1]} 在 {nar[i]} 之前出现（须升序，R43-09 防复发）")
            bad += 1
            break
    m = re.search(r"^## 版本记录\s*$", text, re.M)
    if m:
        rest = text[m.end():]
        nxt = re.search(r"^## ", rest, re.M)
        seg = rest[: nxt.start()] if nxt else rest
        if not re.search(r"^\| *版本 *\|", seg, re.M):
            fail("6.34 changelog `## 版本记录` 标题未紧邻版本表体（中间插入了其它 `##` 节，R43-10 防复发）")
            bad += 1
    print(f"[6.34] changelog 结构纪律（S43-3）: 叙述节 {len(nar)} 个{'升序合规' if bad == 0 else '异常 ' + str(bad)}；版本记录邻接{'合规' if bad == 0 else '异常'}")


def check_redline_mutex() -> None:
    """6.35 红线语义互斥词对检查（0.0.82 落 round43 §四 4.4 S43-1 试点）。

    维护「禁止性红线关键短语 ↔ 违例措辞」词对表；全库扫描违例措辞，
    若某行出现该措辞且该行无否定词（不/未/无/禁/勿/避/免/否/拒/阻）则 FAIL。
    试点仅含 S-14 一对：红线禁止「内部使用权重反向写回主副本」，违例措辞为
    肯定式「合并回/至主副本」「写回主副本」「回写主副本」「回主副本」。
    否定行（如「不得合并回主副本」描述规则本身）跳过以避免误报。
    """
    pairs = [
        ("S-14", [r"合并[至回]主副本", r"写回主副本", r"回写主副本", r"回主副本"]),
    ]
    neg = re.compile(r"[不未无禁勿避免否拒阻]")
    hits = 0
    for p in pathlib.Path(DOCS).rglob("*.md"):
        try:
            lines = p.read_text(encoding="utf-8").split("\n")
        except Exception:
            continue
        for i, line in enumerate(lines):
            for _, pats in pairs:
                for pat in pats:
                    if re.search(pat, line) and not neg.search(line):
                        fail(
                            f"6.35 红线语义互斥（S-14）：{p.relative_to(DOCS)} 第 {i+1} 行 "
                            f"含违例措辞「{pat}」且无否定词（内部信号不得写回主副本，S-14）"
                        )
                        hits += 1
    print(f"[6.35] 红线语义互斥词对检查（S43-1 试点）: {hits} 处违例")


# ---------------------------------------------------------------------------
# 0.0.84 门禁扩展（round46 结构性建议 S45-1/S45-2/S45-3 落地）
# ---------------------------------------------------------------------------
# S45-1 版本归属互斥检查（6.36）
_LANDED_RE = re.compile(r"已落地|已实现|已支持|已交付|已实施|首迭代实现")
_UNLANDED_RE = re.compile(r"未落地|未实现|未支持|未交付|未实施|完全未实现|完全未落地")
# 契约枚举值（data-model.md L69 / 架构 §3.x）：普通英文词，需词边界精准匹配
_CONTRACT_VALUES = {"permanent", "ondemand", "environmental", "temporary", "intention"}
_ENT_BACKTICK = re.compile(r"`([A-Za-z0-9_]+)`")
_ENT_SNAKE = re.compile(r"(?<![A-Za-z0-9_])([a-z][a-z0-9]*(?:_[a-z0-9]+){1,})(?![A-Za-z0-9_])")
_INTENTION_RE = re.compile(r"(?<![A-Za-z0-9_])intention(?![A-Za-z0-9_])")
# 豁免：历史叙述 / 未来规划 / 债务账目 / 审计产物报告（差异描述是合规的）
_S45_EXEMPT = {"changelog.md", "architecture-blueprint-v1.1.md", "debt-collection.md"}


def _endpoint_registry(text: str) -> set[str]:
    """从 api-spec 抽取端点登记（与 6.23/6.28 同口径）。"""
    eps: set[str] = set()
    for m in re.finditer(
        r"^(?:\*{2}|###\s*)(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s*]+)",
        text, re.M,
    ):
        eps.add(f"{m.group(1)} {m.group(2).split('?')[0].rstrip('/')}")
    return eps


def check_version_mutex() -> None:
    """6.36 版本归属互斥检查（round46 S45-1 落地）。

    对同一实体（端点 / 契约值 / 事件类型 / 表字段 / 通用命名实体），若其在
    全库权威设计文档中同时被赋予「已落地/v0.1.0」与「未落地/v1.1+」两类显式
    版本归属判断，则构成自相矛盾——直接对应 round45 两项高风险（R45-01 契约
    能力粒度、R45-02 事件枚举范围）的共同根因「版本标签与规格内容脱节」。

    机制：自举式倒排索引。仅对「同一行内同时含实体名与显式版本归属动词」的
    位置建立 实体 → {landed, unlanded} 标签集合；同行内同时出现两标签（多为
    「不是未落地，而是已落地」式澄清句）不计入；跨文档或同文档不同行出现两
    标签即 WARN。

    已晋升 FAIL（round46 首轮 WARN 观察一轮——round47 全库 0 违例，round48 晋升
    FAIL，对齐报告 §4.4 S45-1 原始 FAIL 意图）。

    豁免文档：changelog（历史叙述）、blueprint-v1.1（未来规划）、
    debt-collection（债务账目）、analysis/（外部对照产物）、版本记录表行
    （`| 0.0.x |`）——这些对 v0.1.0/v1.1+ 的差异描述是合规的，不构成矛盾。
    """
    api_path = DOCS / "specification" / "api-spec.md"
    endpoints: set[str] = set()
    if api_path.is_file():
        endpoints = _endpoint_registry(api_path.read_text(encoding="utf-8"))

    # 实体 → 文档 → {标签集合}
    inv: dict[str, dict[str, set[str]]] = {}

    def tag(entity: str, doc: str, kind: str) -> None:
        inv.setdefault(entity, {}).setdefault(doc, set()).add(kind)

    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in _S45_EXEMPT or "analysis" in parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in text.split("\n"):
            s = line.lstrip()
            if re.match(r"^\| *0\.0\.", s):  # 版本记录表行（历史叙述）
                continue
            landed = _LANDED_RE.search(line)
            unlanded = _UNLANDED_RE.search(line)
            if landed and unlanded:
                continue  # 同行澄清句，跳过
            if not (landed or unlanded):
                continue
            found: set[str] = set()
            for m in _ENT_BACKTICK.finditer(line):
                found.add(m.group(1))
            for m in _ENT_SNAKE.finditer(line):
                found.add(m.group(1))
            if _INTENTION_RE.search(line):
                found.add("intention")
            for ev in endpoints:
                if ev in line:
                    found.add(ev)
            for ent in found:
                if len(ent) < 3:
                    continue
                if landed:
                    tag(ent, rel, "landed")
                if unlanded:
                    tag(ent, rel, "unlanded")

    hits = 0
    for ent, docs in inv.items():
        kinds: set[str] = set()
        for k in docs.values():
            kinds |= k
        if "landed" in kinds and "unlanded" in kinds:
            where = "; ".join(f"{d}:{'/'.join(sorted(v))}" for d, v in docs.items())
            fail(f"6.36 版本归属互斥：实体「{ent}」同时被标为已落地与未落地（{where}）")
            hits += 1
    print(f"[6.36] 版本归属互斥检查（S45-1）: {hits} 处实体跨文档/跨章节版本标签矛盾")


def check_table_scope_consistency() -> None:
    """6.37 表格内容与引言范围词一致性（round46 S45-2 落地）。

    若某表格的紧邻引言含**排他性上限限定词**「仅列 / 仅含」并附带明确计数
    「N 类/项/种/个/条」，而其后紧跟的表格数据行数 > N，则引言的范围限定
    与表格实际内容不一致（典型如 round45 R45-02：引言写「仅列核心类型」却
    表列全部 10 类）——WARN。

    仅对排他性「仅列/仅含」触发；「核心 / 部分 / 首迭代 / 仅 N 项（其中）」
    等描述「表中子集」或「另一张表」的软词不触发（此类计数本就不等于表体行
    数，误报率高）。已晋升 FAIL（round46 首轮 WARN 观察一轮——round47 全库
    0 违例，round48 晋升，保守口径维持不变）。
    """
    upper_qual = re.compile(
        r"(仅列|仅含)\D{0,12}?(\d+)\s*(类|项|种|个|条)"
    )
    hits = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in _S45_EXEMPT or "analysis" in parts:
            continue
        try:
            lines = p.read_text(encoding="utf-8").split("\n")
        except Exception:
            continue
        for i, line in enumerate(lines):
            # 检测表格起始：当前行以 | 开头且下一行是表头分隔行
            if not line.lstrip().startswith("|"):
                continue
            nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
            if not re.match(r"^\|?[\s:|-]+\|[\s:|-]+\|", nxt):
                continue
            # 取表格前 1~3 个非空行作为引言
            intro = ""
            j = i - 1
            cnt = 0
            while j >= 0 and cnt < 3:
                if lines[j].strip():
                    intro = lines[j].strip() + " " + intro
                    cnt += 1
                j -= 1
            m = upper_qual.search(intro)
            if not m:
                continue
            claimed = int(m.group(2))
            # 统计数据行：从表头分隔行之后算起，直到非 | 行
            rows = 0
            k = i + 2
            while k < len(lines) and lines[k].lstrip().startswith("|"):
                rows += 1
                k += 1
            if rows > claimed:
                fail(
                    f"6.37 表格范围词不一致：{rel} 引言称「{m.group(0)}」"
                    f"但后续表格实有 {rows} 数据行（> {claimed}）"
                )
                hits += 1
    print(f"[6.37] 表格内容与引言范围词一致性（S45-2）: {hits} 处引言范围限定与表体行数不符")


def check_threshold_self_consistency() -> None:
    """6.38 阈值型监控规则自洽性（round46 S45-3 落地）。

    对「指标 / 阈值 / 触发动作」三列监控表，若同文档存在该指标的当前值声明
    且当前值已越过阈值（监控规则在交付态即恒触发、自毁），则 WARN——对应
    round45 R45-03「阈值型监控自毁」根因。

    仅当阈值可解析为简单数值（可带 %）且同文档能定位到显式当前值声明
    （当前/已达/已知/现状/为/＝ + 数值）时才判定，解析失败的模糊情形跳过
    （保守，避免误报）。已晋升 FAIL（round46 首轮 WARN 观察一轮——round47
    全库 0 违例，round48 晋升，保守口径维持不变）。
    """
    mon_header = re.compile(r"指标.*阈值.*触发|阈值.*指标.*触发|监控.*指标.*阈值")
    num = r"(\d+(?:\.\d+)?)\s*%?"
    cur_pat = re.compile(
        r"(?:当前|已达|已知|现状|目前)\D{0,15}?(" + num + r")|"
        r"([A-Za-z_一-龥]{1,20}?)\s*(?:为|＝|=|已达|当前)\s*(" + num + r")"
    )
    hits = 0
    for p in md_files():
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        parts = set(p.relative_to(DOCS).parts)
        if p.name in _S45_EXEMPT or "analysis" in parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if not line.lstrip().startswith("|"):
                continue
            nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
            if not re.match(r"^\|?[\s:|-]+\|[\s:|-]+\|", nxt):
                continue
            if not mon_header.search(line):
                continue
            # 解析表头列位置
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            try:
                mi = header.index("指标")
                ti = header.index("阈值")
            except ValueError:
                continue
            k = i + 2
            while k < len(lines) and lines[k].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[k].strip().strip("|").split("|")]
                if len(cells) <= max(mi, ti):
                    k += 1
                    continue
                metric = cells[mi]
                thr = re.search(num, cells[ti])
                if not metric or not thr:
                    k += 1
                    continue
                try:
                    threshold = float(thr.group(1))
                except ValueError:
                    k += 1
                    continue
                # 在同文档搜索该指标的当前值声明
                cur_m = cur_pat.search(text)
                # 仅当声明中出现的名词与指标名有足够重叠时才采信
                if cur_m:
                    val = cur_m.group(1) or cur_m.group(3)
                    noun = cur_m.group(2) or ""
                    if val and (metric[:2] in noun or noun[:2] in metric) and len(metric) >= 2:
                        try:
                            cur_val = float(val)
                        except ValueError:
                            k += 1
                            continue
                        if cur_val >= threshold:
                            fail(
                                f"6.38 阈值监控自洽性：{rel} 指标「{metric}」"
                                f"当前值 {cur_val} 已 ≥ 阈值 {threshold}（交付态恒触发）"
                            )
                            hits += 1
                k += 1
    print(f"[6.38] 阈值型监控规则自洽性（S45-3）: {hits} 处监控规则交付态即越阈")


def check_batch_version_record_coverage() -> None:
    """6.39 受改批次版本记录覆盖性（round54 R54-01 防复发，WARN 级软门禁）。

    R54-01 缺陷：traceability-map 版本记录 0.0.90 行混入本属 0.0.93 的
    内容、且 0.0.93 行整体缺失——「批次声明受改、版本记录无对应行」的
    登记缺陷（round32 曾系统性补登 14 处、round53 R53-02 同类复发）。
    本检查以 changelog 最新批次叙述节的「受改 N 份文档（A / B / C）」
    清单为输入，逐文档核对版本记录是否含该批次行（| 0.0.NN | 行），
    缺失即 WARN（软门禁，不阻断 exit 0——防「触及即登记」纪律回潮）。

    解析策略（保守防误报）：
      ① 最新批次号：changelog 版本记录表 | 0.0.NN | 行取 max（同 6.32）；
      ② 最新批次叙述节：`## 0.0.NN（` 起至下一个 `## 0.0.NN（` 或
         `## 版本记录` 止；
      ③ 受改清单：正则 `受改\s*\d+\s*份?文档?（([^）]+)）` 提取括号内容，
         按 `/` 或 ` + ` 分割条目；
      ④ 条目解析：剥 markdown 链接（[x](y) → x）、剥 .md 后缀、trim；
         「本文件」→ changelog.md；跳过含「scripts/」「.py」「.html」
         「.sql」「.yaml」「.json」「审计报告」「analysis/」的条目；
         缩写映射：architecture→architecture-v0.1.0、blueprint→
         architecture-blueprint-v1.1、README→README.md；
      ⑤ 定位失败或目标非 md（无法在 docs/ 下唯一 basename 匹配）→
         跳过（不误报）；
      ⑥ 目标文档版本记录区（兼容 `## 版本记录` / `## §12 版本记录`
         两种标题）须含 `| 0.0.NN |` 行，缺失 → WARN。
    豁免：最新批次叙述节无「受改 N 份文档（…）」形态时跳过不判。
    """
    changelog = DOCS / "governance" / "changelog.md"
    if not changelog.exists():
        return
    cl_text = changelog.read_text(encoding="utf-8")
    vers = re.findall(r"^\| (0\.0\.\d+) \|", cl_text, re.M)
    if not vers:
        return
    latest = max(vers, key=lambda v: [int(x) for x in v.split(".")])
    # 提取最新批次叙述节
    m_start = re.search(rf"^## {re.escape(latest)}（", cl_text, re.M)
    if not m_start:
        return
    seg = cl_text[m_start.start():]
    m_end = re.search(r"^## (?:0\.0\.\d+（|版本记录)", seg[m_start.end():], re.M)
    if m_end:
        seg = seg[: m_start.end() + m_end.start()]
    # 提取受改清单
    list_m = re.search(r"受改\s*\d+\s*份?文档?（([^）]+)）", seg)
    if not list_m:
        print(f"[6.39] 受改批次版本记录覆盖性: 最新批次 {latest} 无受改清单（跳过）")
        return
    items = re.split(r"\s*(?:/|\+)\s*", list_m.group(1))
    alias = {
        "architecture": "architecture-v0.1.0",
        "blueprint": "architecture-blueprint-v1.1",
        "README": "README",
        "本文件": "changelog",
    }
    skip_mark = ("scripts/", ".py", ".html", ".sql", ".yaml", ".json", "审计报告", "analysis/")
    warn_cnt = 0
    for item in items:
        raw = item.strip()
        if not raw:
            continue
        # 剥 markdown 链接
        lm = re.match(r"\[([^\]]+)\]\([^)]+\)", raw)
        if lm:
            raw = lm.group(1)
        if raw.endswith(".md"):
            raw = raw[:-3]
        raw = raw.strip()
        if not raw:
            continue
        if any(mk in raw for mk in skip_mark):
            continue
        name = alias.get(raw, raw)
        # basename 唯一匹配 docs/ 下 .md（排除 analysis/ 与 reviews/）
        cand = DOCS / f"{name}.md"
        cand_rel = f"{name}.md"
        hits = [
            p for p in md_files()
            if p.name == cand_rel and "analysis" not in p.relative_to(DOCS).parts
        ]
        if len(hits) != 1:
            continue
        target = hits[0]
        t_text = target.read_text(encoding="utf-8")
        # 版本记录区（兼容 ## 版本记录 / ## §12 版本记录）
        vr = re.search(r"^#{1,6}\s*.*版本记录.*$", t_text, re.M)
        if not vr:
            continue
        vr_sec = t_text[vr.start():]
        row_pat = rf"^\|\s*{re.escape(latest)}\s*\|"
        if not re.search(row_pat, vr_sec, re.M):
            warn(
                f"6.39 受改批次版本记录覆盖性：changelog {latest} 批次声明受改 "
                f"「{raw}」（{target.relative_to(DOCS)}），但其版本记录无 {latest} 行"
                f"（触及即登记，R54-01 防复发）"
            )
            warn_cnt += 1
    print(f"[6.39] 受改批次版本记录覆盖性: 最新批次 {latest}，受改清单 {len(items)} 项，漏登记 {warn_cnt} 项")


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
    check_feature_list_refs()
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
    check_feature_flag_count()
    check_falsification_carry()
    check_self_imposed_gate_debt()
    check_endpoint_source()
    check_endpoint_section()
    check_cognitive_deprovision()
    check_section_refs()
    check_section_version_marks()
    check_contract_consistency()
    check_error_code_sets()
    check_example_discipline()
    check_punctuation_discipline()
    check_gov_exec_record()
    check_changelog_structure()
    check_redline_mutex()
    check_version_mutex()
    check_table_scope_consistency()
    check_threshold_self_consistency()
    check_batch_version_record_coverage()
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
