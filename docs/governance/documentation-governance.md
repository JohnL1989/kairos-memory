---
title: 文档治理规范
aliases:
  - 文档维护规则
  - doc-governance
tags:
  - kairos
  - governance
  - documentation
created: 2026-07-21
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# 文档治理规范

> 三轮审计反复发现"改了 A 没改 B"的根因。本文定义文档维护的元规则，防止文档腐烂。

---

## §1 更新联动规则

> **⚠ 执行要求**：下表为硬性联动规则——任何修改操作（不限于文档编辑，含架构评审、PR 审查、代码重构）均须在修改完成前检查并更新右侧文档。不符合联动规则的提交应被 PR 审查驳回。历史审计发现「改了 A 没改 B」的根因是联动规则未被执行，而非未定义。

修改以下任一资产时，必须同步更新右侧文档：

| 修改对象 | 必须同步的文档 |
|:--------|:--------------|
| 架构设计（层/组件/接口） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)、[implementation-map.md](../specification/implementation-map.md) |
| 数据模型（表/列/索引） | [data-model.md](../specification/data-model.md)、[api-spec.md](../specification/api-spec.md) |
| API 端点（新增/变更/废弃） | [api-spec.md](../specification/api-spec.md)、[integration-design.md](../development/integration-design.md)、[user-guide.md](../user/user-guide.md) |
| 配置参数（新增/删除/默认值变更） | [configuration.md](../ops/configuration.md)、[deployment.md](../ops/deployment.md)、[coding-conventions.md](../development/coding-conventions.md) |
| 功能清单（新增/删除功能） | [feature-list.md](../specification/feature-list.md)、[claim-implementation-matrix.md](../specification/claim-implementation-matrix.md) |
| 非功能指标（阈值/容量/RTO） | [nfr-specification.md](../specification/nfr-specification.md)、[reliability.md](../ops/reliability.md) |
| 安全红线（新增/修订） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8、[threat-model.md](../security/threat-model.md)、安全规格文档 |
| 测试用例（新增场景） | [test-strategy.md](../quality/test-strategy.md)、[test-plan.md](../quality/test-plan.md)（用例库） |
| CLI 命令（新增/变更） | [api-spec.md](../specification/api-spec.md) CLI 表、[quick-start.md](../user/quick-start.md)、[user-guide.md](../user/user-guide.md) |
| 裁决模型 / 核心概念语义（改名或重定义） | [cognitive-foundation.md](../foundation/cognitive-foundation.md)（含**正文散述**与**规则汇总表**）、[design-philosophy-relations.md](../foundation/design-philosophy-relations.md)（含 **ASCII 关系图内文字**）、[glossary.md](../references/glossary.md)（单一事实源，**必改**）、[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) 对应章节、[adr.md](./adr.md) |

**语义变更的特别约定**：概念改名或重定义时，仅改「定义处」不算完成。必须同时清理三类易漏载体——① ASCII/Mermaid 图内的文字；② 表格单元格内的简写表述；③ [glossary.md](../references/glossary.md) 的术语释义。这三处不参与正文阅读流，最容易在改动中被跳过。

**自行检查**：每次 commit 前运行 `grep -rn "旧值\|旧名" docs/` 确保无旧值残留；语义变更还须运行 `python scripts/doc-audit.py` 的废弃术语检查（第 13 项）。

---

## §2 交叉引用规范

1. 引用同一文档内的章节：用 `§X.Y`（如 `§3.2`、`§0.5`）
2. 引用跨文档章节：用 `[文档名](相对路径) §X`（如 `[架构](../foundation/architecture-v0.1.0.md) §3.2`）
3. 引用认知基础→架构：一律使用词汇桥接表（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.6）中的映射
4. 禁止引用不存在的章节号——新增或重排章节后必须 grep 全库更新所有交叉引用

**大章标题风格约定（决策：标题归一闭环）**：全库大章标题为两种形态（归一后的既定状态，新文档按此选择）：

- **§N 数字序**（`## §N 标题`）——工程/规格/治理文档（architecture、api-spec、data-model、documentation-governance、release-guide、runbook、security-specification、requirements-baseline、test-plan、detailed-design、configuration 的架构镜像小节）；
- **中文序**（`## 一、标题`）——认知/叙述类文档（cognitive-foundation、observability、technology-stack、architecture-blueprint 等）。

小节（`### N.M`）一律数字编号。引用一律用数字（`§N`/`§N.M`，含对中文序大章文档的引用——如「认知基础 §1.3」，与标题文字解耦）。引言性无编号大章（「引论」「组件索引」）为允许例外。变更大章标题风格属结构性变更，触发 §2.2 连锁复核流程。

**死链检测**：每次里程碑前运行 `grep -Pn '§\d+\.\d+' docs/` 逐一核实目标是否存在（`-P` 启用 PCRE 正则，标准 grep 不支持 `\d`）。

### §2.1 机制定义唯一化（人工门禁，2026-08-04 决策）

> **背景**：全库曾出现六处【高】级矛盾（知识演化两套判定、临时契约审计痕迹三处冲突、"时序优先"残留、契约枚举三套命名、5D 排序残留、dd→api-spec 章节错位）**全部是"同一机制多版本并存"**——doc-audit 的链接/数值/编号检查均无法检测语义级重复定义。此类矛盾机器不可判，须由人工门禁兜住。

**规则**（三项，均为人工程序，非脚本可执行）：

1. **机制章节声明权威**：每份规格文档中，跨文档被引用的机制（如知识演化追踪、遗忘调度器、契约枚举、分域真理路由、临时契约审计痕迹等）须在其定义章节开头显式声明"本节为权威定义，其余章节/文档引用之"——其他出现处只承载概述或引用，不承载第二套判定规则。已声明范例：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「本节为演化判定的权威定义」、§0.4「§5.2 为权威」。
2. **同机制表述全库检索**：新增或修改任一机制的定义时，须 `grep -rn "<机制关键词>" docs/` 列出全部出现处，逐处判断：(a) 引用处是否指向权威定义；(b) 是否有第二套阈值/流程/枚举（若有，删除或改写为引用）；(c) 枚举/阈值类差异是否属"两个不同参数"（若是，补参数名区分注记，如架构 §0.9 的 100ms/200ms 双窗口）。检索结果与处置记入该次变更的 changelog 条目。
3. **冲突裁决标注**：无法立即收敛的语义冲突，须显式标注"以 XX 为准，见 <链接>"并登记于 [debt-collection.md](debt-collection.md) 或差距表——不允许两处定义并存而无裁决标注。

**检查清单**（评审 PR / 里程碑时人工执行）：同机制是否仅一处定义阈值/流程/枚举？其余出现处是否为概述或带权威引用？矛盾处是否已标注裁决？

### §2.2 结构性变更连锁复核（人工流程规则，2026-08-06 决策）

> **背景**：第九轮审计 H-01 类「同源漏修」连续六轮复发——§3.2→§3.3 引用漂移 29 处（含审计遗漏 2 处同源）的根因是**章节结构性变更后缺乏强制性的全库连锁复核流程**。门禁 6.14（机制名→权威章节映射抽检）覆盖"机制名 + §X 同行引用"，但章节**结构本身**（迁移/更名/删除/重排）的连锁影响是人工流程缺口。

**触发条件**（满足任一即触发本流程）：章节迁移、章节更名（含标题文字变更）、章节删除或合并、文档拆分/合并、机制权威落点变更、大章序号风格变更（如 §N ↔ 中文序）。

**强制步骤**（变更前与变更后各一遍）：

1. **变更前基线扫描**：`grep -rn "§X" docs/` 列出该章节的全部引用（跨文档 `[doc](path) §X`、同文档裸 `§X`、configuration 类镜像章节 `### §X`）；记录引用总数作为复核基数。
2. **变更执行**：修改标题/迁移内容，保持小节编号（`### X.Y`）稳定优先——小节编号是引用主锚点，大章标题文字次之。
3. **变更后复核清单**（逐项核对，结果登记入该次 changelog 条目）：
   - (a) 全部基线引用逐一复核：新标题下引用是否仍可导航（门禁 2/18 自动兜底跨文档链接引用）；
   - (b) **同源遗漏扫描**：与变更章节同义/近义的机制名、同章节族（§X 下的全部小节）重新 grep——H-01 类漏修多发生在"改了 A 处忘了 B 处同源"；
   - (c) **镜像章节检查**：configuration「### §X」类按架构章节镜像组织的小节、技术栈等"章节号对齐"文档是否需同步；
   - (d) **反向指引检查**：被迁章节原位置是否留有反向指引（如架构 §3.2 首段「见 §3.3」）；
   - (e) 门禁复跑：doc-audit 2/18（章节引用）、6.14（机制映射）、6.15（硬行号禁令）全绿。
4. **复核登记**：复核结果（引用基数、改动数、同源遗漏发现数）写入该批次 changelog 条目——与门禁 6.14 自动抽检形成双保险。

**检查清单**（评审 PR / 里程碑时人工执行）：结构性变更是否完成基线扫描与复核登记？同源语义（近义词/同章节族）是否全覆盖？镜像文档是否同步？反向指引是否保留？

---

## §3 审查周期

| 周期 | 审查内容 |
|:----|:---------|
| 每次代码 commit | 关联文档是否同步更新（§1 联动表） |
| 每次里程碑（Phase 交付） | 运行 `scripts/doc-audit.py`（交叉引用死链检测 + 章节引用校验 + 数值一致性检查 + 版本记录校验） |
| 每月 | 全量文档状态审计（draft → design-freeze 晋升 / 废弃标记） |
| 每次外部评审接收后 | 评审建议逐条回复并更新对应文档 |

> **执行记录（设计阶段）**：代码启动前的「全量文档状态审计」暂缓执行；最近一次文档一致性自审于 2026-07-31 完成（全面重新设计口径调整轮），修复了旧项目残留引用、跨文档数值漂移与编号注册表问题，并完成全库交叉引用格式规范化——跨文档章节引用统一为 `[文档名](相对路径) §X` 链接格式（见 changelog 0.0.1）。2026-08-03 完成全库两轮审计 + 独立复核（135 项修复 + 15 项决策）；2026-08-04 完成市场理念吸收（D-322~325）与全库深度审计修复（changelog 0.0.8 批次）；2026-08-05 完成开发就绪度/全面深度/Marvis/第四轮/第五轮/系统架构图/内容架构审视/第六轮/第七轮等批次审计；2026-08-06 完成第十轮至第十五轮深度审计（0.0.29~0.0.37）与本轮全面审计修复（0.0.38，含版本标记全库收敛、编号注册表补全、豁免条款登记）（批次明细见 [changelog.md](changelog.md)）。**后续文档修订一律遵循 §2 格式**，新增或修改跨文档引用时必须使用链接格式。文档一致性审计脚本 `scripts/doc-audit.py` 已建立并纳入里程碑门禁（§3）。待代码启动后，按本周期恢复每月全量审计并写入执行日期。

---

## §4 状态管理

> **当前阶段声明**：代码启动前，全部文档保持 `draft` 状态。晋升至 `design-freeze` 的规则待代码启动后执行。此暂缓不改变治理规则的效力——规则在代码启动后即刻生效。

> **frontmatter 字段语义（0.0.38 批次登记）**：`updated` = 内容最后修改日期（批次实质修改文档时同步）；`last_reviewed` = 最近一次人工审查/一致性核对日期（≥ updated）。批次登记版本记录时：实质触及的文档两者均更新至批次日期；仅登记版本记录未修改正文的文档只更新 `updated`。doc-audit 校验 `updated` 不早于版本记录最新批次日期。

| 状态 | 含义 | 晋升条件 |
|:----|:-----|:---------|
| `draft` | 初稿/未定稿，内容可能不完整 | 完成自审 + 至少一轮外部审阅 |
| `design-freeze` | 设计已冻结，待代码实现后验证 | 架构层设计决策全部锁定，仅修正 P0 一致性缺陷 |
| `v0.1.0` | 与可运行版本一致，可依赖 | 对应模块代码已实现并通过验收 |
| `deprecated` | 已被替代，仅保留历史参考 | 新文档已发布，旧文档标记废弃原因和替代路径 |

---

## §5 编号与命名注册

以下命名空间在各自文件中维护，新增或变更必须先注册再使用：

| 命名空间 | 注册位置 | 格式 |
|:--------|:--------|:----|
| 功能编号（W/R/M/SF/F/PM/A） | [feature-list.md](../specification/feature-list.md) 功能分类统计 | 分类前缀 + 两位数序号 |
| 校准能力编号（CAL-01~06） | [feature-list.md](../specification/feature-list.md) 校准类能力 | CAL-两位数（与测试用例 TC-CAL- 三位数消歧：能力编号两位、测试编号三位） |
| 认知声明编号（C-01~C-37，C-23 已废弃） | [claim-implementation-matrix.md](../specification/claim-implementation-matrix.md) | C-两位数 |
| 操作编号（OP-001~OP-066） | [specification/operation-catalog.md](../specification/operation-catalog.md) | OP-三位数 |
| 安全红线编号（S-01~S-19） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8 | S-两位数 |
| S-20~S-22（v2.0 多 Agent 校准扩展） | [social-calibration-roadmap.md](social-calibration-roadmap.md) | S-两位数 |
| 闭环编号（DC-XXX） | [governance/debt-collection.md](debt-collection.md) | DC-三位数 |
| Mnemosyne 闭环编号（MNM-XXX） | [governance/debt-collection.md](debt-collection.md) | MNM-三位数 |
| 差距编号（G-XXX） | [governance/cognitive-architecture-gap.md](cognitive-architecture-gap.md) | G-两位数（允许子编号 G-09a） |
| 校准测试编号（CAL-XXX） | [quality/test-plan.md](../quality/test-plan.md) | CAL-三位数 |
| 债务溯源编号（ARC-D-XXX） | [governance/debt-collection.md](debt-collection.md) | ARC-D-三位数 |
| 社会性校准里程碑编号（SCR-XXX） | [governance/social-calibration-roadmap.md](social-calibration-roadmap.md) | SCR-两位数 |
| 测试用例编号（TC-XXX） | [quality/test-plan.md](../quality/test-plan.md) | TC-前缀 + 两位数 |
| 错误码（ERR-XXX-NNN） | [references/error-reference.md](../references/error-reference.md) | ERR-XXX-NNN |
| 债务编号（D-0xx~D-4xx，分段见下） | [governance/debt-collection.md](debt-collection.md) | D-三位数 |
| 决策编号（D-XX，两位，01~27） | [adr.md](./adr.md)「审计决策迁移」节（现为权威定义源；原定义于 reviews 审计报告,已迁移） | D-两位数 |
| ADR 编号（ADR-001~012） | [adr.md](./adr.md) | ADR-三位数 |
| 架构风险编号（RSK-001~RSK-NNN） | [governance/risks.md](risks.md) | RSK-三位数 |
| 张力编号（T-XXX） | [governance/risks.md](risks.md) | T-三位数 |
| 方法论风险编号（MRK-XXX） | [governance/risks.md](risks.md) | MRK-三位数 |

> **消歧说明（强制规则）**：决策编号（D-01~D-27，两位）与债务编号（D-0xx~D-4xx，三位）同前缀并存——引用决策时须写'决策 D-0X'，引用债务时写'债务 D-0XX'，避免歧义。**全库引用必须显式标注体系**（如「决策 D-15」「债务 D-015」）；doc-audit 不覆盖此检查（位数差异无法正则区分），由评审与人工审查执行。已知违例已逐一标注（认知基础 D-019/D-15、架构 CJ-009 D-006 等）。

**禁止**：同一名称出现在两处不同定义的文档中。若必须引用，加注 `（见 §X）` 指向唯一事实源。

**债务编号分段语义（RC-16）**：`D-` 三位数按百位分段，段内不得断号（断号须保留墓碑条目占位，见 doc-audit.py §14）：

| 段 | 含义 | debt-collection 段落 |
|:--|:-----|:----------------|
| D-0xx | 架构设计间隙（文档级可修，认知-工程差距·活跃区） | 一、架构设计间隙 |
| D-1xx | 架构扩展设计项（需设计阶段完成） | 二、需设计阶段完成项 |
| D-2xx | 代码级实现项·基础运行时（注册表/编译器/管道/CRI） | 三、需实现阶段完成项 |
| D-3xx | 代码级实现项·认知机制落地（逻辑-因果/校准/完整性轴等） | 三、需实现阶段完成项 |
| D-4xx | 代码级实现项·韧性/治理（DFA/P6 后悔率等） | 三、需实现阶段完成项 |

> **前置依赖声明规则（Marvis 建议 R-9）**：新增债务登记时，若该债务存在已知前置依赖（被其他债务阻塞或阻塞其他债务），须在条目「预期版本」段注明前置依赖编号，并同步登记于 [debt-collection.md](debt-collection.md) §六 关键路径依赖表。无前置依赖的债务注明「无前置依赖」。此规则确保债务间排期关系可判定——审计复核时检查新条目是否遗漏前置声明。

> **版本记录占位惯例（全库惯例）**：各文档版本记录**仅登记触及本文档的 changelog 批次**（doc-audit §12 校验单调递增与日期不倒退，不做跳号连续性检查——「仅登记触及批次」为全库惯例，未触及的批次不要求占位）。触及本文档但未逐条登记的连续批次区间，以**合并占位行**补注：`| 0.0.X~0.0.Y | 日期 | （合并占位：changelog 0.0.X~0.0.Y 批次的变更未逐条登记于本文档，见 [changelog.md](changelog.md) 全景） |`（缺失区间合并为单行，不逐条拆行）。

### §5.1 前缀冲突防护（2026-08-03 决策 D-14）

风险与功能曾共用 `R-` / `M-` 前缀，仅靠位数区分（两位 = 功能，三位 = 风险），其中 `R-19`（三信号混合检索）与 `R-019`（架构风险预留位）视觉上极易混淆。现已按下表分离：

| 旧前缀 | 新前缀 | 语义 | 迁移范围 |
|:------|:------|:-----|:--------|
| `R-001` ~ `R-019` | **`RSK-001` ~ `RSK-019`** | 架构级风险 | [risks.md](risks.md) 一、架构级风险 |
| `M-001` ~ `M-002` | **`MRK-001` ~ `MRK-002`** | 方法论风险 | [risks.md](risks.md) 三、方法论风险 |
| `R-01` ~ `R-28`（两位） | *不变* | 检索类**功能**编号 | [feature-list.md](../specification/feature-list.md) 等 5 份 |
| `M-01` ~ `M-23`（两位） | *不变* | 记忆管理类**功能**编号 | [feature-list.md](../specification/feature-list.md) 等 5 份 |

> **为何不反向统一**：把功能编号补零为三位（`R-001`~`R-028`）会与风险编号**直接撞号**，且影响 5 份文档共 51 个编号——方向错误且代价更大。改风险侧仅涉及 2 份文档 13 个编号。
>
> **为何用 `MRK-` 而非 `MIT-`**：`M-001`/`M-002` 在 [risks.md](risks.md) §三 登记的语义是「方法论风险」（monitoring 状态 + 影响评估 + 跟踪版本），属风险条目而非缓解措施条目，故取 **M**ethodological **R**is**K** 缩写。

**约束**：今后新增风险一律使用 `RSK-` / `MRK-` 前缀；`R-` / `M-` 两位数形式**专属功能编号**，不得再用于风险。

**`S-` 前缀保护（0.0.38 批次登记）**：`S-` 前缀为安全体系专用（安全红线 S-01~S-19、社会性校准扩展 S-20~S-22）——**审计/修复批次的问题编号不得使用 `S-` 前缀**（历史遗留「S-01 标题归一」类批次编号已消歧，见 0.0.38 changelog）；批次内问题编号使用 `R-xx`/`P-xx` 或描述性编号，必须与安全红线编号区分时冠以「批次」限定词。

### 严重级别词汇映射

| 体系 | 取值 | 用途 |
|:----|:----|:-----|
| 告警级别（observability） | critical / warning / info | 运行告警严重度（小写） |
| 风险等级（threat-model） | Critical / High / Medium / Low | 威胁风险评估（首字母大写） |
| 事件响应（security-spec §事件响应） | P0 / P1 / P2 | 安全事件响应优先级 |
| 映射关系 | P0 ≈ Critical ≈ critical；P1 ≈ High ≈ warning；P2 ≈ Medium/Low ≈ info | 跨文档引用时按映射翻译 |

---

## §6 单一事实源原则

1. 每个数值/枚举/命名**只有一个定义位置**
2. 其他文档引用该值时使用交叉引用，不重复写值
3. 例外：版本记录中的历史描述不受此限（记录已发生的事实）
4. 违反即标记为「数据漂移」，在下次审查中修复
5. **豁免 1（债务账目批次注记）**：debt-collection 债务条目「状态」「历史背景」「来源」等账目字段中的审计评估批次注记（如「状态（0.0.32 评估）」）为账目可追溯性需要，不受「零版本标记」约束——评估结论的作出批次是债务账目的事实组成部分。豁免范围仅限债务账目字段；正文段落、表格注释、yaml 注释等其他位置的批次标记一律禁止
6. **豁免 2（实证参考基线登记）**：参数校准类声明可标注参考来源系统与许可证（如「市场理念吸收…noah-gen3-type2，MIT 许可」），限用于参数/阈值/校准类声明的基线标注；其余正文「吸收/借鉴」标记须收敛为纯机制描述

---
## 版本记录

> 草稿阶段初始版本号为 0.0.1。发生实质性内容变更（数值核定、结构调整、决策落地、新增章节）时，按 0.0.2 → 0.0.3 … 递增修订号，并在版本记录中说明变更原因；待定稿后升级至 1.0.0。门禁（doc-audit.py §12）校验版本记录单调递增且日期不倒退。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 文档治理规范：更新联动/交叉引用/审查周期/状态管理/编号注册/单一事实源。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复——frontmatter/版本记录同步正文（D-14/RC-09/RC-16 已修订内容）；§3 补 2026-08-03/08-04 审计批次记录；§5 补决策编号注册条目与消歧说明，新增严重级别词汇映射小节。 |
| 0.0.3~0.0.10 | 2026-08-04 | （合并占位：changelog 0.0.3~0.0.10 批次的变更未逐条登记于本文档，见 [changelog.md](changelog.md) 全景） |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：决策/债务编号消歧说明强化为强制规则。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次：新增 §2.1 机制定义唯一化人工门禁（三项规则+检查清单）。 |
| 0.0.13 | 2026-08-04 | （占位：changelog 0.0.13 批次无涉及本文的变更，见 [changelog.md](changelog.md) 全景） |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：§5 决策编号注册更新为 D-01~D-27 双权威源（fix-report + cognitive-architecture-fixes）。 |
| 0.0.15~0.0.16 | 2026-08-05 | （合并占位：changelog 0.0.15/0.0.16 批次的变更未逐条登记于本文档，见 [changelog.md](changelog.md) 全景） |
| 0.0.17 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.17，Marvis 建议 R-9 落地）：§5 债务编号分段语义补「前置依赖声明规则」——新债务登记须声明前置依赖并同步关键路径依赖表。 |
| 0.0.18 | 2026-08-05 | 审计归档批次（changelog 0.0.18）：§5 决策编号注册表定义源改指 `adr.md`「审计决策迁移」节（原 reviews 审计报告已归档）;执行记录段 reviews/ 目录链接改指 `audit-history-summary.md`。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次（changelog 0.0.24）：§3 执行记录补 08-05 批次审计记录（2-05）；版本记录补 0.0.3~0.0.10/0.0.13/0.0.15~0.0.16 占位行（4-01）。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：§5 补版本记录占位惯例（仅登记触及批次 + 合并占位格式，4-3）；D-4xx 类别示例 DAP→DFA。 |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（changelog 0.0.29）：§2 补大章标题风格约定（S-01，§N 数字序/中文序双形态）；新增 §2.2 结构性变更连锁复核人工流程规则（D-02/M-13 建议 3）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：§6 补豁免 1（债务账目批次注记）与豁免 2（实证参考基线登记）；§5 注册表补 ADR/OP/C-xx/CAL 能力编号命名空间，§5.1 补 S- 前缀保护规则（审计批次编号禁用）；§4 补 frontmatter 字段语义（updated/last_reviewed）；消歧说明范围更新；S-01 撞名消歧；执行记录补 08-06 批次；零版本标记收敛。 |
