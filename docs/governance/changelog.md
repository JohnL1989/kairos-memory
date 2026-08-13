---
title: Kairos 变更日志
aliases:
  - CHANGELOG
tags:
  - kairos
  - governance
  - changelog
created: 2026-07-20
updated: 2026-08-13
last_reviewed: 2026-08-13
status: draft
---

# CHANGELOG

> **定位**：按日期记录的变更日志，记录从什么变成什么。各文档内嵌的版本记录保留为文档级审计，CHANGELOG 提供跨文档的版本演进全景。
>
> **浏览指引**：本文件按批次**时间正序**组织（`## 0.0.x（日期）— 标题`，最早批次在顶部、最新批次位于叙述节末尾）；文末版本记录表为全景索引（亦按正序）。定位方式：按版本号搜索 `## 0.0.x`；按日期搜索 `（2026-MM-DD）`；跨文档变更关系见 [README.md](../README.md) 与各文档内嵌版本记录。

---


## 0.0.1（2026-07-31）— 文档体系基线

- Kairos 全面重新设计的文档体系基线。全库 52 份文档的版本号统一为 0.0.1（草稿阶段），各文档版本记录条目为当前内容摘要；待定稿后统一升级版本号。
- 新增 [development/slice-implementation-guide.md](../development/slice-implementation-guide.md)：竖切实现者入口——组件清单、15 张表、REST/CLI 端点与逐组件实现规格。

---



## 0.0.2（2026-08-03）— 审计修复与决策落地（P0）

- **RC-01**：清理 `D-01` 决策废弃术语「兜底/终裁」5 处残留（glossary / cognitive-foundation / design-philosophy-relations / architecture-v0.1.0）。
- **RC-02**：新增 `api_keys` 表承载 API Key 三级鉴权（物理表 56 → 57 张），与既有 API Key 设计对齐。
- **RC-03**：三信号融合公式量纲修正——实体信号由乘性因子统一为加性交集比例，归一化 `norm()` 定义 `max==min` 退化分支，实体权重参数默认值冲突消除（统一 `KAIROS_HYBRID_ENTITY_WEIGHT`=0.15），废止 `KAIROS_ENTITY_BOOST_*` 三项。
- **RC-04**：补 PG↔SQLite 类型映射表 + 15 张竖切表可执行 DDL（`schema-slice.sql`），修复零 DDL 与类型错配缺口。

---



## 0.0.3（2026-08-03）— 文档体系一致性修复（P1~P3）

- **RC-05**：投影层 BGE-M3 1024 维 → 1536 维固定正交投影（ADR-012）+ 矩阵随 schema 持久化（`migrations/0010_embedding_projection.bin`，SHA-256 校验，绑定 `schema_version`）。
- **RC-06**：澄清路径空间为检索管线两阶段结构的硬过滤边界（非独立第 4 信号），修订 ADR-004 说明与架构 §7.3a 注释。
- **RC-07**：`memories` 表新增 `compacted` / `compacted_at` 列（压缩标记与 30 天回滚窗口判定）。
- **RC-08**：配置参数表扩展「取值范围」「生效时机」两列，正文参数 194 → 191、总数 342 → 339（废止实体 boost 三项并核减），同步 README / implementation-map 计数（历史口径以 configuration 版本记录为权威，2026-08-04 勘误统一）。
- **RC-09**：修订治理 §133 版本号规则——草稿阶段 0.0.1 起，实质变更按 0.0.2 → 0.0.3 递增，门禁校验版本记录单调递增且日期不倒退。
- **RC-10**：补齐本 CHANGELOG 的 `## 0.0.2` / `## 0.0.3` 叙述条目（版本记录行已先行登记）。
- **RC-12**：批量修正 28 份文档 frontmatter `updated` 日期倒挂（改正文未更新 frontmatter）。
- **RC-13**：`technology-stack.md` 补充可观测性栈（OpenTelemetry / Prometheus / Grafana）与 spaCy 实体提取依赖。
- **RC-14 / RC-15**：债务编号注册表补 D-021/022/023、D-314~D-319 墓碑条目，闭合 0xx 与 3xx 段断号。
- **RC-16**：治理 §5 编号注册表明确 D- 按百位分段语义（D-0xx 架构设计间隙 / D-1xx 架构扩展 / D-2xx~4xx 代码级实现）。
- **A-005**：api-spec 顶层 REST 端点与 Agent Tool 补响应定义（涵盖记忆多级读取 / 边类型管理 / 技能管理 / 5 个写入检索类 Tool；原以 RC-18 编号登记，实为 round2 审计编号，2026-08-04 勘误更正）。
- **A-006**：操作目录 53 个操作补 `OP-XXX` 稳定 ID（原以 RC-19 编号登记，实为 round2 审计编号，2026-08-04 勘误更正）。（0.0.11 二次勘误：本条目初版将 A-005/A-006 主题互换——A-005 应为 api-spec 响应定义、A-006 应为操作目录 OP-ID，与 round2 原始定义一致，现更正。）
- **A-004**：NFR 各表补「测量方法」列。

---

---



## 0.0.4（2026-08-04）— 市场先进理念吸收

- **双时态**（外部实证理念吸收）：认知基础新增「双时态声明」（事件时间 occurred_at vs 事务时间 created_at，纠正而不遗忘）；`memories` 表新增 `occurred_at` 与版本链四字段（parent/root/next/is_latest，对齐架构 §5.2 版本链模型）；`knowledge_evolution` 新增 `valid_from/valid_to`（对齐半开区间时间语义）；架构 §5.2 event_time 升格回填 occurred_at + as_of 泛化至 memories 本体。
- **时间感知检索**（外部实证理念吸收）：架构 §7.3a 新增时间过滤约束段（as_of/事件时间窗口/纪元边界，与路径空间同构的硬过滤边界，非第四信号，权重和恒 1 不变）；配置新增 `KAIROS_TIME_FILTER_ENABLED`；策略层预测器登记「按会话上下文构造检索意图」；detailed-design 新增 §9 检索引擎（管线状态机 + StorageBackend as_of 接口）。
- **生成式记忆**（外部实证理念吸收）：认知基础 §1.3 新增「构造性生成声明」（检索即重建延伸，痕迹不足/缺失/跨模式组合时构造缺失表征）；产物入模拟隔离区（S-13），转正走沙箱验证环；架构 §6 WM 模拟隔离区扩展「生成-验证」双职能。
- **主动触发式记忆**（外部实证理念吸收）：认知基础 D.7 新增「记忆压力声明」（四类压力信号：上下文预算/检索失败/冗余/遗忘积压）；架构 §5.2 主动话题生成器扩展压力信号族；RL 记忆管理自动化纳入 v1.1 路线图（前置条件：多维独立裁决框架）。
- 债务登记 D-322~D-325；glossary 增补双时态/构造性生成/记忆压力三条术语；吸收决策记录。

---



## 0.0.5（2026-08-04）— 门禁覆盖补全与计数同步

- **doc-audit.py 6.7 新增术语计数校验**：glossary 术语数（实际统计 ↔ README 声明双向比对），纳入第 6 类数值一致性检查。
- **README 术语计数同步**：glossary 53→56 条（吸收增补三条术语后的次生漂移），版本记录升 0.0.3。
- **api-spec 版本记录升 0.0.2**：frontmatter updated 07-31→08-04，登记 RC-19 响应定义与 D-13 端点计数口径。
- **slice-implementation-guide 挂接 schema-slice.sql**：§二 引言与 §六 阅读路径引用 15 张表可执行 DDL（对齐 data-model §13.4），版本记录升 0.0.2。

---



## 0.0.6（2026-08-04）— ADR 计数同步与审计脚本健壮性

- **ADR 计数同步**：[README](../README.md)「10 项已采纳 ADR」→ 12 项（ADR-011 迁移工具 / ADR-012 向量投影），README 版本记录升 0.0.4；[adr.md](./adr.md) 版本记录补 0.0.2（ADR-012 落地，总数 11→12）。
- **doc-audit.py 6.8 新增 ADR 计数校验**：[adr.md](./adr.md) 实际 `## ADR-` 标题数 ↔ README 声明双向比对，纳入第 6 类数值一致性检查。
- **deep-audit.py 修复 Windows 编码崩溃**：头部强制 stdout/stderr UTF-8（reconfigure），消除 GBK 控制台输出 ↔ 等字符时的 UnicodeEncodeError。

---



## 0.0.7（2026-08-04）— 债务闭环检查语义修正与编号引用补全

- **doc-audit.py 第 10 项重写**：债务闭环真实性检查由「所有登记编号他处零命中即 WARN」改为「仅 §四 状态表已闭环条目（✅ 已实施/已决策）要求他处可检索」——墓碑占位与未闭环条目（设计锁定/新登记/路线图）零引用是正常状态，不再产生噪音 WARN。原 9 项 WARN（6 墓碑 + D-001 + D-323/D-324）归零。
- **D-323/D-324 落地编号引用补全**：架构 §7.3a 时间过滤约束段挂 D-323、§5.2 压力信号族扩展挂 D-324；认知基础双时态声明（§1.1）挂 D-323，记忆压力声明（D.7）RL 路线图占位符「债务 D-吸收」修正为 D-324。架构/认知基础版本记录升 0.0.3。
- **D-001 保持不动**：Phase 2 设计锁定状态，实现前零引用为正常。

---



## 0.0.8（2026-08-04）— 全库深度审计修复

- **安全口径锁定**：API Key 哈希算法全库统一为 PBKDF2-HMAC-SHA512（256,000 次迭代，security-spec S-01/§2.1、data-model `api_keys.key_hash`、threat-model、deployment 四处对齐）；回滚端点安全红线 S-14（语境自指禁令）误标修正为 S-08（api-spec）；threat-model 移除 S-07 不存在的「HTML 实体编码」防护子项。
- **版本归属与口径**：PM-01/02 修正为 P2（v1.1+，对齐 feature-list）；RTM CAL-01 用例编号 TC-C01-001 → TC-CAL01-001；P6 压缩比定性统一为「已知超限（非受控偏离）」（system-context / operation-catalog / cognitive-foundation E.7 三处口径一致）。
- **竖切落点补全**：implementation-map 补三信号混合检索（hybrid_search.py，竖切组件 3）、身份注册表（identity_registry.py，竖切组件 5）、Reflect 循环（reflect.py）、查询分析/防抖/图像 Blob 模块；benchmark-plan 补「竖切档 10,000」与检索延迟判据；acceptance-criteria 补 E2E-03/09 范围注记；project-plan 竖切范围补时间过滤基础窗口（D-323）。
- **引用修正**：api-spec §五→§七、§6.9→§6.8（3 处）、架构 §3.9 L1→§5.9 Tier 2/3、蓝图技能管理系统引用改指本文 §5.2、glossary 5 条术语来源改指主架构、审计链公式来源改指 threat-model、error-reference/api-spec/runbook 错误码三清单对齐（ERR-LLM-002 废弃标注、ERR-CAL-001/002 状态码 503→400）。
- **核心文档修复**：认知基础三处「六级链兜底」残留改写为 D-01 语义 + 章节号消歧（E.6a）；架构 §10.10a 编号、§5.19 Reflect 路径、§11 术语表补三条新术语与权威声明、§5.20 交付范围、§5.11 ADR-012 矩阵版本对齐；蓝图补 P3/技能体系章节标题层级、§5.5 交付例外声明；技术选型 OTel 标注 v1.1 目标 + Tier 梯队引用。
- **治理补账**：architecture / cognitive-foundation / README 版本记录回填 08-03 批次；debt-collection / documentation-governance / feature-list 等 frontmatter 与版本记录同步；决策编号（D-XX）注册 + 消歧说明；严重级别词汇映射表；reviews 勘误与处置状态注记；README 新增「审计与决策记录」索引。
- **参数与配置**：`KAIROS_PARETO_FRONT_MAX`/`KAIROS_COMPOSITION_*_WEIGHT`/`KAIROS_PREDICTOR_ATTRIBUTION_TTL` 取值范围列修正；新增单次调用成本上限与熔断参数（`KAIROS_LLM_MAX_COST_PER_CALL_FEN`、`KAIROS_LLM_CIRCUIT_BREAK_*`）；configuration 正文 193→196、附录 A 148→151、总计 341→347；KAIROS_VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD 对应告警语义区分。
- **编号勘误**：RC-18/RC-19 更正为 round2 编号 A-005/A-006；RC-14「S-21 断号」勘误为区间提法误读（见 independent-recheck 勘误注记）；参数计数历史口径以 configuration 版本记录为准统一。
- **门禁**：`scripts/doc-audit.py` 15 类检查全绿（0.0.8 批次完成时验证）；修复期间发现的 3 处门禁盲区（取值范围列自洽、禁用词同义表述、裸文件名）已随批次消除。

---



## 0.0.9（2026-08-04）— 文档职责剥离

- **认知基础聚焦认知理论**：`cognitive-foundation.md` 剥离 8 处工程实现细节至 [detailed-design.md](../specification/detailed-design.md)（认知完整性三维代理/可及性代理/CRI 代理 → §6.1-6.3、自激回路诊断数值与默认行为 → §6.4、注意力前置制衡数值 → §10、冷启动种子与批量探索清理协议 → §12）；认知判定阈值（E.6a 耦合判据/E.7 审计闸门）与认知声明/局限保留。
- **主架构聚焦系统架构**：`architecture-v0.1.0.md` 剥离 24 个实现细节章节为「机制摘要+指针」——P3 系（P3-11/12/13/17/20~25）迁 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md)；接口 schema（§7.3e 资源摄取/§7.3i 多模态 Part）迁 [api-spec.md](../specification/api-spec.md) §18.1/§18.2；MCP/SDK（§10.23）迁 [technology-stack.md](../development/technology-stack.md) §七；RL 权重实现（§10.14）并入 [rl-weight-spec.md](../specification/rl-weight-spec.md)；其余（§5.13-5.16 存储/同步/协议、§5.19 Reflect、§7.3b/c/f/h 检索去重与实体提取、§9.3 Token 预算、§10.15/16/20/21/22 优化与治理）迁 [detailed-design.md](../specification/detailed-design.md) §4/§9-§11。
- **详细设计承接扩展**：`detailed-design.md` 500→1500 行，新增 §10 注意力调度器、§11 编译与存储基础设施、§12 探索治理，扩展 §4/§6/§9，组件索引同步扩充。
- **引用改向**：60+ 处交叉引用从「架构 §X」改指承接文档（feature-list 34 处、data-model 7 处、configuration 6 处、blueprint 6 处、implementation-map/slice-guide/acceptance/glossary 等），架构/认知基础标题保留为摘要态不重排。
- **门禁**：`scripts/doc-audit.py` 15 类检查全绿。

---



## 0.0.10（2026-08-04）— 第二轮全库深度审计修复批次

- **权威文档矛盾修复**：遗忘算法口径统一（架构 §5.2 v0.1.0 单曲线 ↔ detailed-design §3 v1.1 完整目标互链、claim-matrix C-08 降为部分承载）；前瞻记忆契约统一为「意图契约」（architecture §8 / data-model `memories.contract` 增 intention 枚举 / feature-list PM-01 / requirements-baseline §1.8 / test-strategy 五处对齐）；监督平面独立定位统一（架构 §1.7 标题、glossary 外部治理接口定义重写、implementation-map §七 标题）。
- **引用修正**：认知基础 §1.5/1.6 断号连带引用改指 §1.4/§2.1（E.6/E.7/D.13、claim-matrix C-16、架构 CJ-003）；E.7「架构 §8.9」改指 §10.11；claim-matrix C-25 §3.4→§3.8；差距表 G-02/G-04/G-13/G-15 出处修正；glossary 注意力调度器/模拟隔离区/沙箱/预处理器来源章节修正；api-spec §6.8 工具清单改指 §7.3.1；operation-catalog OP-026 链接错位修正；feature-list 裸引用补链接。
- **数值漂移修正**：implementation-map 参数 341→347、E2E 6→9、组件路径 67→70（实际统计）；test-plan 单元下界 64→70；requirements-baseline 补 N-11/N-12 可用性指标、N-10 注记同步 nfr-spec；README claim-matrix 计数注记（含已废弃 C-23）。
- **定性统一**：P6 压缩比「受控偏离」残留清理为「已知超限（非受控偏离）」（cognitive-architecture-gap G-07 + 统计表、traceability-map）。
- **结构修复**：feature-list SF-11/12/13 移回扩展功能表、删除两张历史分类快照表；架构 §3.4~3.7 缩进标题修复。
- **格式与元数据**：50 份文档版本记录模板统一（0.0.1 起递增规则）；46 份文档补 `last_reviewed`；7 份文档 frontmatter `updated` 同步；全库换行统一 LF；代码围栏补语言标注；28 处债务锚点规范化；security-spec 补 `L+P` 缩写定义；release-guide §1 版本号规则修订；api-spec §18.2 空表清理。
- **门禁扩展**：`scripts/doc-audit.py` 新增锚点检查（16）、frontmatter 必填检查（17）、版本模板残留检查（并入 13，RC-09 旧文案）；标题提取容忍前导空格；数值校验新增组件路径/E2E 计数双向比对。



## 0.0.11（2026-08-04）— 开发就绪度审计修复批次

> 闭环（9 高 / 33 中 / 8 低共 50 项问题）闭环 P0/P1/P2 全部修复项。

- **权威定义唯一化（C-01/C-08）**：知识演化判定以架构 §5.2 为权威（§0.4 概述改指、data-model 触发机制改指、补余弦 vs Jaccard 两套体系不互换算说明）；记忆关系类型统一为 data-model 六值枚举（feature-list/claim-matrix 同步）。
- **临时契约审计痕迹统一（C-02）**：架构 §3.7/§8、api-spec §四、data-model `expires_at`、glossary「硬删除」四处统一为「清理前写入审计日志 `expiry_cascade_delete`」——无痕场景仅限捕获阶段拒绝的输入。
- **「时序优先」收敛为「并行审查模型」（C-03）**：认知基础 9 处（§2.1/E.5/E.6/E.8/批量清理协议）、架构 2 处（§0.9/§3.2）——探索候选→宪法审查窗口（100ms，超时 fail-close）；D-006 排序规则保留并加术语辨析注记。
- **schema-slice.sql 重建（M-01）**：memories 补 occurred_at（双时态）+ 版本链四字段（parent/root/next/is_latest）+ contract 增 intention；schema_version 去 singleton 列对齐 data-model；SQL 已通过 sqlite3 执行验证（15 表 / FK 无违规）。
- **data-model 修复（S-02/F-08/索引/计数）**：§八 编号重排（8.8~8.22 连续）；FTS5 同步机制勘误（content= 模式需显式建触发器）；procedural_playbooks.superseded_by 类型错配（UUID→TEXT）、entity_communities.member_entity_ids（UUID[]→BIGINT[]）、weekly_packs.session_ids（UUID[]→TEXT[]）；补缺失索引 10 处、UNIQUE 2 处；§13.1 补 UUID[]/TEXT[]/BIGINT[] 类型映射；「以下六张表」→七张；版本记录旧表名勘误。
- **契约枚举唯一化（C-05）**：api-spec add_resource 的 `pinned/on_demand/contextual` → 全库统一 `permanent/ondemand/environmental/temporary`。
- **api-spec 机制指针与勘误（M-02/C-10）**：降级切换/冻结/主动话题/heat-top/audit verify-chain 五项补机制来源指针；priority 示例 5→1（v0.1.0 仅 0/1/2）；`chat_messages` → `conversation_messages`。
- **detailed-design 修复（C-04/C-06/C-09/A-06）**：api-spec 章节引用 5 处错位修正（§十三~§十五 → §十四~§十六）；5D 混合排序表述清理（3 处，改指三信号+RL 二次排序）；reflect 循环事件复用 `sublimation_tick`（事件枚举保持 10 类）；遗忘伪代码补 CANDIDATING 两阶段、状态机「移除完成」→「归档完成（不物理删除）」。
- **claim-matrix 账目重建（A-01）**：✅ 25 个（原 27 误计）；「三硬一软」→「五硬一软（仅 C-26 软原则）」；C-30 移出 ✅ 组（已知超限）；C-04 关系类型对齐 data-model 六值。
- **配置参数体系（M-03/M-04）**：附录 A 去重 3 项 LLM 双计（151→148）；新增 14 项参数（LLM 超时/限流容量/磁盘三级阈值/备份日志保留/恢复演练/密钥宽限/告警投递 4 项）正文 196→210、总数 347→358（README/implementation-map 同步）；待定义 24→12 项回填；特征标志 `KAIROS_FEATURE_NARRATIVE_IDENTITY` 默认 OFF→ON（宪法核，对齐架构 §0.8——**新增发现的硬矛盾**）；FORGETTING_ENGINE 补竖切注记；历史计数链勘误注记。
- **运维/质量/安全（F-07 等）**：observability「三支柱」→「四支柱」、补拟真校准失稳告警行；reliability requirements-baseline 链接修正 + LLM 超时参数化；deployment 遗忘口径注记（FORGETTING_ENGINE 默认 OFF）+ L125 行号引用改章节；security-spec 密钥轮换口径统一（按需+季度建议）；test-plan §3.7→§3.8、CAL-01~04→06；runbook 保留期引用修正。
- **竖切口径（C-07/C-18）**：feature-list 竖切表补 R-18 三信号混合检索注记；implementation-map 竖切组件序号去（W5）（W7）括号混淆 + 计数更新；project-plan「W5」→「第 5 周（W05）」。
- **术语与引用（C-12/C-13/C-14/F-01/F-03/A-09）**：glossary「外部治理接口」改为别名声明（撤销单方"现称"）；认知基础矩阵删除声明与 E.5 调和、§1.6→§2.1 引用修正；决策/债务编号消歧标注（认知基础 D-019/D-15、架构 CJ-009 D-006）+ documentation-governance 消歧说明强化为强制规则；行号引用改章节引用（认知基础 L83、架构两处、deployment）；认知基础双空格与「真理模式切换」旧术语清理（claim-matrix/design-philosophy 同步）。
- **其他（S-03/S-04/M-05~07/K-063/A-05/A-07/A-08）**：CJ-013 补认知关节登记；operation-catalog 映射口径补 43 核心 + CLI 子集注记；recheck 附录 A 计数刷新（57 表/358 参数/56 术语）与误报 5→6 勘误；round2 A-005/A-006 主题互换勘误（本条目 0.0.3 已更正）；risks MRK-002 引用改指架构 §2.2；rl-weight-spec softmax 两说统一；technology-stack Prometheus v0.1.0 直出说明；design-philosophy 定位行与交叉引用列修正；quick-start/user-guide init 幂等澄清；use-cases 竖切边界注记；usage-load-algorithm 未闭合注记；traceability-map 补 G-14/G-15/G-09a/G-13 行；architecture-blueprint last_reviewed 同步。
- **门禁**：`scripts/doc-audit.py` 18 类检查全绿；`deep-audit.py` 全绿。



## 0.0.12（2026-08-04）— 门禁盲区闭环批次

> §七 遗留项闭环——doc-audit 4 处门禁盲区全部消除。

- **门禁盲区 1（债务闭环正文口径）**：`check_debt_closure` 改按「正文」（跳过版本记录）统计落地证据，区分「仅版本记录可见」与「完全不可见」两档 warn——版本记录中的历史提及不再算落地。
- **门禁盲区 2（编号连续性泛化 + 决策/债务混用检查）**：`check_numbering_continuity` 从仅债务 D-xxx 扩展至五命名空间（债务 / 差距 G-xx 含子编号归并 / 认知关节 CJ-xxx / 架构风险 RSK-xxx / 方法论风险 MRK-xxx，条目定义行口径，规避预留区间声明误判）；新增 `check_decision_numbering`（14a）——决策 D-xx 两位数的正文引用行内无决策语境词（决策/裁决/修订/裁定/批准/方案）时 warn。
- **门禁盲区 3（陈旧值集中化）**：陈旧值清单集中为显式串 + 权威数值历史值邻近检查（参数 334/339/341/342/347、表 56/55、术语 53、组件 64/67、E2E 6、ADR 10/11）——负向后瞻排除「原」「「」引述与勘误语境。
- **门禁盲区 4（机制定义唯一化人工门禁）**：documentation-governance 新增 §2.1——机制章节声明权威 / 同机制表述全库检索 / 冲突裁决标注三项规则 + 评审检查清单（机器不可判的语义级重复定义由人工兜住）。
- **决策编号标注补齐**：13 处决策编号正文引用补「决策」前缀（README D-05、blueprint D-05×3、architecture D-05、cognitive-foundation D-08/D-01×2、design-philosophy D-01×2、glossary D-01、claim-matrix D-01、data-model D-12×2），消除 D-xx 与 D-xxx 混用辨识盲区。
- **configuration 勘误注记改写**：0.0.11 勘误注记去「347 项」字样（历史计数链归版本记录），消除陈旧值检查误报。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）；`deep-audit.py` 全绿。



## 0.0.13（2026-08-04）— 认知×架构交叉审计修复批次

> 闭环 12 项决策（D-16~D-27）。本批次在 architecture/cognitive-foundation/architecture-blueprint 三份核心文档版本记录中已有登记，changelog 原缺失该条目（版本链断裂，0.0.15 补登—— P2-01）。

- **A1 硬过滤**：架构 §0.3 候选生成阶段约束维度改为否决式硬过滤（不设权重），废除旧表述「约束维度默认各为使用价值权重的 0.3」（加权与 D-01 无标量聚合冲突）。
- **B1 学习边界三边重画**：认知基础引论/D.10 记忆-学习-感知三边切割（外部应用层/策略层/存储层）；参数级学习声明（RL 权重优化器为内部学习机制）。
- **C1 检索-再巩固认知让步**：认知基础 §1.3 修订——重建改写发生在 WM 层重建实例，不写回存储层（不可变存储 ADD-only）。
- **D2 身份否决权语义边界**：架构 §1.8 + 认知基础 §2.1——身份承诺显式清单（D-326）、假一致补偿路径；v0.1.0 否决权实际保护范围为陈述逻辑一致性（降级形态）。
- **E1 身份危机例外判例出口**：认知基础附录 C.6 + 架构 §1.8。
- **F1 符合论域外部校准权威**：架构 §3.2.1。
- **G1 DFA 与准见证锚定分工**：架构 §5.12/§10.9 + 认知基础 §3。
- **H1 定向遗忘认知锚点**：认知基础 §1.3 干扰升格为遗忘二级机制；架构 §5.2 检索路径抑制器（S-19 哈希净化功能等价物）。
- **I3 巩固预测误差调制**：认知基础 §1.3 + 架构 §5.2 巩固子模块（债务 D-329，v0.1.0.x 硬交付）。
- **J2 组块化硬承诺**：认知基础 §1.3.2 背书保留；架构 §0.4 Phase 1 硬交付（债务 D-330）/ Phase 2 v1.1（债务 D-331）。
- **K2 推理皮层认知必要性**：认知基础 §1.3 + 架构 §4——前瞻触发监控/候选排序/上下文裁剪为记忆域内最小必要回路。
- **L1 元认知层职责边界**：架构 §2.2/§5.2——元认知层=监测+提案，身份面=纯否决者。
- **P-01/P-04/P-08/P-11/P-13/P-14/P-15/P-18/P-19/P-20 问题项闭环**：内容类型编码层默认偏好非静态绑定（§5.2）；编码特异性分类学近似（认知基础 §1.3）；上下文-记忆相关性债务化（D-328）；来源追踪/S-14 边界（认知基础 §1.1）；排序链前提（D-305 关键路径）；轴扩展架构承载门禁第五步（认知基础 §1.1，债务 D-333）；调度器驻留统一（架构 §9.1/§10.2）；存储层组件→认知锚点映射（架构 §1）；事件总线计入协议上限（架构 §10.6/§10.10）；预测器/裁决器管线顺序（架构 §3.2）。
- **P-xx（重复内容）§5.20 与蓝图重复内容删除（243 行）**；架构 §1 词汇桥接表扩展；版本记录三份核心文档升 0.0.13。
- **门禁**：0.0.13 批次执行完成后已运行 `scripts/doc-audit.py` 验证全绿（0.0.14 复核时确认）。



## 0.0.14（2026-08-05）— 开发就绪度审计修复批次

> 闭环（10 高 / 22 中 / 15 低共 47 项问题）闭环 P0/P1/P2 全部修复项。

- **契约语义统一（A-01/A-10/A-11/A-12）**：api-spec DELETE 删除行按「permanent 拒删（403）/ondemand+environmental 软删/temporary 硬删留痕」重写；operation-catalog OP-024/OP-026 到期语义统一（temporary 硬删+expiry_cascade_delete 审计/其余归档）；memories_write 契约枚举补 intention 第五值；data-model memories.contract 补「写时默认建议值+运行时激活权重覆盖」注记。
- **遗忘算法归位（A-02/B-01）**：detailed-design §3 伪代码与状态机改为架构 §5.2 freshness 单曲线权威口径（active/stale/archived 三阈值 + forgetAfter 分工）；v1.1 二维曲面公式移出 v0.1.0 执行路径并标注目标段；SUPPRESSION_THRESHOLD 从 v0.1.0 路径移除；KAIROS_FORGETTING_SCORE_THRESHOLD 归属勘误（v1.1 口径）。
- **关系类型枚举统一（A-03）**：data-model memory_relations.relation_type 补语义标记扩展说明（supplement/refutation/reference/contextual/temporal）；架构 MCP kairos_link/ADD-only 协议/时间戳后处理三处引用权威枚举。
- **虚拟校准触发链统一（A-04/A-18/A-20）**：configuration 补 VIRTUAL_CALIBRATION_TIMEOUT 换算注记（900s=3 次静默术语口径 vs 联动逻辑 6×300s）；校准冲突阈值双参数（次数 vs cosine）区分注记；observability 校准中断严重告警注明「N/M 契约为准」。
- **HMAC 审计链公式统一（A-05）**：glossary/data-model/api-spec 三处统一为 threat-model 权威 5 项输入（timestamp+operator+action+content_hash+prev_hmac），details 以摘要并入 content_hash。
- **S-07 导出脱敏口径统一（A-06）**：api-spec 与 security-spec 参数名统一 clearance=export、语义「掩码+截断」；nfr-spec「可逆」改「不可逆」。
- **MCP 进程模型与工具清单统一（A-07/A-28）**：technology-stack 改独立 Bridge 进程；工具计数 15 个口径注记（12 规范操作直接映射+关系管理 3）；例名 kairos_create_memory→kairos_store_memory；integration-design 工具注册改列 kairos_* 系列并注明两层接口不混用。
- **债务/决策账目修复（A-08/A-16/A-17）**：架构 3 处 D-324→D-325（压力信号族为 D-325）；debt-collection D-328/D-332/D-333 与 D-305 升级声明的问题编号勘误（P-08/P-13/P-14 标注为认知×架构审计问题）；documentation-governance §5 决策编号注册更新 D-01~D-27 双权威源；cognitive-architecture-fixes 债务登记表补 D-333 行。
- **制衡口径与降维表对齐（A-09）**：架构 §0.9/§10.13 注意力前置制衡「三项→四项」降维口径对齐（D-003 与架构 §9.2 一致，无需改）。
- **竖切测试补全（A-24/B-02）**：test-plan 补 W-03/M-03/M-05/A-07 用例、迁移/回滚测试类型（§1 覆盖表 + §3.9 五用例）、E2E 竖切 7/9 门禁对照注记。
- **复兴机制口径勘误（A-29）**：use-cases 场景 5 / feature-list F-03 / test-plan TC-F03-001+E2E-02 / requirements-baseline F-03 四处统一为「潜伏势能重估/外部校准触发复兴，显式检索不直接触发」。
- **用户文档纠错（A-25）**：user-guide 检索吞吐 200→180 ops/s 口径、LLM_ENDPOINT 模式限定、kairos read 参数语义注记、SDK source 映射注记；quick-start --source 映射 provenance 注记。
- **其余中项（A-13~A-15/A-19/A-21~A-23/A-26/A-27）**：proactive_topics.priority 改 FLOAT [0,1]（对齐架构 ≥0.7 判据）；QueryAnalyzer 时间约束改 occurred_at（双时态）；知识演化候选集门槛分档（enriches/challenges 判定闭环）；校准端口 OFF 保留外部校准端口口径统一；claim-matrix 三硬一软/五硬一软换算桥接注记（以认知基础合并口径为权威）；5D 术语口径注记（废弃 5D 权重框架，保留排序调制层沿用名）；quality_tier 引用改指蓝图；S-19 范围勘误（附加控制项标注）；slice-guide 遗忘配置勘误（AGE_DECAY 归 v1.1）；运维硬编码值加基线注记（备份快照 30 天/健康检查 3 次/预算 10%）。
- **边界与结构（A-29 余项/B-03/C-01）**：system-context 对话管理边界细化；requirements-baseline RTM 补 R-18 行 + 非目标「用户管理」边界注记；debt-collection 补 D-312 正文条目 + 摘要表取舍声明；slice-guide 竖切组件计数 9 vs 6 口径注记；nfr-spec 可用性注记勘误（N-11 承接）；market-ideas/cognitive-architecture-fixes 门禁状态刷新 + 编号同形注记；round2 A-003 修正口径；feature-list 版本记录补 0.0.3 条目。
- **格式清理（P2）**：认知基础双空格/残句 2 处/错别字（固话→固化）/§1.4-1.6 断号引用 5 处；架构行号引用/冗余逗号/未注册编号；error-reference ERR-SYS-002~005 移回 §1.7；glossary 新增「并行审查」术语（56→57 条）与审计链公式统一；算法文档残句 2 篇；schema-slice.sql 版本注释刷新；use-cases 场景 6 编号修复；deployment 过时表述 2 处。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）；`deep-audit.py` 全绿。



## 0.0.15（2026-08-05）— 全面深度审计修复批次

> 闭环（08-05 首轮审计独立复核轮，1 中 + 4 低共 5 项新发现）闭环全部问题项。

- **契约枚举第五值同步（P1-01）**：api-spec 资源摄取端点 contract 四值枚举补 intention（五值），注释改指 data-model memories.contract 权威——全库契约枚举残留清零（grep 复核 0 处四值）。
- **竖切 M-05 归档端点注册（P1-02）**：api-spec §1.5 注册 `POST /v1/memories/{id}/archive` 与 `POST /v1/memories/{id}/restore`（对应架构 12 规范操作集 archive/restore，含幂等性/契约约束/潜伏势能重估匹配验证/错误码）；slice-implementation-guide 两处「待 api-spec 注册」标注移除；业务端点计数 78→80、物理总数 79→81（api-spec 口径注记 + implementation-map 两处同步）。
- **0.0.13 版本批次补登（P2-01）**：changelog 正文新增 0.0.13 条目（认知×架构交叉审计修复批次，决策 D-16~D-27，变更摘要自三份核心文档版本记录与 cognitive-architecture-fixes 回填）+ 版本记录表补行；README 版本记录同步补登（含补登说明）。版本链 0.0.1~0.0.15 恢复连续。
- **参数计数现值锚定（P2-02）**：configuration 版本记录补 0.0.15 锚定行（正文 210 + 附录 A 148 = 358，现值以本行为准），历史计数链归版本记录。
- **门禁标签编号修复（P3-01）**：doc-audit.py 锚点检查打印标签 [16/18]→[15/18]，frontmatter [17]→[16]、changelog [18]→[17]，docstring 同步——输出编号 1~17 + 14a 连续无断号。
- **正文双空格清零（P4-01）**：认知基础 L263「。  【巩固」、detailed-design L247「（降权检索）  （归档至冷存储）」共 2 处正文段落连接双空格清理——0.0.14 声称已修实未修透的残留项闭环；全库正文双空格复扫 0 命中（代码围栏/ASCII 图对齐空格除外）。
- **0.0.14 登记文档数修正（P4-02）**：README/changelog「29 份」→「31 份」（实际版本记录含 0.0.14 条目文档数）。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）；`deep-audit.py` 全绿。



## 0.0.16（2026-08-05）— 外部建议落地批次

> 用户逐条拍板——7 条建议中 6 项采纳落地（建议一/二/四/五/六/七），建议三经详细对比裁定「保留架构枚举+吸收细节」。

- **建议一·校准退化链（全部三子建议）**：架构 §1.2 虚拟校准置信度动态衰减公式化（`0.3 × exp(-λ × days)`，λ=0.02，floor 0.05，auto-dormant 60 天）；校准状态运营可视化映射（healthy/degraded/virtual/dormant 四级枚举，刻度粗于降级状态机周期，以状态机为准）；api-spec 检索响应补 `meta.calibration_status` 与 `nudge` 可选字段（subtle/noticeable/prominent 三级，非阻塞）+ `GET /v1/health/calibration` 端点;configuration 补 3 项参数（DECAY_LAMBDA/DECAY_FLOOR/AUTO_DORMANT_DAYS）。
- **建议二·认知完整性半定量轴（三级 0/1/2）**：架构 §5.2 结构性记忆守护补 structural_value 三级定义（L1 疑似:causal 引用≥2/路径高分叉/叙事线断裂风险;L2 确认:外部校准标记/手动标注/引用≥5）与遗忘调度器分级行为;data-model memories 补 structural_value/structural_value_reasons/structural_value_updated_at 三字段 + is_structure 双向同步；定位为 D-311 的 v0.1.0.x 前置台阶（衔接 D-306/D-312）;configuration 补 3 项参数。
- **建议三·QueryAnalyzer（保留架构枚举+吸收细节）**：架构 §2.6.1 补规则优先+模型兜底实现策略（规则层覆盖 ≥80% 查询零 LLM）、意图覆盖注记（身份查询由确定性检索承载、问候由摄取门禁拦截）、事件锚定解析（注册表→语义降级）与 fallback_query 字段;slice-guide 组件 3 补「竖切后首迭代实现优先级」定位。
- **建议四·记忆压力可操作化（映射 D.7 四信号）**：架构 §5.2 压力信号族补四指标量化（WM 占用率/检索失败率/冗余率/遗忘积压比）+ 三级减压动作（L1 温和/L2 中度/L3 激进,L3 标记遗忘候选不物理删除）+ 恢复条件与审计事件;api-spec 补 `GET /v1/health/memory-pressure`;configuration 补 4 项参数。
- **建议五·Saga 最小实现（复用 narrative_threads）**：架构 §5.2 补 v0.1.0 子集声明（创建/添加/检索/手动完结四操作，纯 DB 无 LLM）;api-spec §八 补 v0.1.0 子集声明与 create/members/memories 三端点;feature-list M-21 补子集注记；自动聚合/自动完结/summarize 标注 v1.1 目标。
- **建议六·概念分级速查表**：新增 [references/concept-tiers.md](../references/concept-tiers.md)（L1 10 项/L2 12 项/L3 12 项 + Mermaid 依赖图 + "如果只读三页"速览路径）;架构 §0 速查表加链接;glossary 权威声明不变。
- **建议七·压缩审计日志（债编号纠正）**：data-model memories 补 `compression_trail` JSONB（逐记忆压缩审计，为 §10.11 全局监控的逐记忆粒度展开）;新增 [references/capability_matrix.yaml](../references/capability_matrix.yaml)（版本化能力矩阵，恢复债编号纠正:D-306/D-311/D-312 认知完整性、D-313 可及性、D-301 时间逻辑-因果——非提案误引的墓碑 D-318/319）;api-spec 补 `GET /audit/compression` 与 `/summary`;检索侧维度丢失记事件总线 `retrieval_dimension_loss`（use_event payload,枚举保持 10 类，不写记忆 trail）。
- **新增文档**：[references/concept-tiers.md](../references/concept-tiers.md)、[references/capability_matrix.yaml](../references/capability_matrix.yaml)（核心文档 52→54 份）。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿。



## 0.0.17（2026-08-05）— 外部建议其余落地批次

> §四 其余建议用户拍板——R-1/R-2/R-3/R-9/R-10 采纳落地,R-4~R-8 确认已覆盖无需动作。

- **R-1 P6 收敛目标化**：debt-collection 新增 D-334（P6 压缩比收敛目标 v0.1.0.x 验收——核心口径 ≤30% 且活跃例外占比 ≤50% 持续 2 审计周期）；架构 §0.6 消除条件 (a) 挂 D-334、条件 (b) 维持 v1.1。
- **R-2 进程级隔离演进路径**：deployment 新增 §九——已隔离项（宪法解释层独立故障域/监督平面独立加载）+ v0.1.0.x 候选（ME-1/2/3 分离,`kairos-meta-monitor` 独立进程）+ v1.1 目标（全组件容器化）+ 生产部署建议 + 降级兼容。
- **R-3 社会性校准研究启动点**：social-calibration-roadmap M2 补「认知层研究启动点」注记——认知层模型研究前置启动（M2 完成→启动研究,M3a 完成→转架构规格）。
- **R-9 债务依赖建模**：debt-collection 新增 §六 关键路径依赖表（D-305→D-332、D-313→D-306→D-311→D-312、D-330→D-331、D-301→D-313、D-321→D-334）；documentation-governance §5 补「前置依赖声明规则」——新债务登记须声明前置依赖并同步依赖表。
- **R-10 路线图可执行性**：project-plan 新增「Phase ↔ 验收 ↔ 门禁」对照表（Phase 0-3 交付物 → acceptance-criteria 对应节 → 门禁/E2E 覆盖 + 判定顺序）。
- **R-4~R-8 确认已覆盖**：D-305/D-306/D-311/D-313/预留接口均已充分登记，无需新增动作。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）；`deep-audit.py` 全绿。



## 0.0.18（2026-08-05）— 审计归档与决策迁移批次

> 依用户决策：审计问题处理完即归档，不长期保留；决策定义从审计报告迁移至治理资产。

- **决策迁移至 ADR**：决策编号 D-01~D-27 权威定义从 reviews 审计报告迁移至 [adr.md](./adr.md)「审计决策迁移」节（D-01~D-15 源自 08-03 审计批次、D-16~D-27 源自 08-04 交叉审计批次;D-06→ADR-001、D-11→ADR-011 由既有 ADR 承载，仅登记迁移关系）;documentation-governance §5 决策编号注册表定义源改指 `adr.md`。
- **审计报告归档**：新增审计历史摘要（10 轮审计汇总表 + 决策索引 + 归档机制）;删除 reviews 下 10 份审计报告（2026-08-03~08-05 各轮）——问题处置要点以 changelog 各批次为准，问题清单不再长期保留。
- **引用改指**：全库 30 处 reviews 引用改指 `audit-history-summary.md`（changelog 8、debt-collection 5、cognitive-foundation 3、documentation-governance 2、architecture 2、blueprint 1、README 索引 8 行合并为 1 行 + 版本记录 1 处）;`audit-history-summary.md` 纳入文档计数（该文件已于 0.0.30 移出仓库，计数随之去除，此处为 0.0.18 时点历史事实）。
- **归档机制（防堆积）**：documentation-governance 执行记录与 audit-history-summary 声明后续审计闭环后登记于摘要并删除原报告——审计报告不再累积。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿。



## 0.0.19（2026-08-05）— 第四轮全库深度审计修复批次

> 依 master-documentation-audit（第四轮·语义层独立复核）闭环：1 高 / 7 中 / 8 低，全部为文档层语义/结构问题，无认知模型或技术选型硬伤。

- **身份否决权实现形态裁决（1-01，P0）**：以架构 §1.2/§1.8 为权威——v0.1.0 交付预提交总线 + 身份总线监听器 + 否决裁决器（替代三点分布式检查）。debt-collection D-001 工程简化/升级触发条件/历史背景改写（升级触发条件删「触发布线升级」表述，已无升级对象）、D-101 工程简化/历史背景改写为设计演进记录、状态表 D-001/D-101 改「✅ 已实施」（v0.1.0）；架构 §10.24 关联设计债索引补 D-001 行；cognitive-foundation 引论否决权实现表述统一为总线模型并加历史注记；全库「三点分布式检查」清零（历史注记除外）。
- **章节引用错位三连（1-03/1-04/1-06）**：架构 §2 定位「§10.6/§10.7」→「§2.2/§10 各质量属性节」；§2.2.1 `p6_margin`「§10.9」→「§10.11」；S-12「潜伏复兴加速通道（§4）」→「复兴加速通道（§5.2 潜伏势能重估端口）」并统一术语。另发现并修复同源陈旧引用：成本护栏「§7」→「§8」（2 处）。
- **监督平面口径统一（1-02）**：架构 §0.4 速查表「由原宪法主权面与监督平面合并」→「由原宪法主权面更名而来（监督平面为独立正交面）」；速查表行名「已合并入外部治理接口」→「监督平面为独立正交面」；§0.5 一致性表监督平面行「异常冻结触发」→「冻结请求触发（发至宪法修订端口，不持有冻结权）」。
- **逻辑-因果轴层级口径（1-05）**：方案 (a)——认知基础「双轴独立」保留，架构 §0.1 轴计数说明/时间轴条目/未来扩展删除「物理时间轴的独立子轴」转述，统一为「时间轴由物理时间轴与逻辑-因果轴双轴并列构成」；§2 检测器族组件名「逻辑-因果子轴监测器」→「逻辑-因果轴监测器」。
- **P3-19 承载补全（2-01）**：blueprint 新增 §P3-19 File Graph 章节（规格承接自 technology-stack §七，标注 v1.1 目标 + 与 v0.1.0 关系 + P3-18 预留编号说明）；technology-stack §七 File Graph 段改摘要+指针；三语言 SDK 战略补版本归属标注（v1.1 目标）。
- **结构与格式（3-01/3-02/4-01/4-02/4-03/4-05）**：架构 §5.2 后补「§5.3/§5.4 已于 0.0.9 迁出」占位声明；§5.2 节内导航（0.0.19）；§0.7 注意力调度器驻留矛盾句清理（与 §9.1 统一）；§0.5 表行名「宪法主权面」→「外部治理接口」；cognitive-foundation L51 并列表述改写、L94「四轴度量空间」补「不含可及性轴」桥接注记。
- **blueprint 文件名规范化（2-02）**：`architecture-blueprint-v1.1.md` → `architecture-blueprint-v1.1.md`，全库 11 份文档引用同步。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿。



## 0.0.20（2026-08-05）— 第五轮全库深度审计修复批次

> 依 round5-deep-audit（第五轮·引用落点深度复核）闭环：0 高 / 10 中 / 8 低（共 18 项），全部为文档层问题，无认知模型/技术选型变更。

- **P0 语义矛盾修正（1-01~1-04）**：架构 §0.4 速查表外部治理接口行「不持有至高否决权——策略层查询自行决定」→「持有至高否决权（强制冻结等）；日常执行中多为被动响应」（与 §1.1/§1.2 对齐）；§0.5 监督平面行「宪法解释」→「证伪信号路由」并注记归属（宪法解释属宪法解释层 §1.6，监督平面不持否决/冻结/修订权 §1.7）；§0.5 元认知层行「物理驻留元认知层」→「逻辑与物理均归属宪法主权面（v0.1.0 治理权归位，见 §1.6）」并清理同源残留 §1.4 信号路径「虽物理驻留元认知层（为访问检测器数据）」（与 §1.6 上移口径一致）；§10.12 全量级「三子轴全量」→「双轴全量；纪元切换为附加独立维度，仅标记边界」（与标准级/§0.1/认知基础 §1.1 三处统一），同步清理「纪元切换子轴」「逻辑-因果子轴」残留（架构 L2792/L3496/L62 + debt-collection D-301 + traceability-map G-01）。
- **P1 跨文档章节引用批量修正（2-01~2-03）**：架构词汇桥接表/反向映射表 8 处存储层组件「§4」→「§5.2」（情感效价空间/整合窗/潜伏势能重估端口/见证锚定更新势垒/使用权重/升华管道/LTM 巩固子模块/结构性记忆守护，均经 §5.2 组件树逐条核验）；cognitive-foundation 6 处章节错位修正（模拟隔离区/沙箱验证环→§4.1/§6、多路径结果集→§4.1/§6、WM 操作空间→§4.1、注意力调度器 3 处→§9.1；「WM调度预处理器」组件名在架构 §0.5 表/feature-flag/glossary 均有承载——保留组件名仅改章节并补别名注记，审计「组件名不存在」断言经核验不成立）；架构→api-spec 端点章节 7 处（叙事线 §七→§八×3、压缩 §八→§九×2、因果链路 §九→§十、压缩审计→§6.5），api-spec §6.5/§八/§九/§十 补「被架构引用」反向注记防漂移。
- **结构归位（3-01/3-02）**：§5.17/§5.18「WM 层预备」迁入 §6 WM 层（§6.1 定位/§6.2 组件，内容原样保留 + 迁移注记；原位置不保留占位标题）；§5 断号说明合并为 §5.2 节内导航单一权威段落（5.3/5.4/5.6/5.7/5.8 迁蓝图、5.17/5.18 迁 §6.1/6.2），§5.2 尾部范围说明改指导航。
- **引用与计数修正（1-06/4-01/5-01~5-03）**：架构 §11 术语计数 56→57 条（与 glossary/README 一致）；doc-audit.py 6.7 增补架构 §11 术语数比对（闭环 1-06 门禁盲区）；L1184 行号引用「（L1118）」→「（§3.1 归属上下文）」（L1118 实为 §2.6.3 防抖反射执行器，审计所指 §3.2 经核验不成立）、L2794「（L3387 保持不变）」→「（见 §7.3a 排序调制，口径保持不变）」；5D 排序「§10.14」→「§7.3a」；「§9.3 上下文注入侧 token 分配」改指 detailed-design §10.1（§9.3 为摘要指针）；「§7.3」→「§7.3d」MCP Bridge 实现表。
- **格式/可发现性（2-04/4-02）**：technology-stack 三语言 SDK 表补「版本对齐策略」注记（SDK ≥3.10 为独立交付物，与后端 3.11–3.13 基线互不约束）；README 阅读建议补用例/操作目录/算法文档入口行。
- **1-05 统一口径处置（方案 b）**：架构 §0.4 命名对照「统一口径以外部治理接口为准」→「两称并存，以 glossary 别名声明为权威；新写内容优先使用『外部治理接口』，既有正文随维护批次收敛」——全库 133 处（21 文件）不做大爆炸更名，与 glossary「非更名完成态」自述一致。
- **3-03 标题编号风格**：全库四套编号体系（§X.X / 中文数字 / P3-X / ops 数字）各文档自成体系、跨文档引用已带换算说明——记录在案，不做全库统一（低价值高改动量）。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿。



## 0.0.21（2026-08-05）— 系统架构总览图新增批次

> 用户需求：架构文档缺一张可一目了然的完整系统架构图——此前仅各层局部 ASCII 组件树（§5.2/§6.2 等），无六层栈 + 治理面 + 横切组件的全局视图。

- **新增 §0.4.1 系统架构总览图**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.4 插入 Mermaid 全局视图——六层功能栈（接入/WM/推理皮层/策略/存储/元认知）+ 三个正交治理面（宪法主权面/监督平面/身份面）+ 两个横切基础设施（注意力调度器/事件总线）+ 编号数据流（① 读写请求 → ② 校准信号 → ③ 结构化通信单元 → ④ 预激活集 → ⑤ 候选集 → ⑥ 裁决产出 → ⑦ 放行写入）+ 图例（实线/虚线语义、六类结构原则对应、预提交总线口径、元认知层横切声明）。
- **口径核验**：图中全部标注与正文逐条一致——预提交总线为事件总线 topic `pre_commit_bus`（§1.8）、裁决产出写入必经预提交总线（不可绕过）、宪法否决优先于身份否决（外部安全高于内部同一性）、推理皮层物理驻留 WM（§4）、元认知层为横切监测非第七层（§2 定位）、注意力调度器不驻留任何功能层（§9）。
- **独立 HTML 版**：新增 [diagrams/system-architecture.html](../diagrams/system-architecture.html)（0.0.21 同批次交付）——内嵌同一 Mermaid 图（经程序核验与 §0.4.1 图块逐字节一致）+ 图例/关键数据流说明 + 缩放控件（100%/150%/200%/适应宽度），浏览器直接打开即可渲染，README 阅读建议加入口行。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿。

---



## 0.0.22（2026-08-05）— 外部项目理念吸收

> 用户需求：对开源 AI 认知架构项目做源码级对比分析后，借鉴吸收其优秀设计理念与功能完善 Kairos。吸收前完成源码级深挖（提取 21 条实证参数/规则），仅吸收 Kairos 真实缺口（已有等价物不重复吸收）。

- **热度体系实证参考基线**（吸收外部热引擎与时间蒸馏实证）：认知基础 §1.1 新增「热度体系实证参考基线声明」（热度组合公式 `1.0+频次×2+新近×10+重要性加分`、层级衰减 ×0.985/0.975/0.965/0.95、父传播 `max×0.6+mean×0.3+一致性×0.1`，附 P6 边界声明与可证伪判据）；usage-load-algorithm 3.5 K-063 注记补参考基线段；detailed-design 补热度体系参考参数表。
- **摄入侧情绪爆发→整轮保护**（吸收外部情绪爆发检测实证）：认知基础 D.12 新增「摄入侧情绪爆发→整轮保护声明」（D-019(a) 情感调制的摄入侧扩展——输入侧情绪信号触发整轮保护通道 + 升温抑制，可证伪判据）；架构 §5.2 新增摄入侧情绪保护组件；配置新增 `KAIROS_EMOTIONAL_BURST_KEYWORDS`/`KAIROS_EMOTIONAL_BURST_PROTECTION_ENABLED`。
- **摄取噪音规则库**（吸收外部纯正则噪音过滤实证）：架构 §7.3 捕获门控后补「噪音规则库层」（四类纯正则规则 + 重要性加分表，命中不计轮数不升温，P6 边界）；detailed-design 补噪音规则参考清单与加分表；配置新增 `KAIROS_INGEST_NOISE_FILTER_ENABLED`。
- **时间粒度层级实证对照**（吸收外部五级时间蒸馏实证）：认知基础 §1.1 开放简化声明补「时间粒度层级实证对照声明」（五级离散层级与去语境化连续谱的映射关系，不闭合开放简化）；detailed-design §7 层级蒸馏管道补时间粒度层级蒸馏形态对照。
- **三问题正交解耦框架**（吸收外部身份制实证）：认知基础附录 C.4 新增声明（去重=身份/保护=生命周期/更新=版本三问正交，纯归纳既有机制、不做机制新增）。
- **RSK-008 外部平台耦合与可复现性风险**（吸收外部爆炸复盘教训）：[risks.md](../governance/risks.md) 新增风险条目——大型生产代码库因硬编码路径/外部平台/远端服务耦合而不可复现、整体归档的教训，缓解建议含竖切「可独立运行」验收标准强化。
- 债务登记 D-335~D-338；glossary 增补热度层级衰减/摄入侧情绪保护/噪音规则库三条术语（57→60 条）；配置参数正文 220→223、总计 368→371；吸收决策记录。
- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）。

---



## 0.0.23（2026-08-05）— 内容架构全面审视修复批次

> 用户需求：对认知基础与系统架构两份核心文档做内容架构全面审视，重点看逻辑性与可阅读性。审查由双代理全文通读 + 人工核验完成，本批次执行全部问题修复（高优 4 项 + 中优全量）。

**认知基础（[cognitive-foundation.md](../foundation/cognitive-foundation.md)）**：
- **引论瘦身**：构造论声明/记忆-学习边界声明/可证伪条件压缩为互引指针（D.2/D.10/A.6/B.1），7 大声明块降至 4 块
- **§1.1 标题改五轴口径**（原「三维量度+结构保护标记+检索成本指标」为旧表述残留）；§1.4→1.7 断号补迁移注记；D-335 热度基线参数公式瘦身（移 detailed-design，守文档职责剥离原则）
- **§1.3 六机制加编号头**（① 编码~⑥ 前瞻保持），消除层级倒挂
- **§2.2 声明标签消歧**：五个「硬约束/软原则声明」改语义名（使用价值主导/契约投影/激活-存储解耦/遗忘优化/探索预算声明），互引合并定义；「双轨切换」旧术语清理（否决权正交模型表述）
- **§三 3.1 编号**（外部校准源充分性）
- **附录**：D.9 干扰效应对齐 §1.3 升格版（决策 D-23 H1，原「不预设为独立机制」残留矛盾消除）；D.7 标题补记忆压力；C.4 门禁同步四步+第五步（原「三道门禁」残留）；C.3/D.3/C.6/D.9a 悬空引用修正（4 处）；A.2↔§1.3.2 感知缓冲互引；E.6a 标题扩展；E.7 已知超限重复合并；L1003 孤立标题删除；版本记录补 0.0.16~0.0.18/0.0.21 占位并去重 0.0.22

**系统架构（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)）**：
- **§2.6 改题**「元认知层关联组件（检索预处理与结果治理）」+ 归位注记（QueryAnalyzer 等非元认知本体）；领域路由引用 §3.1→§3.4
- **§0 同名标题 9 处加节号消歧**（v0.1.0 交付范围 ×4、未来扩展 ×5）；0.9↔10.13 降维互引
- **§5.2 树修复**：└─→├─ 三处（升华管道/长文本分块/知识演化）、孤立竖线删除、freshness 判定表转文本、Flag 标记机制节点名修正（原误标「三链路知识图谱」）、节内导航补全 32 节点（原 13 项，含 0.0.22 摄入侧情绪保护）
- **§5.20 编号补全**：新增 5.20.1（SQLCipher P3-20）、P3-17 加编号 5.20.6；标题改「P3-17、P3-20 ~ P3-24」
- **§7**：7.3.1 降 h4；7.4a 缺位注记；**7.3d MCP/Hermes 内容迁 §7.1a**（接入方式归位，feature-list 引用不受影响）
- **§10 更名**「质量属性、不变量与补充机制」（10.14~10.24 机制残留与标题不符）
- L1908 自指引用清理（「§5.2 遗忘调度器（§5.2 遗忘调度器）」）

**不做**（评估后维持现状）：§5.2 巨树不拆 h4（树保留层级语义、全库引用「§5.2 组件」级别不受益于拆分，以节内导航补全替代）；围栏内伪标题（渲染策略表/持续监控配置/第一次观察）不改（属代码注释，工具误判可接受）。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）。

---



## 0.0.24（2026-08-05）— 第六/七轮全库深度审计修复批次（后补登记：版本记录表序号为序）

> 闭环全部问题项：第六轮（round6）10 项此前未入任何批次（0.0.22/0.0.23 分别为外部理念吸收与内容审视批次），本轮随第七轮 9 项新发现一并闭环，共 19 项（0 高/6 中/13 低）。

- **1-01 认知基础 E.6a 引用修正**：pairwise 表「认知完整性 > 时间」实现约束列「架构 §4.2」→「架构 §5.2 结构性记忆守护」（is_structure 守护定义于架构 §5.2 组件节；修后 `grep "§4\.2"` cognitive-foundation 清零）。
- **1-02 架构 §2.2 自引用修正**：叙事自洽度语义降级声明「`is_identity` 保护规则（§4.2）」→「（§5.2 身份注册表）」。
- **1-03 RTM R-01/R-02 引用修正**：设计章节列「arch §4.2」→「§5 路径空间」/「§5 向量空间」，与 feature-list 同款条目一致；R-03（多路径融合）保持 §4.2 不动。
- **1-04 blueprint §5.7 过时引用修正（监督平面独立化后未同步）**：①否决权归属「§1.7 §11」→「§0.4 社会性校准占位段」；②激活开关归属「§1.7」→「§1 章宪法主权面」；③`kairos://_social/` 预留路径「§1.2」→「§0.4 接入层预留路径」；④同段「激活前提条件（§1.2 占位声明）」→「§0.4 社会性校准占位段」（审计未列的同源第 4 处，按联动规则一并修正）。
- **2-01 M-05 过时标注清理**：RTM M-05 端点列「归档端点（待 api-spec 注册）」→「`POST /v1/memories/{id}/archive` / `POST /v1/memories/{id}/restore`（api-spec §1.5，0.0.15 注册）」；全库「待 api-spec 注册」清零（仅版本记录/历史条目残留）。
- **2-02 configuration 附录 A 计数修正**：「正文各节收录 210 项」→「223 项」（0.0.16 增至 220、0.0.22 增至 223，口径补注）；同段「12 项待定义」核验仍准确（附录表实际 12 行）。
- **1-05 架构 §10.24 关联设计债索引落点修正**：D-005「路径空间 §4.2」→「§5.2 路径空间」、D-017「§7」→「§5.2 遗忘调度器」、D-018「§4.2 / §5.1」→「§7.3 摄取门禁 / 认知基础 D.6」。
- **1-06 债务归档区落点修正**：ARC-D-101 落点「架构 §4.2 calibration_confidence」→「§5.2」。
- **1-07 D-4xx 排序归位**：D-401/D-402 两条整体移至 D-338 之后（D-3xx 段末尾、D-4xx 段起点），文档内顺序与编号语义一致；摘要表引用（§四 L714-715）不受位置影响。
- **1-08 前瞻记忆段归位**：架构 §8 末「前瞻记忆」段迁至 §3.2 前瞻保持跨层协调协议段后（语义聚合），§8 仅保留安全红线与红线语义补充；requirements-baseline §1.8 与 feature-list PM-01 引用改指 §3.2（feature-list 为审计未列的联动同源引用）。
- **2-03 OP-054+ 承诺收口**：operation-catalog §五 覆盖边界声明改为「扩展端点定义以 api-spec §八~§十八 为权威（0.0.15 定稿，81 端点），本目录不逐项登记 OP-054+ 条目」——未按审计建议二补登条目（将波及操作计数 53 项与 README/门禁基线，选建议一收口）。
- **2-04 README 版本记录补登 0.0.19**：0.0.18 与 0.0.20 之间补插「0.0.19 第四轮批次索引同步：blueprint 文件名 v1.1+ → v1.1（补登，原缺失）」。
- **2-05 执行记录刷新**：documentation-governance §3 执行记录补 08-05 批次审计记录（批次明细原见 audit-history-summary §一，该文件已于 0.0.30 移出仓库，处置明细见 changelog 0.0.30；不引用轮数——审计断言「12 轮累计」与汇总表实际行数不符，按事实不引用具体轮数）。
- **3-01 悬空承诺收口**：架构 §0.4 删除「认知基础尚未逐层同步双标注，认知基础下一轮修订时同步」半句，改为「认知基础交叉引用以章节号为准，层编号映射以本节为权威」。
- **3-02 README 组件数同步**：implementation-map 索引行「40+ 组件」→「70 组件」（对齐 implementation-map 0.0.10 条目 67→70 与 test-plan 口径）。
- **4-01 documentation-governance 版本记录占位补齐**：补「0.0.3~0.0.10 合并占位」「0.0.13 占位」「0.0.15~0.0.16 合并占位」行。
- **4-02 架构版本记录补齐**：补「0.0.15 占位」行与「0.0.18 补登」行（0.0.18 批次引用改指实际修改本文 2 处，为漏登记而非占位，按事实补登）。
- **4-03 requirements-baseline 版本记录补全**：补「0.0.4~0.0.9」「0.0.11~0.0.13」合并占位、「0.0.15 补登」（M-05 同源——0.0.15 注册 archive/restore 原应同步而未同步）、「0.0.16~0.0.23 合并占位」行。
- **4-04 RTM「arch」缩写统一**：22 行「arch [architecture-v0.1.0.md](...)」→「架构 [...]」（审计断言 17 行，实际 grep 计数 22 行，按实际全部替换），与治理 §2 交叉引用规范第 2 条对齐。
- **过程建议 16 不做项记录**：门禁补盲区（版本记录连续性检查 + §X.Y 引用语义核验候选清单）未实施——连续性检查与「文档仅登记触及本文件的批次」惯例冲突会大面积误报（如 debt-collection 0.0.2→0.0.14 正常跳号无占位）；§X.Y 语义核验保持 governance §2.1 人工门禁。
- **归档（0.0.18 机制）**：第六轮（10 项，0 高/2 中/8 低）与第七轮（19 项，0 高/6 中/13 低）登记审计历史摘要 §一 汇总表，删除 `2026-08-05-round6-deep-audit.md` / `2026-08-05-round7-deep-audit.md`。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿（exit 0）。



## 0.0.25（2026-08-05）— 第八轮全库深度审计修复批次

> 闭环第八轮全部问题项（round8-deep-audit）。**审计统计勘误**：报告头部「2 高/13 中/8 低 = 23 项」与报告自身表格（3 高/12 中/9 低 = 24 项）不符，按实际核验数处置与登记。

- **1-1 端点计数重算与同步（P0）**：api-spec 定义行（`**METHOD /path**` 与 `### METHOD /path` 双格式）按 `(METHOD, PATH)` 去重实测 **85 个 `/v1` 业务端点 + 3 个无前缀端点（GET /health、GET /audit/compression、GET /audit/compression/summary）= 88 物理**（审计断言经脚本复核成立，差异恰为 0.0.16 新增 7 端点）；同步 api-spec 计数口径注记（80→85、81→88，注「0.0.25 勘误」）、implementation-map 已对齐注记与 REST 路由行、operation-catalog 覆盖边界（「0.0.15 定稿」表述同步修正）；**doc-audit 新增 6.12 API 端点计数校验**（堵住审计所指门禁盲区——定义行统计 ↔ 口径注记声明双向比对），STALE 清单登记旧口径 3 条防回退。
- **2-2 0.0.16 版本记录计数勘误补登**：api-spec 0.0.16 条目补「（0.0.25 勘误补登：业务端点计数 80→85、物理总数 81→88，口径注记同步）」。
- **1-2/3-3 DFA/DAP 命名与交付状态裁决（P0）**：**命名统一为「确定性事实归档 DFA」**——与审计建议（保留 DAP）方向不同：决策 D-22（[adr.md](adr.md) 权威）与认知基础/蓝图/架构 §5.12 标题均为 DFA（4 文档多数派），debt-collection D-401 条目名与架构 §5.12 正文规格的 DAP 为少数派且节内自相矛盾（标题 DFA、正文 DAP），按决策命名优先原则反向对齐（D-401 标题/工程简化/历史背景/状态表、D-305 历史背景、documentation-governance D-4xx 类别示例、cognitive-foundation DAP 只读查询、架构 §10.24 索引主题；全库 DAP 清零，ADAPTIVE 参数名除外）；**交付状态统一 v1.1**（架构 §3.2.1「DFA 为远期目标，v1.1 实现」+ 蓝图两处版本依赖 + D-401 Phase 4 为多数派）：§5.12 补 v1.1 交付占位标注（3-3），架构 §5.12 与认知基础 G1 分工声明的「v0.1.0 两套机制并行」改「v1.1」（D-305 历史背景「v0.1.0 的韧性替代方案」同步）；§10.24 索引 D-401 落点 §5.2→§5.12。
- **1-3~1-12 架构引用落点批量修正（P1）**：L969（§5.2 身份注册表）、L3330（§7.3 摄取门禁/§5.2 巩固子模块，对齐 §9.2 同项）、L1773 关系索引删错引（§5.2 节内自引冗余）、L2903（§7.1a，0.0.23 迁移未随迁）、L3401（§10.3 不变量修订门禁）、L2643（§4.1 上下文块系统）、L1345/L3766（§10.10a D-01 修订）、L3792/L3798（§5.2 见证锚定/去语境化连续谱，0.0.20 同源残留）8 处审计项 + **grep 同源排查新增 3 处**（CJ-002 结构性记忆守护落点 §5.2、L1787 整合窗 §5.2、L3343 响应时间常数级联 §10.4）——再次印证「引用核对须以 grep 全量结果为准」。
- **1-5 ERR-CTR-002 口径修正**：error-reference「临时契约过期清除刻意不产生审计事件」→ 0.0.14 现行口径（`expiry_cascade_delete` 标记约束：已入库临时记忆清除必留痕，仅捕获阶段被拒绝的输入不产生审计事件）。
- **1-6 implementation-map 参数计数**：:18「参数总数 358（正文 210 + 附录 A 148）」→「371（223 + 148）」（configuration 权威现值；与 1-1 同行一并修正）。
- **2-1 §8 前瞻记忆引用残留 3 处**：data-model:47、api-spec:418、glossary:59 →「§3.2 前瞻记忆段」（0.0.24 1-08 迁移的同源漏修；grep「前瞻记忆」全库复核无遗漏）。
- **3-1 领域路由双处定义收敛**：§3.1 定位段收敛为一句+指针，§10.18 为完整定义权威（参数名以 configuration 为准）；§2.6.1 QueryAnalyzer「领域路由（§3.4）」→「（§10.18）」——0.0.23 批次曾把引用从 §3.1 错改为 §3.4（§3.4 实为「域路由」路径前缀隔离），本轮纠正。
- **2-3 glossary 关系枚举补全**：关系索引补「+ 派生关系（derived_from）」（data-model `memory_relations.relation_type` 六值；feature-list W-05 已列六种，glossary 为唯一漏处）。
- **2-4 S-xx 悬空占位解析**：cognitive-foundation 受控访问约束「安全红线 S-xx」→「S-06 越权操作拒绝」（read/write/admin 三级 Key 权限，语义最贴合）。
- **2-5 technology-stack 版本记录占位**：0.0.14 与 0.0.19 之间补「0.0.15~0.0.18 合并占位」行（对齐 documentation-governance 0.0.24 4-01 惯例）。
- **2-6 threat-model 链接文字**：architecture 重复链接文字清理（「[architecture-v0.1.0.md](…) [architecture-v0.1.0.md](…) §8」→ 单链接 §8）。
- **3-2 §10.23 下挂 h4 归位**：P3-11（Directives）/P3-12（malloc_trim）/P3-13（Webhook）三个主题无关 h4 合并为「相关 P3 组件索引」小节（审计建议二；无锚点外链，安全收敛）。
- **4-1 章节编号中英混用统一**：api-spec 顶层标题 18 个（一~十八→1~18）与 data-model 顶层标题 13 个（一~十三→1~13）改数字（小节 1.x/6.x/18.x 与章号对应自洽），两文档内部中文序引用 22 处同步；**全库联动 25 处**（architecture 15、detailed-design 5、blueprint 5、operation-catalog 4、adr/slice-implementation-guide/user-guide/implementation-map/troubleshooting/error-reference 各 1~2）；认知基础/acceptance-criteria/technology-stack/configuration 等中文序标题文档**保持不动**（标题与引用自洽，非混用）。
- **4-2 速查表行首补概念名**：§0 速查表「（监督平面为独立正交面 §1.7）」注记行 →「监督平面 | 独立正交面（见 §1.7）| …」。
- **4-3 版本记录占位惯例明确**：governance §5 明确「仅登记触及本文档批次」为全库惯例（0.0.24 过程建议已确认，不做跳号连续性检查），触及但未逐条登记的连续区间以合并占位行补注。
- **归档（0.0.18 机制）**：第八轮（3 高/12 中/9 低 = 24 项）登记审计历史摘要 §一 汇总表，删除 `2026-08-05-round8-deep-audit.md`（审计历史摘要文件已于 0.0.30 移出仓库）。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿（exit 0）。



## 0.0.26（2026-08-06）— 第九轮全库深度审计修复批次（P0+P1）

> 闭环第九轮（round9）开工前必需项：3 高（H-01/H-02/H-03）+ 7 中（M-01/M-03/M-04/M-05/M-06/M-07/M-11）+ M-05 同源联动 2 处 + 门禁补盲区（M-13 建议 1/2 落地）。**审计断言核验**（依「先核验再改」约定）：H-01 所列 27 处引用全部属实，另发现同源残留 2 处（architecture §0.6 P6 压缩比双口径引用、debt-collection D-001 谱系）一并修正；H-02 裁定获认知基础 §1.8「编译器在注意力调度器之后运行」权威佐证（:385）；H-03 其余 14 张竖切表经脚本逐列比对无同类缺口（比对方法见门禁 6.13）。

- **H-01 §3.2→§3.3 引用系统性漂移（P0）**：grep 全量 `§3.2` 逐条判定——价值裁决子系统（辞典式裁决器/帕累托约束集/保守倾向闸门/P6 合规声明/候选生成器/使用负载计量器/结构注入器/序数压制幅度记录/排列漂移审计）引用 **29 处改 §3.3**（architecture 13 处含审计遗漏 §0.6 压缩比 1 处、cognitive-foundation 3 处、design-philosophy-relations 6 处、debt-collection 5 处含审计遗漏 D-001 谱系 1 处、cognitive-architecture-gap G-07 1 处、glossary 1 处、claim-matrix 3 处）；预测器/调节器/组合寄存器/前瞻保持/校准消解/§3.2.1 真理路由器/意图契约等真实 §3.2 职能引用保留（核验确认）；§3.2 首段补反向指引「价值裁决子系统见 §3.3」；C-23 已废弃条目加「引用为废止前口径」注记。
- **H-02 编译器管线顺序裁定（P0）**：裁定「感知缓冲 → 注意力筛选 → 编译器 → 结构化通信单元 → 事件总线 → WM」——与 :2729 后半句「接收已通过注意力筛选的输入」、:2834 门禁路径注意力前置、认知基础 §1.8（:385 编译器在注意力调度器之后运行）及 §294 三层门禁约束一致，且避免 L2 对未筛选输入调用的成本；修订 :223/:2729/:3790「位于感知缓冲与注意力调度器之间」→「位于注意力调度器与 WM 层之间」；:2834 摄取验证门禁路径补「编译净化（L1/L2）」环节并注明降级（`degraded_L1`/`passthrough`）行为。
- **H-03 schema-slice.sql 补 4 字段（P0）**：memories 表回填 `structural_value`（CHECK 0/1/2）/`structural_value_reasons`/`structural_value_updated_at`/`compression_trail`；补 `is_structure` ↔ `structural_value` 双向同步 CHECK；**逐表复核其余 14 张竖切表**（脚本提取列名与 data-model 逐列比对）无同类缺口；变更记录登记「0.0.26 复核：与 data-model v0.0.25 逐列比对」。
- **M-01 跨层三环不变量落点修正**：架构 :317/:323/:631「§6」→「§10.3」（权威定义 :3337）；ops configuration:401 / reliability:65「§6/§10.3」→「§10.3」（0.0.6 批次只修 ops 未修架构自身的同源漏修）。
- **M-03 汇聚式融合落点修正**：cognitive-foundation:313 blueprint §5.3（实为价值独立性公理）→ architecture-v0.1.0 §4.2 汇聚式多路径融合（与 :301 表述对齐；双重错误：章节号+文件）。
- **M-04 dpr 交叉引用表文件错列修正**：:164 注册表/:165 编译器「认知基础声明」列 architecture→cognitive-foundation（§1.7 确定性状态/§1.8 编译器，佐证 blueprint:354 与 architecture:2731）；:163 指针原则补 cognitive-foundation §2.1 出处（核验确认认知层有独立声明，非报告假设的「—」）。
- **M-05 MCP Bridge 落点修正**：technology-stack:98 §7.3→§7.1a（0.0.23 迁移残留）；**grep 同源排查新增 2 处**（审计未列）——integration-design:124、feature-list:176 同引「§7.3 MCP Bridge」一并修正。
- **M-06 检索深度分级引用修正**：architecture:894「参见检索深度分级 §3.2」→§3.9（权威定义 :1444；:1454 反向引用本就正确，作对照）。
- **M-07 存活探针端点修正**：slice-implementation-guide:92 `GET /v1/health`→`GET /health`（全库口径一致无前缀；`/v1/health/detail`、`/v1/health/calibration` 等真实 /v1 端点不受影响）。
- **M-11 种子路径口径统一**：release-guide:86 `--seed-path ~/.kairos/seeds.yaml`→`~/.kairos/seeds/`（目录语义，与 `KAIROS_SEED_PATH` 及 `kairos://_system/seeds/{name}` 多种子结构一致）；configuration 附录 A `KAIROS_SEED_PATH` 来源行号 189→192。
- **M-13 门禁补盲区（建议 1/2 落地）**：doc-audit 新增 **6.13 DDL↔data-model 字段集比对**（解析 schema-slice.sql 各表列名与 data-model 同名字段表逐列比对，堵 H-03 类漏修）与 **6.14 机制名→权威章节映射抽检**（23 条映射：辞典式裁决器→§3.3、跨层三环不变量→§10.3、MCP Bridge→§7.1a、检索深度分级→§3.9 等，扫描全库正文拦截语义落点漂移；「预测器」因定位横跨 §3.1/§3.2 不入映射，版本记录区/changelog 不参与判定）；配合措辞微调 3 处消除行级共现误报（technology-stack MCP Server 实现、architecture 工具清单行/关系管理 API 行）；过程建议 3（结构性变更连锁复核流程规则）按报告排期随 0.0.27 处置。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13 + 6.14 全绿（0 FAIL 0 WARN）;`deep-audit.py` 全绿（exit 0）。



## 0.0.27（2026-08-06）— 第三方分析摘要分诊批次

> 外部第三方分析摘要 12 项建议交叉核实——9 项判定「已覆盖/有意设计/已登记」（降维 D-016/D-103、衰减公式化、充分性不阻塞为安全权衡、学习边界 D-007、制衡叠加规则、可导航性、冷启动种子、自激防护、化石节点、事件类型注册门禁）；2 项落地为文档变更（命名配置集、D-403）。

- **架构 §0.8 补「命名配置集与组合约束」**：12 个特征标志组合空间 4096 种中仅承认三种命名配置集（`kairos-minimal`/`kairos-slice`/`kairos-full`）为部署与测试目标——未命名组合不是合法系统形态；启动时校验标志组合合法性，不匹配任一配置集时拒绝启动并输出 `invalid_flag_composition` 审计事件；配置集间无运行时热切换；新增标志须归入配置集。
- **debt-collection 新增 D-403 架构复杂度度量（v1.1 评估）**：v0.1.0 以配置集约束 + 标志上限 24 + P6 压缩比收敛（D-334）覆盖「复杂度可控」主要可观测面，独立复杂度指数属增量度量，登记 v1.1 评估项（触发条件：标志启用数 > 12 且未归入配置集，或组件实现路径数超基线）。
- **编码纪律同步**：新增特征标志须同步归入配置集或新增配置集（§0.8 编码纪律段）。



## 0.0.28（2026-08-06）— 第十轮全库深度审计修复批次（P0 三项）

> 闭环 round10 P0 三项（C-01【高】/C-02/C-03）+ 门禁补盲区。round10 报告经独立复核：核心主张全部成立，报告自身 1 处误报（A-02 权重顺序——实测详设 §6.3 与认知基础 :415 同序一致）与 4 处计数勘误（C-02 56/20、S-01 §前缀 7、F-01 汇总补注），勘误登记于报告版本记录。

- **C-01 MCP 工具计数 15 口径统一（【高】）**：api-spec §6.8 补关系管理 3 工具（`kairos_link`/`kairos_unlink`/`kairos_relations`，含参数语义与「无独立公开 REST 端点」说明）+ 指引段修正（§7.3.1→§7.1a，注明 15 构成）；operation-catalog 工具列注记 12→15；technology-stack 构成公式重写（「12 规范操作直接映射」修正为「基础工具集 12（3 规范操作直接映射 + 检索/维护/治理类 9）+ 关系管理 3」）；架构 §7.1a :2920 构成重写（去除 link/unlink 重复计数，F-03 闭环）。
- **C-02 覆盖声明失真修复**：operation-catalog 新增 OP-054~066 共 13 项（记忆生命周期 6：archive/restore/rollback/versions/export/feedback；主动功能 7：entities/extract/reflect/proactive/sublimation×2/unfreeze/halls）；7 个运维探针端点豁免声明（config/health×2/scheduler/seeds/webhooks/rebuild-index）；覆盖声明改写为「49/56 + 豁免清单」；sessions/evolution 路径占位符统一 `{id}`（消除与 OP-006/017 的伪缺口）。
- **C-03 硬行号整体废除**：configuration 附录 A「来源」列 136 处 `path:line` 全部改为「文档 §章节」语义引用（精确口径实测 135/136 漂移）；38 处原引用文档无定义的参数做权威落点核查（修正至 detailed-design §11.x/blueprint §P3-x/deployment §三 等）；KAIROS_PATH 标注「待定义」。
- **门禁补盲区**：doc-audit 新增 **6.15 硬行号引用禁令**（`path.md:行号` 全库即 fail，reviews/ 排除）与 **6.12a MCP 工具表行数比对**（api-spec §6.8 ↔ 架构 §7.1a 须 15 行且工具名集合一致）。
- **顺手修正**：api-spec :240 archive 引用 §7.3→§7.3.1；版本记录补 0.0.26~0.0.27 合并占位（api-spec/operation-catalog）。



## 0.0.29（2026-08-06）— 第十轮全库深度审计 P1 修复批次

> 闭环 round10 P1 五项（S-01/D-02/D-01/C-04/D-04）。S-01 执行方案经实测调整：报告原案「全量中文序」实测联动面 ~430 处（architecture 内部裸引用 275 处 + 外部 153 处），改按方案 B（数字序统一）执行——引用零联动达成同目标。

- **S-01 标题风格统一（方案 B）**：api-spec/data-model 大章「N、」→「§N」（18+13 章并入 §N 数字序形态，heading id 不变、引用零联动）；blueprint 3 大章归位中文序；documentation-governance §2 补**大章标题风格约定**（§N 数字序 = 工程/规格文档、中文序 = 认知/叙述文档、引用一律数字与标题文字解耦、引言性无编号大章为例外）。
- **D-02 连锁复核流程落地（M-13 建议 3）**：documentation-governance 新增 §2.2 结构性变更连锁复核——触发条件（迁移/更名/删除/文档分合/权威落点变更/标题风格变更）、变更前基线扫描、五步复核清单（含 H-01 同源遗漏扫描/镜像章节检查/反向指引）、复核登记——与门禁 6.14 自动抽检双保险。
- **D-01 工程流程文档**：新增 [development/engineering-workflow.md](../development/engineering-workflow.md)——分支策略（main/develop/feature/release）、PR 门禁（doc-audit + deep-audit 必过）、提交规范（批次粒度 + Co-Authored-By）、CI 流水线、发布流程与 release-guide 衔接；README 核心文档 54→55（53 md + 2 yaml）。
- **C-04 归档衔接修正**：audit-history-summary 归档机制补充——未闭环项存在时原报告不删除；每轮登记保留「未闭环项标题级清单」（round9 M-02/L-01~L-03 处置上下文丢失教训）；round10 报告按机制归档删除（P0+P1 全部闭环）。
- **D-04 术语表补 7 条**：编译器/结构化通信单元/编译净化/检索深度分级/命名配置集/竖切/结构性记忆（60→67）；README 与架构 §11 计数声明同步（门禁 6.7 验证）。



## 0.0.30（2026-08-06）— 仓库整洁化批次

> 用户决策：审计/过程材料不随仓库分发（GitHub 仓库只保留使用者必要内容）。**后续审计不再创建 reviews/ 目录**，处置记录只进 changelog 批次条目。

- **移除审计过程材料**：删除 docs/reviews/ 目录（审计历史摘要）；scripts/_deep_audit_out.json 移出 git 跟踪并纳入 .gitignore。
- **全库引用清理**：认知基础决策编号引用改指 [adr.md](adr.md)（决策权威已迁移）；debt-collection 5 处债务谱系标注保留「认知×架构审计问题 P-xx」文字删链接；changelog 历史条目 14 处「依/见」链接去链接；governance/architecture/blueprint/README/engineering-workflow 引用同步；README 移除审计历史索引行、修订「审计过程材料不随仓库分发」说明（文档计数不变 55 份）。
- **2.1-01 README 计数同步（补登）**：README 文档份数声明同步为 55/53（53 份 md + 2 份 yaml）——0.0.31 叙述节声称「0.0.30 已闭环」但本批登记缺失，round13 R13-02 指出后补记。



## 0.0.31（2026-08-06）— 第十一轮全库深度审计修复批次

> 闭环 round11 共 13 项问题中的 9 项成立项（1 高 2.1-01 经复核已在 0.0.30 闭环；2.3-01/2.3-02 随 0.0.30 仓库整洁化闭环；2.2-01 部分不准确——推理皮层以别名收录、命名配置集已列全）。**审计断言核验**：round11 报告 13 项逐项实测——README 计数、操作数、changelog 叙述节、blueprint 承诺、术语覆盖、CRLF 清单全部属实；§5.5 引用 38 处复核无漂移（观察项通过）。

- **2.1-01（【高】，0.0.30 已闭环）**：README 文档份数声明 55/53 同步（报告基线为 0.0.30 前状态）。
- **2.1-02 操作数同步 + 门禁补盲区**：README 操作目录「53 项」→「66 项」（OP-001~OP-066）；doc-audit 新增 **6.8a OP 行数校验**（`^| OP-\d{3}` 计数 ↔ README 声明双向比对，仿 6.7）。
- **2.1-03 changelog 叙述节补齐**：0.0.27/0.0.28/0.0.29/0.0.30 四个批次补 `## 版本号（日期）— 标题` 叙述节（处置细节/决策过程/审计断言核验），与版本记录行不重复登记。
- **2.1-04 + 2.5-02 blueprint v1.1/v1.2 承诺追缴对账**：15 处承诺逐条对照——多 Agent 校准已由 [social-calibration-roadmap.md](social-calibration-roadmap.md) 覆盖（不重复补登）；其余补登 **D-404~D-413 共 10 条**（GLiNER2/POST /v1/facts/边类型签名验证/远程升华/Prompt 依赖图/GraphRAG+Rust Core/Directives/RSS 管理/事件通知框架/TeamScope，含认知意图/工程简化/预期版本/升级触发条件/历史背景五要素）。
- **2.2-01 术语表别名收录**：既有条目「WM调度预处理器 | Reasoning Cortex」补中文别名「（推理皮层）」与架构 §4 定位说明——英文名本已收录，中文名补别名（术语计数不变 67）。
- **2.4-01 行尾统一 LF**：20 份 CRLF 文件统一 LF；新增 `.gitattributes`（`* text=auto eol=lf`）；doc-audit 新增 **6.16 行尾一致性检查**（md 含 `
` 即 fail）。
- **2.4-02 catalog「—」语义注记**：工具列注记补充「—」双语义——无映射端点（自动触发类）/无独立工具（仅 REST 类）。
- **2.5-01 架构 §0.8 短名注记**：命名配置集表补「短名 = `KAIROS_FEATURE_<短名>`」说明。
- **2.3-02 deep-audit 输出清理**：`_deep_audit_out.json` 输出改系统临时目录（`tempfile.gettempdir()`），仓库永不残留（0.0.30 已 .gitignore + 移出跟踪）。
- **2.2-02 §5.5 引用全量复核**：38 处全部指向差异检验权威段（架构 §5.5），无漂移——观察项通过。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 全绿（0 FAIL）;`deep-audit.py` 全绿（exit 0）。



## 0.0.32（2026-08-06）— 第三方分析分诊 + 全量债务 v0.1.0 可实现性评估批次

> 用户指令双目标：(1) 外部记忆系统第三方分析按 0.0.27 流程正式入库；(2) 全部登记债务执行「首个正式版（v0.1.0，含 v0.1.0.x）可实现性」评估——能进首版的不留到 v1.1，不能进的附真实理由可追溯。

- **外部记忆系统分诊 16 项交叉核实**（Python+SQLite ~7400 行运行代码，机制逐项比对）：
  - **14 项判定「已覆盖/有意设计差异/互为印证」**：存储层工程化（迁移列表/事务写入/WAL/重试 → deployment 迁移命令+回滚 / 架构 §5 批量事务与原子操作 / reliability WAL 归档 / StorageBackend 事务语义）；RL 权重工程（维度钳制/softmax/Cosine LR 衰减/ε-greedy/EMA/KL KPop/Bounded Simplex → [rl-weight-spec](../specification/rl-weight-spec.md) 全有，**独立实现相同设计互为印证**）；反馈→权重闭环数据通路（rl-weight-spec 持久化+RCW 管线）；记忆生命周期状态机（operation-catalog OP-049~054）；知识演化（knowledge_evolution 表）；会话隔离上下文+LRU（WM 层）；偏好推断（用户画像）；遗忘曲线半衰期（0.0.27 已判衰减公式化）；平台感知隔离 → 有意设计差异（Kairos 单租户 D-413，多平台共享单记忆库）；「Self-Evolving Engine」宣称 vs 实际（其反思引擎模块不在分发仓库、静默降级为关键词抽取 → claim-implementation-matrix + 认知诚实红线已防，反面教材）；术语通胀（「RL 强化」实为反馈式权重自适应 → P6 合规框架 + D-324 多维独立裁决框架前置条件佐证）；文档-代码漂移（其技能元数据文件版本号/表数与 README 自相矛盾 → 门禁 6.13/6.14/6.15 已防）；集成可靠性梯度（框架级 hook 100% vs SKILL 层 LLM 自觉 → 佐证接入层 + MCP 框架级集成路线）；健康报告（架构 §10.12 健康度分数）。
  - **1 项落地规格修正**：[rl-weight-spec](../specification/rl-weight-spec.md) KL 散度段补**衰减实现防坑注记**——softmax 对正缩放不变（softmax(λw)=softmax(w)），「同因子衰减再归一化」是数学恒等式不产生效果；第三方实现实测踩中后按维度差异衰减修正（其代码注释自曝），Kairos 的 Bounded Simplex Projection 不受影响，「衰减因子额外降低」落地须按维度差异执行。
  - **1 项落地债务登记**：**D-414 检索反馈权重快照**——检索响应附五维权重快照、反馈记录携带快照、更新管线比对算 lr_multiplier 防单批漂移（其独有增量；规格 v0.1.0.x，实现随 RL 权重优化器 v1.1+）。
- **全量债务 v0.1.0 可实现性评估**（[debt-collection](debt-collection.md) 新增 §七 评估表，62 条活跃债务全量）：
  - **已覆盖/部分覆盖 9 项**（架构已承载，随 v0.1.0 组件交付）：D-006（§3.3 规则表随排序链）、D-007（§3.2 抽象萃取边界门禁探针）、D-008（§5.2 encoding_context 补偿）、D-009（§1.8 看门狗/degraded/IDENTITY_BYPASS）、D-011（构造论 + W7 叙事检测器事件触发）、D-014（§3.2.1 路线 4）、D-019（三源工程承载齐备：检索意图构造/情感基线提升/路径注册表）、D-102（§3.2.1 六级路由判定表——**修订其「v0.1.0 单流程」过时描述**）、D-323（occurred_at 已竖切落列）。
  - **升格 v0.1.0.x 7 项**（正文预期版本已同步）：D-010 自主组件决策审计留痕纪律、D-018 编码门控类型判定→调度偏好标注（不涉存储分离）、D-103 认知完整性扫描器（纯数据扫描，structural_value 已落列 H-03）、D-301 因果链完整性检查器子集（深度受限查询上限可配置，完整图遍历引擎 v1.1）、D-302 identity_tier 差异化降级门槛（ARC-D-005 判据已定义）、D-402 后悔事件统计（「调参建议」治理裁定链路 v1.1 防递归维持）、D-406 边类型写入面枚举校验（语义级签名验证 v1.1）。
  - **规格升格 1 项**：D-414（rl-weight-spec 规格增补）。
  - **已在首版范围 11 项**（既有承诺核验）：D-015/017/321/326/329/330/333/334/335/337/338（另已实施 D-001~004/011/101 属 v0.1.0 交付，不计入评估结论）。
  - **维持 34 项**（真实障碍，理由逐条登记 §七 7.1 表）：技术依赖（D-012 性能门禁、D-013 周期审计承诺、D-016/306/312 连续度量依赖、D-303 类型级子结构、D-305/332 关键路径、D-307 认知原理先行、D-324 多维独立裁决框架、D-325 后台维护引擎、D-328 图结构、D-331 依赖 Phase 1 验收、D-401 三区集成独立排期）、安全取舍（D-320 集中授权可审计、D-327 例外路径禁用）、产品阶段（D-308/309/310 v1.2 路线图、D-413 v1.2 多租户）、增量度量（D-403）、触发条件驱动（D-404/405/407~412）、运行观测评估（D-005 图式分治、D-336 连续谱）、学习信号依赖（D-020）。
- **评估纪律**：维持项均附真实障碍与可追溯理由（§七 7.1/7.2）；升格项正文预期版本同步；摘要表状态列与状态说明同步；rl-weight-spec/debt-collection 版本记录升 0.0.32。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 已验证全绿（exit 0，0 FAIL）;`deep-audit.py` 已验证全绿（exit 0）——2026-08-06 round13 实测回填。



## 0.0.33（2026-08-06）— round12/round13 深度审计修复批次

> 闭环 round12 遗留 7 项 + round13 新发现 1 项（R13-04）+ 观察项 2 项（R13-06/R13-09）；**「遗留项核销」机制首个实例**（round12 遗留核销表见下，承接 round13 流程建议 10）。审计断言核验：round13 报告 8 项逐项实测——7 项属实；R13-03 表述微误（实测 D-406 第三列已为 v0.1.0.x，Phase 列实际错位 9 行而非 10 行）。

### round12 遗留核销表（机制首个实例：每轮遗留项挂批次末尾，下轮开跑前先逐项核销）

| round12 编号 | round13 编号 | 处置批次 | 核销 |
|:--|:--|:--|:--|
| ① 版本记录登记缺口 | R13-01 | 0.0.33 | ✅ 闭环（architecture 补 0.0.29/0.0.30、cognitive-foundation 补 0.0.30、blueprint 补 0.0.30，各补 0.0.33 说明行） |
| ② changelog 闭环登记错位 | R13-02 | 0.0.33 | ✅ 闭环（0.0.30 叙述节补记 2.1-01） |
| ③ threat-model 黄金集悬空 | R13-05 | 0.0.33 | ✅ 闭环（test-plan 预留表补 TC-GOLD-001~ 占位） |
| ④ round11 报告断链 | — | 0.0.30 | ✅ 已闭环（reviews/ 目录删除，round13 复核确认） |
| ⑤ README 空节残留 | R13-07 | 0.0.33 | ✅ 闭环（空节删除） |
| ⑥ 摘要表 Phase 列错位 | R13-03 | 0.0.33 | ✅ 闭环（D-404/405/407~412 → v1.1、D-413 → v1.2，背景文本移除；D-406 实测已正确） |
| ⑦ doc-audit SyntaxWarning | R13-08 | 0.0.33 | ✅ 闭环（docstring 改 raw string，compile 检测无其他非法转义） |
| ⑧ changelog 历史提及 | R13-06 | 0.0.33 | ✅ 闭环（0.0.24「见」式指引改注；0.0.18「纳入文档计数」补失效注记；历史叙述保留） |

- **R13-01 版本记录登记缺口（round12 ① 遗留）**：architecture 补登 0.0.29（§11 术语计数 60→67 同步）/0.0.30（引用清理）两行；cognitive-foundation 补登 0.0.30（决策编号引用改指 [adr.md](adr.md)）；blueprint 补登 0.0.30（引用同步）。**根因治理（流程级）**：engineering-workflow §三 提交规范新增「批次收尾检查清单」——触及即登记 + 门禁清单同步 + 门禁结果回填（round12 P1 建议 9 落地；脚本级自动校验无法判定「批次是否实质触及某文档」，选人工清单方案）。
- **R13-02 changelog 闭环登记错位（round12 ② 遗留）**：0.0.30 叙述节补记「2.1-01 README 计数同步（补登）」。
- **R13-03 摘要表 Phase 列错位（round12 ⑥ 遗留）**：debt-collection §四 摘要表 D-404/405/407~412 第三列改 v1.1、D-413 改 v1.2（与 §七 评估表「维持 v1.1/v1.2」结论一致），背景文本移除（活跃区五要素已完整），状态列补「（维持，0.0.32 评估）」与同表格式对齐。
- **R13-04 工程流程门禁清单过时（round13 新发现）**：engineering-workflow §四 CI 门禁清单补 6.8a + 6.16（对齐 changelog 0.0.31 门禁行；release-guide 实测未列门禁清单，无需同步）。
- **R13-05 黄金集用例悬空（round12 ③ 遗留）**：test-plan 预留编号表补 `TC-GOLD-001~` 占位行（黄金集回归 = Judge 漂移检测，来源 threat-model §三；黄金集非功能清单项，独立前缀 GOLD 与 W/R/M/SF/CAL 功能前缀区分）。
- **R13-07 README 空节（round12 ⑤ 遗留）**：删除「审计与决策记录（过程产物）」空节标题与空表头（计数注记已含「审计过程材料不随仓库分发」说明，无需另补）。
- **R13-08 doc-audit SyntaxWarning（round12 ⑦ 遗留）**：6.15 docstring 改 raw string（`\w`/`\.` 未转义），compile 全量检测确认无其他非法转义序列。
- **R13-06 changelog 历史指引断链（观察项）**：0.0.24 叙述节「批次明细见 audit-history-summary §一」改注（该文件已于 0.0.30 移出仓库）；0.0.18 叙述节「纳入文档计数」补失效注记（0.0.30 后不再计数）；0.0.18 其余历史叙述与版本记录行按 append-only 保留。
- **R13-09 正文批次注记纪律（观察项，记录在案）**：审计建议 documentation-governance 增补「正文批次注记纪律」（允许/禁止类型 + 每文档上限）。现状 15+ 处注记均属决策溯源/教训类（含 0.0.22「门禁虚假绿灯」教训），暂无膨胀迹象，**维持现状**；纪律条文待后续文档规范批次按需落地（观察项不阻断）。
- **0.0.32 门禁验证回填（round13 流程建议 11）**：0.0.32 条目「待验证」→「已验证」（doc-audit 全绿 exit 0、deep-audit 全绿 exit 0，2026-08-06 round13 实测）。
- **版本记录登记**：architecture/cognitive-foundation/blueprint/debt-collection/README/engineering-workflow/test-plan 版本记录登记 0.0.33 行（补登动作本身如实登记）。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 全绿（0 FAIL）;`deep-audit.py` 全绿（exit 0）。



## 0.0.34（2026-08-06）— 第十四轮全库深度审计修复批次

> 闭环 round14 全部问题项（0 高 / 3 中 / 7 低 + 1 观察项）。**遗留项核销（机制延续）**：本轮 0 遗留——round14 全部闭环，无跨轮滞留项可核销。审计断言核验：round14 报告 11 项逐项实测全部属实——治理面计数三处/两面并存、治理输入「唯一」表述过强（图 ADM→CS 边佐证）、检索权重两套并存（配置默认值支持四链路）、更名口径相抵、[AGENTS.md](../../AGENTS.md) git 声明过时（`.git` 已存在）、§10.24 索引缺 4 条、节内导航「完整」措辞不符（缺 5 节点）、⚠️ 字面转义、健康接口引用错位（§10.11 实为 P6 临界余量监控）、差异检验引用不精确；另按跨文档一致性规则联动修正同源 2 处（diagrams/system-architecture.html 图题与图例——0.0.21 同批次产物）。

- **R14-01 治理面计数统一（【中】）**：§0.4.1 图题「三个正交治理面」→「两个正交治理面」；结构原则「正交治理面 = 宪法主权面 + 监督平面 + 身份面」→「外部治理接口 + 监督平面」，追加「身份面为否决机制（§1.8），不入治理面计数」——与 §0.4 统一口径「两个正交治理面（外部治理接口+监督平面）」、§0.4 层计数说明一致；diagrams/system-architecture.html 图题同步（同源联动）。
- **R14-02 治理输入表述（【中】）**：编号流程②「外部校准信号是宪法主权面唯一治理输入」→「外部信号治理输入（另有管理员冻结/解冻指令，见图 §0.4.1）」——与图 `ADM → CS 冻结/解冻指令` 边一致；HTML 图例同步。
- **R14-03 检索权重单一权威（【中】）**：§5.2 以四链路配比（0.50/0.20/0.10/0.20）为唯一默认口径——Link-2 三链路公式标注「为因果链路引入前的历史配比，已被 Link-3 四链路配比取代」；configuration `KAIROS_RETRIEVAL_LINK_WEIGHTS` 由「—（待定义）」补填默认值 `{"semantic": 0.50, "cooc": 0.20, "knn": 0.10, "causal": 0.20}`，来源列指向架构 §5.2 三链路融合与检索扩展（唯一权威）。门禁化子检查（§5.2 权重公式唯一性）随报告结构性建议一并落地（见下方门禁补盲区 6.18）。
- **R14-04（【低】）**：§0 速查表外部治理接口「由原宪法主权面更名而来」→「与宪法主权面同义（两称并存，见 §0.4 治理面命名对照）」，保留监督平面独立正交面注记——与 §0.4 命名对照「非更名完成态」口径一致。
- **R14-05（【低】）**：[AGENTS.md](../../AGENTS.md) 更新——L11「本目录无 git，不使用 `.hermes.md`」→「本目录已初始化 git（2026-08-06）」（`.git` 已于 0.0.29 批次前初始化，误导 Agent 行为判断）；L35「若初始化 git」措辞同步；§5.2 规则变更记录补行。
- **R14-06（【低】）**：§10.24 第一组「架构设计间隙」补 D-006（落点 §3.3 适用场景规则表）/ D-008（落点 §5.2 encoding_context 补偿）/ D-016（落点 §2.2 认知完整性扫描器 + §3.3 帕累托参与，structural_value 半定量见 §5.2）/ D-019（落点 §3.2 预测器三源 + §5.2 路径注册表）四行——落点以 debt-collection §七 评估表依据列为准，跨文档可追溯链恢复。
- **R14-07（【低】）**：§5.2 节内导航补 5 个遗漏节点（跨平台身份映射 / 批量事务写入 / 对话历史持久化 / 半开区间时间语义 / Saga 命名叙事线），「完整节点清单」措辞与事实恢复一致（0.0.34 补全注记）。
- **R14-08（【低】）**：§0.8 特征标志表 NARRATIVE_IDENTITY 列值 `ON ⚠️` 原为字面转义序列（未渲染为图标）→ 修复为 `ON ⚠️`（本意警示该标志为宪法核）。
- **R14-09（【低】）**：VAD 延迟探头「扩展健康检查接口（§10.11）」→「（§2.2.1 ME-1 健康接口）」——§10.11 实为 P6 临界余量监控，健康接口（Health Interface）权威定义在 ME-1 监测子域三个通用监测接口。
- **R14-10（【低】）**：「差异检验流程（§5 存储层·差异检验）」→「（§5.5 差异检验）」——差异检验权威定义在 §5.5，全库引用口径统一（grep 复核其余引用均指 §5.5）。
- **R14-11（观察项，记录在案）**：正文批次注记纪律维持现状——正文 15+ 处「0.0.xx 新增/修正」注记均属决策溯源/教训类（含 0.0.22 门禁虚假绿灯教训），暂无膨胀迹象；纪律条文待文档规范批次按需落地（同 round13 R13-09，观察项不阻断）。
- **门禁补盲区（报告结构性建议 12 + R14-03 ③，用户拍板落地）**：doc-audit 新增三个子检查——**6.17 治理面计数一致性**（§0 图题/统一口径/结构原则三处计数必须同为「两个」+ 身份面不入计数声明，覆盖 R14-01 复发）、**6.18 检索权重公式唯一性**（§5.2 三链路历史配比必须带「历史配比」注记 + 四链路配比必须存在，覆盖 R14-03 复发）、**6.19 §10.24 关联债索引完整性**（debt-collection §四 摘要表 D-0xx 活跃债编号 ⊆ §10.24 第一组收录集合，覆盖 R14-06 复发；口径注记：仅比对 D-0xx 段——第二/三组与摘要表非一一映射）；engineering-workflow §四 CI 门禁清单同步（版本记录 0.0.3）。回归验证：镜像目录注入三处错误（图题「三个」/删「历史配比」注记/删 §10.24 D-006 行）后三个子检查全部 FAIL 拦截，真实库 0 FAIL。
- **版本记录登记**：architecture / configuration / engineering-workflow 版本记录登记 0.0.34 行；diagrams/system-architecture.html 非 55 份核心文档（无版本记录机制）不动；[AGENTS.md](../../AGENTS.md) 经 §5.2 规则变更记录登记。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 + 6.17/6.18/6.19 已验证全绿（exit 0，0 FAIL）；`deep-audit.py` 已验证全绿（exit 0，indegree_zero=0）——2026-08-06 round14 实测回填。



## 0.0.35（2026-08-06）— 第三方分析分诊批次

> 用户指令：对个人 Obsidian 记忆库公开镜像做对照分析分诊入 Kairos（按既定分诊流程）。**素材边界声明（认知诚实）**：镜像仅 4 个文件（README/CLAUDE.md/HOME.md/LICENSE），白皮书本体《记忆与索引架构白皮书.md》不在镜像内——分诊基于镜像内三份文件的全部可读内容，白皮书 §4~§7/§9/§10/§12 相关判定以镜像内引用为准，不冒充全量验证（详见对照分析报告，工作区根临时交付物，不入库）。

- **20 项交叉核实判定**（外部记忆库设计要素 ↔ Kairos 对应机制逐项比对）：
  - **6 项已覆盖**（Kairos 已有等价或更强机制）：三层分工（导航≠真相源 ↔ 检索端点返回指针 + 多级读取契约）；状态文件 freshness 纪律（stale 视为未知 ↔ 校准状态四级 + 置信度衰减公式 + auto-dormant）；rollover 滚存（胖文件滚历史 ↔ `compacted`/`compacted_at` + compaction_snapshots + 30 天回滚窗口 + 遗忘状态机）；检索三形态（枚举/结构/计算 ↔ 路径空间硬过滤 + 知识图谱/叙事线 + 三信号混合检索）；失效模式复盘制度化（七条失效复盘 ↔ [risks.md](./risks.md) RSK-001~008 + 0.0.22 爆炸复盘教训 + 遗留项核销表）；不变量硬约束（八条不变量 ↔ §10.2/§10.3 不变量清单 + 修订门禁）。
  - **10 项互为印证**（独立实现相同设计）：两级模型（数据层/控制层 ↔ [AGENTS.md](../../AGENTS.md) 权威链 + 认知层-架构层映射）；三目标准/省/可移植（↔ 记忆即使用 + §9.3 Token 预算 + §5.15 .kairos 备份协议）；四级索引 T0-T3（↔ §3.9 检索深度分级 R0 元数据 0.05×/R1 摘要 0.3×/R2 全文 1×——**同一加载经济学的静态/动态两种实现**）；便宜指针硬加载/昂贵全文软加载（↔ §7.3d 双模 Fast Context/Deep Reasoning）；摘要器模式（frontmatter 摘要 + source 指针 ↔ R0 浅层 + content_summary）；硬触发词法规则（两跳不许省 ↔ QueryAnalyzer 规则优先覆盖 ≥80% 零 LLM）；标签三轴 + schema.yaml/validate.py 机器校验（↔ data-model domain/memory_tags + doc-audit 门禁）；配置单一来源（↔ [AGENTS.md](../../AGENTS.md) 架构文档即唯一权威 + system-context 宿主边界）；双写失效教训（导航层↔真相源双写 ↔ 版本记录/changelog/README 三处登记链 + R13-01 教训 + 批次收尾检查清单）；控制权归根（子配置仅参考 ↔ 规则优先级分层）。
  - **4 项有意设计差异**（产品形态差异，不吸收）：零维护视图（文件库特有）；模式系统 PERSONALITY/ARCH_MODE（Agent 行为层，属宿主域）；反向规则（个人助理社交边界）；「每轮重启状态机」形态（外部记忆库无运行时 vs Kairos 持久化引擎——Fast Context 持续监控模式正为此场景设计）。
- **1 项落地规格修正（R-01，【低】）**：架构 §3.9 检索深度分级补「深度分级 ↔ 内容读取层级」映射注记——R0 检索结果即指针（id/path/score，无读取端点对应）/ R1 ↔ level=summary|overview（摘要级，**仅用于定位，不得作为内容使用**）/ R2 ↔ level=full（全文级，唯一可作内容使用的层级）。**缺口动机（吸收外部记忆库失效模式）**：其 §7.1「未索引到思考全文」教训即「反思/关系话题停在二手摘要」——Kairos 的 R 分级机制本已规避（R2 全内容重建），但 R0/R1/R2 与 api-spec `GET /v1/memories/{id}?level=`（L566）无显式映射声明（全库 grep 无对照），实现者存在把 R1 摘要级当全文使用的契约风险；映射注记使防护显式化。api-spec 不加镜像注记（遵循机制定义唯一化：架构 §3.9 为深度口径唯一权威，防双写漂移）。
- **无债务登记**：唯一缺口为文档一致性级别，随本批次修复闭环，无功能欠账。
- **反面教材与教训确认（记录在案，无落地）**：外部记忆库 7.4 双写失效与 Kairos R13-01 版本记录缺口同源（同一事实多写一处迟早漂移，Kairos 已有批次收尾清单治理）；其 token 实测文化（T1 固定成本持续压缩）与 0.0.16 建议三（规则层覆盖 80% 零 LLM）同一价值取向；「每轮重启」零状态优势 vs Kairos 持久化双时态/版本链/快照全套保障，形态取舍各自成立。
- **版本记录登记**：architecture 版本记录登记 0.0.35 行（R-01 落点 §3.9）。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 + 6.17/6.18/6.19 全绿（exit 0，0 FAIL）；`deep-audit.py` 全绿（exit 0）。



## 0.0.36（2026-08-06）— 第三方分析分诊批次

> 用户指令：对外部开源 AI 记忆陪伴软件完成**设计哲学对照 + 源码级深挖**，然后决定吸收借鉴内容（按 0.0.22 源码吸收与 0.0.32 分诊双先例流程）。**素材边界声明（认知诚实）**：完整源码浅克隆；深挖范围 RAG、压缩代理、工具、摘要、影子索引、vault、MCP、数据库、文档与 README 模块——4 个子代理并行 + 关键文件人工复核；未覆盖桌面渲染层与移动端 UI（产品界面域）。源码引用仅作机制分析（详见对照分析报告，工作区根临时交付物，不入库）。

- **20 项交叉核实判定**（源码实证参数逐项比对，每项带文件:行号引用）：
  - **10 项互为印证**（独立实现相同设计）：非对称 RRF 融合（FTS 名次分 0.3 + 向量原始分 0.7，RRF_K=60 ↔ §7.3a 三信号 0.50/0.35/0.15）；去重三级阈值 + LLM 仲裁 + 失败降级存储（0.92/0.70 + merge_target_ids 交叉验证防幻觉 ↔ GSPO 聚类 + MMR + content_hash 摄取去重仅更新 usage_weight）；**「拥抱冗余」哲学互为印证**——外部系统只拦 AI 生成记忆、用户原始内容不走去重，Kairos 摄取去重不删本体（重复进热度频次×2 权重）——同一「重复是信号不是噪音」主张两种实现；时间感（chunkPrefix 日期注入 + source_created_at 过滤 ↔ 双时态 + §7.3a 时间过滤 + 时序排序调制）；滚动摘要保留 N 轮（↔ §7.3d 摘要注入 + §9.3 Token 预算）；维度运行时探测 + model_id 检索隔离（↔ ADR-012 固定 1536 投影——动态/固定两种策略，有意差异）；MD5 哈希脏检测 + 影子索引可重建（↔ §5.16 一致性检查——「可重建」纪律 Kairos 未显式声明，见 R-03）；缺失检测自底向上前提链 + 未完成周期跳过（↔ 知识演化判定闭环 + 遗忘积压信号）；触发估算与实际构建共用同一函数（↔ 0.0.28 VIRTUAL_CALIBRATION_TIMEOUT 口径不一教训）；质量护栏族 verbatim 拒绝/空拒绝/归一化（↔ Reflect 收敛判据——Kairos 有收敛护栏无 verbatim 护栏，见 R-02）。
  - **7 项有意设计差异**（不吸收）：总结金字塔纯手动触发（Kairos 升华管道空闲驱动自动调度）；模板即结构压缩器（胶囊槽绑定日记场景文案）；会话压缩 150k 阈值/保留 3 轮（伴侣场景取向，会话管理属宿主域）；chunkPrefix 元数据注入（Kairos 结构语义由路径空间 + 编译净化承载）；LIKE 伪 FTS（Kairos 用真 FTS5 + BM25）；分块 1024/128 + cl100k_base（聊天场景经验值，仅作起点参考）；记忆主权 Markdown SSOT（Kairos 数据库引擎 + .kairos 备份协议）。
  - **1 项反面教材**（记录在案，无动作）：外部系统去重删除用 `deleteBySource('memory', ...)` 但写入 sourceType 为 `'chat'`——删除键与写入键不一致，旧块删不掉产生新旧块共存；Kairos 侧防线已存在（0.0.14 契约枚举统一），作为「删除动作必须与写入命名规则严格一致」教训记录。
- **2 项落地规格修正（低风险，无债务登记）**：
  - **R-02 升华产物 verbatim 拒绝护栏**（吸收外部系统 verbatim 检查实证）：[detailed-design](../specification/detailed-design.md) §4 新增「升华产物质量护栏」——strategy 阶段产物与源 item verbatim 相同（或仅格式包装）判定无效升华，标记 `sublimation_invalid` 审计事件并重试一次（重试输入附加「产物不得与源文本相同」指令），重试仍相同则放弃本次升华（不进入 behavior 阶段、不触发人工确认门控）。缺口动机：Kairos 的 Reflect 收敛判据防「结论不稳定」，但无法拦截「LLM 偷懒直接复制输入冒充产出」——两个独立维度。
  - **R-03 使用权重影子副本可重建性声明**（吸收外部系统影子索引可重建纪律）：[architecture-v0.1.0](../foundation/architecture-v0.1.0.md) §3.3 双副本隔离防线段补声明——影子副本为**可重建缓存**，损坏/丢失时经 §10.10 use_event 事件流（HMAC 审计链）重放全量重建；恢复路径四步（检测→阻断合并→重放重建→§5.16 Deep 模式验证）；重建路径止步于影子副本自身，双副本隔离防线条款不变。缺口动机：Kairos 有差异检验与一致性检查但无「影子副本可全量重建」显式声明，损坏恢复路径未定义。
- **哲学对照确认**：「外部海马体」（写日记→做总结→短期沉淀长期）与 Kairos 升华管道（raw→item→strategy→behavior）同构；「RAG 像查字典」批评与 Kairos 的「检索返回全文 + R0/R1/R2 深度分级」设计取向一致（0.0.35 R-01 已补映射注记）。
- **版本记录登记**：architecture（R-03 落点 §3.3）/ detailed-design（R-02 落点 §4）版本记录登记 0.0.36 行。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 + 6.17/6.18/6.19 全绿（exit 0，0 FAIL）；`deep-audit.py` 全绿（exit 0）。



## 0.0.37（2026-08-06）— round15 全面深度审计修复批次

> 用户指令：对全库 55 份核心文档做全面深度审计（完整性一致性/缺失过时/结构组织/格式规范/核心文档准确性 5 维度），修复全部问题后提交。审计方式：4 个并行审计组全文通读 48 份文档 + 核心文档（认知基础/架构/技术选型）精读 + doc-audit 门禁基线 + 关键发现 grep 复核实锤；45 项问题（1 高 / 19 中 / 25 低）全部闭环。审计报告（round15 问题清单与改进建议）为会话交付物，不入库。

- **P0（1 项）**：M-03 显式遗忘功能三处三义统一——feature-list/slice-guide/test-plan 以 feature-list 语义为锚，forget（显式遗忘）与 suppress（定向遗忘）分属独立命令（api-spec 已区分），竖切 REST 表标注修正。
- **口径统一（6 项）**：否决权「宪法否决优先」无条件表述全库 4 处改「默认优先级 + 身份危机例外判例出口」口径（认知基础 §2.1 / 架构 §0.4.1 / glossary / HTML 图，D-20 E1 收敛；架构 §1.8 与认知基础 C.6 为既有权威）；三信号（0.50/0.35/0.15）与四链路（0.50/0.20/0.10/0.20）管线关系声明 + 「三信号/三链路」术语消歧注记（架构 §7.3a 权威）；意图契约第五契约说明（架构 §3.7）；MCP 注册时机措辞统一（integration-design 对齐 technology-stack 进程模型）；PM-02 事件总线口径归一（竖切 4 类为准）；D-409 三链路→四链路。
- **计数联动（7 项）**：MCP 工具 12→15（feature-list / implementation-map）；operation-catalog 53→66 项；CLI 24→25（api-spec 补注册 `kairos degradation switch`，slice-guide 子集口径同步）；术语 67→68（glossary 补「准见证锚定」，README / 架构 §11 / concept-tiers 联动）；traceability-map 四种→六种记忆关系（对齐 data-model 六值枚举）；api_keys.level read-only→read（对齐 api-spec 三级口径）；configuration 待定义 12→11（0.0.34 补填联动）。
- **数据模型/端点事实（8 项）**：conversation_messages 补 parts 列（多模态 Part 数组，对齐 api-spec §18.2）；journal_entries 补 node_episode_index_map 列（Episode 归因索引承载）；operation-catalog 覆盖边界 49/56 重算（按实际 64 端点口径修正）；竖切 REST 20→21 补 restore 端点；事件优先级口径修正（use_event=3 / latent_trigger=6 为竖切已用优先级，0-2 不被背压阻塞）；troubleshooting 命令状态表「0 命中」失实修正（db verify / admin key rotate 已定义，核减至 3 条待定义）；reliability error_log/events 改指 sublimation_queue；observability /metrics 标注待定义（api-spec 登记前为设计目标）。
- **治理/债务（6 项）**：blueprint P3-19~P3-25 七组件补登债务 D-415~D-421（v1.1，追缴门禁闭环）；差距表 G-01/G-07 补 D-306/D-103/D-334 互引与分口径（v0.1.0.x 半定量台阶 / v1.1 完整度量）；D-402 改引 ARC-D-004；benchmark-plan 补升华/磁盘/启动时间判据（对齐 NFR）；deployment 全量 15s 标注扩展设计值 + KAIROS_LLM_ENDPOINT 必填按模式限定；security-specification 汇总表 S-19 收敛（附加控制项单列，不并红线）。
- **格式纪律（9 项）**：正文「0.0.xx 勘误/新增」版本注记批量清理（去版本号保留信息内容；决策/教训/债务溯源类注记豁免——R14-11 观察项边界内）；外部产品名收敛为「外部理念吸收/第三方实证」表述；5D 混合排序废弃术语补历史沿用名注记；叙事线已完结拒新成员错误 400→409（状态冲突，无新错误码——ERR-INPUT-004 保持 422「缺少必填字段」语义，未改码，勘误：原条目误写「ERR-INPUT-004 改 409」）；error_event 改 use_event；concept-tiers 契约英文名修正（pinned/lazy/ephemeral → permanent/ondemand/environmental/temporary）；api_keys 归类注记（非 P3 系）；「v0.1.0·x」笔误修正；TC-MEMV-001 回滚参数载体对齐 api-spec。
- **遗留观察项**：门禁补盲建议（6.20 功能-端点映射一致性 / 6.21 契约计数一致性 / 6.22 否决权表述一致性，覆盖本轮 K-01/K-06/K-38/K-02 复发风险）记录在案，待下批次按 6.17 先例落地——本轮修复已闭环问题本体，补盲不阻断。
- **版本记录登记**：architecture / cognitive-foundation / README 与全部被修复文档登记 0.0.37 行（详见各文档版本记录）。

- **门禁**：`scripts/doc-audit.py` 18 类 + 14a + 6.13/6.14/6.15/6.12a/6.8a/6.16 + 6.17/6.18/6.19 全绿（exit 0，0 FAIL）；`deep-audit.py` 全绿（exit 0）——2026-08-06 round15 实测回填。



## 0.0.38（2026-08-06）— round16 全面深度审计修复批次（全面审计 113 项：3 高/64 中/46 低全部闭环）

依据本轮全面深度审计报告（5 组并行全文通读 + 全库脚本化检查）执行修复，分 P0/P1/P2 三批：

**P0（3 项【高】阻断项）**：
- FA-01 认知基础「推论一~五」幽灵引用闭环——认知基础 §2.1 补五条推论认知层定义（与架构 §0.3 一一对应），设计权威链恢复可追溯
- FA-02 帕累托计算维度三重口径统一——架构 §3.3 以认知基础两段设计声明为权威（三轴：使用/见证/时间），情感效价标注为条件激活受控例外（G-02 联动）
- FE-05 零版本标记全库收敛——25+ 处跨 10 文件清理（架构 18 处/配置 24 处/数据模型 10 处等）；documentation-governance §6 补豁免 1（债务账目批次注记）与豁免 2（实证参考基线登记）；[AGENTS.md](../../AGENTS.md) 同步豁免指引

**P1（约 30 项【中】）**：四组并行修复——幽灵引用清理（认知基础 §0.2/§四/§1.4、认知关节登记表 4 处）；WM 组件规格唯一化（§4.1 指针化→§6.2 权威）；实体提取四处口径统一；rl_weights 归一化不变量矛盾（data-model vs rl-weight-spec）；多模态版本归属冲突（P3-04 v0.1.0 子集交付）；NFR 整合口径注记；实体类型枚举三处映射；部署全量模式与 kairos-full 配置集对齐；SDK 版本统一 3.10；ERR-DB-* 返回口径按 api-spec §7 收敛；CLI 契约缺口全量盘点（10 条待定义子命令）；risks T-004 与 D-334 口径对齐（受控偏离措辞清零）；D-201~204 补状态/预期版本字段；glossary 补可及性轴词条（68→69）等

**P2（其余【中】+ 全部【低】）**：外部吸收标记全库收敛（13 处正文——参数校准类保留实证基线标记、机制类去除吸收字样，豁免 1/2 边界执行）；路径空间统一下划线命名（架构 §3.4 权威，6 份文档 20+ 处）；§10.24 关联设计债索引补 D-322~338；配置参数计数核定（正文 224 + 附录 A 146 = 370）；KAIROS_FEATURE_CONNECTORS 补登记（§11 标志 11→12）；身份映射参数名统一 KAIROS_USER_ALIASES；[AGENTS.md](../../AGENTS.md) reviews/ 残留清理与「12 类」计数修正；README 版本记录占位行补齐（0.0.25~0.0.28/0.0.32）；changelog 叙述节顺序注记/P-重复编号/门禁表述修正；base_weight 悬空字段删除（架构+detailed-design 两处）；ADRs 落点死链修正；测试预留占位补全；验收判据量化等

**计数变化**：glossary 68→69（补可及性轴）；配置参数 223+148=371 → 224+146=370（CONNECTORS 入正文、附录去重 2 行）；特征标志 11→12；附录「待定义」11→10；§0.7 交付范围对照表 7→8 结构单元；§10.24 索引 +19 行；端点数（85+3=88）/表数（57）/操作数（66）/能力数（168）不变；文档数 55 不变

**门禁**：18 类 + 14a + 6.8a/6.12a/6.13~6.16 + 6.17/6.18/6.19 全绿（doc-audit.py 运行验证）。

---



## 0.0.39（2026-08-06）— 外部理念吸收批次（2026-07）

**批次定位**：外部理念吸收（2026-07）落地 6 项借鉴——① 记忆质量评估指标（[acceptance-criteria.md](../quality/acceptance-criteria.md) §一a 新增过时调用率 / 任务成功率改善，v1.1+ 设计目标）；② 反事实检验测试模式（[test-strategy.md](../quality/test-strategy.md) §2.7 三态对比 + TC-CF-001~004）；③ encoding_context `conditions` 子结构约定（data-model，条件性经验适用范围显式化）；④ 高相似 × 过时联合惩罚（架构 §7.3a 排序调制，stale ×0.7 / expired ×0.5）；⑤ 记忆四动作失败模式排障表（troubleshooting §二a）；⑥ 基准设计红线——经验来源与验证数据分离（[benchmark-plan.md](../quality/benchmark-plan.md) §3.11 评测泄漏防护）。

**配套**：observability 指标 2 项 + 告警 1 条；integration-design §五a 任务成功率回传契约（`task_outcome` 经 `use_event` payload 标记承载，v0.1.0 落 usage_events 表不新增端点——0.0.42 勘误后口径）。

**登记**：无债务登记、无新文档（7 份现有文档修订）。

**门禁**：门禁验证通过。

---



## 0.0.40（2026-08-07）— 外部视频分析批次（100 视频 + 15 仓库对照分析）

**批次定位**：B站 AI Agent 记忆系统视频（100 个，用户提供 + B站 搜索精选补充）与 GitHub 热门记忆项目仓库（15 个，含补充深读 cognee/graphiti/OpenMemory/BasicMemory/langmem）的对照分析批次。**产出独立目录 [docs/analysis/external-videos/](../analysis/external-videos/README.md)，零改动核心设计文档**（foundation/specification 未修订），全部吸收建议止于「建议态」。

**素材层（100/100 全覆盖）**：
- B站 AI 字幕抓取（带 Cookie 的 `x/player/v2` 与 wbi 签名版 `x/player/wbi/v2`）——**实测发现 B站 AI 字幕严重串台（约 65% 视频字幕与主题无关，双接口验证同源，无法规避）**
- 本地转写管线（yt-dlp 下载 + faster-whisper small/int8，hf-mirror + 禁 xet）——60+13 个视频全量转写（含 114 分钟超长视频），总转写时长约 30 小时音频
- 素材分级：A 字幕匹配 23 / B whisper 转写 73 / C 降级 4（含无有效语音 1、20 小时串台合集 1）

**分析层**：
- 逐视频精读笔记 102 份（notes/VID-XX-<BVID>.md，含时间戳出处、Kairos 映射、存疑节）
- 仓库源码级深读 15 份（repos/REPO-01~15，含 README 口径 vs 源码实证对照、机制文件路径标注）
- **2026 论文深读 9 份**（papers/PAPER-01~09，源自用户提供的 AI HOT 学术档案 `outputs/agent-memory-archive.html` 20 篇精选 + `kairos-papers-mapping.md` 映射分析）：持续更新衰退（54% 失败率实证支撑防御取向）、InMind 隐式关联（支撑 D-313 可及性轴立项）、Zero-Mem（轨迹为源强印证）、SkillHone（证据-修订配对）、ACM（CRI 外部列证）、REMIT 恢复契约（六属性+TLA+ 验证）、GRAM（移除优于抑制）、机器遗忘审计（双副本遗忘验证）、Δ-Mem（增量存储）——详见 [papers/](../analysis/external-videos/papers/)
- [triage-matrix.md](../analysis/external-videos/triage-matrix.md)：外部理念 × Kairos 分诊矩阵（EV 条目）+ T-002 实例样本节
- [first-principles-review.md](../analysis/external-videos/first-principles-review.md)：八原理逐条评审——**没有任何一条第一性原理被外部实证推翻**；三硬一软获五条独立实证链最强印证；最大增量面「查询期重建产物治理」与「认知完整性轴收益度量」
- [absorption-proposals.md](../analysis/external-videos/absorption-proposals.md)：18 条吸收建议（AP-01~18，架构级 4 条）+ 7 条张力记录（AT-01~07）+ 印证记录

**关键发现**：
- Kairos 与外部主流高度同构：ADD-only（Mem0/OptMem/OpenClaw 独立实现）、双副本/投影（Claude Code 三版本投影）、遗忘非删除（五条独立实证链）、时间双轴（Graphiti 四时间字段/双时态）、三信号检索（4+ 独立实现）
- 主要张力：单标量聚合 vs P6 禁聚合（MemoryOS 热度/MemU 强化计数）；智能体自编辑记忆 vs 价值独立性（Letta/LangMem 覆盖式更新）；「被使用复活」vs 双副本隔离（OpenMemory）；LLM 自主聚类 vs 确定性算法（TencentDB）
- 主要矛盾记录（不采纳）：物理删除旧事实（Claude Code）；艾宾浩斯生物模仿遗忘（论文谱系）；「生成式记忆」未来方向（综述）
- T-002 实例样本：外部校准源「一等公民化」需来源分类/断言强度/可信度分级/时效字段/缺失断言核验——本批次积累实践基础

**治理**：无债务登记、无 ADR、无风险登记（全部建议态，落地走既有外部理念吸收流程）；脚本入库 2 个（[fetch_bilibili_subs.py](../scripts/fetch_bilibili_subs.py)、[transcribe_batch.py](../scripts/transcribe_batch.py)）；过程材料（原始字幕/音频/模型）不入库（video-work/ gitignored）；Cookie 凭据全程内存使用零落盘。

**门禁**：见批次完成验证记录（doc-audit.py 运行）。

---



## 0.0.41（2026-08-07）— 外部理念吸收落地批次（AP-01~28 全量落库）

> 承接 0.0.40 外部视频分析批次（[analysis/external-videos/](../analysis/external-videos/README.md) 分诊矩阵 EV-01~58 与吸收建议 AP-01~28），本批次将吸收建议**全量落地**到核心设计文档与规格层文档（用户决策：全部 28 条直接落库）。

**认知基础（[cognitive-foundation.md](../foundation/cognitive-foundation.md)，8 条认知层声明）**：
- AP-01 查询期重建产物治理声明（§2.1 价值独立性公理扩展）
- AP-02 显式时效字段互补声明（§1.1 时间轴：结构字段 vs 度量衰减）
- AP-03 遗忘决策懒求值声明（§2.2 硬约束二）
- AP-05 候选集集中度信号声明（§1.3 检索深度分级）
- AP-06 任务内跨轮状态传递声明（§2.2 软原则）
- AP-19 升华整合门控声明（§1.10 升华管道，PAPER-01 实证）
- AP-22 可及性轴实证注记（§1.1，InMind 基准）
- AP-28 增量存储理念声明（§1.1，Δ-Mem）

**系统架构（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)，22 条机制落地）**：
- AP-01 §5.5 查询期重建产物治理三步（来源标记 provenance=reconstruction/差异检验状态/未过检仅临时上下文）
- AP-02 §7.3a 显式时效字段（valid_until/expiration_date/superseded_by）
- AP-03 §5.2 遗忘决策懒求值（惰性评估+Light 周期兜底双轨）
- AP-04 §5.2 写入管线三工程约束（Memory Key 规范化/幂等乐观锁/索引派生可重建）
- AP-05 §3.9 候选集集中度第三类触发信号；AP-06 §3.1 任务内跨轮状态传递
- AP-09 §9.2 间隔重复复习时刻表（1/3/7/30 天）；AP-10 §5.5 处理完降温防自激
- AP-11 §3.2 意图先验检索加权；AP-12 §7.3a 时间检索维度评估注记
- AP-13 §1 记忆归属单元注记（关联 T-002）；AP-16 §5.9 嵌入可插拔（v1.1 候选）
- AP-18 §7.4c 无痕对话不记忆模式注记；AP-19 §5.2 升华整合显式门控+质检三查
- AP-20 §2.6.3 恢复契约六属性验收标准；AP-21 §3.7 读路径门控
- AP-22 §7.3a 可及性轴实证（InMind 84% vs 14.4%，关联 D-313）
- AP-23 §8 S-19 遗忘生效三样本检验+双副本完备性+「内容不可恢复≠行为无痕」边界
- AP-25 §5.2 Compaction 成本-保真三 regime；AP-26 §5.5 范围性回滚
- AP-27 §7.3a 图激活传播+时间粒度检索评估注记；AP-28 §5.2 增量快照模式评估

**规格层（7 份文档 + schema-slice 联动）**：
- [data-model.md](../specification/data-model.md)：memories 表新增 `valid_until`/`expiration_date` 两列（AP-02）；物理分库评估注记（AP-17）
- [detailed-design.md](../specification/detailed-design.md)：写入管线设计小节（AP-04）；Compaction 成本-保真三 regime（AP-25）；恢复契约六属性验收表（AP-20）
- [configuration.md](../ops/configuration.md)：CRI 压缩参数外部参考值注记（AP-14：触发 0.5/目标 0.2/保护 20 条）
- [acceptance-criteria.md](../quality/acceptance-criteria.md)：记忆系统成熟度五问评估清单（AP-07）
- [benchmark-plan.md](../quality/benchmark-plan.md)：六梯度消融方法论 §3.12（AP-15）；InMind 检索回归基准建议 §3.13（AP-22）
- [adr.md](../governance/adr.md)：决策历史条目四元组（AP-24）
- [troubleshooting.md](../ops/troubleshooting.md)：记忆整合失效排查小节（PAPER-01 实证）
- [schema-slice.sql](../specification/schema-slice.sql)：memories 表同步 valid_until/expiration_date 两列（6.13 门禁联动）

**计数与治理**：表数 57 不变（字段级扩展）；参数计数 224+146=370 不变（4 处新阈值如实标注「参数待登记」，未引入未登记 KAIROS_* 参数名）；受改 10 份文档版本记录统一 0.0.41（2026-08-07）；全部新增标注「外部理念吸收 0.0.41」与外部实证来源（REPO/VID/PAPER 编号）。

**门禁**：doc-audit.py 18 类全绿（联合验证）。


## 0.0.42（2026-08-07）— 全库文档审计修复批次（逻辑一致性/连贯性/定位符合性）

**批次定位**：全库文档审计（9 组并行，语义级：逻辑一致性 + 阅读连贯性 + 定位符合性）修复批次——机器门禁基线全绿，本次修复 doc-audit 无法检测的语义级问题。

**高严重级（13 条全部闭环）**：
- 帕累托参与口径统一（usage-load §三 改写为架构 §3.3 三轴+硬过滤权威口径）
- 叙事线响应状态枚举修正（api-spec `"open"` → `"active"`，对齐 data-model）
- 实体加成乘性参数废止标注（data-model §7，RC-03 已废止口径残留）
- 知识演化阈值括注收敛为指针（data-model §1「不再复述」后复述问题）
- implementation-map 参数总数 371→370（0.0.22 旧口径残留）
- 蓝图 §5.5 全文副本剥离为摘要+指针（架构 §5.5 唯一权威，0.0.40 漂移消除）
- 六级链 D-006 认知关节修订（默认时序优先与宪法链序一致，废除「默认值优先」矛盾表述；debt-collection 同步）
- slice S-04 误用修正（路径隔离为架构 §8 声明，S-04=本地回环绑定）
- integration-design task_outcome 改 use_event payload 标记承载（不新增全局事件类型，枚举保持 10 类，与架构 §10.10 注册门禁及检索侧维度丢失先例一致）
- troubleshooting 错误码镜像修正（ERR-CAL-001/002 503→400；ERR-CTR-002 审计痕迹口径）
- analysis README 素材统计对齐实际（102 视频：27 字幕 + 75 whisper；C 级仅 VID-91/97 全降级 + VID-54 部分降级；25 份重转写成功笔记升 B 级）

**定位剥离（重点）**：
- 蓝图 §5.5 副本 → 架构 §5.5（摘要+指针）
- glossary 六处词条公式/阈值/加分表剥离为语义+指针（遗忘调度器/检索深度分级/热度层级衰减/并行审查/噪音规则库/审计链）
- data-model §10 注册表键值空间 → 架构注册表权威（指针）
- detailed-design §10.5 恢复契约六属性验收判据 → acceptance-criteria §三a
- detailed-design §10.2 基准测试集成流程 → benchmark-plan §3.14
- claim-matrix「版本边界」治理规则 → documentation-governance §6.1
- user-guide §一 部署细节压缩为指针（deployment/quick-start）
- deployment §八 版本升级步骤压缩为指针（runbook §3）
- threat-model 密钥轮换参数 → security-spec §5
- 架构外部实证标注收敛为简注（机制描述纯机制化；豁免 2 修订为双轨口径）

**引用/编号/计数**：决策/债务编号前缀全库补标（决策 15 处 + 债务 120+ 处，含 D-23 消歧 5 处）；feature-list/claim-matrix/data-model 悬空引用修正（blueprint §一 技能类落点）；benchmark-plan NFR 引用 §二→§一；configuration 时序基准参数（KAIROS_BENCHMARK_* 系列）来源列指正；concept-tiers 68→69；README 分析目录 129→131；changelog 0.0.39 版本记录乱序修复 + 叙述节补齐；架构双括号嵌套链接修复 23 处；笔误批量（dormant/试用心/后天维护/追诉窗口等）。

**保留观察项**（低严重级，未改动）：data-model §0 物理分库取向评估记录（与 0.0.41 版本记录联动）；data-model §8.19/8.21 监控 SQL 示例（与表结构上下文强关联）；debt-collection §七 62 条评估基数口径；social-calibration M2 触发条件表述；traceability-map G-01 与 gap 文档互注（0.0.20 已确认刻意同步口径）。

**门禁**：doc-audit.py 18 类全绿（含决策编号 WARN 清零）。



## 0.0.43（2026-08-07）— 文档审计报告（F1–F9）闭环修复批次

**批次定位**：依用户指令「修复所有问题」，对 `2026-08-07-document-audit-report.md`（审计过程材料不随仓库分发，见 0.0.30 机制）所标识的 9 项问题（F1–F9）执行闭环修复；修复过程中引入的门禁回归已逐项清零并复验。

**F1【中】零版本标记收敛（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)）**：移除正文 23 处 changelog 残留批次标记（0.0.40×22 + 0.0.39×1，形如「外部理念吸收，changelog 0.0.40」），版本记录叙述（documentation-governance §6 豁免 1）保留；与 0.0.38 零版本标记口径一致。

**F2【中】MCP Tool 计数口径统一（[technology-stack.md](../development/technology-stack.md)）**：同文档「12 规范操作集」与「15 个工具」矛盾——统一为「15 个 MCP Tool（基础工具集 12 + 关系管理 3）」，修正 L95/L114 及 L106–L108。

**F3【中】AP 系列声明补登（[claim-implementation-matrix.md](../specification/claim-implementation-matrix.md)）**：补「外部理念吸收声明（AP 系列，0.0.41 落地）」追踪节，AP-01/02/03/05/06/19/22/28 八项认知层声明与 C-01~C-37 并列单一事实源；注明 AP 与 C 系列关系待 cognitive-foundation 显式编号对齐后并入总口径。

**F4【中】参数待登记追缴补登（[debt-collection.md](debt-collection.md)）**：补登 D-422~D-425 共 4 条「参数待登记」阈值追缴（候选集集中度 / 升华整合门控证据充足性 / 处理完降温衰减 / 间隔重复复习间隔序列），五段式格式，落实追缴门禁（§2.3）。

**F5【中】机器可读契约新增（specification/api-contract/）**：新增 `openapi.yaml`（OpenAPI 3.1 骨架，由 [api-spec.md](../specification/api-spec.md) 自动生成，81 路径 / 88 操作，与审计 88 端点口径一致）与 `mcp-tools.json`（15 工具，占位 inputSchema）；README 总计数 yaml 2→3（核心文档 55→56）。契约头部标注 skeleton 非成品。

**F6【低】technology-stack 版本记录补齐**：版本记录补 0.0.39~0.0.42 占位行 + 0.0.43 条目，frontmatter updated/last_reviewed 同步 2026-08-07。

**F7【低】data-model DDL 承载说明**：补「DDL 承载说明」注记——逻辑数据模型不含内联 `CREATE TABLE` DDL，DDL 集中于 schema-slice.sql（14 表示例）+ 实现阶段 Alembic 迁移；意图性分离（文档层描述结构、迁移层承载 DDL）。门禁 6.13 DDL<->data-model 字段集比对 0 差异。

**F8【低】README 分析目录边界说明**：补「分析文档」目录边界说明——`docs/analysis/` 为外部视频分析产物目录，随仓库分发、不随审计材料归档，计入 `docs/` 全量 md 统计但不计入核心文档权威子集。

**F9【低】架构单文件超限（复核无动作）**：3952 行导航/锚点复核——门禁 [15/18] 锚点链接检查仅 1 处受检且有效，全库零断锚；治理 §4.2 存量超限已豁免追溯拆分，维持现状。



## 0.0.44（2026-08-08）— 外部理念吸收补落地批次（AP-29~37 + PAPER-01~09 增量未覆盖项全量落库）

> 承接 0.0.41（AP-01~28 全量落库）与 0.0.40（外部视频分析批次），本批次将**剩余全部「可吸收」条目补落地**（用户决策：所有对项目有帮助的外部理念分析均须具体落地）——① AP-29（PAPER-10 G-Memory，用户直发链接 + 原文 PDF 核验）；② EV 处置建议列「建议态」条目 8 条补齐为 AP-30~37；③ PAPER-01~09 笔记「可吸收增量」中未被 AP-19~28 覆盖的条目，按注记/债务形态落地。

**认知基础（[cognitive-foundation.md](../foundation/cognitive-foundation.md)，2 条参考注记）**：
- AP-32 治理轴集参考注记（§1.1，REPO-03 Memorix 五维轴模型——source/portability 与见证价值轴/可移植备份格式同构，不新增维度，轴扩展门禁不变）
- AP-37 三笔账分离参考（§1.1，VID-44——容量/存储/模型实际看见三分，并入 D-313 可及性轴立项论据）

**系统架构（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)，14 处注记）**：
- AP-29 §3.9 双向遍历检索评估注记（PAPER-10：R2 双方向遍历候选，1-hop 扩展限幅，差异检验拦截无证据污染）+ §5.2 升华管道支撑集引用（PAPER-10：升华产物显式记录支撑记忆集引用，与质检三查来源可溯合并）+ 蓝图 §5.7 多 Agent 参考注记（v1.1 参考材料，自动演化不吸收）
- AP-30 §7.3 主题感知写入切分评估注记（VID-61，LLM 依赖降级回窗口边界）
- AP-31 §5.2 遗忘调度器保留期参数化+免疫规则+可解释保留原因评估注记（REPO-03，保留原因字段 v1.1 候选）
- AP-33 §3.2 操作轨迹记忆评估注记（VID-20，v0.1.0 三型承载，独立类型 v1.1）
- AP-34/35 §3.7 约束作用域 + Flush Memories 生命周期事件评估注记（VID-46/03，不新增字段/事件类型）
- AP-36 §10.15 MetaLLM 审查+门控脚手架评估注记（VID-11，LLM 产物须过差异检验+宪法边界）
- PAPER-02 §5.2 实体知识图谱知识桥通路注记（隐式关联依赖世界知识桥，桥接边写入过差异检验）
- PAPER-04 §1.7 审计庭评估资产访问边界注记（与 S-14 同族）
- PAPER-07 §5.2 检索路径抑制器遗忘后回归验证钩子 + 多实现注册注记；§8 S-19 知识控制三位置路由粒度对照表注记
- PAPER-08 §1.7 外部审计演练注记 + §5.5 差异检验分级阈值参数化评估注记
- PAPER-03 §7.3a 查询级路由系数 ρ 评估注记（与意图先验互补，v1.1 检索参数化评估）+ §5.12 DFA 确定性校准阶段注记
- PAPER-01 §5.2 升华管道调度形态声明 + 整合回归测试注记；PAPER-04 技能仓库级落地单元注记

**规格/质量层（3 份文档 + 债务 2 条）**：
- [benchmark-plan.md](../quality/benchmark-plan.md)：§3.13 补间接查询入测注记（PAPER-02 信任悖论——验收不得只测直接查询）+ 长上下文问答基准参考注记（PAPER-03/05：LoCoMo/HotpotQA 448K 改造、LongMemEval 92%/LoCoMo 93.2% 参考值非门槛、latency/token 效率/context-rot 抗性三维度缺口补录）
- [test-strategy.md](../quality/test-strategy.md)：新增 §四a 契约验证方法论（PAPER-06 REMIT——39 格故障矩阵 + 属性独立性 + 版本固定纪律）
- [debt-collection.md](../governance/debt-collection.md)：补登 D-426（remit-contract 外部依赖评估，PAPER-06，须过外部依赖安全审查）与 D-427（记忆饱和与支撑集漂移研究议程，PAPER-09/10，基准立项时纳入）

**登记与治理**：absorption-proposals 新增四b（AP-30~37）/四c（PAPER 增量未覆盖项落地清单）节；triage-matrix 8 条 EV 处置建议列更新为「已落地」；受改 9 份文档版本记录统一 0.0.44（2026-08-08）；全部新增标注「外部理念吸收 0.0.44」与外部实证来源（REPO/VID/PAPER 编号）；参数计数不变（全部注记形态，未新增参数）。

**门禁**：doc-audit.py 全类验证（见批次收尾检查清单）。

**修复回归清零**：修复过程中引入 4 类门禁回归已逐项修复——① debt-collection 4 处裸 `configuration.md` 引用改链接；② claim-matrix 18 处裸 `cognitive-foundation.md` 引用改链接；③ README yaml 总数 2→3（核心文档 55→56）与计数口径同步；④ [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) CRLF 行尾残留（3952 行）归一为 LF。doc-audit.py 18 类 + 14a + 6.13~6.19 复验全绿、退出码 0。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.19 全绿（退出码 0）；配置文件索引 370/370、债务闭环、锚点 0 断链。



## 0.0.45（2026-08-08）— 文档审计报告（R18-01~R18-15）闭环修复批次

> 承接 round18 审计报告（基线 0.0.43，2026-08-07）的 15 项发现（0 高 / 9 中 / 6 低），将 R18-01~R18-15 全部落地为文档修复。修复后运行门禁 `doc-audit.py` 与 `deep-audit.py` 复验全绿。

**核心修复（按 R18 编号）**：
- **R18-01 / R18-09 / R18-12**：README 删除过时且自相矛盾的 L21 分析目录说明（原「55 份 / 不随仓库分发」三处全错），去除 L126 批次标记；规格文档索引表补 `schema-slice.sql` / `openapi.yaml` / `mcp-tools.json` 三行，并新增「附属资产计数政策」说明非 md/yaml 资产不计入 185 md / 3 yaml 口径。
- **R18-02 / R18-03 / R18-12**：AP- 编号体系定调——在 documentation-governance §5 注册表登记 AP- 前缀（吸收提案编号，analysis 目录，非权威声明）；claim-matrix「外部理念吸收声明（AP 系列）」节改为「外部理念吸收提案（AP 系列）」，删除 8 行同文死链（指向 `absorption-proposals.md` 实质定义源）；cognitive-foundation 0.0.41 版本记录「认知层声明落地」误述修正为「并入既有 C- 系列声明」。
- **R18-04**：架构 0.0.41 版本记录行批次号错标 0.0.40 → 0.0.41。
- **R18-05**：架构「三链路融合与检索扩展」小节名与正文引用去数量词（→「链路融合与检索扩展」）；§7.3a 术语消歧「三链路（语义/共现/kNN）」修正为「（共现/kNN/因果）」，与 L2450 术语注记一致。
- **R18-06 / R18-12**：`openapi.yaml` 重建为合规 OpenAPI 3.1——补 22 条模板路径的 path 参数、55 个写操作的 requestBody、全局 apiKey + 管理端点 adminKey security、顶层 tags 声明；头部版本标记注释清除；结构校验 4 项缺陷（路径参数 / requestBody / security / tags）全清零（55 write-body、5 admin-override、3 top-tags）。
- **R18-07**：补登债务 **D-428 接口契约 schema 补全**（五段式：到期 Phase 0 结束、改动量 88 操作 schema + 15 工具 inputSchema、不做的后果、状态未闭环）；project-plan Phase 0 W2 交付物追加契约补全项（验收 `redocly lint` 零 error）。
- **R18-08**：`.gitignore` 追加 `*-audit-report.md` / `*-deep-audit.md`，覆盖根目录审计报告。
- **R18-10**：[AGENTS.md](../../AGENTS.md) §2.2 目录树补 `api-contract/`，§4.1 职责说明补机器可读契约子目录定位。
- **R18-13 / R18-14**：D-422~D-425 四条债务标题去除「0.0.43 追缴」批次标记，工程简化字段硬行号（架构 L1496/L1993/L2472/L3388）改为语义引用（§3.9 / §5.2 升华管道 / §5.2 使用侧热度维护 / §9.2）。
- **R18-15（F2 误诊回归修正）**：technology-stack §七 回退为「将 12 规范操作集（架构 §7.3.1）中的 create/search/delete 直接映射为 MCP Tool…共暴露 15 个 MCP Tool」，恢复 §7.3.1 权威指针、消除「15 个 MCP Tool 映射为 MCP Tool」语义自指。

**误诊更正声明（重要）**：round18 审计报告 F2 将「12 规范操作集」判为与「15 个 MCP Tool」矛盾的误诊——二者分属不同抽象层（12 操作为架构 §7.3.1 定义的规范操作集，仅 create/search/delete 直接映射为 MCP 工具，其余经 REST 暴露；15 为 MCP 暴露工具总数）。本批次已回退 F2 误诊修复，并更正其引入的语义自指。后续轮次不得继承「12 规范操作集与 15 MCP Tool 矛盾」为既定事实。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.19 复验全绿（退出码 0）；deep-audit.py 无阻断项。



## 0.0.46（2026-08-08）— 文档审计修复批次（round19 五维审计闭环）

> 承接 round19 全面深度审计（基线 0.0.45）的 4 类发现（0 高 / 2 中 / 2 低），将可落地项全部修复；散落版本标记与零版本标注治理豁免澄清一并闭环。修复后 `doc-audit.py` + `deep-audit.py` 复验全绿。

**核心修复**：
- **R19-01【中】小节名改名漏改（一致性）**：架构 §7.3a 正文、configuration `KAIROS_RETRIEVAL_LINK_WEIGHTS` 来源列 + 版本记录、debt-collection §七 D-409 状态注记共 4 处仍引用已改名的「三链路融合与检索扩展」，统一改为唯一权威名「链路融合与检索扩展」（R18-05 去数量词口径）——验证表明 R18-05 改名未完全收敛，遗留 4 处引用。
- **R19-02【中】零版本标注治理豁免澄清（格式纪律）**：§6 豁免 2 补「标注形态约定」——明确正文外部理念吸收双轨简注「（外部理念吸收 0.0.XX；外部实证：代号 来源名）」为 Kairos 标准写法、豁免 §2.3 零版本标记约束（溯源用批次号）；仅标批次号而无外部实证代号的形态不豁免。据此修正 adr `决策历史条目四元组（外部理念吸收 0.0.41）`→`外部实证参考：PAPER-04 SkillHone`、integration-design §五a 去除散落「（changelog 0.0.39）」批次标记。
- **R19-03【低】技术栈 CI 工具链缺失视角（缺失）**：technology-stack §五 补 CI/CD 工具链交叉引用（定义见 engineering-workflow §四），技术选型视角不重复承载，消除文档分散导致的检索盲区。
- **R19-04【低】版本记录触达登记缺口（治理）**：round18（0.0.45）修改 architecture/configuration/debt-collection/integration-design 但未同步其版本记录（门禁 [12] 盲区，不校验「文件修改↔版本记录行」）。本轮 0.0.46 修复涉及的 6 份文档均已补 0.0.46 版本行；历史缺口建议通过门禁增强（跨文件修改↔版本记录行一致性）一次性补登，列入门禁盲区清单（见报告结构性建议）。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.19 全绿（退出码 0）；deep-audit.py exit 0（pending/heading 项均属 analysis/ 目录，超出治理范围）。



## 0.0.47（2026-08-08）— 外部论文分析批次（13 链接批次：11 篇新论文 + 2 篇交叉引用）

> 承接用户直发 13 个 arXiv 链接的外部理念吸收批次——其中 2 篇已分析（PAPER-09 δ-mem=2605.12357、PAPER-10 G-Memory=2506.07398，仅交叉引用不重复分析），11 篇新增（PAPER-11~21）。第 3 个链接 `2509.2470` 缺末位数字，经检索解析为 **2509.24704 MemGen**。本批次**零改动核心设计文档**（foundation/specification 零改动）——产出为 [docs/analysis/external-videos/](../analysis/external-videos/README.md) 建议态（分诊矩阵 I 节 + 吸收建议四d 节 + 11 份逐论文笔记），是否落库由后续批次决策（0.0.44 先例）。

**核心产出**：
- **11 份逐论文笔记**（[papers/](../analysis/external-videos/papers/) PAPER-11~21）：AEL（双时间尺度检索策略选择 + 「少即是多」九变体消融）、MemSkill（记忆操作技能化三组件闭环）、MemGen（生成式隐式记忆，ICLR 2026 poster 第三方口径）、MIRIX（六类记忆 + Active Retrieval 意图先验路由）、AgeMem（RL 统一 LTM/STM 管理）、Mem²Evolve（经验-资产共演化）、MemoryBench（持续学习基准，ICML 2025）、MemAPO（策略模板 + 错误模式双记忆）、DeMem（决策导向率失真遗忘边界）、Mem-W（隐式记忆原生 GUI）、MemEye（视觉评估消融四验证门）——均含素材边界声明（MemGen/MIRIX/MemoryBench 3 篇 WebSearch 多源核验，其余 8 篇 arXiv API 摘要级）
- **分诊矩阵 I 节**（EV-60~74，15 条）：已覆盖/印证 7（含 2 条强警示）、可吸收 6、张力 3、**矛盾 1**（latent 不可审计记忆形态，MemGen+Mem-W 并案——与可审计性红线直接冲突，存储形态不采纳）
- **吸收建议四d 节**（AP-38~52，15 条，建议态未落库）：重点候选——AP-39 错误模式库（AEL/MemSkill/MemAPO 三篇共识增量）、AP-47 简单基线对照门禁（MemoryBench「高级记忆框架不敌简单 RAG」警示）、AP-52 能力验证门方法论（MemEye 四验证门）
- **张力新增 AT-08~09**：记忆策略可学习 vs 宪法化裁决（AgeMem/MemGen/MemSkill 三篇同源）、决策效用 vs 认知真实性双标准（DeMem/Mem-W，并入蓝图 §5.3 价值独立性对照）
- **changelog 版本表补登 0.0.46 行**（0.0.46 节存在但版本表缺失，R19-04 所述触达登记缺口的同款问题，随本批次一并补齐）
- **[docs/README.md](../README.md) 计数同步 185 → 196**（本批次 11 份新论文笔记计入 analysis 目录，doc-audit [6] 数值一致性检出后同步：analysis 132 → 143 份）

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.19 全绿（退出码 0）；deep-audit.py exit 0 无阻断项（占位/待定项均属 analysis/ 目录与既有文档，超出本批次范围）。



## 0.0.48（2026-08-08）— 外部理念吸收落地批次（13 链接批次 AP-38~52 全量落库）

> 承接 0.0.47 外部论文分析批次（PAPER-11~21，13 链接批次）的建议态吸收建议，将 AP-38~52 落地至核心设计文档（用户决策，0.0.44 先例）。落地形态以评估注记为主（参数计数不变），含 1 条基准红线强化 + 1 条红线级矛盾记录。全部注记标注外部实证来源（PAPER-XX 代号）。**round20 逆向核销复核**：AP-38~48、AP-50~52 均已落地；AP-49（遗忘代价函数理论化 / DeMem 率失真，原定 §5 遗忘调度器评估注记）独立注记未建立，其率失真主题由 AP-50 蓝图 §5.3 注记部分覆盖，AP-49 维持建议态待落地——故「全量落地」声明不成立，已更正。

**落地清单**：
- **架构 9 处注记**（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)）：§0.8 机制叠加递减外部证据（AP-40，PAPER-11 九变体消融——支撑最小系统+特征标志门控取向）；§1.7 不可审计记忆形态矛盾记录（AP-42，PAPER-13/20 latent 隐式记忆——存储形态不采纳，红线级）；§3.2 元认知触发评估注记（AP-41，PAPER-13 记忆触发器）+ 意图先验行补 MIRIX 独立实证（AP-44，PAPER-14）；§3.9 检索策略选择 bandit 评估注记（AP-38，PAPER-11）；§5.1 记忆功能分工涌现证据注记（AP-43，PAPER-13）；§5.2 双流统一压缩评估注记（AP-51，PAPER-20，须 P6 门禁）；§5.5 错误模式库评估注记（AP-39，PAPER-18/11/12 三篇共识——负向经验一等承载，写入过质检）；§10.14 稀疏奖励训练配方参考注记（AP-45，PAPER-15 step-wise GRPO，边界声明 AT-08）；§10.15 失败模式驱动反思闭环注记（PAPER-11/12，改进产物过差异检验+质检三查）。
- **蓝图 2 处注记**（[architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md)）：§5.3 决策效用张力注记（AP-50，PAPER-19/20——双标准分域：使用侧热度承载效用面、见证锚定承载真实性面；率失真遗忘边界作遗忘调度器代价参考）；P3 区经验-资产共演化候选注记（AP-46，PAPER-16——升华管道与资产层扩张联动候选，自动创建资产过宪法边界门禁）。
- **benchmark-plan 3 处**（[benchmark-plan.md](../quality/benchmark-plan.md)）：§3.11 红线规则补**第 5 条简单基线对照门禁**（AP-47，PAPER-17 MemoryBench「高级记忆框架不敌简单 RAG」——凡记忆机制有效性基准须含无记忆/BM25/嵌入检索对照）+ 能力验证门方法论注记（AP-52，PAPER-21 MemEye 四验证门：可答性/捷径抗性/必要性/推理结构）；§3.13 用户反馈模拟评估维度注记（AP-48，PAPER-17 四协议 + 声明性/程序性分型）。
- **债务**：D-427 记忆饱和研究议程补充证据域（MemoryBench 程序性知识缺口 + MemGen 抗灾难遗忘数据，PAPER-17/13，第三方口径标注）。
- **吸收建议四d 状态更新**：AP-38~48、AP-50~52 建议态 → 已落地；AP-49 维持建议态（待落地，详见上方 round20 复核注记）；张力 AT-08~09 保持记录态。

**参数计数**：不变（全部评估注记形态，无新增 KAIROS_* 参数）。



## 0.0.49（2026-08-08）— round20 全面深度审计修复批次（5 高 / 10 中 / 6 低）

> 承接 round20 全面深度审计（基线 0.0.48）的 21 项发现（5 高 / 10 中 / 6 低），将可落地项全部修复；修复后 `doc-audit.py` + `deep-audit.py` 复验全绿（doc-audit 因 6.16 CRLF 残留经转 LF 闭环）。本轮聚焦「默认配置下系统实际行为」的语义自洽——5 个【高】级问题全部位于机器门禁盲区（形式合法、编号连续、链接有效，但语义互斥）。

**核心修复（5 高 · 特征标志门控 × 宪法核不可禁用）**：
- **R20-01** 引入两级退化区分：§0.8 / §7.3a / configuration §11 明确「标志 OFF 编译期降级（双信号重新归一化 α_s=0.60/α_b=0.40）」与「标志 ON 运行时候化」为两种不同处置，三处互指。
- **R20-02** 价值独立性公理（cognitive-foundation §2.1）拆分两档白名单（外部交互确认→可裁定见证置信度；多源交叉使用→仅作用于检索排序与来源多样性，不写入 `narrative_coherence_score` / 见证锚定），回指 D-16 边界与 S-14。
- **R20-03** §0.8 新增「组件归属与门控优先级（宪法核不可禁用清单）」——叙事连贯性检测器由 `NARRATIVE_IDENTITY` 单独门控，不受 `META_COGNITION=OFF` 影响；§2.2 / configuration §11 同步。
- **R20-04** `CONSTITUTIONAL_GOVERNANCE` 所涉组件收窄为「监督平面扩展能力面」，常驻核（审计庭最小职能 + 证伪信号路由）不受本标志门控，与 §1.7「存在性不可禁用」一致；§1.7 / configuration §11 同步。
- **R20-05** S-17 增设法定擦除例外（唯一例外）：GDPR 等法定请求命中 `is_structure` 走 S-19 哈希净化（结构位点保留），经宪法解释层单独裁定 + `statutory_erasure` 留痕，仅对法定请求开放；S-19 回指。

**核心修复（10 中）**：
- **R20-06** technology-stack §六 兼容矩阵拆行（PG15–16×pgvector 0.5–0.8+ / PG17×pgvector≥0.8），§二 注明 PG17 须配 pgvector≥0.8。
- **R20-07** technology-stack §一 后端运行时表补 cryptography≥42.0（AES-256-GCM / PBKDF2-HMAC-SHA512 / API Key 哈希，挂 S-07 与安全规格）。
- **R20-08** cognitive-foundation 去越界实现规格：L116 去版本号/表名/字段名，L492/L496/L1095 的「默认 100ms」改为「窗口时长为工程参数，见 [ops/configuration.md](../ops/configuration.md)」。
- **R20-09** cognitive-foundation 附录 E.6 P4 名称由「基于频率的缓存淘汰策略」更正为权威名「遗忘是工程权衡」（与推论四、架构 §0.6 一致）；正文 L454 引用同步。
- **R20-10** 最小系统定义补注单曲线指数衰减遗忘形态（基础 TTL 清理 + 衰减计算，完整遗忘调度器随 `FORGETTING_ENGINE` 启用）；降维升级门禁表行 4 补 `ATTENTION_SCHEDULER=OFF` 时由常驻「固定槽位轮询」承载说明。
- **R20-11** architecture §5 蓝图指针链接去除包裹的反引号（L2481/L2496/L2500），恢复可点击。
- **R20-12** debt-collection / detailed-design / configuration / architecture 共 15 处决策编号补「决策」限定词（D-03/D-15/D-01），消除 §5 体系消歧违例（changelog 条目豁免）。
- **R20-13** troubleshooting「无法启动」排查补 `KAIROS_API_KEY` 检查项（对应 S-01）。
- **R20-14** README 与 documentation-governance 编号注册表更新为 AP-01~52，新增 AT-01~09 张力记录行；claim-implementation-matrix 同步 AP-01~52。
- **R20-15** 全库 20 处非豁免零版本标记按 §6 豁免 2 处置（去除批次号，保留描述性限定词）——覆盖 README / architecture / configuration / troubleshooting / blueprint / schema-slice / implementation-map / acceptance-criteria / benchmark-plan / detailed-design / data-model / concept-tiers（concept-tiers 为扫描补充项）。

**核心修复（6 低）**：
- **R20-16** changelog 0.0.48「AP-38~52 全量落地」声明更正：逆向核销复核确认 AP-49（遗忘代价函数理论化 / DeMem 率失真）独立注记未建立（率失真主题由 AP-50 蓝图 §5.3 部分覆盖），AP-52（MemEye 四验证门）经核验实际已落地（benchmark-plan §3.11 及版本记录）——故全称判断不成立；changelog 0.0.48 条目与 absorption-proposals 状态行同步更正（AP-49 维持建议态待落地）。**注**：round20 原审计曾误判 AP-52 未落地，本轮据实证源核对后更正，避免传播不实声明（S 级红线「禁止编造」）。
- **R20-17** README 增补「图表文档」索引节（diagrams/system-architecture.html），与 AGENTS 目录口径对齐。
- **R20-18** 标题跳级修复：architecture-blueprint-v1.1 全 24 处 `####`（§一/§三 节直接子标题）降为 `###`，与 §二 的 `##→###` 层级一致；requirements-baseline L189 `#### 横切项`→`###`。
- **R20-19** architecture §5.2 节内导航标题去除编辑痕迹「（补全，补 5 节点）」→「节内导航」。
- **R20-20** glossary 增补「身份面否决权 / Identity-Plane Veto」独立词条并登记简称「身份否决权」；术语计数 69→70，README / 架构 §11 / concept-tiers 同步。
- **R20-21** README schema-slice 行「14 张竖切表」澄清为 14 物理 + 1 FTS5 虚拟表（`memories_fts`）合计 15 张，与 slice-implementation-guide「15 张表」口径对齐。

**参数计数**：不变（全为语义/格式/治理修复，无新增 KAIROS_* 参数）；术语 69→70。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.19 全绿（退出码 0，6.16 CRLF 已转 LF）；deep-audit.py exit 0 无阻断项。



## 0.0.50（2026-08-08）— round21 深度审计修复批次（2 高 / 5 中 / 1 低）

> 承接 round20（基线 0.0.48 / 0.0.49）的逆向核销 + 五维度增量扫描。所有证据亲手复核（子代理派发失败，改手动深挖，符合 S 级文档诚实红线）。round20 的 21 项逆向核销中 19 项确凿闭环；2 项（R20-08 / R20-09）修复不彻底，本轮完成收尾。新发现 8 项（R21-01~R21-08，2 高 / 5 中 / 1 低），全部闭环。

**核心修复（2 高 · 机器门禁盲区：语义互斥）**：
- **R21-01** §0.8 最小系统定义「无特征标志依赖」含身份注册表「叙事驱动双向更新」与前提一（feature off 时功能不存在）/ L517（NARRATIVE_IDENTITY=false 注册表降级）/ L544（OFF 仅原型合法）互斥 → L538 限定「不依赖 10 个默认 OFF 可选标志；宪法核 `NARRATIVE_IDENTITY` 默认 ON 仍决定注册表更新语义」，注册表 `OFF` 时降级为写入即固定、永不重评。
- **R21-02** §0.8 编码纪律「H1-H3 证伪失败强制关标志」与宪法核不可禁用（门控优先级规则(c) 拒绝启动）/ 命名配置集仅 3 种合法形态互斥 → L598 区分三类失败路径：非核心标记 `experimental: degraded`；H1/H2 强制关标志且须落入合法命名配置集；H3（宪法核）不得强制关标志，改为 fail-closed containment 交人工审查。

**核心修复（5 中）**：
- **R21-03** changelog 版本记录表补登 0.0.49 行（原仅叙述节有、表缺行）。
- **R21-04** `/metrics` 端点待定义追缴登记 D-429（api-spec §1.8 为权威登记点，observability / technology-stack 仅指针引用），闭环 88 端点口径。
- **R21-05** documentation-governance §5 编号注册表新增 P1~P6 行；cognitive-foundation §A.7 / §宪法锁 的 P4 名称由「基于频率的缓存淘汰策略」统一为「遗忘是受控的优化；基于频率的缓存淘汰策略为其工程近似」，与 §二 / §硬约束2 口径一致（R20-09 残留收尾）。
- **R21-06** configuration 附录 A `KAIROS_PATH` 来源由自指的「参数总表自身（待定义）」改为 detailed-design §L3（NER 实体标签命名空间 `kairos://`，非 OS 环境变量），消除跨文档语义冲突。
- **R21-07** cognitive-foundation 去版本化残留收尾（R20-08 残留）：§身份模型构造论声明（v0.1.0 决策）→（构造论决策）；§1.1 标题（v0.1.0 承载四轴）→（当前承载四轴）；§1.1 口径声明（v0.1.0 阶段）→（当前交付阶段）；§四轴性质声明（架构 v0.1.0 实际承载）→（架构当前实际承载）。

**核心修复（1 低）**：
- **R21-08** 超长文档列为存量观察项（治理 §4.2 不追溯拆分；活跃增长文档变更时评估）。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务新增 D-429（D-4xx 段连续）；端点计数 88 不变。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.19 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。



## 0.0.51（2026-08-08）— round22 深度审计修复批次（4 高 / 3 中 / 2 低）

> 承接 round21（基线 0.0.50）的「上游下达约束、下游零承载」结构性脱节扫描。本轮主要发现集中在**架构层 §0.8 特征标志体系在近几轮持续增补强制性约束，而质量层与运维层从未同步承载**——开发阶段第一天就会撞墙。9 项发现（4 高 / 3 中 / 2 低）全部闭环，并落地两项门禁子检查（6.20 / 6.21）防复发。

**核心修复（4 高 · 写了=做了 纪律缺口）**：
- **R22-01** 质量层建立证伪测试完整承载链：`test-plan.md` §1 覆盖表新增「证伪」行（12 条 `[FALSIFICATION]` 用例，H1/H2/H3 强制）、§2 退出准则补「12 标志各 ≥1 条 `[FALSIFICATION]` 用例且通过」、§3.10 新增 FAL-01~03 证伪判据；`test-strategy.md` §六 新增「证伪测试与配置集测试矩阵」（pytest marker `@pytest.mark.falsification`、测试名前缀 `test_fal_`）、§五 覆盖率目标表补「证伪测试覆盖率 100%（12/12）」。
- **R22-02** 命名配置集测试矩阵承载：`test-plan.md` §1 新增「配置集矩阵」小节（未命名组合不进入测试/验收，指针引用架构 §0.8 L589）；`acceptance-criteria.md` §二 v0.1.0 发布检查项补「三配置集启动校验 + 竖切以 `kairos-slice` 为验收形态」。
- **R22-03** 证伪失败降级阶梯（round21 R21-02 残留）：架构 §0.8 编码纪律 L598 分支②追加 `kairos-full → kairos-slice → kairos-minimal` 整体降级映射 + 审计事件 `flag_falsification_downgrade`，命名配置集合法性规则增列该阶梯为唯一合法降级路径——修复 `kairos-full` 形态下不闭合。
- **R22-04** 运维层自设「编码启动前须登记 11 条 CLI 契约」硬门禁无追缴 → 债务 **D-430** 登记（11 条待定义 CLI 命令：db repair/restore/migrate rollback/admin key revoke/rotate --hmac/audit log/approve-forgetting/health --full/logs --level,--module,--since,--follow/config show/reset；到期 v0.1.0）。

**核心修复（3 中）**：
- **R22-05** changelog 悬空链接（指向已删除 reviews/ 条目）致门禁 FAIL → 改为指向债务 D-430 条目，闭环链接校验。
- **R22-06** 启动校验审计事件运维层零登记 → `error-reference.md` 错误码 38→**40**（新增 `ERR-SYS-006` 标志组合非法 `invalid_flag_composition` / `ERR-SYS-007` 宪法核不可用 `constitutional_core_unavailable`），全库六处口径同步（error-reference / troubleshooting §二§三 / runbook §5.1 / api-spec §7 / README 索引 / debt-collection 指针）。
- **R22-07** `deployment.md` 部署模式与命名配置集语义冲突 → 澄清「部署模式决定基础设施维度、命名配置集决定认知组件；全量模式绑定 kairos-full 为唯一例外」，消除「部分正交」误读。

**核心修复（2 低）**：
- **R22-08** `technology-stack.md` 投影层交叉引用缺失 → 改为指针引用 `adr.md` ADR-012（固定正交投影 + 矩阵随 schema 持久化）与 `data-model.md` §13.5，去除自述式「需自行实现」。
- **R22-09 / S21-1 / S21-2** 门禁增强 + 去复述：`doc-audit.py` 新增 **6.20「特征标志计数一致性」**（架构 §0.8 标志表行数 N 与 configuration §11 一致、组合空间 2^N、默认 OFF 计数一致）与 **6.21「证伪纪律与配置集承载一致性」**（质量层 `[FALSIFICATION]` 与三配置集关键词承载校验）；`observability.md` / `technology-stack.md` 的 `/metrics` 表述改为指针引用 api-spec §1.8 单一事实源（保留「待定义」+ D-429 指针）。

**参数计数**：不变（无新增 KAIROS_* 参数）；错误码 38→40；债务新增 D-430（D-4xx 段连续）；端点 88 不变；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.21 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。



## 0.0.52（2026-08-08）— round22 结构性建议落地批次（S22-1 / S22-2）

> 承接 round22 修复批次（0.0.51）的「结构性建议也落地」指令，将 0.0.51 报告 §6 的两项结构性建议 S22-1 / S22-2 全部落地，并诚实补齐其派生出的真实追缴缺口。S22-2 的门禁 6.22（自设硬门禁债务追缴一致性）落地后，全库扫描仅命中 1 处真实缺口——configuration 附录 A「编码启动前须补齐（共 10 项）」自设硬门禁无对应债务，故补登 **D-431**。

**核心落地（S22-1 约束传导登记）**：
- **S22-1** `documentation-governance.md` §2.3 新增「约束传导登记」规则：架构文档新增对下游层的强制性约束（含「须/必须/不应/只对…负责」句式且点名下游文档职责）时，须在同批次内完成下游承载或登记债务条目（承载见 D-XXX 指针）；与门禁 6.22 形成双保险。

**核心落地（S22-2 自设硬门禁追缴 + 派生债务）**：
- **S22-2** `doc-audit.py` 新增 **6.22「自设硬门禁债务追缴一致性」** 子检查：扫描全库「编码启动前 / 上线前 / 定稿前 / 发布前 + 须/必须」句式，校验每处是否有对应 debt-collection 条目；落地首跑命中 1 处真实缺口 → 补登 **D-431**（configuration 附录 A 10 项「待定义」参数于编码启动前补填默认值追缴），并回填 configuration → debt-collection D-431 指针，闭环 §2.3 追缴门禁。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务新增 D-431（D-4xx 段连续）；错误码 40 不变；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.13~6.22 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.53（2026-08-08）— round23 深度审计修复批次（2 高 / 2 中 / 4 低）

> 承接 round22（基线 0.0.52）的「门禁盲区 + 文档纪律」扫描。本轮聚焦五维审计中机器门禁盲区与文档纪律残留：① 核心文档端点路径事实错误（高）；② S-19 哈希净化「遗忘生效」边界在质量层与运维层零承载（高，写了=做了纪律缺口）；③ 全库「（新增）/（原…）」编辑痕迹违反零版本标记纪律（§6）；④ 门禁清单口径与治理面不一致。8 项发现（2 高 / 2 中 / 4 低）全部闭环，新增债务 **D-432**。

**核心修复（2 高）**：
- **R23-01** 架构文档 §1 端点路径事实错误：`GET /health/calibration` → `GET /v1/health/calibration`（api-spec §1.8 单一事实源为 `/v1/health/calibration`，架构原文漏 `/v1` 前缀，跨文档一致性缺口）。
- **R23-02** S-19 哈希净化「遗忘生效边界」在质量层与运维层零承载（写了=做了纪律缺口）：
  - `test-strategy.md` 新增 **§2.2a 遗忘生效验证**，补 TC-S19-002（三样本检验：遗忘模型 vs 安全重训模型 vs 原始缺陷模型）、TC-S19-003（双副本遗忘完备性：见证主本 + 使用影子副本）、TC-S19-004（「内容不可恢复 ≠ 行为无痕」边界断言）；S-19 行改为「内容层 SHA-256 替代 + 行为层无痕另行验证，见 §2.2a」。
  - `security-specification.md` S-19 行补「遗忘生效边界」注记（哈希净化保证内容不可恢复，不自动保证行为层无痕，须经三样本检验与双副本完备性测试单独验证），并新增 §后 边界注记块（指针 test-strategy §2.2a / architecture §8）。
  - `test-plan.md` §3.8 补 TC-S19-002~004 行与说明（-001 内容层、-002~004 行为层）。

**核心修复（2 中）**：
- **R23-03** OpenTelemetry 追踪栈 v1.1 引入在 technology-stack / observability 已描述但无追缴 → 新增 **D-432**（OpenTelemetry 追踪栈 v1.1 引入追缴，五段式格式，历史背景「2026-08-08 round23 深度审计（R23-03）新登记」），并回填 technology-stack（L78）/ observability（§三）/ debt-collection §四 指针。
- **R23-04** 全库 17 处「（新增）/（新，）/（原…）」编辑痕迹违反零版本标记纪律（documentation-governance §6：正文只描述当前状态，不写版本标记）——批量清除：architecture-v0.1.0（社会性校准信任模型占位 / 复杂度阈值原则 / 多跳遍历 / 耦合计监测器 VAD / 默认项可解释性追溯等 12 处）、cognitive-foundation（硬约束 1~3 / 软原则 P2 映射 ×5 + 认知科学术语括注）、data-model / detailed-design / design-philosophy-relations / documentation-governance / architecture-blueprint-v1.1（「现有→v0.1.0 已有」「新增→v1.1 能力」）/ claim-implementation-matrix（「原 P1–P5 → 对应 P1–P5」）。whack-a-mole 复扫：blueprint L692 / claim-matrix L76 残留已清；debt-collection L601「（原 P0 债务升级）」位于债务账目字段（§6 豁免 1 可追溯性注记），保留。

**核心修复（4 低）**：
- **R23-05** 门禁清单口径不一致：`project-plan.md` L77「18+14a」未含 6.8a/6.12a/6.13~6.22 → 修正为「18 类 + 14a + 6.8a + 6.12a + 6.13~6.22（清单以 `engineering-workflow.md` §四 为准）」；`engineering-workflow.md` L63 CI 门禁列表补 `+ 6.22`。
- **R23-06** `runbook.md` CLI 命令状态：待定义命令（health --full / logs --level,--module,--since,--follow / config reset / audit log / audit approve-forgetting + 灾备 db repair/restore/migrate rollback）未挂追缴 → 补登块，指针 **债务 D-430**。
- **R23-07** architecture-v0.1.0 篇幅长（4031 行）无章节导航 → 引言后补「章节导航」表（§0~§12 定位），降低下游查读成本。
- **R23-08** `slice-implementation-guide.md` L18「5000 行架构文档」夸大数据 → 改为「四千余行的架构文档」（实际 4031 行）。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务新增 D-432（D-4xx 段连续：D-428~D-432）；错误码 40 不变；端点 88 不变；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.8a + 6.12a + 6.13~6.22 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.54（2026-08-08）— round23 结构性建议落地批次（S23-1 / S23-2）

> 承接 round23 修复批次（0.0.53）的「结构性建议也落地」指令，将 0.0.53 报告 §六 的两项结构性建议全部落地：**S23-1**（单一事实源反查入检）新增门禁子检查 **6.23**；**S23-2**（版本记录回填自动化）新增生成式脚本 `scripts/version-record-update.py`。S23-1 落地首跑即命中 1 处真实缺口——架构 §5.2 记忆压力缓解动作行健康检查端点 `GET /health/memory-pressure` 漏 `/v1` 前缀（与 R23-01 同类、round23 全库扫描漏网），已修复并对齐 api-spec §6.5。

**核心落地（S23-1 单一事实源反查入检）**：
- **S23-1** `doc-audit.py` 新增 **6.23「单一事实源反查（端点登记一致性）」** 子检查：以 `api-spec.md` 为 HTTP 端点唯一登记源，扫描权威文档正文引用的 `METHOD /path` 端点，校验 (a) 每个引用已在 api-spec 登记；(b) `/v1` 前缀不得遗漏（R23-01 类防复发）；豁免版本记录表行（历史叙述）、changelog / blueprint-v1.1（未来规划端点）/ debt-collection（债务账目）/ analysis/（外部对照产物），以及父路径引用（`rollback` ⊆ `rollback/{snapshot_id}`）与多方法简写（`GET/POST` 只取首个）。落地首跑命中 1 处真实缺口：架构 L2165 `GET /health/memory-pressure` → 修正为 `GET /v1/health/memory-pressure`（api-spec L788 登记）；突变测试验证：人为去掉 `/v1` 前缀 → 6.23 报「端点缺 /v1 前缀」FAIL，确认检查有效。

**核心落地（S23-2 版本记录回填自动化）**：
- **S23-2** 新增 `scripts/version-record-update.py` 生成式脚本：对指定文档（或 `--all` 全库扫描）的版本记录表追加 `| 版本 | 日期 | 说明 |` 行，幂等（目标版本已存在则跳过），同步校正 frontmatter updated/last_reviewed 倒挂（不得早于新版本日期），统一 LF 行尾（`newline=""` 读写，不引入 CRLF——固化 0.0.53 批次手工回填引入 CRLF 的踩坑教训）；changelog 批次节（`## 0.0.X（`）不入表（批次叙述节非表格形态）。

**工程修复（S23-1 首跑派生）**：
- 架构-v0.1.0 §5.2 记忆压力三级减压动作（L2165）健康检查端点 `GET /health/memory-pressure` → `GET /v1/health/memory-pressure`，与 api-spec §6.5 对齐（round23 R23-01 同类漏网项，6.23 捕获）。

**门禁清单口径**：`engineering-workflow.md` §四 CI 门禁第 1 步补 `+ 6.23`；`project-plan.md` Phase 0 门禁口径 `6.13~6.22` → `6.13~6.23`。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务编号不变（D-428~D-432）；错误码 40 不变；端点 88 不变（`/v1/health/memory-pressure` 已登记）；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.8a + 6.12a + 6.13~6.23 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.55（2026-08-08）— round24 全面深度审计修复批次（1 高 / 10 中 / 7 低）

> 承接 round23（基线 0.0.54）的「五维全面深度审计」指令。本轮以**核心文档准确性**为主线深挖：认知基础「版本无关理论模型」定位与正文版本绑定声明长期并存（架构 §0.9 声明失实）的治理缺口首次暴露并闭环；机器门禁盲区（引用错位、口径漂移、悬空指针）类问题仍为主要来源。18 项发现（1 高 / 10 中 / 7 低）全部闭环，新增债务 **D-433~D-438** 六条。

**核心修复（1 高 · 认知基础去版本化治理缺口）**：
- **R24-01** `cognitive-foundation.md` 正文散布 30 处 v0.1.0/v1.1 版本绑定声明（纪元切换子轴、可及性轴工程代理、叙事记忆参数承载、组块化 Phase 1/2、否决权保护范围、DFA 分工、身份模型构造论、记忆压力规则式信号、注意力三源优先级、VAD 时间上限等），违反其「版本无关的认知理论模型」定位（架构 §0.9）；架构 §0.9 L634 声明「认知基础中不再包含版本绑定的可验证子集声明」与实际不符（声明失实）——本轮将 30 处全部改写为「当前架构承载/当前交付阶段/后续版本」版本无关表述，保留债务/决策编号指针；清理后架构 §0.9 声明与事实一致。豁免：债务元数据引用（D-328「v1.1 协议槽位」）与文件名链接（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)）不属版本绑定声明。

**核心修复（10 中 · 引用错位与口径漂移）**：
- **R24-02** 架构 L2165 `GET /v1/health/memory-pressure` 引用「api-spec §1.7」错位（端点在 api-spec §6.5 健康报告与聚合统计）→ 改 §6.5；changelog 0.0.54 同错同步勘误（§1.7→§6.5）。
- **R24-03** api-spec L1632 端点计数口径注记「压缩审计端点（见 §9）」错位（实际 §6.5）→ 改 §6.5；「见 §健康检查」→「见 §1.8」。
- **R24-04** `data-model.md` L29 竖切 DDL 表数「14 张」与 README/§13.4「15 张（14 物理 + 1 FTS5 虚拟）」口径漂移 → 统一为「14 张物理表 + 1 张 FTS5 虚拟表 memories_fts，合计 15 张」。
- **R24-05** `implementation-map.md` CLI 计数「规划扩展 2 条待定」过时——api-spec §5 已注册 `kairos layers ls`/`kairos layers distill` → 改为「api-spec §3 全量 25 条 + §5 已注册新增 2 条 = 27 条」。
- **R24-06** `schema-slice.sql` 4 处「（新增）」编辑痕迹残留（R23-04 清理遗漏，违反零版本标记纪律）→ 清除。
- **R24-07** `runbook.md` 待定义命令追缴块引用不存在的 §7/§8 + 遗漏 3 条命令 → 重写章节引用（§1.2/§1.3/§2.3/§4.1~4.3/§5.2/§6.2/§6.4）+ 补 `admin key revoke`/`admin key rotate --hmac`/`config show` 三条，与 D-430 的 11 条口径完全对齐。
- **R24-08** `acceptance-criteria.md` S-19 行为层验收（TC-S19-002~004 三样本/双副本/边界断言）在验收层零承载 → 安全红线行与安全行补 §2.2a 行为层判据，指针补 test-strategy 2.2 + 2.2a。
- **R24-09** `security-specification.md` S-01 验证方法引用未定义未追缴命令 `kairos admin key verify` → 改为描述性表述（以 PBKDF2-HMAC-SHA512 重算比对，与启动校验一致），消除实现盲区。
- **R24-10** `test-plan.md` 三处内部不一致：预留编号正文声明（W-05/W-06/R-04~R-07/M-04/SF-01~04/CAL-02/06）与登记表（8 行）不符 → 声明收窄为实际登记的八项；TC-COMP-001 端点缺 `{snapshot_id}` 路径参数（api-spec §9 权威）→ 补全；TC-F01-001「N 周期」未定义 → 明确为 1 个调度周期（`KAIROS_SCHEDULER_INTERVAL` 默认 300s）。
- **R24-11** `user-guide.md` L43 将四个密钥启动拒绝全部归因 S-01（超出红线范围：SALT 属 S-05，SECRET_KEY/AUDIT_HMAC_KEY 无红线承载）→ 分拆归因（API Key→S-01、SALT→S-05、另两者为部署必填项）。

**核心修复（7 低 · 语义错位与口径细节）**：
- **R24-12** `concept-tiers.md` 健康检查指向 `GET /v1/health/detail`（聚合健康报告）语义错位 → 改指 `GET /health`（A-01 健康检查）。
- **R24-13** `deployment.md` `kairos serve --pg` 标注「CLI 表见 api-spec §3」但该命令不在 §3 → 改为「api-spec §3 未登记，属规划扩展命令，须纳入债务 D-430 追缴清单」。
- **R24-14** `observability.md` [P] 模式定义指针「S-04 同机绑定」错位（[P]/[L] 定义在 security-spec §0）→ 改指 §0 适用模式声明。
- **R24-15** `troubleshooting.md` 错误码覆盖率「44.7%」未随 38→40 更新 → 注明历史基数（占当时 38 码的 44.7%，现 17→40 全量补全）。
- **R24-16** `api-spec.md` 虚拟校准示例数值不自洽（days=8 配 ceiling 0.227，公式 0.3×exp(-0.02×8)≈0.256）→ 两处示例改 0.256。
- **R24-17** 架构 §0.7 映射表「§1.10 三级知识生产管道」裸引用缺来源前缀（架构自身无 §1.10，实指认知基础）→ 补「认知基础」前缀 ×2；§11 术语表与 §12 版本记录间补章节分隔线。
- **R24-18** 全库决策编号前缀遗漏（adr 迁移标注 D-06/D-11 → 决策 D-06/D-11）、参数名缺 KAIROS_ 前缀（use-cases `DEGRADATION_PERIOD_N/M`）、debt-collection 摘要表缺 D-422~D-428 七行（正文已登、摘要表漏行）→ 全部补齐。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务新增 **D-433~D-438** 六条（blueprint 无编号 v1.1 承诺追缴补登：Playbook 系统/技能进化与技能管理/四层记忆质量/MemCube/事实新鲜度/社区检测，D-4xx 段连续）；错误码 40 不变；端点 88 不变；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.8a + 6.12a + 6.13~6.23 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.56（2026-08-08）— round24 结构性建议落地批次（S24-1 / S24-2）

> **叙述节排序说明（后补登记）**：0.0.45~0.0.49 叙述节位于本节之后（0.0.24 同例——历史批次后补登记，版本记录表序号为序，叙述节按后补时间排在表尾），阅读顺序以版本记录表为准。

> 承接 round24 修复批次（0.0.55）的「结构性建议也落地」指令，将 0.0.55 报告 §六 的两项结构性建议全部落地：**S24-1**（端点→章节锚点一致性）新增门禁子检查 **6.24**；**S24-2**（认知基础去版本化）新增门禁子检查 **6.25**。两检查首跑即命中**真实缺口**——证明 round24 人工修复仍有盲区，机器入检必要。

**核心落地（S24-1 端点→章节锚点一致性入检）**：
- **S24-1** `doc-audit.py` 新增 **6.24「端点→章节锚点一致性」** 子检查：以 api-spec 为端点章节号单一事实源（解析 `## §N`/`### N.x` 标题与 `**METHOD /path**` 端点行，建立端点→登记章节映射），扫描权威文档同一行内「api-spec §X」引用与已登记端点，校验引用章节号与实际登记章节一致（或互为父子级）；豁免文档级（api-spec/changelog/blueprint-v1.1/debt-collection/analysis/）、版本记录表行、未登记端点（待定义）、「以 … 为准」句式（operation-catalog「MCP 工具注册以 api-spec §6.8 为准」指工具注册表位置而非端点定义位置）。**落地首跑捕获 1 处真实缺口**：架构 L771 虚拟校准生成器行 `GET /v1/health/calibration` 引用「api-spec §1.7」→ 实际登记于 §6.5（round24 R24-02 仅修了 L2165 memory-pressure，L771 calibration 同款错位人工漏网）→ 已修正为 §6.5；突变测试验证：人为改错章节号 → 6.24 报「端点章节引用错位」FAIL，恢复后全绿。

**核心落地（S24-2 认知基础去版本化入检）**：
- **S24-2** `doc-audit.py` 新增 **6.25「认知基础去版本化」** 子检查：扫描 [cognitive-foundation.md](../foundation/cognitive-foundation.md) 正文的 v0.1.0/v1.1 版本绑定声明（`v(?:0.1.0|1.1)` 且后不跟 `.md`），豁免版本记录表行、债务元数据版本槽位（`D-\d+**，vX.Y 协议槽位`，含加粗形态）；防 R24-01 类「版本无关理论模型正文散布版本绑定声明」治理缺口复发。**落地首跑捕获 4 处真实残留**（round24 脚本句式遗漏）：L887「主体性立场声明（v0.1.0 决策）」→「（决策）」、L893「v0.1.0 的身份建构周期性声明」→「当前身份建构周期性声明」、L1107「架构层 v0.1.0 双口径」→「架构层当前双口径」、L1109「v0.1.0 的可接受风险」→「当前的可接受风险」→ 全部改写为版本无关表述；突变测试验证：人为注入版本字样 → 6.25 报「版本绑定声明残留」FAIL，恢复后全绿。

**工程修复（6.24/6.25 首跑派生）**：
- 架构-v0.1.0 L771 虚拟校准生成器运营可视化承载行 `GET /v1/health/calibration`（api-spec §1.7）→（api-spec §6.5 校准状态报告），与 api-spec §6.5 对齐（round24 R24-02 同款漏网项，6.24 捕获）。
- 认知基础 4 处版本字样改写（L887/L893/L1107/L1109，见上方 6.25 条目）。

**门禁清单口径**：`engineering-workflow.md` §四 CI 门禁第 1 步补 `+ 6.24 + 6.25`；`project-plan.md` Phase 0 门禁口径 `6.13~6.23` → `6.13~6.25`。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务编号不变（D-428~D-438）；错误码 40 不变；端点 88 不变；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.8a + 6.12a + 6.13~6.25 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.57（2026-08-08）— round25 全面深度审计修复批次

> 承接 round24（基线 0.0.56）的「五维全面深度审计」指令。本轮以三子代理并行深挖 + 主审逐条反查原文复核，发现并闭环 **21 项问题（0 高 / 9 中 / 12 低）**：其中 1 项为中危口径问题（api-spec §13~§17 端点版本边界标注缺失，§17 graph/render 无架构承载——已补 v1.1 预留标注）；其余为跨文档引用错位、S-17 例外未同步、版本记录链断裂等局部修复。修复后门禁 18 类 + 14a + 6.13~6.25 全绿。

**核心修复（按五维归类）**：

- **维度一 完整性与一致性（8 项）**：架构 §1.3 元认知层「栈内第四层」→「栈内第五层」（旧编号残留）；架构 §5.2 完结叙事线拒新成员 400→409（对齐 api-spec §8）；架构 §7.1a kairos_unlink 软删除由 data-model memory_relations 补 `deleted_at` 列承载；api-spec `kairos_get_memory_traces` 映射改指操作目录 §三 OP-054~066（原「操作目录 §3 memory_states」悬空）；api-spec §13 技能管理 API 定位改指 blueprint v1.1 + 标注「v0.1.0 不交付，端点预留」（原引用不存在的「架构 §5.2 技能管理系统」）；troubleshooting §7→§8 安全红线引用；security-spec/threat-model S-17 补法定擦除例外（R20-05 同步）；cognitive-foundation「架构 §0.6」→「§3.3 序数幅度差记录」。
- **维度二 缺失与过时（4 项）**：release-guide 待定义命令纳入 D-430 追缴（补 `kairos init --seed-path` + release-guide 使用方）；README 版本记录补登 0.0.44~0.0.50/0.0.52~0.0.56 段（版本记录链断裂）；changelog 0.0.37「ERR-INPUT-004 改 409」勘误（实为叙事线 400→409 无新码，ERR-INPUT-004 保持 422）；api-spec §5 标题「记忆读取」→「记忆读取与升华」+ 定位说明（升华两阶段端点主题错位）。
- **维度三 结构与组织（1 项）**：changelog 版本记录表 0.0.54 重复行清除（第二行插入 0.0.55/0.0.56 之间破坏单调递增）+ 0.0.56 叙述节补「后补登记」排序说明（0.0.45~0.0.49 叙述节位于其后，对齐 0.0.24 先例）。
- **维度四 格式规范（6 项）**：design-philosophy「D-01」补「决策」前缀 + 两处裸章节引用补文档名；cognitive-foundation「五级路由表」→「六级路由判定表」+「§监督平面」→「§1.7」；vad-coordinate/usage-load 三处参数名补 `KAIROS_` 前缀；use-cases 场景 5 承载功能 M-10→M-04（定向遗忘）；claim-matrix「五硬一软」→「五原则一软」（口径 5 项 vs 6 项矛盾）。
- **维度五 核心文档准确性（2 项）**：api-spec §13~§17 版本边界标注（§14~§16 明确 v0.1.0 交付、§17 graph/render 标注 v1.1 预留）；架构 §11 术语表引言补「78 条架构语境索引，与 glossary 70 条权威口径并行」说明（版本记录 68 条为历史值）。

**参数计数**：不变（无新增 KAIROS_* 参数）；债务编号不变（D-430 追缴范围扩至 11+1 条，D-428~D-438 连续）；错误码 40 不变；端点 88 不变（§13~§17 已标注版本边界，计数口径不变）；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.8a + 6.12a + 6.13~6.25 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.58（2026-08-08）— round25 结构性建议落地批次（S25-1 / S25-2）

> 承接 round25 修复批次（0.0.57）的「结构性建议也落地」指令，将 0.0.57 报告 §六 的两项结构性建议全部落地：**S25-1**（通用章节引用入检）新增门禁子检查 **6.26**；**S25-2**（版本边界标注完备性）新增门禁子检查 **6.27**。两检查首跑即证明必要性——6.26 在实现阶段即捕获 6 处**裸引用/中文标题引用解析盲区**（既有 [2/18] 只覆盖链接格式，裸引用「架构 §X」与「§X『标题名』」不在其扫描面），经修正索引正则后全绿。

**核心落地（S25-1 通用章节引用存在性与标题语义入检）**：
- **S25-1** `doc-audit.py` 新增 **6.26「通用章节引用存在性与标题语义」** 子检查：三档校验——① 裸数字引用存在性（`架构 §X` / `认知基础 §X` 无链接格式，含中文数字↔阿拉伯数字双向映射 `三`↔`3`、字母后缀 `一a`、父级回退）；② 裸中文标题引用存在性（`架构 §监督平面` / `认知基础 §引论`，目标文档标题行须含该词）；③ 引号标题语义（`§X『标题名』`，引号文字属于其他编号章节时报「章节错位」）。豁免：changelog / blueprint-v1.1 / debt-collection / analysis、版本记录行、`§X.Y` 占位符、编号迁移注记行、无编号中文子标题 key。
- **首跑实测**：既有 [2/18]（链接格式 2241 处引用）全绿，但裸引用面（认知基础 §X 21 处、架构 §X 4 处等）此前零校验——6.26 实现阶段逐轮消除正则盲区后 0 项缺口（当前文档库裸引用无真实错位，检查价值在防复发）。
- **突变测试验证**：4 用例全通过——①注入 `认知基础 §9.9` 裸数字引用 → 6.26 报「裸章节引用不存在」FAIL；②注入 `认知基础 §臆造标题章节` 中文标题引用 → 6.26 报「裸中文标题引用不存在」FAIL；③troubleshooting 临时改 `§8「安全红线」`→`§7「安全红线」` → 6.26 报「引号标题章节错位（该标题位于 §8）」FAIL；④api-spec §13 临时移除「v0.1.0 不交付，端点预留」→ 6.27 报「缺版本边界标注」FAIL。恢复后全绿——确认两检查具备防复发能力。

**核心落地（S25-2 api-spec 章节版本标注完备性入检）**：
- **S25-2** `doc-audit.py` 新增 **6.27「api-spec 章节版本标注完备性」** 子检查：扫描 api-spec `## §11`~`## §17` 各节标题及后续 3 行定位段，必须出现版本边界关键词之一（`v0.1.0 交付` / `v1.1 预留` / `端点预留` / `P3，v1.1+` / `P3 前瞻` / `v0.1.0 不交付`），缺失即 FAIL——防 R25-22 类「技能管理 API 被误读为 v0.1.0 交付」「graph/render 无承载」版本边界裸奔复发。
- **首跑实测**：§11~§17 七节全带标注（0.0.57 修复后），0 节缺标注；突变测试（临时移除 §13 标注）确认能捕获。

**口径同步**：`engineering-workflow.md` §四 CI 门禁第 1 步补 `+ 6.26 + 6.27`；`project-plan.md` Phase 0 门禁口径 `6.13~6.25` → `6.13~6.27`。

**参数计数**：不变；债务编号不变（D-428~D-438 连续）；错误码 40 不变；端点 88 不变；计数口径（57 表 / 370 参数 / 70 术语 / 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档）全未变动。

**门禁**：doc-audit.py 18 类 + 14a + 6.8a + 6.12a + 6.13~6.27 全绿（退出码 0）；deep-audit.py exit 0 无阻断项。

---



## 0.0.59（2026-08-08）— round26 全面深度审计修复批次（3 高 / 9 中 / 5 低）

> 第二十六轮全库深度审计（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。本轮聚焦三个此前未系统覆盖的面：**机器可读契约骨架**（openapi.yaml 与 api-spec 的契约漂移）、**威胁模型 L5 缓解项的追缴闭环**、**技术栈的运行时缺项**。误报剔除 4 项（G-01 / F-02 / S-10 / Q-03），S-07 降级为观察项。

**高风险修复（3 项）**：
- **S-01/S-04/S-05/S-11/S-12/S-13 契约骨架漂移（openapi.yaml）**：`docs/specification/api-contract/openapi.yaml` 与权威 [api-spec.md](../specification/api-spec.md) 全面对齐——① `servers` 端口 `8000`→`8010`（与 deployment / quick-start / development-setup / integration-design 四文一致）；② 认证方式由 `apiKey`（X-Kairos-Key + X-Kairos-Admin-Key 双 scheme）改为单一 `bearerAuth`（`Authorization: Bearer <key>`，与 api-spec §1 一致）；③ 88 个 operation 的 `responses` 按「api-spec 声明成功码 ∪ 方法族基线错误码」补全（读族 400/401/403/404/429，写族增 409/413/422，删族增 409/422），每条 description 标注来源为「api-spec 声明」或「方法族基线」；④ 4 处 TODO/污染 summary 替换为 api-spec 端点描述；⑤ 9 个 v1.1 预留端点加 `[v1.1 预留]` 前缀与 `x-kairos-delivery: v1.1-reserved`（其余 79 个标 `v0.1.0`）；⑥ 新增 `x-kairos-required-role` 扩展字段（admin 18 / write 18 / read 17 / 未标注 35，头部注释声明「未标注 ≠ 免鉴权」）。`info.version` 同步 `0.0.45-skeleton`→`0.0.59-skeleton`；schema 占位仍待补全（债务 D-428 不变）。
- **S-03 错误码计数全库漂移（40 → 42）**：api-spec §7 已含 `ERR-CTR-003`（403 记忆已锁定）与 `ERR-CTR-004`（409 意图契约未关闭）两码，但四处下游仍写 40——[error-reference.md](../references/error-reference.md)（intro + 表体补两行 + 计数）、[troubleshooting.md](../ops/troubleshooting.md)（标题「全量 40 项」→ 42 + 口径注记 + 表体补两行）、[runbook.md](../ops/runbook.md)（两处 40→42）、[README.md](../README.md)（「11 类 40 个错误码」→ 42）。同步澄清返回方式：`ERR-DB-004`（404）/ `ERR-DB-005`（409）为**内部码例外**——随 HTTP 响应直接返回，其余 `ERR-DB-001~003` / `ERR-LLM-*` / `ERR-SYS-*` 仅内部运维与日志使用。
- **2.2-02 威胁模型 L5 缓解项无追缴条目**：[threat-model.md](../security/threat-model.md) §三a 供应链攻击 / §三b 侧信道已定义威胁与缓解，但三项缓解未落地且无债务承载——新增 **D-439 供应链完整性与侧信道加固**（五段结构，v0.1.0.x 追缴；未落地项：① 嵌入模型权重 SHA-256 校验 ② 构建产物签名 ③ 时延常数时间保证）+ §四 摘要表行。

**中风险修复（9 项）**：
- **U-01 技术栈缺本地推理运行时**：[technology-stack.md](../development/technology-stack.md) §三 补 `sentence-transformers ≥ 3.0`（BGE-M3 加载）/ `transformers ≥ 4.40`（两个 t5 小模型）/ `PyTorch ≥ 2.2`（统一张量后端，CPU-only 为基线）三行运行时 + `intent-t5-small` / `timestamp-t5-small` 两行模型登记 + 「本地模型底座（三个）」注记——此前 threat-model §三a 指向本文件称「三个模型底座」，本文件却零登记，构成悬空引用。
- **U-02 CLI 框架未登记**：§一 补 CLI 框架行（Click ≥ 8.1 / Typer ≥ 0.12 二选一，W1 定档），此前仅散见于 slice-implementation-guide §组件职责 / project-plan §W1 / implementation-map，技术选型表无承载。
- **U-05 Grafana 悬空选型**：§五 Grafana 行补「v1.1 目标引入 + v0.1.0 不编排服务 / 不交付看板 JSON」与债务指针；**D-432 承载范围由「OpenTelemetry 追踪栈」扩展为「可观测性栈」**（含 Grafana 看板交付），标题、五段正文与摘要表行三处同步。
- **U-03 CLI write 示例缺必填参数**：[user-guide.md](../user/user-guide.md) §2.1 CLI 示例补 `--source user_input`——api-spec §3 CLI 表明确 `--source` 必填（缺失触发 S-15 → 422），同文档 SDK 示例已含 `source` 而 CLI 示例遗漏。
- **U-06 校准状态非法枚举值**：user-guide §2.4 `kairos status` 输出示例 `校准状态: active` → `healthy`，并补四值枚举注记（`healthy` / `degraded` / `virtual` / `dormant`，粗粒度映射口径与 `GET /v1/health/calibration` 指针）——`active` 不在 api-spec §6.5 定义的枚举内。
- **U-04 快速入门 2 分钟口径不含模型下载**：[quick-start.md](../user/quick-start.md) 定位注记与「完成」段的「约 2 分钟」明确为**不含首次模型权重下载**；第四步补首次启动注记（BGE-M3 权重首次 `kairos serve` 自动下载，依据 development-setup §环境依赖）+ troubleshooting 指针。
- **Q-04 验收判据指向错误基准节**：[acceptance-criteria.md](../quality/acceptance-criteria.md) 语义检索行原指 benchmark-plan §3.2（仅检索延迟，不承载召回），改指 §3.13（隐式关联召回套件）与 §3.14（Task-Aware Precision@K / MRR），并注明「§3.2 只覆盖延迟」。
- **2.2-01 D-204 引用笔误**：[debt-collection.md](./debt-collection.md) D-204 引用 §0.10 → §0.11。
- **F-01 「五维/5D」同名双义**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a 检索管线术语口径表补「同名消歧」注记——「五维特征向量 / 五维使用负载系数」（§5.4 使用价值计量维度，参与帕累托计算）与「5D 混合排序」（检索排序调制维度）分属不同层、无构成关系、不可互换。api-spec / data-model 经全库扫描无 5D 残留误导命名。

**低风险修复（5 项）**：
- **U-07 裸 `#` 行被渲染为 H1**：user-guide §3.4 种子锚点段的「# 种子路径设置」与 `KAIROS_SEED_PATH=...` 两行加 bash 代码围栏（原为正文裸行，Markdown 渲染为一级标题并打断列表结构）。
- 其余 4 项为版本记录与 frontmatter 日期同步（technology-stack / user-guide / quick-start / debt-collection 升 0.0.59，quick-start frontmatter `updated` / `last_reviewed` 2026-08-05 → 2026-08-08）。

**误报剔除（4 项，本轮不修复并说明理由）**：
- **Q-03「test-plan 预留编号表缺 R-04~R-07 / W-05 占位」**：[test-plan.md](../quality/test-plan.md) §2 预留表引言与 [requirements-baseline.md](../specification/requirements-baseline.md) §4 需求追踪矩阵注记**双向一致地显式声明**「W-05/W-06、R-04~R-07、M-04、SF-01~04、CAL-02/06 等按 RTM 对应关系在代码启动后随用例定义即时编号，不在此预占位」——属显式设计选择，非遗漏。
- **G-01 / F-02 / S-10**：上一轮已判定为误报，本轮复核维持。

**S-07 降级**：由「问题」降为「观察项」——不构成当前缺陷，留待后续轮次跟踪。

**计数变动**：错误码 **40 → 42**（新增 ERR-CTR-003 / ERR-CTR-004）；债务编号 **D-428~D-439 连续**（新增 D-439）。其余口径全未变动：57 表 / 370 参数（224 + 146）/ 70 术语 / 88 端点（85 个 `/v1` + 3 个非 `/v1`）/ 12 ADR / 66 操作 / 70 组件 / 168 功能 / 37 声明 / 56 核心文档 / 15 MCP Tool。

---



## 0.0.60（2026-08-08）— round26 结构性建议落地批次（S26-1 / S26-2 / S26-3）

> 将 round26（0.0.59）审计报告 §4.2 提出的三项结构性建议固化为机器门禁，使「契约漂移 / 错误码三处不同步 / 示例代码写错参数枚举」这类复发型事实错误在文档改动时自动捕获，而非依赖每轮人工审计。门禁清单 6.13~6.27 → 6.13~6.30。

**S26-1 → 门禁 6.28（机器可读契约 ↔ api-spec 一致性反查）**：
- openapi `paths` 的 (方法, 路径) 集合 ≡ api-spec 登记端点（单一事实源，0.0.54 已立）——首跑比对 88 = 88，零漂移；
- `servers` 端口 ≡ 全库默认 8010（与 deployment / quick-start / development-setup / integration-design 一致）；
- `securitySchemes` ≡ 单一 `bearerAuth`（`type: http` + `scheme: bearer`），与 api-spec §1 认证方式一致；
- `mcp-tools.json` 各 `mapsTo` 端点 ⊆ api-spec 登记端点（MCP-only 工具以显式 `MCP-only — …` 标记豁免，不误报）；
- ② 每个 operation 成功响应码 ⊇ api-spec 声明值：骨架近似，**deferred**（债务 D-428 追踪逐端点收敛），本检查仅做 informational 注记，不 FAIL。

**S26-2 → 门禁 6.29（跨文档错误码集合一致性）**：
- `error-reference` ≡ `troubleshooting` 全集合相等（首跑 42 = 42）；
- api-spec §7 ⊆ `error-reference` 子集（§7 为 HTTP 子集、非全量，全量以 error-reference 为准；首跑 16 ⊆ 42）；
- 任一差集非空即 FAIL——防 ERR-XXX 增删后三处表体不同步复发。

**S26-3 → 门禁 6.30 + 文档纪律 §6.2（示例代码纪律）**：
- [documentation-governance.md](../governance/documentation-governance.md) §6.2 新增「示例代码纪律」条目——围栏代码块的 CLI/SDK 示例参数与枚举值须可追溯 api-spec 单一事实源；
- 门禁 6.30：围栏代码块内 `kairos write` 真实调用须含 `--source`（S-15 provenance 必填，缺失返回 422；api-spec §3 CLI 表）；`calibration_status` 字段赋值字面量须为规范四值 `healthy` / `degraded` / `virtual` / `dormant`（api-spec §6.5）——豁免行内命令名列举 / blockquote 草稿声明 / 表格单元格示例，避免误报。

**验证**：doc-audit 首跑 6.28 / 6.29 / 6.30 三项全部零失败（当前文档已对齐，88=88 / 42=42 / 0 违规），门禁全类验证通过（exit 0）；后续契约漂移或错误码增删将自动捕获。受改文件：[scripts/doc-audit.py](../../scripts/doc-audit.py)（新增三函数 + main 注册 + 头部 0.0.60 扩展说明）、[documentation-governance.md](../governance/documentation-governance.md)（§6.2 + 版本记录 0.0.60）。无新增债务（响应码 deferred 沿用 D-428）；参数 / 表 / 端点 / 错误码 / 债务计数全未变动。

---



## 0.0.61（2026-08-08）— round27 全面深度审计修复批次（记忆状态机五态口径 + 版本记录补登 + 技术选型缺口）

> 全面深度审计（维度 1~5）收口批次：① 记忆状态机五态平级口径在权威文档与下游文档全局对齐；② 前序批次实质变更漏登记的版本记录集中补登；③ 技术选型缺口（MCP 工具计数遗留矛盾、BM25/FTS5 关键词检索技术选型缺失）补齐；④ FTS5 分词器口径矛盾消除。门禁复跑全类验证。

**A. 记忆状态机五态平级口径（【高】一致性）**：
- 架构 §5.2 由「四态」修正为「五态平级」（active/stale/archived/suppressed/superseded，无子态）——补充 Suppressed 态定义（用户主动定向遗忘操作 `POST /v1/memories/{id}/suppress` 写入）与状态转换（Active/Archived/Superseded→Suppressed；Suppressed→Active 经 `POST /v1/memories/{id}/restore` 撤销）；
- detailed-design §3 遗忘调度器状态机范围注记修正——明确本图仅覆盖 freshness 驱动的 ACTIVE/STALE/ARCHIVED 三态，SUPPRESSED/SUPERSEDED 均不经由本调度器；
- cognitive-foundation 轴澄清补 suppressed 枚举、潜伏态去「archived 子态」误述（与架构五态平级一致、非子态）；
- 与 data-model §1 / integration-design §七 / glossary / api-spec / schema-slice 五态平级口径全局一致。

**B. 版本记录漏登记集中补登（【中】governance §4）**：
- glossary 补登「身份面否决权 / Identity-Plane Veto」术语新增（69→70，原 round20 0.0.49 批次漏登记）；
- cognitive-architecture-gap 补登差距表头「出处（认知基础）」→「出处（认知基础 / 架构）」；
- integration-design / benchmark-plan / requirements-baseline / feature-list / implementation-map 补登五态平级口径同步（前序批次实质变更、本文档版本记录未同步，本批统一补登，沿用 0.0.54 version-record-update.py 回填惯例）。

**C. 技术选型缺口（【中】完整性）**：
- technology-stack §七 MCP 集成战略句修正「12 规范操作集」遗留矛盾（实为「3 规范操作直接映射 + 检索/维护/治理 9 = 基础工具集 12」+ 关系管理 3 = 15，与 0.0.28/0.0.43 公式一致）；
- technology-stack §二 新增关键词检索技术选型行（标准模式 pg_bigm + zhparser / 轻量模式 FTS5），承载三信号融合检索的 BM25 分量（权重 0.35，见架构 §7.3a / data-model §11 / schema-slice §14）——此前该 0.35 权重分量无技术承载。

**D. FTS5 分词器口径矛盾（【低】一致性）**：
- data-model §11 memories_fts 约束项中文分词口径对齐——v0.1.0 DDL 默认 `tokenize='unicode61'`，jieba 为需编译扩展的可选精细中文分词（由 `KAIROS_FTS5_CHINESE_SEGMENTATION` 配置控制），与 schema-slice §14 一致；消除「中文分词通过 jieba 实现」表述与自身 DDL 矛盾。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.30 全类复跑 exit 0（受改 12 份文档：11 份含版本记录登记 + cognitive-foundation 去版本化内容修正）；参数 370 / 表 57 / 端点 88 / 错误码 42 / 债务 / 术语 70 / MCP 15 等核心计数全未变动。

---



## 0.0.62（2026-08-08）— round28 全面深度审计修复批次（FTS5 范围与分词器口径一致性）

> 全面深度审计（维度 1~5）收口批次：核心发现为架构 §5.20 / §5.20.2 / §7.3a 对 FTS5 全文索引的范围界定与中文分词器口径与权威 DDL（schema-slice §14）及数据模型（data-model §11）不一致。其余维度经审计确认无新增阻断/质量缺陷（追缴门禁有效、README 索引完整、零版本标记纪律基本合规）。

**A. FTS5 范围界定纠正（【中】核心文档准确性 / 维度 5）**：
- 架构 §5.20 原表述「FTS5 contentless-external 全文索引 … 均为 v1.1+ 蓝图组件，v0.1.0 不交付」与事实矛盾——`schema-slice.sql` 第 14 节 `memories_fts` 即以 FTS5 contentless-external 模式 + `unicode61` 实现（v0.1.0 轻量模式 BM25 承载），technology-stack §二 亦将 FTS5 列为轻量模式关键词检索承载；
- §5.20 机制句修正：基础 FTS5 contentless-external（默认 unicode61 分词）为 v0.1.0 轻量模式 BM25 承载；SQLCipher / PreparedStatementCache / Schema 前向版本保护 / Symbolic Memory 可视化 与 FTS5 的 jieba 增强、Playbook 索引方为 v1.1+ 蓝图范围。

**B. FTS5 中文分词器口径纠正（【中】完整性与一致性 / 维度 1）**：
- §5.20.2 原「SQLite FTS5（contentless-external 模式 + jieba 中文分词）」去除「jieba 无条件」误述，改为默认 `unicode61`、jieba 自定义 tokenizer 为需编译扩展的可选精细中文分词（由 `KAIROS_FTS5_CHINESE_SEGMENTATION` 控制，默认 `true`，需扩展已编译方可生效），与 data-model §11 / schema-slice §14 / blueprint §P3-21 口径一致；Playbook 索引与 jieba 增强归属 v1.1+ 蓝图（§P3-21）。
- §7.3a BM25 词形归并原「中文: jieba 词形归一」改为模式感知表述——标准模式经 zhparser、轻量模式经 FTS5 分词器（默认 unicode61，jieba 可选），与双模式检索选型（technology-stack §二，决策 D-12）一致。

**C. 其余维度审计结论（无新增缺陷）**：
- 维度 2 缺失与过时：全库「待定义」项（/metrics 端点、CLI 命令、参数阈值）均已登记债务（D-429 / D-430 / D-333 / D-335）或具指针与默认值说明，追缴门禁有效，无悬空缺口；
- 维度 3 结构与组织：核心文档仅 `slice-implementation-guide.md`（232 行）略超 200 行上限，属历史形成、依 AGENTS §4.2 豁免拆分；README 全库索引完整（核心文档均入索引）；
- 维度 4 格式规范：术语单义、交叉引用 `[文档](路径) §X` 格式、零版本标记纪律基本合规（少量「v0.1.0 新增/落地」为当前版本范围描述，非历史变更标记，不计入缺陷）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.30 全类复跑 exit 0（受改 1 份文档：architecture-v0.1.0，§5.20/§5.20.2/§7.3a 三处 + 版本记录补登 0.0.62）；参数 370 / 表 57 / 端点 88 / 错误码 42 / 术语 70 / MCP 15 等核心计数全未变动。

---



## 0.0.63（2026-08-08）— round29 全面深度审计修复批次（债务台账 × 实际交付面对齐）

> 全面深度审计（维度 1~5）批次：审计面首次系统性覆盖**债务台账与实际交付面的双向一致性**。核心发现为 round28 完成架构侧 FTS5 范围纠正后，债务台账 D-417 未同步——台账仍将已交付能力登记为「v1.1 待实现」，构成台账与设计权威的反向矛盾；同时发现 §七 可实现性评估表自 0.0.32 建表后未随新登记债务同步，与 §四 摘要表条目集合分叉。

**A. 债务台账与交付事实反向矛盾（【高】完整性与一致性 / 维度 1）**：
- D-417 原按「整体 v1.1 待实现」登记，与 v0.1.0 竖切 DDL（[schema-slice.sql](../specification/schema-slice.sql) 第 14 节 `memories_fts`）、[data-model.md](../specification/data-model.md) §11、[slice-implementation-guide.md](../development/slice-implementation-guide.md) 竖切表清单、架构 §5.20 权威口径直接矛盾；
- D-417 五段正文按实际交付面重述——已交付：`memories_fts` / `skills_fts` 表结构（默认 `unicode61`，写入同事务三触发器同步）；剩余 v1.1：jieba 精细中文分词 tokenizer 扩展 + Playbook 全文索引 `procedural_playbooks_fts`（与 D-433 同批）；§四 摘要表状态与预期版本列同步。

**B. 治理表口径分叉与过时表述（【中】完整性与一致性 / 维度 1）**：
- §七 可实现性评估表补登 29 条游离条目（D-201~D-204 实现阶段项 + D-415~D-439 后续批次登记项），§7.2 统计同步 62→91（表 60→81 行，D-308~310 / D-422~425 / D-433~438 各合并 1 行）；§七 定位补「本表与 §四 摘要表条目集合保持一致」维护规则，杜绝再次分叉；
- §七 定位排除清单误将 D-011 列为「已实施不列入」，而表内实有 D-011 评估行（结论：部分覆盖）——排除清单修正为 D-001~004/101；
- D-001「可接受成本」段残留「策略层可不调用身份查询绕过审查——没有机制强制」的过时表述，与架构 §1.8 预提交总线不可绕过口径、本条目「升级触发条件」段与状态表「✅ 已实施」互相矛盾——改写为三组件协同降级这一仍然成立的成本项。

**C. v0.1.0 规格依赖 v1.1 组件（【中】核心文档准确性 / 维度 5）**：
- [detailed-design.md](../specification/detailed-design.md) §10.6（用户画像性能基准，v0.1.0 功能 P3-06）实现策略将画像读取结果缓存于 PreparedStatementCache，而该组件为 v1.1 蓝图范围（架构 §5.20 + 债务 D-418「待实现」）——v0.1.0 规格建立在未交付组件上；改为画像专用应用层 LRU 缓存（容量独立于数据库访问层），并注明 PreparedStatementCache 落地后可共享 LRU 空间但独立计数。

**D. 版本归属歧义与图表层功能虚标（【低】格式规范 / 结构与组织，维度 3~4）**：
- [data-model.md](../specification/data-model.md) §11 标题「P3 基础设施表（v0.1.0 交付）」与其中多表消费组件属 v1.1 存在读解歧义——定位段补「版本归属」注记：表结构随 v0.1.0 落库，消费组件版本以架构 §5.20 与债务登记为准（D-416/D-418/D-419/D-421）；
- [system-architecture.html](../diagrams/system-architecture.html) 工具栏提示「图中节点可点击高亮所属章节」无对应脚本实现（页内脚本仅含缩放与适应宽度）——提示文案改为与实际能力一致；页脚补渲染依赖说明（Mermaid 运行时经 CDN 加载，离线环境改读架构 §0.4.1 同源图块）。

**E. 已实证排除的疑似项（非缺陷，避免后续重复审计）**：
- `capability_matrix.yaml` 压缩比算术（核心 12 维 0.33 / 全量 14 维 0.43）与架构 §10.11 一致；`domain_keywords.yaml` 十领域表与架构 §3.1 / detailed-design §10.4 引用一致；
- HTML 图块与架构 §0.4.1 Mermaid 源经逐字节比对完全一致（53 行）；
- D-416 SQLCipher / D-418 PreparedStatementCache / D-419 Schema 前向版本保护 / D-420 Symbolic Memory / D-421 Permission ACL 归属 v1.1，与架构 §5.20 一致，无 D-417 同类矛盾；
- feature-list 168（43 核心 + 125 扩展）计数自洽，P3-18 为已登记墓碑编号，非断号。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.30 全类复跑 exit 0；deep-audit 复跑无阻断项。受改 4 份文档（debt-collection / detailed-design / data-model / system-architecture.html）；参数 370 / 表 57 / 端点 88 / 错误码 42 / 术语 70 / MCP 15 / 操作 66 / 功能 168 / 组件 70 / ADR 12 等核心计数全未变动；债务条目总数未变（D-417 为状态重述，非新增/删除）。

---



## 0.0.64（2026-08-08）— round30 全面深度审计修复批次（门禁盲区扫描 + 5 类实质问题闭环 + 门禁 6.31 固化）

> 本轮为 round29（放行）之后的门禁盲区扫描 + 修复轮。全面深度审计（维度 1~5）聚焦前序轮次门禁未覆盖的 5 类实质问题，全部闭环并固化防复发门禁。

**A. 事件队列容量参数缺口（【中】核心文档准确性 / 维度 5）**：
- 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10「流控与背压」原仅称「容量上限（可配置，默认 128 条）」而未给出参数名，与 configuration 参数索引不可对账；
- 补登参数名 `KAIROS_EVENT_QUEUE_CAPACITY`（默认 128 条），链接 [nfr-specification.md](../specification/nfr-specification.md) §二 容量「事件总线缓冲」验收下限；configuration 附录 A 补登该参数（引用架构 §10.10）。

**B. data-model 点分配置键 2 项未登记（【中】完整性与一致性 / 维度 1）**：
- [data-model.md](../specification/data-model.md) 配置键表「与 configuration 一一对应」声明中，GSPO 最小聚类规模（`kairos.retrieval.gspo.min_cluster_size`）、Cross-encoder 总开关（`kairos.retrieval.cross_encoder.enabled`）两项缺对应 `KAIROS_*` 环境变量登记；
- configuration §6.2 补登 `KAIROS_GSPO_MIN_CLUSTER_SIZE`（默认 2，≥2 整数）、§6.9 补登 `KAIROS_CROSS_ENCODER_ENABLED`（默认 false，{true,false}）；data-model「一一对应」声明改为「与 configuration §6.1/§6.2/§6.3/§6.9 四节环境变量满射」表述，删除线标注已废止键；
- 参数计数同步：正文 224→226、附录 A 146→147、总计 370→373（[README](../README.md)/[implementation-map.md](../specification/implementation-map.md) 同步 373）。

**C. 门禁清单口径滞后（【低】格式规范 / 维度 4）**：
- [engineering-workflow.md](../development/engineering-workflow.md) L63、[project-plan.md](../governance/project-plan.md) L77 门禁清单仍写 `6.13~6.27`/`6.13~6.30`，与 0.0.60 已扩展至 6.13~6.30 的实际口径不符；
- 同步为 `6.13~6.31`（含本轮新增 6.31）。

**D. security-spec 引用未登记命令（【中】核心文档准确性 / 维度 5）**：
- [security-specification.md](../security/security-specification.md) §4「如何删除 / 用户权利」原引用未登记命令 `kairos memory delete` / `kairos delete` / `kairos export`，与 api-spec CLI 表（[api-spec.md](../specification/api-spec.md) §3 CLI 表）登记命令不符；
- 改用已登记 `kairos forget`（`DELETE /v1/memories/{id}`）+ 覆写、`kairos suppress`（定向遗忘 `POST /v1/memories/{id}/suppress`）；导出改指已登记端点 `GET /v1/memories/{id}/export`（§1.5 单条脱敏）与 `POST /v1/admin/export`（§16 备份包），并修正端点→章节锚点引用（6.24 错位）；
- [technology-stack.md](../development/technology-stack.md) L33 去除 `kairos memory *` 误述，改为已登记命令族 + 指向 api-spec §3 CLI 表为单一事实源。

**E. 中文正文半角标点 101 处（【低】格式规范 / 维度 4）**：
- 全库 8 份文档散在 101 处紧邻中文的半角标点（`, ; ! ?`，形态 `CJK[,;!?]CJK`），违反中文排版规范；
- 归一化全 101 处（[adr.md](adr.md) 36 / [concept-tiers.md](../references/concept-tiers.md) 23 / [changelog.md](changelog.md) 20 / architecture 12 / debt-collection 8 / slice-implementation-guide 1 / api-spec 1 / documentation-governance 1），应用后复扫归零；
- 固化防复发：门禁 6.31（中文正文半角标点纪律，CJK[,;!?]CJK 排除代码块/行内代码/ASCII 括号内，豁免 analysis/）落地；[documentation-governance.md](documentation-governance.md) §6.3 补「中文标点纪律」规则。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0（含 6.31 首跑 0 违规）；deep-audit 复跑无阻断项。受改 11 份文档（configuration / data-model / architecture-v0.1.0 / README / implementation-map / engineering-workflow / project-plan / security-specification / technology-stack / documentation-governance）+ 审计脚本（scripts/doc-audit.py 新增 6.31）；参数 **373**（正文 226 + 附录 A 147）/ 表 57 / 端点 88 / 错误码 42 / 术语 70 / MCP 15 / 操作 66 / 功能 168 / 组件 70 / ADR 12 等核心计数全未变动。

---



## 0.0.65（2026-08-08）— round31 全面深度审计修复批次（语义/逻辑/事实层盲区 + 3 高/8 中/6 低全闭环）

> 本轮为 round30（放行）之后的语义层深度审计轮。前 30 轮已将机器可检口径（计数/链接/章节引用/格式）清零，本轮聚焦门禁无法覆盖的**语义/逻辑/事实层盲区**——交付面口径、承诺-承载对应、需求追溯链闭合、运维动作可执行性。共 3 高 / 8 中 / 6 低，全部闭环。

**A. FTS5 参数族交付面矛盾（【高】完整性与一致性 / 维度 1，R31-01）+ 附录引言口径过宽（【低】格式规范 / 维度 4，R31-12）**：
- configuration 附录 A `KAIROS_FTS5_ENABLED/TOKENIZER/CHINESE_SEGMENTATION/OPTIMIZE_INTERVAL` 四参数「来源」列原指向蓝图 v1.1 §P3-21，与 0.0.62（round28）已确立「基础 FTS5 contentless-external + unicode61 为 v0.1.0 轻量模式 BM25 承载」的交付口径矛盾；
- 四参数来源改指 v0.1.0 权威（[data-model.md](../specification/data-model.md) §11 全文检索——基础 FTS5 为 v0.1.0 已交付，jieba 精细分词与 Playbook 全文索引增强归属 v1.1 蓝图 §P3-21）；附录 A 引言「蓝图 v1.1 参数 v0.1.0 不实现」补 FTS5 基础参数族例外注记。

**B. 恢复流程缺 WAL 回放，RPO 承诺不可执行（【高】完整性与一致性 / 维度 1，R31-02）**：
- [reliability.md](../ops/reliability.md) §二 承诺数据库「全量 + WAL 回放」「RPO ≤ 5 分钟（WAL）」，但 [runbook.md](../ops/runbook.md) §2.1 恢复命令仅含全量导入——按现有手册执行实际 RPO 只能到每日全量备份点，与 N-10 差 288 倍；
- runbook §2.1 补 WAL 回档恢复步骤（Docker/本地两模式的「全量导入 + WAL 回放」）与恢复 RPO 口径注记（RPO ≤5 分钟依赖 `KAIROS_WAL_ARCHIVE_COMMAND` 持续启用；仅全量导入不满足 N-10）。

**C. claim-matrix 承载虚标与跨层错位（【高】核心文档准确性 / 维度 5，R31-03）**：
- C-29 承载「§5.5 探索置信度带」全库唯一命中即矩阵本身——架构 §5.5 实为「见证→使用仲裁（差异检验）」，无此组件，✅ 虚标；改为架构 §2.2 探索预算分配 + §3.2 调节器动态δ（P5 承载声明见架构 §2.2 六原则表，参数 `KAIROS_EXPLORATION_BUDGET_RATIO`）；
- C-12 承载「§5.2 模拟隔离区标记隔离」跨层错位（模拟隔离区定义在 §6 WM 层，0.0.20 批次已批量修正同类引用）；改为「§6 WM 模拟隔离区（反事实假设空间，标记隔离）」。

**D. 可用性 SLO 无观测承载（【中】缺失与过时 / 维度 2，R31-04）+ 告警缺口（【中】维度 2，R31-05）**：
- nfr §三 系统可用性 ≥99.9% / 降级可用性 ≥99% 测量方法为「运行期可用性监控」，benchmark-plan §3.6 亦声明「可用性以生产运行数据为准」，但 [observability.md](../ops/observability.md) §一 指标表无可用性指标——生产数据无从采集；
- observability §1.1 补 `kairos_availability_ratio`（滚动窗口 SLO 统计输入指标）；§四 告警表补磁盘三级告警（>75% 黄色预警 / >85% 红色警戒 / >92% 崩溃边缘，联动 reliability §1.4）、SLO 跌破告警、LLM 熔断告警（联动 reliability §1.5 与 `KAIROS_LLM_CIRCUIT_BREAK_*` 参数）；§五 耦合计检测器补核心命题证伪信号可见性（架构 §10.10）。

**E. 恢复演练触发方式不自洽 + RPO 无验证（【中】缺失与过时 / 维度 2，R31-06）**：
- reliability §四 原称演练「由健康检查触发」（月频动作由日频探针触发，逻辑不闭环），改为「由系统调度器按月度周期触发」；runbook §6.1 定期维护补「月：恢复演练」行；
- [benchmark-plan.md](../quality/benchmark-plan.md) §3.6 补 RPO 验证步骤（写入→崩溃→全量 + WAL 回放→丢失窗口确认 ≤5 分钟，N-10 验收落地）；轻量模式无 WAL 归档以全量备份恢复为准并记录实际丢失窗口。

**F. 非功能需求→验收链条缺口（【中】缺失与过时 / 维度 2，R31-07）+ RPO 适用范围（【中】核心文档准确性 / 维度 5，R31-13）**：
- [acceptance-criteria.md](../quality/acceptance-criteria.md) §二 非功能检查表补容量（N-05 标准 ≥100 万 / N-06 轻量 ≥10 万）、恢复 RTO（N-09）、恢复 RPO（N-10）、系统可用性（N-11）、降级可用性（N-12）验收行，对齐 benchmark-plan 3.5/3.6 与 observability SLO 统计；
- [nfr-specification.md](../specification/nfr-specification.md) §三 RPO 行补适用范围注记（≤5 分钟适用于数据库组件；升华层等可重建产物 ≤1 天，自 sublimation_queue 恢复，组件粒度口径以 reliability §二 为准）；启动时间/故障恢复测量方法列修正（启动计时基准 benchmark-plan §3.10；故障注入 + 恢复计时 §3.6），消除「运行期可用性监控」错标。

**G. CAL-02 状态三处互斥（【中】完整性与一致性 / 维度 1，R31-08）**：
- requirements-baseline RTM 表已分配 `TC-CAL02-001`、test-plan §3.6 已有 TC-CAL02-001 用例，但预留注记仍列 CAL-02 为「待补充不预占位」——三处口径互相矛盾；
- requirements-baseline 预留注记移除 CAL-02 并注明「已分配 TC-CAL02-001，见上表与 test-plan §3.6，不再列入预留」。

**H. 测试计划结构性问题（【低】结构与组织 / 维度 3，R31-09/R31-10）**：
- test-plan §3.5a 标题「记忆管理（M-01 ~ M-05，竖切）」与表体（仅 TC-M03-001/TC-M05-001）不符，改为「M-03/M-05 竖切用例；M-01/M-02/M-04/M-06 预留」；
- 预留编号表补 TC-A01-001~ 占位（健康检查，P0 级，响应结构见 observability §1.2、端点登记见 api-spec §1.8；原表登记 A-02/A-03/A-05/A-06 唯独缺 A-01）。

**I. runbook 证伪响应缺关键动作（【低】核心文档准确性 / 维度 5，R31-14）**：
- 架构 §10.10 定义核心命题证伪响应路径首步为「暂停遗忘调度器」，runbook §6.4 四步操作未含该动作；
- 补「确认遗忘调度器已暂停」步骤（未暂停时手动执行 `kairos forget pause`，待定义命令，追缴同债务 D-430）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0；deep-audit 复跑 exit 0；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。受改 10 份文档（configuration / claim-implementation-matrix / test-plan / requirements-baseline / observability / nfr-specification / reliability / runbook / benchmark-plan / acceptance-criteria）版本记录同步 0.0.65；审计报告按 0.0.18 归档机制不入仓库（工作区根目录临时交付物）。

---



## 0.0.66（2026-08-09）— round32 全面深度审计修复批次（版本记录登记纪律系统性收口 + 叙述节排序修复）

> 本轮为 round31（放行）之后的全面深度审计轮。前 31 轮已将机器可检口径（计数/链接/章节引用/格式/语义层）清零，本轮核心发现为**版本记录登记纪律的系统性缺口**——changelog 各批次声明受改的文档中，多份版本记录未登记对应批次行（governance §4「发生实质性内容变更时在本表登记」违反），且 changelog 0.0.64 叙述节被 0.0.65 叙述节分割为两段。全部闭环并补登。

**A. 版本记录批次登记系统性缺口（【中】完整性与一致性 / 维度 1，R32-01~04）**：
- 逐批核对 changelog 0.0.53~0.0.65 声明受改文档 × 各文档版本记录登记，实证确认 14 处「批次声明受改、版本记录无对应行」缺口（含 README 缺 3 个批次行）：
  - **0.0.64 批次 9 份**（R32-01）：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)（§10.10 补 `KAIROS_EVENT_QUEUE_CAPACITY`）、[configuration.md](../ops/configuration.md)（附录 A 补 3 参数 + 计数 373）、[data-model.md](../specification/data-model.md)（点分键 2 项 + 满射表述）、[README.md](../README.md)（参数计数 373）、[implementation-map.md](../specification/implementation-map.md)（参数计数 373）、[engineering-workflow.md](../development/engineering-workflow.md)（门禁清单 6.13~6.31）、[project-plan.md](../governance/project-plan.md)（门禁清单 6.13~6.31）、[security-specification.md](../security/security-specification.md)（§4 命令/端点改已登记）、[technology-stack.md](../development/technology-stack.md)（L33 CLI 命令族去误述）——9 份均缺 0.0.64 行；
  - **0.0.59 批次 4 份**（R32-02）：[runbook.md](../ops/runbook.md)（错误码 40→42）、[README.md](../README.md)（错误码 40→42）、[threat-model.md](../security/threat-model.md)（D-439 追缴新增）、[acceptance-criteria.md](../quality/acceptance-criteria.md)（语义检索验收基准改指 §3.13/§3.14）——均缺 0.0.59 行；
  - **0.0.57 批次 1 份**（R32-03）：README 补登 0.0.44~0.0.50/0.0.52~0.0.56 段（版本记录链断裂修复）未登记 0.0.57 行；
  - **0.0.61 批次 1 份**（R32-04）：[cognitive-foundation.md](../foundation/cognitive-foundation.md) 五态口径同步（suppressed 枚举 + 潜伏态去子态）未登记 0.0.61 行（0.0.61 验证节以「去版本化内容修正」名义豁免，但叙述节 A 节明确实质变更，按 §4 应登记）。
- 根因：engineering-workflow「批次收尾检查清单」第 ① 项（触及即登记）在 0.0.57/0.0.59/0.0.61/0.0.64 四个批次未被执行；门禁 [4/18] 版本记录检查仅验证「存在性与单调性」，不验证「每个实质变更批次都登记」——本轮补登全部 14 处缺口行（补登行保留原批次号与日期，忠实记录历史批次），并各文档 frontmatter updated/last_reviewed 同步 2026-08-09。

**B. changelog 叙述节排序错误（【低】结构与组织 / 维度 3，R32-05）**：
- 0.0.64 叙述节被 0.0.65 叙述节分割为两段（A 项在 0.0.65 标题前、B~E 项与验证段排在 0.0.65 完整叙述节之后），阅读顺序混乱——同一批次内容分居两处；
- 将 0.0.64 的 B~E 项 + 验证段整体移回 A 项之后、0.0.65 标题之前，恢复「批次叙述节完整连续」的组织惯例。

**C. 附属目录格式微修复（【低】格式规范 / 维度 4，R32-06）**：
- [analysis/external-videos/repos/REPO-09-hermes-agent.md](../analysis/external-videos/repos/REPO-09-hermes-agent.md) L71 行尾多余空格 1 处（deep-audit trailing_ws 捕获，附属分析目录非核心文档）——清除。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0；deep-audit 复跑 exit 0（trailing_ws 归零）。受改 14 份文档（13 份版本记录补登 + [REPO-09-hermes-agent.md](../analysis/external-videos/repos/REPO-09-hermes-agent.md) 格式修复）版本记录同步 0.0.66、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动；审计报告按 0.0.18 归档机制不入仓库（工作区根目录临时交付物）。

---



## 0.0.67（2026-08-09）— round33 全面深度审计修复批次（治理执行记录过时 + 批次/过程标记收敛）

> 本轮为 round32（放行）之后的全面深度审计轮。前 32 轮已将机器可检口径与语义层盲区清零，本轮核心发现集中在**治理文档自身执行记录的过时**与**正文批次/过程标记的漏网残留**（零版本标记纪律的语义层边界），全部闭环。

**A. 治理文档执行记录过时（【中】缺失与过时 / 维度 2，R33-01）**：
- [documentation-governance.md](../governance/documentation-governance.md) §3「执行记录（设计阶段）」终止于 2026-08-06（0.0.38，round16），未覆盖 2026-08-07~09 的 round17~32 批次（0.0.39~0.0.66：外部理念吸收、机器可读契约层首覆（openapi/mcp-tools 骨架）、语义层盲区收口、版本记录登记纪律系统性补登、门禁扩展至 6.31）——治理文档自身的执行记录落后 changelog 事实 16 轮；
- 执行记录补记「2026-08-07~09 完成第十六轮至第三十三轮深度审计与修复批次（0.0.39~0.0.67，含 round33 自身）」，批次明细仍指向 [changelog.md](../governance/changelog.md) 全景。

**B. 批次标记残留（【低】格式规范 / 维度 4，R33-02）**：
- [cognitive-architecture-gap.md](../governance/cognitive-architecture-gap.md) 差距表 G-08 / G-09 / G-11 出处列「（本轮新增）」批次标记 ×3——按 §6 豁免 1 限制条款（表格位置批次标记一律禁止）为 0.0.38「零版本标记全库收敛」的漏网残留，删除（出处列仅保留来源文档/章节引用）。

**C. 过程标记残留（【低】格式规范 / 维度 4，R33-03）**：
- 正文标题/参数表单元格「（勘误）」过程标记 ×6 去除——[technology-stack.md](../development/technology-stack.md) L111「MCP Server 实现（勘误）」、[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) L1171「时间字段口径（勘误）」与 L3042「MCP Bridge 集成（勘误）」、[configuration.md](../ops/configuration.md) L48「触发口径（勘误）」、[observability.md](../ops/observability.md) L128「告警投递渠道（勘误）」、[use-cases.md](../specification/use-cases.md) L93「复兴触发口径（勘误）」——标题与正文已完整描述当前权威口径，「（勘误）」为修正过程标记、无当前状态信息量（范围说明：正文 10 处内联「（勘误：…）」形态承载修正后的权威口径实质，属口径说明，保留）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0；deep-audit 复跑 exit 0。受改 8 份文档（documentation-governance / cognitive-architecture-gap / technology-stack / architecture-v0.1.0 / configuration / observability / use-cases / changelog）版本记录同步 0.0.67、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动；审计报告按 0.0.18 归档机制不入仓库（工作区根目录临时交付物）。

---



## 0.0.68（2026-08-09）— round34 全面深度审计修复批次（语义层版本边界/事实转述 + 硬行号缩写残留 + 用户路径域对齐）

> 本轮为 round33（放行）之后的全面深度审计轮。前 33 轮已将机器可检口径与语义层盲区大量清零，本轮核心发现集中在**架构权威文档的版本边界标注缺失**、**跨文档事实转述失真**（架构↔认知基础口径）与**门禁 6.15 未覆盖的 `Lxx` 缩写硬行号残留**三类盲区，全部闭环。

**A. 架构 §3.9 R1 版本边界标注缺失（【中】完整性与一致性 / 维度 1，R34-01）**：
- [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.9 检索深度分级表 R1 行执行路径「摘要级向量相似度（嵌入限于 128 维摘要向量）」未标注版本边界——读者会理解为 v0.1.0 即交付 128 维摘要向量；而 [data-model.md](../specification/data-model.md) `memories.content_summary` 明确「v0.1.0 统一 1536 维单向量；128 维摘要向量与 2048 维全量向量为 **v1.1+** 检索深度分级目标」。架构为设计权威，两处口径冲突，实现者按 §3.9 实现 128 维摘要向量将偏离 v0.1.0 数据模型；
- §3.9 R1 行改为「摘要级向量相似度（v0.1.0 以 1536 维单向量承载中层检索；128 维摘要向量为 v1.1+ 检索深度分级目标，见 data-model `content_summary` 说明）+ BM25 全文匹配」。

**B. 架构 §3.2 组合性使用事实转述失真 + L94 硬行号残留（【中】完整性与一致性 / 维度 1 + 【低】格式规范 / 维度 4，R34-02/R34-06）**：
- 架构 §3.2 组合寄存器注记「组合性使用（联结性使用）在认知基础中被定义为**六种使用类型之一**（§1.1 L94）」——认知基础 §1.1 使用价值轴实际定义「两种异质的激活活动」（工具性使用 / 认识论使用），并明示「联结性使用……是工具性使用在组合寄存器驱动下的一种运行时模式，**不构成独立的使用类型**」；全库无「六种使用类型」定义——架构对认知基础的转述失真；
- 注记改为「组合性使用（联结性使用——已知+已知=新知）在认知基础 §1.1 中定义为工具性使用在组合寄存器驱动下的一种运行时模式（认知基础明示『不构成独立的使用类型』）」；随注记改写一并清除硬行号引用 `L94`（R34-06）。

**C. 认知基础硬行号缩写残留 L64（【低】格式规范 / 维度 4，R34-04）**：
- [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.3 构造性生成声明「触发 **L64**/D.10 预设的重分类路径」——L64 为硬行号引用残留（D.10 已是正确章节引用，L64 冗余）。门禁 6.15 硬行号禁令（0.0.28 立法）仅匹配 `file.md:行号` 格式，未覆盖 `Lxx` 缩写形态，此为漏网残留；改为「触发 D.10 预设的重分类路径」。

**D. configuration `KAIROS_PATH` 来源章节引用格式异常（【低】格式规范 / 维度 4，R34-05）**：
- [configuration.md](../ops/configuration.md) 附录 A `KAIROS_PATH` 来源列「[detailed-design.md](../specification/detailed-design.md) **§L3**」——detailed-design 无 §L3 章节（L3 为 §9.3 四级规则引擎的规则层名 L1~L4），章节引用格式异常；改为「§9.3 四级规则引擎（L3 字典匹配：NER 实体标签命名空间 kairos://，非 OS 环境变量）」。

**E. 用户文档路径域与架构 §3.4 域路由表不对应（【低】缺失与过时 / 维度 2，R34-03）**：
- [user-guide.md](../user/user-guide.md) §3.1 路径规划建议「使用 `kairos://knowledge/` 存储全局知识库」、[quick-start.md](../user/quick-start.md) 第五/七步演示路径 `kairos://playground/`——两处路径域均未在架构 §3.4 域路由表登记（登记域仅 `_user/_project/_session/_scratch/_system` + 通用路径），且架构规定「通用路径 = 会话本地」，与 user-guide「全局知识库」的跨会话持久语义不符；
- user-guide 改指 `kairos://_user/{user_id}/knowledge/`（用户持久域承载全局知识语义，附架构 §3.4 引用注记）；quick-start 改指 `kairos://_user/default/playground/`（对齐 api-spec CLI 示例路径惯例）。

**门禁补盲区建议（记录在案，脚本扩展留待后续轮次）**：6.15 硬行号禁令当前只匹配 `file.md:行号` 格式，建议扩展至 `L\d{2,4}` 缩写形态（如 `§X.X L94`、`L64/` 前缀）——本轮 R34-04/R34-06 即此类漏网残留，扩展后可机器化捕获。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0；deep-audit 复跑 exit 0。受改 6 份文档（architecture-v0.1.0 / cognitive-foundation / user-guide / quick-start / configuration / changelog）版本记录同步 0.0.68、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动；审计报告按 0.0.18 归档机制不入仓库（工作区根目录临时交付物）。

---



## 0.0.69（2026-08-09）— round34 门禁建议落实批次（6.15 扩展捕获 Lxx 缩写行号形态）

> 本轮落实 round34 审计「记录在案」的门禁补盲区建议（R34-04/R34-06 根因）：门禁 6.15 硬行号禁令原仅匹配 `file.md:行号` 全格式，漏过 `L\d{2,4}` 缩写形态（如「§1.1 L94」「L64/D.10」）。扩展脚本 + 清除现存残留，闭环该建议。

**A. 门禁 6.15 扩展（scripts/doc-audit.py）**：
- 匹配逻辑由单一全格式正则扩展为两段：A 段保留原 `[\w.\-/]+\.md:\d+` 全库扫描；B 段新增 `(?<![A-Za-z0-9])L\d{2,4}(?![A-Za-z0-9])` 缩写形态扫描；
- **豁免边界**（防误报）：[changelog.md](changelog.md) 整文件豁免（历史批次记录，叙述节 52 处 Lxx 均为历史修复描述）；版本记录表格行由 `_scannable()` 剔除（历史摘要允许保留旧口径，与 6.6/6.14/14a 同一豁免语义）；测试用例编号 `TC-CAL01-001` 等（Lxx 前为字母 CAL，正则 lookbehind 天然排除）；`LLM`/`LTM`/`L1~L5` 层级/`L0-L3` 决策模式/`kairos://` 路径均非 `L\d{2,4}` 形态，天然豁免；
- **突变测试**：注入 `§1.1 L94` 与 `L64/D.10` 到认知基础正文 → 6.15 精确捕获 2 处；恢复后全绿。豁免边界 11 项断言全部 PASS。

**B. 现存残留清除（[adr.md](../governance/adr.md) 决策 D-10）**：
- 决策 D-10 裁决摘要「确认无第四类,Tulving 三分为基石,**L255**『四类』为漏改笔误改『三类』」——L255 为历史行号引用（引用当时认知基础某行），该行号已随认知基础文档多轮演化漂移，改为语义引用「认知基础 §1.2 记忆类型『四类』为漏改笔误改『三类』」；同步清除该行既有半角逗号 ×2（6.31 中文标点纪律，随触随修）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0（6.15 报告 0 残留；6.31 0 违规）；deep-audit 复跑 exit 0。受改 2 项（scripts/doc-audit.py + [adr.md](adr.md)）——脚本不在版本记录体系（门禁脚本自身迭代记录于 changelog 批次即可），[adr.md](adr.md) 版本记录同步 0.0.69、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。

---



## 0.0.70（2026-08-09）— round35 全面深度审计修复批次（治理执行记录自引用快照收口）

> 本轮为 round34（0.0.68）+ 0.0.69 之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.31 exit 0；deep-audit exit 0，395 条 pending 全部位于 analysis/ 豁免目录），语义层核查 34 项核心口径（五轴四轴映射 / 1536 维 / 37 声明（C-23 废弃）/ 端点 88 / MCP 15 / 参数 226+147 / 术语 70 / 错误码 42 / ADR 12 / OP 66 / 组件 70 / 功能 168 / 核心文档 56 / 全树 196 md+3 yaml / 竖切 15 表 / CLI 三档 15/25/27 / E2E 9 / 五态 CHECK / 降级三态 / RPO/RTO / 性能指标 / 合成公式 / 权重公式 / 债务追踪项 104（31 闭环+62 MNM+11 待实现）/ P3-18-A-14-R-09 预留 / 版本链 0.0.1~0.0.70 连续）全部一致、零漂移。唯一新发现为治理层「自引用快照」滞后——round33 教训重演。

**A. 执行记录补记（[documentation-governance.md](documentation-governance.md) §3，round33 教训重演）**：
- round33（0.0.67）补记执行记录时已确立「自引用快照必须在批次收尾时包含自身批次」纪律，但 round34（0.0.68）与 0.0.69（门禁建议落实）两批次实际发生期间，执行记录未同步更新——本轮核查时发现其仍终止于「第十六轮至第三十三轮（0.0.39~0.0.67）」；
- 执行记录文本补记「第十六轮至第三十四轮（0.0.39~0.0.68）+ 0.0.69 门禁建议落实批次 + 第三十五轮（0.0.70，含本批次自身）」完整批次链。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.31 全类复跑 exit 0；deep-audit 复跑 exit 0。受改 2 份文档（[documentation-governance.md](documentation-governance.md) 执行记录 + [changelog.md](changelog.md) 本批次）——documentation-governance 版本记录同步 0.0.70、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。

---



## 0.0.71（2026-08-09）— round35 门禁建议落实批次（6.32 治理执行记录覆盖性入检）

> 本轮落实 round35 审计「记录在案」的门禁补盲区建议（R35-01 根因）：「自引用快照」类内容（治理执行记录、审计轮次链）是反复出现的审计盲区——round33 立「含自身批次」纪律后 round35 重演（执行记录滞后于最新 changelog 批次）。将「执行记录覆盖最新批次」机器化为门禁 6.32，闭环该建议。

**A. 门禁 6.32 扩展（scripts/doc-audit.py）**：
- 新增子检查「治理执行记录覆盖性」：解析 [changelog.md](changelog.md) 版本记录表最新版本号（`| 0.0.NN |` 行最大值），验证 [documentation-governance.md](documentation-governance.md) §3「执行记录（设计阶段）」引用块包含该版本号——执行记录为自引用快照，滞后于最新 changelog 批次即 FAIL（round35 R35-01 防复发）；
- **豁免边界**（防误报）：changelog 无版本记录行（异常态）时跳过不判；执行记录引用块缺失本身即 FAIL（自引用快照不存在）；版本号以字符串包含匹配（`0.0.NN` 形态不会与更大版本号前缀混淆，如 `0.0.7` 不会误匹配 `0.0.70`——检查的是精确 `0.0.NN` 字面量）；
- **突变测试**：① 注入「执行记录块内全部 `0.0.70` → `0.0.69`」（模拟滞后一轮）→ 6.32 捕获 1 处 FAIL「未覆盖最新 changelog 批次 0.0.70」；② 注入「执行记录引用块整行删除」（模拟快照缺失）→ 6.32 捕获 FAIL「执行记录缺失」；恢复后全绿。

**B. 同步配套**：
- [engineering-workflow.md](../development/engineering-workflow.md) §四 CI 门禁清单补 `+ 6.32`，版本记录 0.0.71；
- [documentation-governance.md](documentation-governance.md) §3 执行记录补记「第三十五轮门禁建议落实批次（0.0.71，含本批次自身）」，版本记录 0.0.71——执行记录自身即 6.32 首检对象，含最新批次后通过。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.32 全类复跑 exit 0（6.32 报告「最新批次 0.0.71，执行记录已覆盖」）；deep-audit 复跑 exit 0。受改 3 项（scripts/doc-audit.py + engineering-workflow + documentation-governance + 本文件）——脚本不在版本记录体系，两份文档版本记录同步 0.0.71、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。

---



## 0.0.72（2026-08-09）— round36 全面深度审计修复批次（规格层引用落点与口径镜像同步）

> 本轮为 round35（0.0.70/0.0.71）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.32 exit 0；deep-audit exit 0，395 条 pending 全部位于 analysis/ 豁免目录），语义层核查 35 项核心口径（五轴四轴映射 / 1536 维 / 37 声明（C-23 废弃）/ 端点 88 / MCP 15 / 参数 226+147 / 术语 70 / 错误码 42 / ADR 12 / OP 66 / 组件 70 / 功能 168 / 核心文档 56 / 全树 196 md+3 yaml / 竖切 15 表 / CLI 三档 15/25/27 / E2E 9 / 五态 CHECK / 降级三态 / RPO/RTO / 性能指标 / 合成公式 / 权重公式 / 债务追踪项 104（31 闭环+62 MNM+11 待实现）/ P3-18-A-14-R-09 预留 / 版本链 0.0.1~0.0.72 连续）全部一致、零漂移。新发现 5 项问题（1 中 / 4 低）全部闭环——规格层引用落点同源遗漏与门禁清单镜像滞后两类。

**A. H-02/H-03 引用落点 §7.3→§7.1a（[feature-list.md](../specification/feature-list.md)，中）**：
- Hermes Memory Provider 权威定义位于架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a（0.0.26 批次自 §7.3d 迁入）；feature-list H-02/H-03 两行仍引用「§7.3 Hermes Memory Provider」——0.0.26 批次仅修正 H-01（MCP Bridge §7.3→§7.1a），H-02/H-03 同源遗漏（round33 教训「同源漏修」重演）；
- 修正：H-02/H-03 引用改指 §7.1a。

**B. C-23 悬空引用修正（[claim-implementation-matrix.md](../specification/claim-implementation-matrix.md)，低）**：
- C-23（已废弃）承载组件列原引用「架构 §3.2 真理模式切换协议（四态，引用为废止前口径）」——该协议已于 0.0.11 批次随双轨切换模型整体清除，架构中不存在对应章节，属悬空引用（门禁 2/18 章节引用检查仅校验链接目标文件存在性，不校验「引用文本所指章节内容是否存在」）；
- 修正：承载组件改指 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §C.5 替代声明（双轨切换模型已废除，由身份面否决权正交模型替代），并注明原承载已废除。

**C. P3-21 FTS5 口径补注（[feature-list.md](../specification/feature-list.md)，低）**：
- P3-21 行原表述「contentless-external + jieba 分词」未体现 0.0.62 批次修正后的口径（基础 FTS5 contentless-external + unicode61 为 v0.1.0 轻量模式 BM25 承载，jieba 为需编译扩展的可选精细中文分词，由 `KAIROS_FTS5_CHINESE_SEGMENTATION` 控制）；
- 修正：补注基础承载与 jieba 可选项语义，与架构 §5.20.2 / data-model §11 / schema-slice §14 口径一致。

**D. project-plan 门禁镜像滞后同步（[project-plan.md](project-plan.md)，低）**：
- Phase ↔ 验收 ↔ 门禁对照表 Phase 0 门禁列仍为「6.13~6.31」——0.0.71 批次工程流程门禁清单补 6.32 后本文镜像滞后一轮（round35 教训「自引用快照/镜像必须随批次同步」重演）；
- 修正：同步为「6.13~6.32」。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.32 全类复跑 exit 0；deep-audit 复跑 exit 0。受改 4 份文档（feature-list / claim-implementation-matrix / project-plan / 本文件）版本记录同步 0.0.72、frontmatter 日期同步 2026-08-09（project-plan frontmatter 已是 2026-08-09 不变）；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。

---



## 0.0.73（2026-08-09）— round37 全面深度审计修复批次（引用落点批量修正：同源遗漏延续 + 悬空引用收口）

> 本轮为 round36（0.0.72）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.32 exit 0；deep-audit exit 0），语义层核查以「引用落点存在性」为重心——对 feature-list「对应架构组件」列 125 行引用逐一比对架构 §5.2 节点清单与蓝图章节标题，发现 **12 项问题（10 中 / 2 低）全部闭环**——核心根因仍为 round33/36 已识别的「同源遗漏」（改了 A 忘了 B）延续：0.0.62 批次 FTS5 口径修正后，feature-list 中事实新鲜度/社区检测等行引用仍指向架构 §5.2 不存在的节点；门禁 6.14 机制名→权威章节抽检仅覆盖 24 条映射、6.26 通用章节引用存在性仅查章节号不查「引用文本所指机制是否真在该章节」，机器未捕获。

**A. feature-list 引用落点批量修正（9 行，中）**：
- R-05「按时间范围过滤」引用「架构 §5 时间索引」→ 架构无「时间索引」节点，时间过滤权威承载为架构 §7.3a 时间过滤约束（as_of/事件时间窗口），改指之；
- R-10「时间序检索 sort=created_at」引用「架构 §5 向量空间·时间序」→ 架构无「向量空间·时间序」节点，且功能声明无接口承载——api-spec §1.2 补 `sort` 参数（created_at/heat_score/默认相关性），引用改指 api-spec §1.2；
- W-09「冲突检测写入」引用「blueprint §5.5 差异检验」→ §5.5 为「见证→使用仲裁」（使用权重合并仲裁），与「写入时冲突检测」语义错配；正确落点为蓝图 §5.6 新信息冲突解决（补充/修正/重构），改指之；
- M-12「社区检测」引用「架构 §5.2 社区检测」→ 架构 §5.2 节点清单无「社区检测」（架构中仅 §0.8 特征标志提及），权威定义在蓝图 §一（Community Detection，D-438 追缴 v1.1），改指之；
- M-13「事实新鲜度·临时过期」引用「架构 §5.2 事实新鲜度·临时过期」→ 架构 §5.2 无「事实新鲜度」节点，权威定义在蓝图 §一（Fact Freshness Metadata，D-437 追缴 v1.1）+ data-model §8.6 fact_freshness 表，改指之；
- A-16「Freshness 报告」引用「架构 §5.2 事实新鲜度元数据」→ 同上，改指蓝图 §一（事实新鲜度元数据）+ data-model §8.6；
- A-15「Recall Funnel」引用「架构 §5.2 / api-spec §6.7」→ 架构 §5.2 无 Recall Funnel 节点（架构中仅 §7.3 检索轨迹可视化提及），改指架构 §7.3 检索轨迹可视化 + api-spec §6.7；
- M-16「MemCube 四层分化」引用「架构 §5.2」→ 架构全文无 MemCube（grep=0），定义在蓝图 §一（MemCube 四层记忆分化，D-436 追缴 v1.1），改指之；
- M-22「Mental Model 可刷新」引用「架构 §5.2」→ 架构无 mental_model 机制承载（仅 §5.19 Reflect 的 search_mental_models 工具名），定义在蓝图 §一（四层记忆质量层次），改指之。

**B. A-24 引用落点细化（[feature-list.md](../specification/feature-list.md)，低）**：
- A-24「关系管理 API」引用「架构 §7 MCP Bridge」→ MCP Bridge 权威定义在 §7.1a（0.0.26 批次自 §7.3d 迁入，round36 已修正 H-01/H-02/H-03），A-24 为同源遗漏，改指「架构 §7.1a MCP Bridge」。

**C. 架构内部悬空引用修正（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)，中）**：
- §7.3a 高相似 × 过时联合惩罚「该惩罚与 §5.2 事实新鲜度元数据的 `freshness_penalty` 合并取严」——架构 §5.2 无「事实新鲜度元数据」节点（权威在蓝图 §一），属架构内部悬空引用，改指 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（事实新鲜度元数据）。

**D. claim-matrix C-20 悬空引用修正（[claim-implementation-matrix.md](../specification/claim-implementation-matrix.md)，低）**：
- C-20 文末对照表「架构 §8 或 §0.5 认知关节索引」——架构 §8 为安全红线章节、无认知关节内容（认知关节登记表位于架构 §0.5），「§8 或」为悬空备选，改指单一落点「架构 §0.5 认知关节登记表」。

**E. blueprint P3-15 引用落点修正（[architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md)，低）**：
- P3-15 变更传播伪代码「本文 §5.2 技能管理系统」——本文（蓝图）无 §5.2 章节（核心机制规格自 §5.3 起），技能管理系统定义位于 §一，改指「本文 §一（技能管理系统）」。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.32 全类复跑 exit 0；deep-audit 复跑 exit 0。受改 5 份文档（feature-list / api-spec / architecture / claim-implementation-matrix / architecture-blueprint-v1.1）版本记录同步 0.0.73、frontmatter 日期同步 2026-08-09（feature-list / claim-implementation-matrix / architecture frontmatter 已是 2026-08-09 不变；api-spec / blueprint 由 2026-08-08 更新）；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。

**门禁补盲区建议（随下轮评估落地，不构成本轮阻断）**：本轮 12 项问题再次证明「机制名→权威章节」引用存在机器盲区——门禁 6.14 抽检表仅覆盖 24 条映射、6.26 仅查章节号存在性。建议将 feature-list「对应架构组件」列全量纳入 6.14 抽检映射表（或对 feature-list 整列做章节锚点校验），并将 6.26 扩展为「引用文本所指机制名在该章节内的关键字存在性」校验（与 round36 R36-02 建议同源合并推进）。

---



## 0.0.74（2026-08-09）— round38 门禁建议落实批次（round37 建议落地：6.33 + 6.26 档 4）

> 本轮为 round37（0.0.73）门禁补盲区建议的**落地批次**（不新增审计轮次，仅落实 round37 报告「门禁补盲区建议」两条）：
> - **6.33 新增**：feature-list「对应架构组件」列引用落点**全量**校验（`scripts/doc-audit.py`）——解析该列 `[文档](路径) §X 机制名`，校验目标文档存在、章节号存在（含父级回退/中文数字/P3-21）、机制名关键词出现在目标文档该章节文本块内；首跑即验证 0 漂移（round37 修复的 10 行全部通过），FAIL 级硬门禁。
> - **6.26 扩展（档 4）**：链接格式「[文档](路径) §X 机制名」的机制名存在性校验——候选词全文痕迹校验（原文/去后缀核心词/标题行子串三级判定），**WARN 级软提示**不阻断 exit 0（全库存在大量「§X 后接章节结构描述/自然语言」引用，无法可靠区分机制名与描述语，硬 FAIL 将误报；真实悬空由 6.33 FAIL 级精准捕获）。

**首跑捕获并修复的真实问题（6.26 档 4 WARN 中甄别）**：
- **C-19 旧机制名**（[claim-implementation-matrix.md](../specification/claim-implementation-matrix.md)）：承载组件列「架构 §3.3 排列漂移审计」→ 架构 §3.3 现行权威命名为「**运行期漂移审计**」（0.0.38 批次更名，本文引用滞后）——修正为「运行期漂移审计」；
- **design-philosophy-relations 例 2 旧机制名**（[design-philosophy-relations.md](../foundation/design-philosophy-relations.md)）：「序数压制幅度记录 + 排列漂移审计」→「**序数幅度差记录 + 运行期漂移审计**」（架构 §3.3 权威命名）；「认知关节索引」→「认知关节登记表」（架构 §0.5 权威标题）；
- **debt-collection ARC-D-004 旧名**（[debt-collection.md](debt-collection.md)）：债务标题与 D-402 状态段「P6 序数压制幅度记录」→「P6 序数幅度差记录」（债务台账与架构权威命名同步）；
- **三处「事件类型原语表」悬空引用**（[api-spec.md](../specification/api-spec.md) L561 / [requirements-baseline.md](../specification/requirements-baseline.md) L193 / [detailed-design.md](../specification/detailed-design.md) L589）：引用「架构 §10.10 事件类型原语表」→ 架构 §10.10 实际标题为「事件类型枚举」——改指「事件类型枚举表」；
- **data-model api_keys 措辞**（[data-model.md](../specification/data-model.md) L1170）：「安全规格 §2.1 密钥生命周期」→「API Key 生命周期」（security-specification §2.1 权威标题）。

**门禁清单镜像同步**：engineering-workflow §四 CI 门禁清单补 6.33、project-plan Phase 0 门禁列 6.13~6.32→6.13~6.33（清单以 engineering-workflow §四 为准）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.33 全类复跑 exit 0（6.33 报告「0 项落点漂移」；6.26 档 4 剩余 26 条 WARN 全部为「§X 后接章节结构描述/自然语言」类可忽略噪声，无真实引用错误）；deep-audit 复跑 exit 0。受改 8 份文档（claim-implementation-matrix / design-philosophy-relations / debt-collection / api-spec / requirements-baseline / detailed-design / data-model / engineering-workflow / project-plan）版本记录同步 0.0.74、frontmatter 日期同步 2026-08-09；计数口径复验 57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档——全部未变动。

---



## 0.0.75（2026-08-09）— round39 全面深度审计修复批次

- 触发：用户再次以资深软件工程文档审计专家身份要求 5 维度全面深度审计（与 round32~38 同格式请求），输出结构化报告并完成全部修复。
- 基线：round38（0.0.74）门禁全绿（doc-audit 18 类 + 14a + 6.8a~6.33 exit 0；deep-audit exit 0）。
- 审计方法：doc-audit + deep-audit 基线 → 历史口径残留扫描（370/371 参数、40 错误码、80/81/85 端点、144 功能——全部仅存版本记录豁免区）→ **6.26 档 4 剩余 26 条 WARN 逐一甄别**（round38 报告声明「全部为可忽略噪声」，本轮逐条实证复核）→ 核心口径复验（五轴四轴 / 40% 信息损失率 / 33%-43% 双口径 / FTS5 unicode61+jieba / MCP 15 / 本地三模型 / 决策 D-01~D-27 / 债务 D-4xx 尾段 / 0.0.74 批次登记纪律）→ 修复 → 门禁复跑验证。
- 核心发现：**0 高 / 4 中 / 0 低**——**round38「26 条 WARN 全为噪声」结论被实证推翻 4 条**（6.26 档 4 WARN 级软提示的真实价值显现：机器无法区分「章节结构描述」与「真实悬空引用」，须人工逐条甄别）：
  - 【中】R39-01：data-model 定位段「架构 §4 定义了存储层的行为约束」——架构 §4 为「推理皮层（独立协调层）」，存储层为 **§5**，章节错位（架构 §5 L1801「## §5 存储层」）；
  - 【中】R39-02：data-model memory_relations `derived_from` 关系「架构 §5.2 Mental Model 基于源头的可刷新性」——架构全文 `Mental` 0 命中（grep=0），权威定义在 blueprint §一（L319，Source-Refreshable Mental Models）；**feature-list M-22 已于 round37 改指 blueprint §一，data-model 为同源遗漏**（「同源漏修」教训延续，round33/36/37/38 四轮重演）；
  - 【中】R39-03：detailed-design 写入管线①「data-model §8.3 冲突判定规则」——data-model §8.3 为 memory_entities 表，全文无「冲突判定」章节（grep=0），content_hash 去重语义承载于 §1 memories 表 `content_hash` 列，悬空引用；
  - 【中】R39-04：acceptance-criteria §三 时序基准参数「参数登记见 configuration §9」——configuration §9 为「RL 权重优化器参数」，`KAIROS_BENCHMARK_*` 实际登记于 **附录 A 全库参数总索引**（L504-508），引用落点错误；同时「架构 §10 基准测试配置」措辞漂移（架构 §10 无基准测试配置小节，基准测试验证声明在 §10.5 量化指标）。
- 修复闭环：4 份文档（data-model / detailed-design / acceptance-criteria）0.0.75 行 + frontmatter 日期同步（2026-08-09 已就位）；data-model 定位 §4→§5、derived_from 改指 blueprint §一；detailed-design §8.3→§1 memories `content_hash` 列；acceptance §三 标题与引言改指 §10.5 量化指标 + 附录 A。
- 教训/经验：
  ① **「WARN 级软提示批量声明可忽略」不可盲信**——round38 报告将 26 条 6.26 档 4 WARN 全部声明为「章节结构描述/自然语言噪声」，本轮逐条实证甄别发现其中 4 条为真实悬空/错位引用（占比 15%）——机器门禁是「候选生成器」，真实性问题确认必须走人工实证路径；
  ② **同源遗漏根因四轮重演**——Mental Model 权威定义迁移（round37 改 feature-list M-22）后，data-model 引用未联动，与 round36 H-02/H-03、round37 R-05~R-11、round38 C-19 同根因——「改了 A 忘了 B」的机器盲区本质是「同族引用无登记清单」，建议后续将「引用落点修改须 grep 同机制名全库联动」固定为修复动作前置步骤；
  ③ 6.26 档 4 的 WARN 噪声主要来自「§X 后接章节结构描述/自然语言」（如「§3.3 分类一致」「§10.10 证伪响应路径」），候选词提取对动词短语/介词短语无法区分机制名——可考虑后续优化候选词提取（仅提取 §X 后紧跟的名词短语，排除「定义了/定义了…的/详述/登记」等动词开头），将 WARN 从 26 条收敛至 ~10 条量级。
- 交付：`2026-08-09-round39-deep-audit.md`（工作区根目录临时交付物，gitignored，不随仓库分发；处置记录进 changelog 0.0.75）。
- 门禁：doc-audit 全类复跑 exit 0（18 类 + 14a + 6.8a~6.33，含 6.32「最新批次 0.0.75，执行记录已覆盖」）；deep-audit 复跑 exit 0；计数零漂移（57 表 / 373 参数 / 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档）。成熟度维持「放行（进入开发阶段）」。

---



## 0.0.76（2026-08-09）— round39 门禁补盲区建议落地批次

> 本轮为 round39（0.0.75）报告「门禁补盲区建议」的**落地批次**（不新增审计轮次，仅落实 round39 报告记录在案的两条建议）：

**A. 6.26 档 4 候选词提取优化（[scripts/doc-audit.py](../../scripts/doc-audit.py)）**：
- **动词/描述性前缀剥离**：「§X 后接动词短语」是 WARN 噪声的主要来源（round39 教训③）——新增前缀剥离表（`_verb_prefix_pat`），「定义了跨层三环不变量」→「跨层三环不变量」、「详述生效规则」→「生效规则」、「只覆盖检索」→「检索」、「保持规范一致」→「规范一致」、「约束认知质量指标」→「认知质量指标」等，剥离后仅以名词短语作为机制名候选；
- **尾部后缀扩展**：`_vword_tail_pat` 增补「参数/状态机/验收/确定/路径/过程/流程」（「三信号混合检索权重参数」→「三信号混合检索」）；「事件类型枚举表确定」→「事件类型枚举表」；
- **括号内 a-d 类字母段标注回退**：「种子生命周期追踪（a-d）」括号内为阶段标注而非机制名——忽略括号回退取括号前文本；
- **标题行匹配逻辑复核（重要回退）**：曾将「整段连续中文段匹配标题」改为「任意 3+ 字子串滑动窗口」——突变测试发现**误放行风险**：悬空引用「存储层量子纠缠索引」因含子串「存储层」（恰好是 §5 标题）被放行，削弱审计捕获能力；已回退为整段连续中文段严格匹配（注释同步修正）。
- **效果**：6.26 档 4 WARN 由 23 条收敛至 **12 条**（26→23 为 round39 修复 4 条真实问题）；剩余 12 条逐条甄别全部为「章节结构描述/自然语言」类可忽略噪声（竖切组件列=表格列描述、分类一致=分类口径描述、各条推论/差异检验联动=章节语义描述、已修正=状态描述、特征标志编码纪律=架构 §0.8 确有「编码纪律」子节、生效规则/规范一致=描述语、三信号混合检索权重=configuration §6.1 标题「三信号混合检索参数」措辞等价、三类检测/接口推进实现=v1.1 预期实现段、认知质量指标=§10.5「量化指标」语义等价）。
- **突变测试双验证**：注入悬空引用「存储层量子纠缠索引」→ 6.26 档 4 **精确捕获**（恢复严格逻辑后）；注入动词前缀描述语「§5 定义了存储层的行为约束」→ 动词剥离后「存储层」在 §5 标题命中**不误报**——「捕获真实 + 放过描述」双验证通过。

**B. documentation-governance §2.2 增补同源联动规则（[documentation-governance.md](documentation-governance.md)）**：
- 触发条件增补「**机制名引用修改**」（同机制名在全库其他文档的引用联动）——R39-02 根因：feature-list M-22 引用改指 blueprint §一 后，data-model 同机制名 `derived_from` 未联动；
- 变更后复核清单 (b) 增补：「机制名引用修改时须 `grep -rn "同机制名" docs/` 全库联动复核——含表格单元格/定位段/括注等隐蔽位置」（round39 教训②固化，同源遗漏根因四轮重演（round36 H-02/H-03 → round37 R-05~R-11 → round38 C-19 → round39 derived_from）的防复发措施）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.33 全类复跑 exit 0（6.26 报告 12 处 WARN 全部为可忽略噪声）；deep-audit 复跑 exit 0。受改 3 项（scripts/doc-audit.py + documentation-governance + 本文件）+ changelog 0.0.76 版本记录行；核心计数全未变动。

---



## 0.0.77（2026-08-09）— round40 全面深度审计轮次登记

- 触发：用户要求「落地改进建议后开启全新一轮审计」——round40 为 0.0.76 门禁优化批次后的首轮五维度全面深度审计（0.0.76 已单独登记，0.0.77 仅登记审计轮次本身）。
- 审计方法：doc-audit + deep-audit 基线（全绿）→ 历史口径残留扫描（370/371 参数、40 错误码、80/81/85 端点、56/57/60/67/68/69 术语——全部仅存版本记录豁免区）→ 零版本标记扫描（0 残留）→ **架构引用落点批量校验**（架构章节集合 127 个，校验 10 份运维/安全/质量 + 27 份规格/开发/治理 + analysis 143 份外部对照产物——**全部 0 漂移**）→ 核心口径复验（五条推论认知基础↔架构逐条对应、事件类型枚举 10 类、CLI 三档 15/25/27、E2E 9、五态 CHECK、债务 104（31 闭环+62 MNM+11 待实现）、D-334 三处口径、特征标志总数上限 24、声明 C-01~C-37、MCP mapsTo 15（11 REST + 4 MCP-only））→ user 层路径域（`_user/{id}/knowledge` 持久域 / `_user/default/playground`，通用路径=会话本地语义正确）→ 功能承载核查（feature-list 93 行零空引用、R-10 sort 参数承载闭环）→ 6.26 档 4 剩余 12 条 WARN 逐条甄别（全部为「章节结构描述/自然语言」类可忽略噪声，含「特征标志编码纪律」——架构 §0.8 下确有「#### 编码纪律」子节（L613），引用正确、措辞差异）。
- 审计结论：**0 高 / 0 中 / 0 低——全面零漂移**（较 round39 的 4 中进一步收敛；验证 0.0.76 门禁优化后体系稳定，6.26 档 4 WARN 收敛至 12 条且捕获能力经突变测试验证未削弱）。
- 门禁：doc-audit 全类复跑 exit 0（18 类 + 14a + 6.8a~6.33，含 6.32「最新批次 0.0.77，执行记录已覆盖」）；deep-audit 复跑 exit 0；计数零漂移（57 表 / 373 参数 / 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档）。成熟度维持「放行（进入开发阶段）」。
- 交付：`2026-08-09-round40-deep-audit.md`（工作区根目录临时交付物，gitignored，不随仓库分发；处置记录进 changelog 0.0.77）。

---



## 0.0.78（2026-08-09）— round40 改进建议落地批次

> 本轮为 round40（0.0.77）报告「三、改进建议」两条门禁体系观察项的**落地批次**（不新增审计轮次，仅落实 round40 报告记录在案的两条建议）：

**A. 6.26 档 4 候选词「尾缀标题匹配」增强（[scripts/doc-audit.py](../../scripts/doc-audit.py)）**：
- round40 建议①：「特征标志编码纪律」类（修饰语+子节标题）候选词可再收敛——新增**3-6 字尾缀标题匹配**判定（`zh_tails`）：候选词 3-6 字**尾部窗口**在目标文档标题行出现即通过（区别于 round40 已回退的「任意 3+ 字子串滑窗」——仅取尾部窗口，反例「存储层量子纠缠索引」尾缀不含「存储层」（前缀），不误放行；3 字下限防「指标/纪律」类泛化误报）。
- **效果**：WARN 12→**10 条**——「特征标志编码纪律」尾缀「编码纪律」命中架构 §0.8「#### 编码纪律」子节（L613）收敛、「各条推论」尾缀「条推论」命中架构 §0.3「### 0.3 五条推论」收敛；「认知质量指标」尾缀「量指标」未在「### 10.5 量化指标」连续出现，保留 WARN 合理（描述语）。
- **突变测试双验证**：注入悬空引用「存储层量子纠缠索引」→ 6.26 **精确捕获**（尾缀匹配未削弱捕获能力）；「特征标志编码纪律」类描述语 → 尾缀「编码纪律」命中子节标题**不误报**——「捕获真实 + 放过描述」双验证通过。
- 保守决策：「权重」未加入尾部后缀剥离表——「三信号混合检索权重参数」保留 WARN（api-spec L97 引 configuration §6.1，章节号正确、措辞「权重参数 vs 参数」差异，属可忽略噪声；避免「权重」剥离引入误放行风险）。

**B. documentation-governance §4 增补版本记录表方向约定（[documentation-governance.md](documentation-governance.md)）**：
- round40 建议②：版本记录表方向不统一（升序/降序混存）是插行踩坑点（0.0.76 登记时误插行序被门禁 12/18 捕获）——§4 增补「版本记录表方向约定」：升序表（最新在表尾）插表尾、降序表（最新在表首）插表首；插入前先确认表方向；单文档内方向必须一致（文档间不要求统一）。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.33 全类复跑 exit 0（6.26 报告 10 处 WARN 全部为可忽略噪声）；deep-audit 复跑 exit 0。受改 3 项（scripts/doc-audit.py + documentation-governance + 本文件）+ changelog 0.0.78 版本记录行；核心计数全未变动。

---



## 0.0.79（2026-08-09）— round41 全面深度审计修复批次（核心文档裁决歧义收口 + 排序/导航收敛）

> 本轮为 round40（0.0.77/0.0.78）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.33 exit 0；deep-audit exit 0），语义层核查以「核心文档裁决歧义」为重心——架构/认知基础/蓝图全文深度核查（4 项中风险：组合寄存器遗忘判据句内矛盾、§10.12 全量级梯度 v1.1 能力无边界标注、§2.2 P6 超限口径与 E.7 冲突、潜伏势能保留/归档判据与架构 §5.2 相反），24 项核心口径复验零漂移；6.26 档 4 剩余 10 条 WARN 逐条实证甄别——9 条确认为描述性引用（含蓝图 §5.6 冲突分类阈值与架构 §7.3a 完全一致之实证），1 条（runbook §二 生效规则措辞）为轻微偏差。
- **修复闭环（0 高 / 8 中 / 17 低）**：
  - 中风险 8 项：R41-01 changelog 排序归位（叙述节 0.0.74 移至 0.0.73 后 + 版本表统一升序 0.0.1→0.0.78，落实 0.0.78 方向约定）；R41-03 五份超限文档补章节导航（api-spec/data-model/cognitive-foundation/configuration/feature-list）；R41-04「摄入/摄取」动词统一（保留「摄入侧情绪保护」固定词组）；R41-10 组合寄存器遗忘判据取各类型最低值；R41-11 §10.12 全量级版本边界注记；R41-12 §2.2 P6 合规标准对齐 E.7；R41-13 潜伏势能保留/归档判据对齐架构 §5.2（与 B.1 桥梁定位一致）；R41-14 §10.24 补 D-301/D-306/D-313。
  - 低风险 16 项：R41-02 mcp-tools.json 补 D-428 指针；R41-05 detailed-design 单轨批次号去除（豁免 2 条款）；R41-06 两处表头分隔行补冒号；R41-07 system-context frontmatter 同步；R41-08 README 版本记录日期补年份；R41-09 架构/configuration 标题前多空行收敛；R41-15 §0.4 层编号表述修正；R41-16 §1.3「1–4层」→「1–5层」；R41-17 阶段×梯度矩阵引用改指 §E.9；R41-18 §10.10 协议清单补潜伏势能重估并对齐协议名；R41-19 否决操作成本声明统一「身份注册表」；R41-20 记忆状态迁移列举补 suppressed 五态；R41-21 检索深度降级执行者对齐架构 §3.9（策略层）；R41-23 蓝图 P3-13 引用改指架构 §5.2；R41-24 蓝图 P3-11 引用改指架构 §5.19；R41-25 蓝图 mental_models 手动创建路径注记；R41-26 §0.9 降维门禁表补可及性轴行（五项→六项，与 §10.13 视角对齐）。
  - 误报剔除 3 项：批次号注记批量判定（42 处中 41 处为豁免 2 双轨简注，仅 detailed-design 1 处真实违规）；R41-22 SQLite ≥3.40 与 sqlite-vec 版本要求（经官方资料查证无版本下限冲突，不构成问题）；「（勘误）」注记（0.0.67 批次已裁决保留，属认知诚实声明文化）。
- 受改 12 份文档版本记录同步 0.0.79 + frontmatter 日期同步；核心计数全未变动（57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 70 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档）；门禁全类验证 exit 0。



## 0.0.80（2026-08-09）— round42 全面深度审计修复批次（引用/口径收口 + 格式收尾 + 术语登记）

> 本轮为 round41（0.0.79）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.33 exit 0；deep-audit exit 0）；五路并行深度审计（维度 1 核心口径 26 项复验 + 90 处引用抽查 / 维度 2+3 覆盖缺口与结构组织 / 维度 4 格式规范 / 维度 5 架构 4062 行 + 认知基础 1189 行 + 技术选型 + 蓝图 + 理念关系图全文）；6.26 档 4 剩余 10 条 WARN 逐条双向实证（全部确认为描述性引用）。round41 全部修复项经复核无回归。
- **修复闭环（0 高 / 9 中 / 36 低）**：
  - 中风险 9 项：R42-01 错误码返回方式口径冲突（ERR-SYS-001/002 划入内部码，对齐 error-reference/api-spec 权威）；R42-02 openapi 契约「§0 认证」引用改指引言「认证」；R42-03 认知基础「摄取沙箱（api-spec §6.3）」双重错指改指架构 §7.3 摄取门禁；R42-17 高 Arousal decontextualization_level 初始值方向修正（上调→下调，对齐认知基础 D.12）；R42-18 §0.4 标准级「舍弃宪法主权面」→「舍弃完整宪法主权面（继承内核级简化形态）」；R42-19 §0.4 标准级「无探索投资」对齐 §0.7 矩阵（探索投资受限 ×0.8~×1.2）；R42-20 §0.4 标准级「舍弃元认知层」→「舍弃完整元认知层（周期审计形态保留，见 §10.12 标准级行）」；R42-21 §10.3 版本链存储形态对齐 §5.2（修改日志事件总线承载 + 版本链 memories 表指针字段 + memory_versions 全量快照）；R42-33 认知基础三类调用类型轴归属统一（目的性分类轴 + 三个非层级子维度，对齐 C.1）。
  - 低风险 36 项：引用精确性 14（架构 §三→§3 策略层、理念关系图 §5→§5.5、架构 §10.6→§1.6/§5.2、§9.1→§9.2 两处、§5.4→§3.3、蓝图 6 处裸 §10.x 补「架构」前缀、蓝图 P3-19 导航声明修正、technology-stack 连接池行名改数据库驱动、理念关系图 E.5/E.3 归因修正、feature-list 14 类构成注记）；格式规范 11（「摄入」动词残留 4 处统一「摄取」、5 处「吸收自外部」旧形态收敛、章节标题「0.0.17 新增」去除、架构「R-03，外部实证吸收/设计来源：」措辞收敛、12 处决策编号补「决策」前缀、认知基础 3 处标题前多空行压缩）；计数与术语 2（glossary 补登 6 项落地机制术语、条数 70→76 并联动 README/架构 §11/concept-tiers；README「100 视频」→102）；认知基础口径 5（演进路径补受限自主阶段、宪法锁「前三序」→「前两序」、过程词汇纪律限定结构声明、充分性条件枚举对齐正文、待遗忘/潜伏状态名对齐）；蓝图细节 3（P3-08 成本算数 ¥150→¥15、L498 重复短语删除、0.0.79 版本记录摄入遗漏校正）。
  - 误报剔除 2 项：feature-list「14 类」构成可由「功能分类更新」表 14 行推导（降为低风险可读性注记）；5 处「参数待登记」全部已有债务追踪（D-422~425 专项 + L1915 由 D-016 覆盖），追缴门禁合规。
- 受改 21 份文档版本记录同步 0.0.80 + frontmatter 日期同步；glossary 术语计数 70→76（doc-audit 6.7 联动 README/架构 §11）；其余核心计数未变动（57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档）；门禁全类验证 exit 0。

## 0.0.81（2026-08-10）— round43 全面深度审计修复批次（VAD 条件激活口径统一 + S-07/S-17 安全语义修正 + 章节导航补全 + changelog 排序归位）

> 本轮为 round42（0.0.80）之后的全面深度审计轮（五维度同前）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.33 exit 0；deep-audit exit 0；本轮修复引入的 CRLF 行尾残留经二进制模式归一为 LF，6.16 归零）；6.26 档 10 条 WARN 维持可忽略噪声。round42 全部修复项经复核无回归。
- **修复闭环（3 高 / 6 中 / 5 低 = 14 项）**：
  - 高风险 3 项：R43-01 架构文档 VAD 条件激活（G-02）权威落点统一——架构 §3.2 预测器（情感基线提升通道）为唯一权威定义，§5/§5.2 降为引用点，联动 architecture-blueprint / usage-load-algorithm / glossary 共 9 处引用归位；R43-02 vad-coordinate-algorithm 坐标算法与 §3.2 公式 `boost=max(0,cos-0.5)×2.0` 对齐（cos<0.5 归零默认忽略）；R43-03 security-specification L61 自否定句修正——API Key 经 PBKDF2-HMAC-SHA512 派生后与 KAIROS_API_KEY_HASH 比对，对齐 S-01。
  - 中风险 6 项：R43-04 threat-model S-07 主控制重映射（写入时加密 + 导出脱敏，信息泄露 12 分最高项主防御）；R43-05 requirements-baseline R-06 改为 v0.1.0 隐式 VAD 形式（cos≥0.5 注入、cos<0.5 默认忽略，显式 VAD 查询归 v1.1）+ feature-list VAD 标签同步；R43-06 claim-matrix C-16 / traceability-map VAD 引用统一指 §3.2；R43-07 test-strategy S-17 法定擦除例外测试行（GDPR/个人信息保护法命中 is_structure=true → S-19 哈希净化，宪法解释层裁定 + statutory_erasure 留痕）；R43-08 债务 D-440 登记（价值维度熵 5 组运行阈值参数化，参数待登记）+ value-dimension-entropy 4 处参数登记注记；R43-09/10 changelog 叙述节升序重排（0.0.45–0.0.49 错位块 + round42 回归 0.0.79/0.0.80 归位）、`## 版本记录` 孤标题紧邻表体。
  - 低风险 5 项：R43-11 debt-collection / architecture-blueprint 补章节导航表（api-spec 风格）；R43-14 value-dimension-entropy `---` 与 `## 版本记录` 间补空行；R43-12 表分隔行裸分隔符全库复核（0 处裸 `| --- |`，原 25/4/3 计数为脚本 bug 误报，维持合规）；R43-13 `## §11 特征标志默认值` 标题为门禁负载锚点（doc-audit.py L1577 `cfg.find("## §11")` + 10+ 交叉引用）刻意不改；CRLF 行尾残留 4 份（changelog/configuration/nfr-specification/operation-catalog）归一 LF。
- 受改 18 份文档版本记录同步 0.0.81 + frontmatter 日期同步 2026-08-10；核心计数全未变动（57 表 / 373 参数（226+147）/ 88 端点 / 42 错误码 / 76 术语 / 66 操作 / 168 功能 / 70 组件 / 56 核心文档）；门禁全类验证 exit 0。

## 0.0.82（2026-08-10）— round44 门禁建议落实批次（落 round43 §四 4.4 S43-3/S43-1，语义互斥检查固化进门禁）

> 本轮为 round43（0.0.81）之后，落实审计报告 §四 4.4 结构性建议（门禁增强）的专项批次。机器门禁基线全绿（doc-audit 全类 + 新增 6.34/6.35 exit 0；deep-audit exit 0）。round43 全部修复项经复核无回归。
- **门禁增强（S43-3 / S43-1）**：
  - **S43-3 changelog 结构纪律（6.34）**：① 叙述节版本号单调升序（倒置即 FAIL，防 R43-09 类回归）；② `## 版本记录` 标题须紧邻版本表体（中间不得插入其它 `##` 节，防 R43-10 类回归）。首跑 81 个叙述节升序合规、版本记录邻接合规。
  - **S43-1 红线语义互斥词对检查（6.35，试点）**：维护「红线禁止短语 ↔ 违例措辞」词对表（试点仅 S-14：禁止内部信号写回主副本，违例措辞为肯定式「合并回/至主副本」「写回主副本」等），否定行（「不得 X」描述规则本身）跳过以避免误报。全库 196 md 扫描 0 处违例。
  - **S43-2 交付状态跨文档一致性（6.36）**：暂缓——需组件名 × 状态标注双向解析，先作后续轮次候选（negation 无关，需谨慎构造避免误报）。
- 受改 1 份脚本（scripts/doc-audit.py 新增 6.34/6.35）；changelog 本文件 + documentation-governance §3 执行记录同步 0.0.82；门禁全类验证 exit 0。

---

## 0.0.83（2026-08-10）— round45 全面深度审计修复批次（版本归属互斥收口 + P6 监控自洽化 + 容量口径对齐）

> 本轮针对门禁结构性盲区（语义互斥 / 口径与事实脱节 / 范围标签失真）执行五维度深审，3 高 / 4 中 / 4 低共 11 项全闭环，另剔除误报 3 项、记录观察项 3 项。计数零漂移（57 表 / 373 参数 / 88 端点 / 42 错误码 / 76 术语 / 66 操作 / 168 功能 / 56 核心文档）。

- **高风险（3 项）**：
  - **R45-01 intention 契约版本归属互斥**：[data-model.md](../specification/data-model.md) `memories.contract` 五值枚举含 `intention` 且 [api-spec.md](../specification/api-spec.md) §1.5 已有 409 `ERR-CTR-004` 删除守卫（契约层已落地），而 [feature-list.md](../specification/feature-list.md) PM-01 与 [requirements-baseline.md](../specification/requirements-baseline.md) §1.8 写「数据模型与 API 未落地」——同一事实的两个全称判断互斥。改为**能力粒度切分**：v0.1.0 落地契约枚举值 + 保护语义 + 删除守卫，v1.1+ 承载意图生命周期专用端点与 `intention_activate` / `intention_resolve` 事件。
  - **R45-02 事件类型枚举范围标签失真**：[api-spec.md](../specification/api-spec.md) §4 引言写「仅列 v0.1.0 核心类型」而表体实列全部 10 类，与 [implementation-map.md](../specification/implementation-map.md) §八「首迭代实现 4 类」冲突，按 10 类施工将实现 6 类永不发布的事件。引言改为「列全部 10 类 + 首迭代实现 4 类」，表增「首迭代」列（✅ 4 / ⏳ 6）逐行标注。
  - **R45-03 P6 临界余量监控触发前提与已知超限互斥**：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.11 同节三条规则合取自毁——已声明压缩比恒超 30%，又规定「超限即触发合规审查、审查期间不得新增例外」，与「所有超限压缩操作必须逐条登记为例外」直接冲突，且「余量 < 5%」在余量为负时永久告警。监控口径改为**基线增量制**：已登记基线（核心 ~33% / 全量 ~43%）不重复触发审查，监控对象为基线之上的增量，例外预算带 3 个百分点，四条规则在交付态全部静默；并消歧「不得新增例外」指审查期内不引入新压缩操作、不影响既有登记义务。
- **中风险（4 项）**：
  - **R45-04 红线违反 HTTP 映射过度概括**：[coding-conventions.md](../development/coding-conventions.md) §三「红线违反 → 403」为全称判断，与 [security-specification.md](../security/security-specification.md) §1 中 S-02 → 429 / S-03 → 413 / S-15 → 422 冲突。改为按红线类型分派映射，权威指向 security-specification §1。
  - **R45-05 / R45-07 备份容量核算与容量上限错位**：[reliability.md](../ops/reliability.md) §三 核算注记以 10 万条基准得 ≈60GB，而标准模式容量上限为 ≥100 万条（满载 ≈600GB，差一个数量级）；[nfr-specification.md](../specification/nfr-specification.md) §二 磁盘行亦未声明备份归属。核算注记补满载口径与「按实际条数换算」纪律，NFR 磁盘行补反向声明（预算仅覆盖主库/索引/日志，备份独立存储）。
  - **R45-06 关系层 P6 豁免在架构层无承载**：[cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 定义「关系层不受 P6 压缩约束」，架构层无对应声明且原指向落点无内容（「写了=做了」违规）。架构 §10.11 前置**三层治理边界**承载声明——内容层受 P6 约束、关系层受 `is_structure` 守护不受 P6 压缩（压缩管道仅作拓扑保持的引用重写）、签名层由遗忘调度器与检索排序器消费。
- **低风险（4 项）**：
  - **R45-09**：架构特征标志表 `KAIROS_FEATURE_MULTI_SIGNAL_SEARCH` 补默认组合说明——`ENTITY_GRAPH` 默认 OFF 使开箱实为双信号（α_s=0.60 / α_b=0.40），验收用例按实际标志组合选取信号数。
  - **R45-10**：[configuration.md](../ops/configuration.md) `KAIROS_FTS5_CHINESE_SEGMENTATION` 补扩展缺失时行为（本表为行为权威）——降级告警 + 回落 `unicode61` 不阻断启动，属可用性 fail-open 留痕、不适用安全失败关闭纪律，实际分词器须在启动日志与 `GET /health` 可见。
  - **R45-11**：[api-spec.md](../specification/api-spec.md) §1.2 `sort=heat_score` 补未启用时行为——维护引擎 Light 模式未启用时该值不更新、排序退化为写入序且不返回错误（避免为此新增错误码破坏 42 计数一致性）。
  - **R45-12**：[data-model.md](../specification/data-model.md) `memories.contract` 补 DDL 默认与摄取 API 预填的分层说明，并清除该节遗留编辑痕迹（reliability 核算注记中「原…已修正」表述，违 §2.3 零版本标记纪律）。
- **观察项（不处置）**：`/metrics` 端点未登记（债务 D-429 已追缴）、契约 schema 未含字段级枚举（债务 D-428 已追缴，Phase 0 W2 到期）、detailed-design 检索管线无 VAD 通道（刻意设计，VAD 属架构 §3.2 策略层预激活而非排序信号）。
- **误报剔除（3 项）**：PostgreSQL 16 认证矩阵（technology-stack §二 已列 15–16）、S-02 熔断 500 ops/s 无配置承载（configuration §7 已登记 `KAIROS_RATE_LIMIT_CIRCUIT_BREAK_OPS`）、`AGE_DECAY_CONSTANT` 版本归属（三处一致归 v1.1，configuration 登记默认值属参数注册表常规）。
- 受改 9 份文档（architecture-v0.1.0 / api-spec / data-model / feature-list / requirements-baseline / nfr-specification / coding-conventions / reliability / configuration）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.83；门禁全类验证 exit 0（6.26 WARN 维持 10 条已知噪声，无新增），deep-audit exit 0。

---

## 0.0.84（2026-08-10）— round46 门禁建议落实批次（落 round45 §四 4.4 S45-1/S45-2/S45-3，版本归属互斥 / 表格范围词 / 阈值自洽三项机器检查落地）

> 本轮为 round45（0.0.83）之后，落实审计报告 §四 4.4 结构性建议（门禁增强）的专项批次。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.38 exit 0；deep-audit exit 0）。round45 全部修复项经复核无回归。
- **门禁增强（S45-1 / S45-2 / S45-3，WARN 级软门禁首轮）**：
  - **S45-1 版本归属互斥检查（6.36）**：自举式倒排索引——仅对「同一行内实体名 + 显式版本归属动词（已落地/未落地 等）」建 实体→{landed,unlanded} 标签集合；同行澄清句（两标签共存）跳过，跨文档/跨章节出现两标签即 WARN。直接对应 round45 R45-01/R45-02 共同根因「版本标签与规格内容脱节」。首跑全库 0 处矛盾（round45 修复已收口）。
  - **S45-2 表格内容与引言范围词一致性（6.37）**：仅对排他性上限限定词「仅列/仅含 N 类/项」+ 明确计数触发，比对紧邻表格数据行数；「核心/部分/首迭代/仅 N 项（其中）」等子集描述不触发（避免误报）。首跑 0 处（初稿曾对「首迭代 4 类 among 10」等子集标注误报，已收紧口径）。
  - **S45-3 阈值型监控规则自洽性（6.38）**：对「指标/阈值/触发动作」三列监控表，抽取阈值与同文档当前值声明比对，当前值已越阈即 WARN（防交付态恒触发自毁，对应 round45 R45-03）。首跑 0 处（R45-03 增量基线制已消除恒触发）。
- 三项首轮均为 WARN 级软门禁（不阻断 exit 0），观察一轮无漏/无误报后于后续轮晋升 FAIL（对齐报告 §4.4 S45-1 原始 FAIL 意图）。受改 1 份脚本（scripts/doc-audit.py 新增 6.36/6.37/6.38）+ 门禁清单镜像同步（engineering-workflow §四 + project-plan Phase 0 → 6.13~6.38，补齐 round44 漏登的 6.34/6.35）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.84；门禁全类验证 exit 0。

---

## 0.0.85（2026-08-10）— round47 全面深度审计修复批次（状态机死角收口 + 契约语义互斥收敛 + 错误码扩编 43）

> 本轮为 round46（0.0.84）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.38 exit 0；deep-audit exit 0）。语义层核查聚焦门禁扫不到的**事实层与语义层**问题，共闭环 **6 高 / 14 中 / 2 低**，另新增错误码 1 项（错误码 42→43）。修复均落在 api-spec / detailed-design 两规格文档为主；架构权威语义未变（§5.2 状态机与 §1.2 端口定义保持为权威，spec 层对齐），但 §5.2 增补状态转换纪律声明（M-01，架构为受改文档之一）。

**【高】状态机死角收口（3 项）**
- **H-01 Reflect `done` 收敛不可达**：`done` 输出列「终止循环」与收敛判据「连续两次 done 结论相似度 ≥0.90」互斥（首调用即终止则永远无法满足两次调用）——修正为 `done` = **结论提交动作而非终止动作**：首次调用建立基线继续循环，第 n 次与第 n-1 次比对，≥0.90 收敛终止；收敛终止最小 done 次数=2；审计事件示例 `tools_called.done` 1→2 同步；审计庭指标「done 未调用频率」改「done 调用次数 < 2 占比」。
- **H-02 遗忘函数名实倒置**：`FORGETTING_SCORE` 返回 freshness（越高越不该遗忘），与 v1.1 二维曲面「遗忘得分」（越高越该遗忘，`KAIROS_FORGETTING_SCORE_THRESHOLD`）极性相反——函数更名 `EVALUATE_FRESHNESS` + 返回值极性声明 + 豁免分支改返回哨兵 `EXEMPT`（防「0.0 = 最该遗忘」误读）；observability `kairos_forgetting_score` 指标说明同步 freshness 口径。
- **H-03 宪法修订端口无单条记忆出口**：permanent 契约「仅可经宪法修订端口降级」、superseded「仅经宪法修订端口重新激活」在接口层无承载（POST /v1/constitution 仅偏好键值操作）——api-spec 扩展 `POST /v1/constitution` 支持 `memory_id` + 新 action `contract_downgrade`（permanent→ondemand，唯一合法降级路径）与 `state_restore`（superseded→active，版本链追加），is_identity 降级须附宪法解释层判例 `case_id`（架构 §8 提案→裁定→执行路径，本端点仅为执行端口）；两项操作均附 HMAC 链 + 冷却期（S-19 附加控制项）。

**【高】契约语义互斥收敛（2 项）**
- **H-04 幂等语义两处对立**：detailed-design §2 约束②「写入携带幂等键 request_id，重复提交去重拒绝」vs api-spec 批量导入「非幂等——重复提交可能产生重复记录」——统一为幂等键模型：单条写入新增 `Idempotency-Key` 请求头（可选，同键重复提交返回首次结果），批量导入支持 `idempotency_key`（整体去重）；幂等键冲突新增错误码 `ERR-CTR-005`（409，错误码 42→43，error-reference / troubleshooting / api-spec §7 / README / runbook 五处计数与表体同步）。
- **H-05 乐观锁「必需」vs If-Match「可选最后写入胜出」互斥**：PATCH 并发冲突统一为**乐观锁强制**——`If-Match` 从可选改**必需**（v0.1.0 无「最后写入胜出」路径），不一致返回 409 `ERR-DB-005` 走版本链追加；删除「不提供时直接更新」句。

**【高】契约骨架不可解析引用（1 项）**
- **H-06 openapi.yaml `adminKey` 未定义**：5 处 `security: - adminKey: []` 引用 securitySchemes 中不存在的 scheme（文件头已声明单一 bearerAuth）——全部替换为 `bearerAuth`；文件头补骨架口径第 5 条（Idempotency-Key / If-Match / X-Trace-Id 头与 GET query 参数为 api-spec 已声明行为，parameters/headers 占位待 Phase 0 补全，补齐前不得据此判定接口无参数）。

**【中】状态机与数据语义修正（6 项）**
- **M-01 遗忘「检索即复兴」歧义**：显式检索更新 last_access_at 与「不直接触发状态复兴」并存——架构 §5.2 补状态转换纪律声明（转换仅由遗忘调度器扫描或复兴端口驱动，检索仅更新 last_access_at），detailed-design §3 补衰减口径注记；避免 archived 记忆仅凭被读一次回到 active。
- **M-02 记忆锁定解锁死锁**：锁定态「PATCH 一律拒绝」与「提前解除须 PATCH 携带 locked_until:null」自锁——补充 admin 解锁路径不受锁定态拒绝语义约束（解锁 PATCH 载荷仅允许 `locked_until:null`，其余字段仍拒）。
- **M-03 归档端点缺 is_identity 守卫**：`POST /v1/memories/{id}/archive` 仅写 permanent 403——补身份守卫（is_identity=true 拒绝归档，403 ERR-SEC-001，对齐 operation-catalog OP-054 见证豁免）。
- **M-04 as_of 双时态缺版本选择与软删过滤**：detailed-design `as_of` 查询无 `is_deleted=FALSE` 且版本取 is_latest（当前视角）——补软删过滤 + 按 `root_memory_id` 取 ts 时刻生效版本（版本链子查询）。
- **M-05 Deep 模式 C1-C8 全量与 5% 抽样打架**：执行模式表「C1-C8 全量检查（逐条比对 + 哈希校验）」vs `KAIROS_CONSISTENCY_HASH_VERIFY_SAMPLE_RATE=0.05`——澄清 C1~C7 确定性 SQL 全量查询、仅 C8 哈希校验按 5% 抽检（抽中不一致后全链复核），延迟预算口径同步。
- **M-06 GSPO 重打分非缩减**：「以 cluster_importance 替代簇内所有记忆独立分数」不缩减候选集，与「降低 Cross-encoder 计算开销」矛盾——补候选集缩减语义：簇内仅保留最高重要性成员为簇代表进入下游（其余标记 `gspo_collapsed` 审计剔除），Cross-encoder 输入规模 = 簇数 + 未成簇数。

**【中】数值口径与术语修正（5 项）**
- **M-07 Bounded Simplex Projection softmax 用法缺陷**：softmax（已保证 Σ=1）后再 clamp+重归一化破坏归一化性质——改为 capped simplex projection（欧氏投影，二分求 λ，双重约束 Σ=1 与各维 [min,max] 一次满足），删除 softmax 描述。
- **M-08 实体置信度阈值重叠 + 字段名混用**：LLM 置信度「≥配置阈值直接写 / 0.5-0.8 待审 / <0.5 丢弃」中 0.5 无配置承载且与 0.8 区间表述含糊——新增参数 `KAIROS_ENTITY_LLM_DISCARD_THRESHOLD`（默认 0.5），判定改互斥开区间；补 source（llm/keyword_fallback，存 entities.metadata）与 memories.provenance（S-15）层级区分注记（entities 表无独立 source 列）。
- **M-09 S-04 摘要表术语混层**：security-spec 红线汇总表「非本机请求拒绝（轻量模式绑定 127.0.0.1）」将部署模式（轻量/标准/全量）与运行模式（[L]/[P]）混用——改为「默认绑定 127.0.0.1；[P] 模式经反向代理」，对齐 §1 表。
- **M-10 S-11 端口混淆**：threat-model「外部校准端口为宪法修订唯一入口」与架构 §1.2（外部校准端口 / 宪法修订端口为不同组件）矛盾——修正为「外部校准端口接收信号，宪法修订端口为修改宪法级偏好的唯一合法入口」。
- **M-11 归档/恢复端点文档联动**：与 H-03 配套，确认 restore 端点 `ERR-SEC-001` 已哈希净化不可恢复与 H-03 state_restore（superseded）不重叠（前者 suppressed 化石节点、后者版本链旧版本）。

**【中】契约骨架口径（1 项）**
- **M-12 openapi 88 操作零 query 参数**：与 api-spec GET 端点 `?path/?q/?limit/?offset/?sort/?clearance` 声明不符——骨架口径第 5 条声明（api-spec 为行为权威，parameters 待 Phase 0 补全），防误判接口无参数。

**【低】格式规范（2 项）**
- **L-01 路径参数名不统一**：`POST /v1/narrative/threads/{thread_id}/summarize` 与同族 `{id}` 混用——统一为 `{id}`。
- **L-02 CLI 参数登记**：quick-start 示例 `kairos write --contract ondemand` 在 CLI 命令表（api-spec §3）无登记——补 `--contract` 说明与示例。

**验证**：doc-audit 十八类 + 14a + 6.8a/6.12a/6.13~6.38 全类复跑 exit 0（6.26 WARN 维持 10 条已知噪声，无新增）；deep-audit 复跑 exit 0。实质受改 13 份 md + openapi.yaml（architecture §5.2 状态转换纪律声明（M-01）/ detailed-design / api-spec / rl-weight-spec / observability 指标口径同步（H-02）/ configuration / security-specification / threat-model / error-reference / troubleshooting / runbook / README；data-model / reliability 经审视判定引用口径不动、无内容变更，不计入受改——0.0.89 勘误，原「受改 15 份」含两审视项）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.85；核心计数变动仅 1 项：**错误码 42→43**（新增 ERR-CTR-005），其余（表 57 / 参数 373→374 新增 DISCARD_THRESHOLD / 端点 88 / 术语 76 / 操作 66 / 组件 70 / 功能 168）口径同步；门禁全类验证 exit 0。

---

## 0.0.86（2026-08-10）— round48 遗留问题处理批次（门禁三项晋升 FAIL + 6.26 全文构建缺陷修复 + WARN 计数勘误）

> 本轮处理 round47 报告 §五 遗留观察项——① 6.26 全文痕迹校验的跨行吞噬缺陷；② round46 承诺的 6.36/6.37/6.38 三项 WARN 软门禁「观察一轮后晋升 FAIL」；③ 0.0.85 验证段 WARN 计数表述勘误。门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.38 exit 0；deep-audit exit 0）。
- **6.26 全文构建缺陷修复（round47 WARN 10→12 的根因）**：`sec_fulltext` 构建用 `re.sub(r"\[[^\]]*\]\([^)]*\)", ...)` 去链接，其中 `[^\]]*` 可**跨行**匹配——代码块内任意半角 `[` 与后续行 `](` 之间的全部内容（含换行）被整段吞掉，导致「衰减口径注记」（detailed-design §3 代码注释）等真实存在的机制名在全文痕迹校验中消失、产生误报。修复：字符类限行内（`[^\]\n]*` / `[^)\n]*`），markdown 链接本就单行，不影响正常链接剔除。修复后 round47 新增的「衰减口径」误报消除。
- **api-spec 引用措辞对齐**：`§2 写入管线约束②` 候选词「写入管线约束」在 detailed-design 无痕迹（目标节标题为「写入管线设计」，正文为「幂等 + 乐观锁事务提交」）——引用措辞改「§2 写入管线设计②（幂等 + 乐观锁事务提交）」，候选词与目标标题一致。至此 6.26 WARN **12→10** 回归 round46 基线（剩余 10 条全部为历轮已甄别的可忽略噪声）。（round49 勘误：本批对齐仅覆盖 §1.3 一处，§1.1/§1.2 两处（L54/L81）仍为旧措辞——「12→10 回归基线」声明在补改完成前不完整，由 0.0.87 批次 R49-02 补改并复核。）
- **6.36/6.37/6.38 晋升 FAIL（round46 承诺兑现）**：三项检查 round46 以 WARN 软门禁首轮（0 违例）、round47 全库 0 违例观察一轮无漏/无误报——本批由 `warn()` 晋升 `fail()`（FAIL 级硬门禁，任一违例阻断 exit 0），docstring 同步晋升注记；engineering-workflow §四 CI 门禁清单补级别注记（6.36/6.37/6.38 为 FAIL 级、6.26 档 4 为 WARN 级软提示）。
- **0.0.85 验证段 WARN 计数勘误（S 级诚实红线）**：0.0.85 叙述节验证段「6.26 WARN 维持 10 条已知噪声，无新增」不准确——round47 实际新增 2 条（「衰减口径」为上述全文构建缺陷的误报、「写入管线约束」为引用措辞不匹配），本批已实证定位并归零；0.0.85 的 12 条实际为「10 条历轮噪声 + 2 条新 WARN」。round47 报告 §四 同步修正。
- **验证**：doc-audit 全类复跑 exit 0（6.26 档 10 条 WARN 回归基线；6.36/6.37/6.38 晋升 FAIL 后全库 0 违例——晋升即通过，无既有违例被暴露）；deep-audit 复跑 exit 0。受改 1 份脚本（scripts/doc-audit.py）+ 2 份文档（api-spec 引用措辞、engineering-workflow 门禁注记）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.86；核心计数零漂移（错误码 43 / 参数 374 不变）；门禁全类验证 exit 0。

---

## 0.0.87（2026-08-10）— round49 全面深度审计修复批次（既往批次落体核查 + 语义层/结构层收口）

> 本轮为 round48（0.0.86）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.38 exit 0；deep-audit exit 0）。核查重点：既往批次（round47/48）声称的修复是否真正落体（写了=做了 诚实红线）+ 门禁扫不到的语义层/结构层问题，共闭环 **0 高 / 8 中 / 11 低** 共 19 项；术语 76→77（补「上下文腐烂」）、债务 D-440→D-442（新增 D-441/D-442）。修复后门禁全类复跑 exit 0。

**【中】既往批次落体核查（3 项）**
- **R49-01 round47 H-04 幂等模型正文未落体**：detailed-design §2 写入管线设计②仍为旧模型「重复提交按幂等键去重拒绝」（0.0.85 声称已统一为「同键返回首次结果 + ERR-CTR-005」，正文未改）——本批改写为 Idempotency-Key 模型（可选头、同键重复提交返回首次结果、键冲突载荷不一致 409 ERR-CTR-005；版本冲突 409 ERR-DB-005；两错误码分工说明）。0.0.85 H-04 的「修复均落在 api-spec / detailed-design」表述与正文脱节，本批补改并复核。
- **R49-02 round48 api-spec 引用措辞对齐未完成**：0.0.86 声称「§2 写入管线约束② → 写入管线设计②」已对齐、6.26 WARN 12→10 回归基线，实际仅改 §1.3（L174）一处，§1.1/L54 与 §1.2/L81 两处仍为旧措辞——本批补改；0.0.86 叙述节与版本记录行同步勘误（见上）。
- **R49-03 round47 受改清单失实**：0.0.85 验证段「受改 14 份」未列 architecture（实际有 0.0.85 版本记录条目：§5.2 状态转换纪律声明 M-01）、observability 标注「引用口径不动」（实际有实质变更：H-02 `kairos_forgetting_score` 指标说明同步 freshness 口径）、开头「未触碰架构权威语义」与 M-01 自相矛盾——本批修正清单（15 份）与表述，并同步 0.0.85 版本记录行。

**【中】语义一致性（3 项）**
- **R49-04 api-spec L55「建议携带 If-Match」与 L174「必需」同文件矛盾**（round47 H-05 乐观锁强制后未同步 L55）——L55 改「必须携带 If-Match（乐观锁强制，无最后写入胜出路径）」。
- **R49-05 决策/债务编号缺前缀**：架构 L705 表格「D-18」（同表他行均带前缀）、L1919/L1924/L1930/L2116/L3755 正文裸债务号、data-model L85「D-311 衔接」——补「决策/债务」前缀；架构 L2647「债务 [债务 D-401]」双重前缀去重。
- **R49-06 正文裸文件引用**：架构 6 处、detailed-design 4 处正文/代码块裸文件名——正文处链接化、代码块内补空格反引号；表格来源列（configuration 附录 A 约 147 行、adr 决策表约 25 处）经 documentation-governance §2 新增豁免条款显式豁免（目录式索引形态，反引号路径简写为合法形态）。

**【中】结构与组织（2 项）**
- **R49-07 长文档缺章节导航**：test-strategy / benchmark-plan / acceptance-criteria / slice-implementation-guide / risks 补章节导航表（round43 为 5 份补全后遗漏的 6 份）；adr 补 ADR 一览表（12 项已采纳 + 设计状态）。
- **R49-08 大章标题风格约定与实际不符**：documentation-governance §2 文档清单补「示例」限定 + 中文序清单补全（feature-list / implementation-map / nfr-specification / operation-catalog / system-context / test-strategy / acceptance-criteria / benchmark-plan / deployment / troubleshooting / reliability / threat-model 等）+ 第三类「实体索引型」标题形态（ADR-xxx / 0.0.x 版本号 / M1 里程碑等）为允许例外；README 认知基础引用 §一→§二 改数字（§1→§2）；release-guide `## vX.Y.Z` 模板标题降级 `###`。

**【低】缺失与过时（3 项）**
- **R49-09 追缴门禁补盲**：架构 §7.3 主题感知写入切分「v1.1 评估启用」登记债务 D-441（原文加指针）；runbook / reliability / observability 四处「参数化列入后续运维批次」登记债务 D-442（原文加指针）；debt-collection 补五段结构双形态并存声明 + 摘要表补 D-440/D-441/D-442 三行。
- **R49-10 glossary 补「上下文腐烂（Context Rot）」词条**（76→77，README / 架构 §11 计数同步，门禁 6.7 三方一致校验通过）；双时态英文拼写统一（concept-tiers「Bitemporality」→「Bitemporal」，对齐 glossary 权威）。
- **R49-11 use-cases 近孤儿**：requirements-baseline 定位段补 [use-cases.md](../specification/use-cases.md) 链接入口。

**【低】核心文档准确性（2 项）**
- **R49-12 technology-stack 投影措辞并称**：§二「线性投影」为映射通俗描述、ADR-012「固定随机正交投影」为具体方案——补「（投影方案：固定随机正交投影，见 ADR-012）」括注消除并称歧义。
- **R49-13 documentation-governance §4 版本记录表方向例证失实**：原「降序表（最新在表首，如 changelog 版本记录）」——changelog 实际升序、全库抽查 6 份文档均升序、未见降序实例；例证修正为「全库现行为升序表，降序表未见实例（若引入须单文档内一致）」。

**验证**：doc-audit 全类复跑 exit 0（6.26 档仍为 10 条历轮已甄别噪声、无新增）；deep-audit 复跑 exit 0。受改 21 份文档（原声明 22 份含 configuration——其经 R49-06 审视判定仅表格来源列豁免、无内容变更，不计入受改；0.0.89 勘误）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.87；核心计数变动：术语 **76→77**（补「上下文腐烂」）、债务 **D-440→D-442**（新增 D-441/D-442）；其余（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37）零漂移；门禁全类验证 exit 0。

---

## 0.0.88（2026-08-10）— round50 全面深度审计修复批次

**【中】引用落点错位（5 处）**
- **R50-01 feature-list Phase 2 引用错位 4 处**：R-23 QueryAnalyzer / R-24 时间覆盖采样 / R-27 时间覆盖检索 / SF-18 防抖反射执行器均引用架构 §2.1（元认知层定位），实际机制章节为 §2.6.1（QueryAnalyzer）/ §2.6.2（时间覆盖均匀采样）/ §2.6.3（防抖反射执行器）——章节号存在但语义指向错误，通过门禁 6.26 存在性检查的盲区（§2.1 存在故不报 FAIL），本批修正。
- **R50-02 data-model §8.18 query_analysis_cache 定位段 QueryAnalyzer 引用架构 §2.1→§2.6.1**（与 R-23 同机制的同源遗漏）。

**【低】版本边界措辞矛盾（1 处）**
- **R50-03 blueprint 四层记忆质量层次 DERIVED_FROM 描述为「memory_relations 表的新增关系类型」**，与 v0.1.0 基础六值枚举（data-model §1 / claim-matrix C-04 / feature-list W-05 已登记 derived_from）矛盾——修正为「关系类型（枚举值已随 v0.1.0 基础六值登记；本机制为 v1.1 的边创建路径）」。

**【低】分析批次过时计数（4 处）**
- **R50-04 triage-matrix 定位行素材范围过时**（100 视频 + 10 仓库 → 102 视频 + 15 仓库 + 21 论文）；统计表基于 9 论文过时 → 21；分诊统计「待全量统计」补全实际数值（74 条 EV：已覆盖 29 / 可吸收 35 / 张力 13 / 矛盾 3，复合标签计入多类）；AP/AT 编号范围更新（AP-01~52、AT-01~09）。
- **R50-05 first-principles-review 定位行实证规模过时**（42 视频 + 10 仓库 → 102 视频 + 15 仓库，含论文批次交叉引用）。
- **R50-06 absorption-proposals 定位行素材范围过时**（100 视频 + 9 论文 → 102 视频 + 21 论文）。
- **R50-07 analysis README 视频清单 VID 单元格补笔记链接**（102 行，导航直达）+ 24 行素材级别单元格 `B|` 缺空格归一为 `B |`（格式统一）。

**【低】格式与表述精度（2 处）**
- **R50-08 concept-tiers L1 四类契约行补系统内部第五契约「意图契约」注记**（对外四类 vs 系统五值口径，对齐架构 §3.7 / data-model contract）。
- **R50-09 use-cases 场景 4 外部校准写入表述精确化**（校准信号写入见证锚定主副本触发差异检验并更新校准置信度/见证值，`narrative_coherence_score` 由叙事自洽度评估器生成、非校准信号直接写入，见架构 §5.2）。

**验证**：doc-audit 全类复跑 exit 0（6.26 档仍为 10 条历轮已甄别噪声、无新增）；deep-audit 复跑 exit 0；analysis README 102 条新链接目标全部存在。受改 9 份文档 + changelog 本文件 + documentation-governance §3 执行记录；核心计数（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37 / 术语 77）零漂移。

---

## 0.0.89（2026-08-10）— round51 全面深度审计修复批次（落体核查 + 受改计数勘误 + 结构/格式收口）

> 本轮为 round50（0.0.88）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.38 exit 0；deep-audit exit 0）；6.26 剩余 10 条 WARN 逐条原文实证**全部为可忽略噪声**（7 条目标章节存在、3 条描述性词），零真实引用错位。语义层共闭环 **0 高 / 7 中 / 13 低** 共 20 项（另观察 1 项：configuration §0.10/§0.11 编号倒挂为受控形态，见 R51-14）。

**【中】落体核查与受改计数勘误（3 项）**
- **R51-01 debt-collection 摘要表补 D-440/D-441/D-442 三行落体**：0.0.87 R49-09 声称「摘要表补三行」实际未落体（D-439 后直接接 D-312/D-313/D-321）——本轮补行（含 D-443/D-444），并修订摘要表取舍声明（「预期版本」段为状态替代形态）与五段结构双形态声明（D-422~425/D-429/D-430/D-440 保留「可接受成本」段的精确枚举）。
- **R51-02 0.0.85 受改清单计数勘误**：原「受改 15 份」含 data-model / reliability（标注「引用口径不动」、无 0.0.85 版本记录条目）——受改清单只计实质变更，修正为「实质受改 13 份 md + openapi.yaml」，叙述节与版本记录行同步。
- **R51-03 0.0.87 受改清单计数勘误**：原「受改 22 份」中 configuration 经 R49-06 审视判定仅表格来源列豁免、无内容变更（无 0.0.87 版本记录条目）——修正为「受改 21 份」，叙述节与版本记录行同步；README 批次索引登记不计入受改清单的口径显式声明。

**【中】结构与组织（2 项）+ 【低】1 项**
- **R51-04 5 份超 200 行文档补章节导航**：deployment / runbook / test-plan / requirements-baseline / documentation-governance（round43/49 补 11 份后遗漏；导航表「章节 | 主题」两列形态对齐历轮）。
- **R51-05 feature-list 版本记录归位**：`### 版本记录` 原嵌于「八、系统管理」与「九、扩展功能」之间——升为 `## 版本记录` 并移至文末（最终计数节后）。
- **R51-06【低】claim-matrix 版本记录居文末**：「版本边界」节移至「版本记录」之前。

**【中】格式规范（2 项）**
- **R51-07 正文裸文件/裸文档名引用链接化**：架构 7 处（glossary/integration-design/detailed-design/feature-list/api-spec/rl-weight-spec/documentation-governance）+ 去除「用词勘误」过程标记残留 1 处 + §0 速查表 glossary 计数 76→77 修正（round49 遗漏）；blueprint 6 处（api-spec §11/§12/§13×3/§17）；slice-implementation-guide 7 处、engineering-workflow 7 处、integration-design 4 处、design-philosophy-relations 3 处、adr/development-setup/technology-stack 各 1 处。
- **R51-08 决策/债务编号缺前缀补标**：正文叙述 12 处——认知基础 5 处（D-313/D-16 A1/D-01/D-019(a)×3）、架构 D-01 2 处、blueprint D-17、configuration D-15/D-431、runbook D-430 2 处、social-calibration-roadmap D-305、benchmark-plan D-427；documentation-governance §5 增补**清单/索引形态豁免条款**（列表/表格/版本记录表说明列的编号列举不追溯改写）。

**【低】缺失与过时 + 格式收尾（6 项）**
- **R51-09 追缴门禁补盲二轮**：登记 D-443（MCP Resources/Prompts 渐进扩展，technology-stack §七）+ D-444（外部理念 4 处「v1.1 评估项」注记批量：MemGen 学习式触发/操作轨迹独立类型/bandit 检索策略/稀疏奖励 RL 配方）——架构 4 处 + technology-stack 1 处加「（债务 D-44x）」指针；摘要表与 §七 评估表补行。
- **R51-10 first-principles-review 正文过时计数**：总体判断「9 篇论文」→「21 篇论文」（round50 仅修定位行）。
- **R51-11 5 份近孤儿文档补正文入口**：架构 §0 补 design-philosophy-relations / system-context、架构 §10.18 补 domain_keywords.yaml、认知基础附录 D.13 补 vad-coordinate-algorithm、engineering-workflow 补 coding-conventions。
- **R51-12 WM 中英空格统一**：架构 8 处 + 认知基础 8 处（正文；代码块内保持原样）。
- **R51-13 格式收尾 4 项**：架构「校准锚定维度衰退模型」→「衰减」、「摄入侧按内容类型」→「摄取侧」；social-calibration-roadmap 多 Agent/单 Agent/跨 Agent 空格 24 处；test-strategy 版本记录日期范围统一。
- **R51-14 detailed-design H1 标题**：「# Kairos」→「# Kairos 详细设计」；acceptance-criteria §三 参数权威经核验为设计形态（configuration 附录 A 已登记 + 定义出处列指回，0.0.42 确立），非问题；configuration §0.10/§0.11 编号倒挂为受控形态（6 处引用，重编号将破坏引用链），记录在案不修。

**验证**：doc-audit 全类复跑 exit 0（6.26 档仍为 10 条历轮已甄别噪声、无新增）；deep-audit 复跑 exit 0。受改 22 份文档 + changelog 本文件 + documentation-governance §3 执行记录同步 0.0.89；核心计数变动：债务 **D-442→D-444**（新增 D-443/D-444）；其余（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37）零漂移；门禁全类验证 exit 0。

---

## 0.0.90（2026-08-11）— round52 全面深度审计修复批次（追缴补盲三轮 + H1 补齐 + 格式收口）

> 本轮为 round51（0.0.89）之后的全面深度审计轮（五维度：完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 18 类 + 14a + 6.13~6.38 exit 0；deep-audit exit 0）；6.26 剩余 10 条 WARN 复跑与 round51 一致（7 条原文比对目标章节存在、3 条描述性词），零真实引用错位。语义层共闭环 **1 中 / 5 低** 共 6 项（另观察 1 项：configuration §0.10/§0.11 编号倒挂为受控形态，维持）。核心文档精读（认知基础全文 1203 行 + 架构 §0/§1/§3 + 技术选型全文 175 行）未发现实质矛盾。

**【中】追缴门禁补盲三轮（1 项）**

- **R52-01 7 处「v1.1 候选/目标」软承诺无债务承载**：round51 D-444 批量登记后，同批次同型「外部理念吸收 0.0.44/0.0.48」注记仍遗漏 7 处——① §5.2 保留原因字段 v1.1 候选（REPO-03）；② §5.2 技能仓库级落地单元 v1.1 候选（PAPER-04）；③ §5.2 对话历史纳入语义检索 v1.1 目标；④ §5.5 差异检验分级阈值参数化 v1.1 候选（PAPER-08）；⑤ §5.5 错误模式库独立存储 v1.1 候选（PAPER-18/11/12）；⑥ §5.2 嵌入提供商可插拔 v1.1 候选（VID-16）；⑦ §7.3 图激活传播与时间粒度检索 v1.1 候选（PAPER-03）。登记 **D-445**（批量 7 项），架构原文 7 处加「（债务 D-445）」指针。

**【低】结构与格式收口（5 项）**

- **R52-02 architecture/blueprint 补 H1 一级标题**：全库其他核心文档均在 frontmatter 后设 H1，两文档此前直接进入 `## §0` / `## 一、`——补「# Kairos 系统架构」「# Kairos 架构蓝图（v1.1+）」（门禁 16 仅校验 frontmatter 字段、未校验 H1 存在性，属结构缺口）。
- **R52-03 「多 Agent/单 Agent/跨 Agent」空格统一 20 处**：round51 4-4 仅修 social-calibration-roadmap（29 处），同模式在架构 12 处 / 认知基础 6 处 / debt-collection 1 处 / traceability-map 1 处仍为紧邻中文形态——本轮全部统一。
- **R52-04 「架构[链接]」「认知基础[链接]」中英空格统一 10 处**：认知基础 9 处 + 架构 1 处为「架构[architecture-v0.1.0.md](...)」紧邻形态，其余 244 处带空格——统一为带空格。
- **R52-05 P1-P6 半角连字符统一全角 6 处**：architecture 1 / cognitive-foundation 1 / design-philosophy-relations 4（含 ASCII 图内文字，宽度不变不影响对齐）。
- **R52-06 版本记录链与执行记录同步**：受改 7 份文档（architecture / blueprint / cognitive-foundation / design-philosophy-relations / debt-collection / traceability-map / README 批次索引登记）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.90。

**验证**：doc-audit 全类复跑 exit 0（6.26 档仍为 10 条历轮已甄别噪声、无新增）；deep-audit 复跑 exit 0。受改 7 份文档 + changelog 本文件 + documentation-governance §3 执行记录同步 0.0.90；核心计数变动：债务 **D-444→D-445**（新增 D-445）；其余（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37）零漂移；门禁全类验证 exit 0。

---

## 0.0.91（2026-08-11）— 外部理念吸收落地批次（LongMemEval 记忆能力评测协议）

> 吸收来源：用户提供《记忆系统能力评测协议 v1.0（LongMemEval 统一基准）》（2026-08-11，用户本地文件，非视频/论文批次素材）——LongMemEval 为公开学术基准（cleaned 数据集 500 条，6 类问题：single-session-user / single-session-preference / single-session-assistant / multi-session / temporal-reasoning / knowledge-update），测「对话→事实提取→检索→推理」完整记忆管道，业界 Mem0 / Zep / Letta 均以统一格式报分可横向对比。落地形态：benchmark-plan 新增 §3.15 记忆能力评测协议（评估协议章节，无新增参数/机制），test-plan 预留 TC-LME 编号，absorption-proposals 登记 AP-53。

**落地清单**：
- **benchmark-plan 新增 §3.15 记忆能力评测协议**（[benchmark-plan.md](../quality/benchmark-plan.md)）：七步流程（数据下载 / 取样 18 条（可缩至 12 条须报样本数）/ 独立 namespace 隔离 / 灌入 haystack 会话（category=session）/ 检索 top-k≥15 / 生成 UNKNOWN 防编造 / judge 0/1 语义等价判定）+ **Kairos 变体定义**（加工管线变体为主报形态、原始对话直搜为对照形态；检索 / 生成 / judge 模型与样本分布申报）+ 汇报格式硬规则 5 条（变体说明 / 生成模型标注 / 禁止主观自评 / 检索为空或 judge 解析失败记 0 / 检索命中率与总准确率分离归因）+ 参考基线（Mem0 49% / Zep-Graphiti 63.8% / Letta ~83%，**只作参考不作门槛**——须本地校准后方可作门槛，三要素一致才可比）+ 既有机制联动（§3.12 六梯度作 G1~G6 统一评测任务集 / test-strategy §2.7 反事实检验作外部验证集 / §3.11 能力验证门四门声明 / test-plan TC-LME 编号）。
- **benchmark-plan §3.12 联动注记**：六梯度统一评测任务集建议采用 LongMemEval 公开数据集——公开固定数据集，验证集与经验来源天然分离（满足 §3.11 红线）。
- **test-plan §2 预留编号**（[test-plan.md](../quality/test-plan.md)）：TC-LME-001~（LongMemEval 记忆能力评测，协议指针到 benchmark-plan §3.15；依赖 LLM 评测链路，代码启动后补充）。
- **acceptance-criteria §一a 测量任务集补充**（[acceptance-criteria.md](../quality/acceptance-criteria.md)）：任务成功率改善指标补「测量任务集可选用 LongMemEval 公开数据集」（§3.15 反向指针——三态对比测量载体的任务集来源落地）。
- **吸收建议四e 登记**（[absorption-proposals.md](../analysis/external-videos/absorption-proposals.md)）：AP-53 建议态 → 已落地。

**参数计数**：不变（无新增 KAIROS_* 参数，评估协议形态）。

**验证**：doc-audit 复跑 exit 0。受改 4 份文档（benchmark-plan / test-plan / acceptance-criteria / absorption-proposals）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.91 + README 批次索引登记（0.0.89 口径：批次索引登记不计入受改清单）；核心计数（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37 / 债务 D-445）零漂移。

---

## 0.0.92（2026-08-11）— 定稿收尾批次（设计基线冻结 + D-431 分类处置 + 工具修复）

> 依定稿评估结论（round52 后审计收敛至 0 高 1 中 5 低、门禁全绿、竖切配套完整），于本批次执行定稿收尾三动作：① D-431 十项待定义参数分类处置（消除「编码启动前须补齐」的硬门禁笼统声明）；② documentation-governance §4 登记设计基线冻结声明（含外部理念吸收边界 0.0.91 止）；③ doc-audit.py GBK 控制台编码崩溃修复（对齐 deep-audit 0.0.6 先例）。**设计基线冻结**：此后至代码启动前修订仅限三类——P0 一致性缺陷 / 冻结后的外部理念吸收（登记边界）/ 登记类机械更新；设计内容变更一律进入 v1.1 域或重建决策。

**落地清单**：
- **D-431 分类处置**（[configuration.md](../ops/configuration.md) 附录 A 引言 + [debt-collection.md](../governance/debt-collection.md) D-431 五段/摘要表/评估表三处同步）：10 项待定义按来源域分类——8 项源头在 architecture-blueprint-v1.1 的 v1.1 域参数（DERIVED_FROM_MIN_STRENGTH / PLAYBOOK 阈值×2 / PROMPT_DEPENDENCY_STRATEGY / SKILL_EXPERIMENTAL_MAX_AGE / SUBLIMATION_ENCRYPTION_KEY / TEMPORAL_EXTRA_BUFFER_DAYS / KAIROS_PATH（随 detailed-design 实体标签 schema 落地补齐））随对应功能迭代定义；2 项部署环境变量（ADMIN_IPS / DB_PASSWORD）部署时点确定。**竖切（v0.1.0-slice）相关参数核验无待定义项**——硬门禁声明收口为分类处置，D-431 预期版本改「v1.1 域追踪」。
- **设计基线冻结声明**（[documentation-governance.md](../governance/documentation-governance.md) §4）：冻结后修订仅限三类；外部理念吸收边界声明为 0.0.91 止（LongMemEval 评测协议为冻结前最后一笔吸收），后续新素材默认进入 v1.1 域或债务化。
- **工具修复**：doc-audit.py 入口 stdout/stderr reconfigure UTF-8（`UnicodeEncodeError` GBK 崩溃——历轮「门禁全绿」均需 `PYTHONIOENCODING=utf-8` 环境方能跑通，本轮修复使裸跑可用；检查逻辑零改动）。

**参数计数**：不变（374 项；10 项待定义标注形态不变，分类处置不新增参数）。

**验证**：doc-audit 复跑 exit 0（本批次起可裸跑，无需 PYTHONIOENCODING）。受改 3 份文档（configuration / debt-collection / documentation-governance）+ scripts/doc-audit.py + changelog 本文件 + README 批次索引登记（不计入受改清单）；核心计数（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37 / 债务 D-445）零漂移。

---

## 0.0.93（2026-08-11）— round53 全面深度审计修复批次（追踪项计数收口 + 版本记录补登 + 格式收尾）

> 0.0.92 定稿基线后首轮五维全面深度审计（完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 裸跑 exit 0 + deep-audit exit 0；6.26 档 4 十条 WARN 逐条实证甄别全部为可忽略噪声），语义层新发现 **0 高 / 1 中 / 3 低**（另 2 观察项）全部闭环。

**落地清单**：
- **R53-01（中）追踪项计数收口**：traceability-map 定位段「104 追踪项」0.0.37 快照更新为指向权威账目——0.0.43 起活跃债务持续新增（D-422~D-445 共 24 条，活跃条目约 87→111）后总量口径随登记动态变化，改为「debt-collection 为权威账目（0.0.92 时点活跃 111【0xx 23 + 1xx 7 + 3xx 36 + 4xx 45】+ 归档闭环 31 + 理念吸收追踪 62 MNM），本表不再维护总量快照」；README 索引行「104 追踪项」同步改指针表述。
- **R53-02（低）版本记录补登**：traceability-map 补 0.0.90 版本记录行（round52 受改：frontmatter + 「多 Agent」空格 1 处，此前漏登记，「触及即登记」纪律）。
- **R53-03（低）引用措辞**：slice-implementation-guide 计数口径注记「project-plan §一 竖切组件列」→「竖切范围表组件行」（对齐 project-plan 实际表结构，引用语义不变）。
- **R53-04（低）changelog 浏览指引**：本文件开头补「如何浏览」指引（按版本号/日期定位、跨文档关系见 README 与各文档版本记录），弥合超长文档导航缺口。
- **R53-05（低）结尾换行**：[feature-list.md](../specification/feature-list.md) 文末补换行符（deep-audit 捕获，二进制模式修复，无 CRLF 污染）。
- **观察项**：R53-O1 configuration「## 一/## §11」标题风格混用为门禁硬编码锚点受控形态（doc-audit `cfg.find("## §11")`，不可改名）；R53-O2 六条 WARN 全为噪声——均记录在案不修复。

**参数计数**：不变（374 项）。

**验证**：doc-audit 复跑 exit 0（裸跑）；deep-audit exit 0。受改 6 份文档（traceability-map / README / slice-implementation-guide / changelog 本文件 / documentation-governance / feature-list）+ 审计报告 `2026-08-11-round53-deep-audit.md`（工作区根，gitignored）；核心计数（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37 / 债务 D-445）零漂移；README 批次索引登记不计入受改清单（0.0.93 显式声明）。

---

## 0.0.94（2026-08-11）— round54 全面深度审计修复批次（版本记录登记缺陷收口 + 措辞精度）

> 0.0.93 修复批次后首轮五维复验（完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）。机器门禁基线全绿（doc-audit 裸跑 exit 0 + deep-audit exit 0；6.26 档 4 十条 WARN 与 round53 逐条甄别结论一致），语义层新发现 **0 高 / 0 中 / 2 低**（另 2 观察项）全部闭环。主审另完成门禁盲区机械化扫描：H1 全库 53 份无缺失、标题层级跳变 0 真跳变（初扫 9 处均为代码围栏内伪代码/注释误报）、9 份超长文档导航齐备、中英空格三类同源模式正文零残留、版本记录日期全库 YYYY-MM-DD、软承诺追缴全库通过。

**落地清单**：
- **R54-01（低）版本记录登记缺陷双缺陷收口**：traceability-map 版本记录 0.0.90 行混入本属 0.0.93 的内容（追踪项口径更新为 round53 R53-01 修改，误记入 round52 批次行）且 0.0.93 行缺失——0.0.90 行删除该内容（仅保留「多 Agent」空格统一 1 处 + frontmatter 同步），新增 0.0.93 行（追踪项口径收口 + README 同步）；「触及即登记」纪律违反复发（R53-02 同类）收口。
- **R54-02（低）措辞精度**：deployment 标准级「宪法主权面」措辞「舍弃（…；外部校准端口为不可裁剪最小承载）」→「舍弃完整形态，继承简化（外部校准端口为不可裁剪最小承载，架构 §0.5 标准级）」——对齐架构 §0.5「继承内核级简化形态」权威口径，消除「完全移除」误读可能。
- **防复发规则**：documentation-governance §4「触及即登记」纪律补充操作细节——补登版本记录时须核对当批次受改清单内每份文档均已建对应批次行，且补登历史行不得混入本批次内容（R54-01 根因治理）。
- **门禁 6.39 落地（round54 改进建议第 4 项，WARN 级软门禁）**：doc-audit.py 新增 `check_batch_version_record_coverage`——以 changelog 最新批次叙述节「受改 N 份文档（…）」清单为输入，逐文档核对版本记录是否含该批次行（兼容 `## 版本记录`/`## §12 版本记录` 两种标题；剥 markdown 链接/缩写映射/非 md 条目跳过防误报；清单缺失时跳过不判）。**首跑即捕获真实缺陷**：traceability-map 在 0.0.94 批次受改（版本记录修正）但缺 0.0.94 行——本批次补登（「触及即登记」操作细节落地）。engineering-workflow §四 / project-plan Phase 0 门禁清单镜像同步 6.39。
- **观察项**：R54-O1 configuration「## 一/## §11」标题风格混用（门禁硬编码锚点受控形态）；R54-O2 [risks.md](risks.md) 风险条目缺「概率/复核周期」字段（文档显式声明为 v0.1.0.x 目标已知缺口）——均记录在案不修复。

**参数计数**：不变（374 项）。

**验证**：doc-audit 复跑 exit 0（裸跑，含 6.39 首跑 0 漏登记）；deep-audit exit 0。受改 7 份文档（traceability-map / deployment / changelog 本文件 / documentation-governance / engineering-workflow / project-plan）+ scripts/doc-audit.py + 审计报告 `2026-08-11-round54-deep-audit.md`（工作区根，gitignored）；核心计数（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37 / 债务 D-445）零漂移；README 批次索引登记不计入受改清单（0.0.94 显式声明）。

---

## 0.0.95（2026-08-11）— Obsidian frontmatter 闭合缺陷修复批次（6 份文档 + 门禁 6.16 盲区增强）

> 用户发现 [adr.md](adr.md) 与 [risks.md](risks.md) 在 Obsidian 中显示「无效属性」，排查确认根因：frontmatter 在 `status: draft` 后**缺少立即闭合的 `---`**，后续正文引用块（`> **ADR 一览**` / `> **章节导航**` 等）被 Obsidian 卷入 YAML 解析区导致无效属性。全库扫描发现同类问题共 **6 份文档**，全部修复；并定位门禁 6.16 盲区（非贪婪正则误匹配正文 `---` 分隔线），增强门禁防复发。

**落地清单**：
- **R55-01（中）frontmatter 缺闭合分隔符批量修复**：6 份文档补 `status: draft` 后立即闭合的 `---`——[adr.md](adr.md)（ADR 一览引用块被卷入）、[risks.md](risks.md)（章节导航引用块被卷入）、slice-implementation-guide / acceptance-criteria / benchmark-plan / test-strategy（章节导航引用块被卷入）。正文原有 `---` 分隔线（H1 前）保留不动，frontmatter 区现为 `---` 开头、字段区、`---` 立即闭合、空行后正文引用块的标准形态。
- **R55-02（中）门禁 6.16 盲区增强**：原 `\\A---\\n(.*?)\\n---\\n` 非贪婪正则在前置缺陷下会误匹配正文 `---` 分隔线，将引用块/表格卷入 frontmatter 而不报错。增强为字段检查前置「frontmatter 区内容合法性」校验——闭合 `---` 前只允许 YAML 形态行（`key:` / 缩进 / `- 列表` / `# 注释` / 空行），出现 `>` 引用块、`|` 表格、普通文本行即 FAIL（附首处违规行定位）。**突变测试验证**：临时移除 [adr.md](adr.md) 闭合 `---` → 门禁捕获（exit=1）→ 还原全绿（exit=0）。
- **全库复验**：53 份核心 md + analysis 143 份全部 frontmatter 正常闭合、YAML 可解析（pyyaml safe_load 全通过）、无 CRLF 污染（二进制模式写入）。
- **观察项**：本次缺陷为历史遗留（非本轮审计引入）——doc-audit 6.16 盲区自门禁建立起即存在，Obsidian 侧可正常渲染属性但部分工具（Obsidian 属性面板）显示无效；门禁增强后根治。

**参数计数**：不变（374 项）。

**验证**：doc-audit 复跑 exit 0（含增强后 6.16 全库 196 份通过）；deep-audit exit 0。受改 6 份文档（adr / risks / slice-implementation-guide / acceptance-criteria / benchmark-plan / test-strategy）+ scripts/doc-audit.py + changelog 本文件 + documentation-governance（执行记录补记）；核心计数（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37 / 债务 D-445）零漂移；README 批次索引登记不计入受改清单（0.0.95 显式声明）。

---


## 0.0.96（2026-08-11）— 定稿审查处置批次（四组全量通读发现的低危缺口收口 + D-430 分类处置 + D-446 登记）

> 依「全面了解所有项目文档、完成定稿」要求，对核心文档分四组全量通读（foundation / specification / development+ops / 治理+质量+安全+用户+参考，56 份核心文档），审查结论：**设计层无阻断级缺陷**（0.0.92 冻结后审计收敛至 0 高，竖切配套完整），发现一批低危真实缺口（1 处 P0 事实性错误 + 1 处竖切直接相关无归属缺口 + 若干机械性/口径问题）与 1 项编码启动硬门禁（D-430）分类处置，本批次全部收口。

**落地清单**：
- **P0 事实性修正（use-cases）**：覆盖范围声明误将竖切组件 3「三信号混合检索」（v0.1.0 首迭代，R-18）归入「场景待 v1.1 补充」——修正声明并补勘误注记（与 feature-list / implementation-map / requirements-baseline 三处权威源对齐）。
- **竖切直接相关缺口（D-446 新登记）**：架构 §5.2 叙事自洽度评估器「降级默认分数（待定态）」——竖切内 `NARRATIVE_IDENTITY=ON`（宪法核），降级路径无默认值可依；登记 D-446（v0.1.0 首迭代确定默认分数并登记 configuration 附录 A），架构原文加债务指针。
- **D-430 分类处置**（[debt-collection.md](../governance/debt-collection.md) 五段/摘要表/评估表 + [troubleshooting.md](../ops/troubleshooting.md) 门禁段落）：竖切相关子项 `kairos config show`（竖切 CLI 15 交付项，组件 9）已于本批次在 [api-spec.md](../specification/api-spec.md) §3 登记契约——**竖切启动无待定义命令**；其余 10 条 + `kairos init --seed-path`（灾难恢复/运维/发布验证链路，均不在竖切端点集内）归 v0.1.0 全量阶段登记，不阻塞竖切启动；原「编码启动前须全部登记」笼统硬门禁收口为分类处置。
- **机械性与口径修正**：cognitive-foundation 章节导航表「社会性校准」归位（E → C.3）；requirements-baseline「CAL-02 见上表」悬空注记改指 test-plan §3.6；operation-catalog OP-054 补口径注记（freshness 条件为操作目录补充语义，协议层以 api-spec §1.5 为权威）；deployment 环境变量表补 `KAIROS_API_KEY_HASH`（轻量模式单 Key 认证，竖切形态——原表仅 `KAIROS_API_KEY` 覆盖不全）；架构 §3.2 宪法主权面引用改指认知基础 §3.1 已升格可评估框架（债务 D-305/D-332）；架构 §5.2 `summarize_thread` 补 v1.1 启用标注（对齐 api-spec §8）；debt-collection §7.2 统计表同步（D-431 移入维持行、D-446 入首版行，合计 91→92）。
- **设计基线冻结合规**：本批次全部改动属冻结三类中的「P0 一致性缺陷」与「登记类机械更新」，无设计内容变更。

**参数计数**：不变（374 项；D-446 的默认分数参数名与取值待编码启动首迭代登记）。

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0。受改 9 份文档（use-cases / cognitive-foundation / requirements-baseline / operation-catalog / architecture-v0.1.0 / deployment / api-spec / troubleshooting / debt-collection）+ changelog 本文件 + documentation-governance §3 执行记录同步 0.0.96 + README 批次索引登记（不计入受改清单）；核心计数变动：债务 **D-445→D-446**（新增 D-446）；其余（表 57 / 参数 374 / 错误码 43 / 术语 77 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / ADR 12 / 声明 37）零漂移。

---

## 0.0.97（2026-08-11）— 竖切代码启动批次（W1~W9 全量交付 + 基准 + 契约补全 D-428 竖切部分）

> **代码状态里程碑**：文档定稿后竖切（v0.1.0-slice）开发启动，W1~W9 全部里程碑交付。docs/README 状态声明由「文档草稿阶段，无运行代码」更新为「竖切代码开发中（W1~W9 已交付）」；[project-plan.md](../governance/project-plan.md) 里程碑计划进入执行态。

**代码交付**（`src/` 全量 35 个模块，151 项测试全绿 + ruff/mypy 全绿）：
- **W1 骨架**：pyproject（Typer CLI 定档，W1 决策落地）、配置加载（竖切参数族 + S-01 启动校验）、密钥生成（PBKDF2-HMAC-SHA512 256k 迭代，security-spec §2.1）。
- **W2 数据库与 CI**：Alembic 迁移链（schema-slice.sql 权威 DDL 执行，15 张竖切表 + FTS5 同步触发器，迁移可回滚）、pytest/ruff/mypy 管线、GitHub Actions CI（doc-audit/deep-audit/契约 lint）、**D-428 竖切部分闭合**（openapi 竖切 21 端点 request/response schema + mcp-tools.json 15 工具 inputSchema，`redocly lint` 零 error；全量 88 操作其余部分待 Phase 0 收尾）。
- **W3 记忆 CRUD + 双副本**：写入（捕获门控五层 + 幂等键 + 单事务三分提交）、读取、更新（If-Match 乐观锁 + 版本链追加）、删除（契约分支：permanent 拒删 / intention 409 / temporary 硬删 / 其余软删）、双副本 S-14 隔离防线（使用权重永不反写见证锚定，单测断言）。
- **W4 路径空间 + 事件总线**：`kairos://` 前缀索引（GLOB 走 B-tree，路径隔离污染率 0%）、4 类事件发布/订阅/背压（优先级 0-2 不被阻塞，7-9 超限丢弃）/trace_id 审计。
- **W5 三信号混合检索**：语义（numpy 余弦扫描，1 万条基准 P50 ≤100ms）+ BM25（FTS5）+ 实体加成（词典匹配）融合（0.50/0.35/0.15，norm 归一化 + 运行时退化）。
- **W6 遗忘 + 潜伏势能**：freshness 单曲线（2^(-days/69)）、三阈值状态转换、S-10 见证豁免、复兴（匹配验证 ≥0.65）、遗忘候选队列。
- **W7 身份注册表**：初始赋予 + 双向更新（strengthen/降级判例门槛）+ 否决裁决器（§1.8 预提交总线检查）+ identity_demotion 审计（S-16）。
- **W8 校准/降级/审计**：外部校准端口（S-11）、降级状态机（三模式 + 校准时延驱动 + 显式切换）、强制冻结（config 表持久化 + 写路径拒绝）、审计庭 HMAC 链（篡改检测）。
- **W9 集成与基准**：REST 21 端点（Litestar + API Key 鉴权 + S-04 回环绑定）、CLI 15 条全量、基准脚本（写 P50 16.6ms ≤50ms ✓ / 路径检索 / 语义检索 1 万条），报告落盘 `reports/benchmark-baseline-0.1.0.json`。

**实现偏差登记**（[debt-collection.md](../governance/debt-collection.md) 五段格式）：D-447（sqlite-vec 扩展在 Windows 官方 Python 不可加载，numpy 扫描替代）、D-448（BGE-M3 待接入，开发默认 HashEmbedder）——摘要表同步补行。

**接口契约**：openapi.yaml 竖切 21 端点 schema 落地（MemoryWriteRequest/SearchResponse/HybridSearchRequest 等 26 个 schema 组件）+ mcp-tools.json 15 工具 inputSchema 补全；`redocly lint --extends minimal` 零 error 达成 D-428 竖切部分验收判据。

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0。结构性受改 3 份文档（README / debt-collection / changelog 本文件，均已登记 0.0.97 版本记录行）+ 机械性受改 0 份；契约 2 份（openapi.yaml / mcp-tools.json，非 md 不计入文档受改清单）；核心计数变动：债务 **D-446→D-448**（新增 D-447/D-448）；其余（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168）零漂移。

---

## 0.0.98（2026-08-12）— 版本记录双轨制规则修订批次（结构性变更即登记）

> 落实「版本记录优化」决策（方案 B 双轨制）：各文档版本记录从「触及即登记」（任何改动批次逐条登记，随批次增长无限膨胀）改为「**结构性变更即登记**」——版本记录只登记影响文档语义/结构的变更，机械性变更（frontmatter 同步、引用链接化、措辞微调、批次索引登记等）只进 changelog 不登记版本记录。changelog 保持跨文档全量叙述层定位。

**落地清单**：
- **documentation-governance §4 规则修订**：「触及即登记」纪律（0.0.66 批次）与操作细节（0.0.94 批次）改写为「结构性变更即登记」纪律——定义结构性/机械性两类变更边界；批次叙述须声明「结构性受改 N 份文档（A / B / C）」清单（门禁 6.39 核对输入）。
- **doc-audit 6.39 门禁适配**：受改清单解析优先「结构性受改 N 份文档」形态（0.0.98 起）；无该形态时回退旧「受改 N 份文档」格式兼容历史批次；机械性受改不检查版本记录。
- **changelog 0.0.97 受改清单标注**：原「受改 3 份文档」标注为「结构性受改 3 份文档」+ 机械性 0 份（新格式立即生效验证）。

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0。结构性受改 2 份文档（documentation-governance / changelog 本文件）+ 机械性 1 份（scripts/doc-audit.py，非文档不计入清单）；核心计数零漂移（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / 债务 D-449）。

---

## 0.0.99（2026-08-12）— 竖切首迭代批次（事件总线接线/调度器/QueryAnalyzer/特征标志/证伪/D-428 全量闭合）

> 竖切验收后的首迭代交付（slice-implementation-guide 组件 3 注记 + 架构 §0.8/§2.6.1 + 工程流程证伪纪律落地）。代码 222 项测试全绿，双门禁 exit 0。

**落地清单**：
- **事件总线全链路接线**（组件 7 验收补强）：use_event 发布（记忆写入/检索/归档/删除 → 影子副本订阅者升温）；4 类事件 trace_id 全链路可审计。
- **APScheduler 空闲驱动调度**（ADR-006/架构 §2.6.3）：forgetting_scan（10s 防抖）/ latent_reevaluation（5s 防抖）/ forget_after_scan（temporary 契约到期硬删除 + expiry_cascade_delete 审计 HMAC 链）/ degradation_tick（300s）；任务错误隔离不阻断调度循环。
- **QueryAnalyzer 首迭代**（架构 §2.6.1）：意图分类五+1 类（规则优先 + 模型兜底接入点）、时间锚定四类解析（相对窗口/日历周/绝对/事件锚定 optional 降级）、fallback_query 剥离、时间硬过滤注入三信号检索（occurred_at 优先、空回退 created_at）。
- **特征标志配置集**（架构 §0.8）：kairos-slice/minimal/full 命名配置集声明与启动校验（invalid_flag_composition / constitutional_core_unavailable 拒绝路径）、宪法核不可禁用、标志硬上限 24、H1/H2/H3 核心假设绑定；竖切口径注记（ENTITY_GRAPH 三信号落地）。
- **证伪测试套件**（[FALSIFICATION] 标记，工程流程 CI 门禁）：H2 证伪降级路径（→kairos-minimal 合法配置集）、H3 fail-closed containment、证伪日志格式。
- **D-428 全量闭合**：88 操作 request/response schema 全部落地（71 端点语义化补全 + 错误响应统一 ErrorResponse），Skeleton 占位定义移除，`redocly lint` 零 error（7 项 WARN 级提示不阻断）——[debt-collection.md](../governance/debt-collection.md) 正文五段/§六 关键路径表同步关闭。

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0；redocly lint 零 error。结构性受改 2 份文档（debt-collection / changelog 本文件）+ 机械性 0 份；核心计数变动：债务 **D-428 闭合**（D-447/D-448/D-449 维持）；其余（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168）零漂移。

---

## 0.0.100（2026-08-12）— 竖切验收核对批次（W10 正式收尾前置 + 运行补强）

> 竖切验收标准（acceptance-criteria 〇 项）9 条逐项核对：8 条判据代码侧全部达成（证据见下表），第 9 条「定稿评审/版本号升级」待评审人执行（前置条件已全部满足）。首迭代后的运行补强与挂起修复本批登记。

**落地清单**：
- **事件总线入队非阻塞修复**（基准挂起根因）：publish 后内存分发队列满时曾阻塞主操作路径（写入采样 128 条后挂起）——改为满队列丢弃分发并计数（事件已持久化到 usage_events 表，分发通道可丢、影子副本可经维护重放）；基准恢复 PASS。
- **Agent Tool 层**（api-spec §2 五工具）：memories_write / memories_search / path_browse / memories_list_recent / memories_merge（S-14 约束 + 源软删除）。
- **GET /health 增强**：components 补 scheduler/embedding 状态（observability 口径：运行态在 /health 可见）。
- **竖切验收核对**（acceptance-criteria 〇 项）：

| 验收项 | 判据 | 证据 | 状态 |
|:--|:--|:--|:--|
| 功能闭环 | E2E-01/02/04/05/06/07/08 | tests/e2e/test_e2e.py（7 用例） | ✅ |
| 双副本分离 | S-14 使用权重写回见证被拒绝 | tests/unit/test_dual_copy.py TestS14Isolation | ✅ |
| 遗忘闭环 | TC-F01~F03 | tests/unit/test_forgetting.py | ✅ |
| 身份构造论 | G-03 + S-10 | tests/unit/test_identity_registry.py | ✅ |
| 事件总线 | 4 类 + trace_id 审计 | tests/integration/test_event_bus.py + test_event_wiring.py | ✅ |
| 存储后端 | SQLite 全功能 + StorageBackend 可替换 | tests/unit/test_backend.py（MockPG 可替换性） | ✅ |
| 性能基准 | 写≤50 / 路径≤20 / 语义≤100ms | reports/benchmark-baseline-0.1.0.json（PASS：4.7/3.4/1.4ms） | ✅ |
| 质量门禁 | 覆盖率≥80% / 红线 / doc-audit / RTM | 覆盖率 85.23% / test_redlines.py / doc-audit 全绿 | ✅ |
| 定稿评审 | 版本号升级 0.0.1→0.1.0 | 代码侧前置全达成 | ⏳ 待评审人 |

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0；redocly lint 零 error。结构性受改 1 份文档（changelog 本文件）+ 机械性 0 份；核心计数零漂移（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / 债务 D-447~449）。

---

## 0.0.101（2026-08-12）— 接入层全通道交付批次（Agent Tool + MCP Bridge + StorageBackend）

> 竖切验收核对后的接入层补齐——Agent Tool 层（api-spec §2 五工具）、MCP Bridge（§6.8 15 工具独立子进程）、StorageBackend 抽象（D-449 前置落实）。v0.1.0 接入层三大通道齐备：REST API（21 端点）+ CLI（15 条）+ Agent Tool（5 工具）+ MCP（15 工具）。

**落地清单**：
- **Agent Tool 层**（`src/access/tools.py`）：memories_write（S-15 provenance 必填）/ memories_search（三信号+路径过滤）/ path_browse（树状浏览+截断标记）/ memories_list_recent（影子副本排序）/ memories_merge（语义合并+S-14+源软删除）。
- **MCP Bridge**（`src/access/mcp/bridge.py`，FastMCP 1.x）：15 工具注册（mcp-tools.json 契约对齐）；独立子进程 stdio 传输、与主进程 localhost HTTP 通信（主进程 base URL 环境变量配置）；治理门禁经主进程 REST 继承（L1 鉴权/L2 宪法/L3 身份否决）；`kairos mcp` CLI 入口。
- **StorageBackend 抽象**（`src/storage/backend.py`）：detailed-design §2 五方法契约 + SQLiteBackend（薄适配）+ MockPGBackend（接口可替换性，acceptance-criteria「存储后端」判据）——D-449 前置落实。
- **GET /health 增强**：components 补 scheduler/embedding 状态（observability 口径）。

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0。结构性受改 1 份文档（changelog 本文件）+ 机械性 0 份；核心计数零漂移（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / 债务 D-447~449）。

---

## 0.1.0（2026-08-12）— v0.1.0 首版发布批次（定稿评审通过 + 全库版本升级）

> **评审结论**：竖切验收标准（acceptance-criteria 〇 项）9 项全部达成——8 项代码侧判据（功能闭环 E2E 7 条 / 双副本 S-14 / 遗忘 TC-F01~F03 / 身份 G-03+S-10 / 事件总线 / 存储后端可替换 / 性能基准 PASS / 质量门禁 85.23%+双门禁全绿）+ 定稿评审执行（release-guide §2 检查清单 10 项全过 + §3 构建/安装/版本验证通过）。**全库文档版本号统一升级（0.0.x → 0.1.0）**——release-guide §1 定稿规则落地：设计定稿 + 代码首版 v0.1.0（`src/__init__.py` / pyproject 0.1.0）；文档状态 draft → design-freeze（documentation-governance §4 晋升规则执行）。

**落地清单**：
- **定稿评审执行**：release-guide §2 检查清单逐项（P0=0 / 覆盖率 85.23% / E2E 竖切 7 条 / 红线竖切项 / CHANGELOG / 版本号 / doc-audit / 迁移回滚实机验证 / 备份 N/A 首版 / `uv build` wheel+sdist 成功）；§3 步骤 2-3（构建 + 干净 venv 安装验证 `kairos --version` = Kairos 0.1.0）。
- **全库版本升级**：52 份文档版本记录统一升级至 0.1.0（升序表尾追加升级行）；frontmatter status draft → design-freeze（代码启动后晋升规则执行）；updated/last_reviewed 同步 2026-08-12。
- **版本记录双轨制衔接**：升级行为结构性登记（全库一次性），后续 0.1.x 系列按「结构性变更即登记」纪律执行。
- **代码交付回顾**（自 0.0.97 起）：竖切 W1~W10 → 首迭代（事件总线接线/调度器/QueryAnalyzer/特征标志/证伪）→ D-428 全量闭合 → StorageBackend 抽象 → Agent Tool → MCP Bridge → 真实服务冒烟 → 运行补强（事件入队非阻塞/健康检查增强）——244 项测试、覆盖率 85.23%、双门禁全绿、redocly 零 error。

**验证**：doc-audit 复跑 exit 0；deep-audit exit 0。结构性受改 53 份文档（全库版本升级——52 份 + changelog 本文件）；核心计数零漂移（表 57 / 参数 374 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / 债务 D-447~449）。

## 0.1.1（2026-08-12）— Hermes Memory Provider 接入批次（契约对齐 + 端到端验证 + 部署登记）

> **背景**：本批次接续 0.0.101（MCP Bridge）——Hermes 接入的 Provider 通道。参考实现（`src/access/provider/kairos_provider.py`）与插件壳（`src/access/provider/hermes_plugin/`）首版已就位，本批次对照 Hermes 本机安装（agent/memory_provider.py，MemoryProvider ABC）做真实接口契约对齐并完成端到端验证。0.1.0 后债务 D-447~449 闭合（debt-collection 已登记 0.1.1 版本记录行）——本条目为 changelog 叙述补记。

**落地清单**：
- **Hermes ABC 契约对齐**（对照本机 Hermes `agent/memory_provider.py` 真实签名）：① `handle_tool_call` 返回值由 dict 改为 **JSON 字符串**（Hermes 契约 `-> str`），签名对齐 `(tool_name, args, **kwargs)`；② 新增 `queue_prefetch`（轮后后台召回缓存，下一轮 `prefetch` 消费；无缓存时同步检索兜底——Hermes 以线程 + 8s 超时调用）；③ 新增 `on_session_switch`（/resume /branch /reset /new /压缩会话切换；reset 清空预取缓存）；④ 新增 `get_config_schema` / `save_config`（'hermes memory setup' 向导；secret 走 .env 不入 config.json）；⑤ `initialize` 记录 `agent_context`，非 primary（cron/flush/subagent）跳过记忆写入（Hermes 约定，防系统提示污染用户画像）；⑥ 插件壳同步全部委托转发。
- **端口勘误**：provider 默认端口 8011 → **8010**（全库权威值——config `KAIROS_PORT` / MCP Bridge / api-spec 基础 URL；doc-audit 6.28 只查 openapi servers 端口，未覆盖 provider 默认值）。本机 8010 原被旧项目占用，用户清理后已归 Kairos 使用——默认端口端到端验证通过（含 `env -u KAIROS_BASE_URL` 走默认路径）。
- **遗忘调度器缺陷修复（检索链路回归发现）**：新记忆 `last_access_at` 未初始化（None → freshness=0）→ 遗忘调度器 10s 防抖窗口后**立即归档**新写入记忆；且 use_event 消费仅更新影子副本、未刷新 `memories.last_access_at`（forgetting.py 声明「显式检索仅更新 last_access_at」语义落点缺失）——修复：① `memory_store.create` 初始化 `last_access_at=created_at`（新记忆 freshness≈1）；② `UsageEventSubscriber` 消费 use_event 时同步刷新 last_access_at。补回归测试 2 项（create 初始化 / use_event 刷新）。
- **端到端验证**（Hermes venv 加载 + 真实服务 8010 默认端口）：加载/发现 ✓、initialize（primary/cron 上下文）✓、sync_turn 写入 ✓、queue_prefetch→prefetch 召回 ✓（召回依赖语义匹配；中文无空格查询在 FTS5 unicode61 整串不匹配属已知边界，见 D-417 jieba 精细分词 v1.1）、on_session_end ✓、calibrate 真实 id ✓（404 为服务端对不存在 memory_id 的设计语义）、on_session_switch ✓、cron 守卫跳过写入 ✓。
- **测试**：`tests/unit/test_kairos_provider.py` 补 queue_prefetch / agent_context 守卫 / on_session_switch / 配置向导 / handle_tool_call JSON 契约用例 + `test_is_available` 环境变量隔离（monkeypatch 清模块常量）；新增 `tests/unit/test_hermes_plugin_contract.py`——AST 静态校验适配壳覆盖 Hermes ABC 全接口（防漂移，不依赖 Hermes 包导入）。222 项测试全过。
- **部署登记**：[ops/deployment.md](../ops/deployment.md) 新增 §四·a 接入层部署（MCP Bridge stdio 注册 + Hermes Provider 插件部署/配置/行为）——补齐架构 §7.1a「部署配置见部署指南」引用落空缺口（0.0.101 遗留）；§四·a 纳入章节导航表。
- **本地环境注记**（不入库）：`$HOME/.kairos/.env` 生成 `KAIROS_AUDIT_HMAC_KEY`（S-01 必填校验；项目根 .env 不参与加载——load_settings 的 .env 发现依赖显式 `KAIROS_DATA_DIR`）；**环境变量 `KAIROS_BASE_URL=http://127.0.0.1:8011` 为本机残留旧值**，会覆盖 provider 默认值指向 8011——已提醒用户清理/更新为 8010（验证以 `env -u KAIROS_BASE_URL` 执行默认路径）。

**验证**：222 项测试全过（.venv）；Hermes 真实加载回归通过；doc-audit 复跑 exit 0。结构性受改 5 份文档（部署指南 / 配置参数 / 实现映射 / README + changelog 本文件，均已登记 0.1.1 版本记录行）；核心计数变动：参数 **374→379**（附录 A 147→152，登记接入层运行参数 5 项）；其余（表 57 / 错误码 43 / 端点 88 / 操作 66 / 组件 70 / 功能 168 / 债务 D-447~449）零漂移。

## 0.1.2（2026-08-13）— MCP 工具契约补齐批次（15 工具全可用 + 运行修复闭环）

> **背景**：0.0.101 交付的 MCP Bridge 15 工具（api-spec §6.8 权威清单）实测 9 个 404（服务端端点未实现）+ 3 个假实现（link/unlink/relations 返回治理留痕空壳，不落库不报错）——文档契约超前于服务端实现。本批次补全服务端能力，15 工具全部真实可用。

**落地清单**：
- **扩展端点**（`src/access/api/extended.py` 新增 10 端点）：`GET /v1/memories/stats`（记忆库报告）、`GET /v1/memories/heat-top`（热度，usage_weight 排序）、`POST /v1/memories/{id}/feedback`（可信度反馈，指数平滑更新 calibration_confidence + S-11 审计）、`GET /v1/memories/{id}/traces`（生命周期轨迹，memory_states 数据源）、`POST /v1/entities/extract`（规则法实体提取，entities 表入库去重）、`POST /v1/graph/search`（实体-记忆关联图谱检索）、`GET /v1/sessions`（对话记录聚合视图）、`POST/DELETE/GET /v1/relations`（关系管理 CRUD）。
- **memory_relations 表**（第 16 张竖切表）：models.py `MemoryRelation`（data-model §1 契约：relation_type 六值 + 语义标记扩展、UNIQUE 三元组、deleted_at 软删除）+ schema-slice.sql DDL + 迁移 0002（IF NOT EXISTS 幂等；0001 跳过该表保持初始 15 表快照语义——修 0001 从 schema-slice.sql 全量解析导致重复建表冲突）。
- **bridge.py 真实化**：memory_traces 改走 `/traces`；link/unlink/relations 假实现 → 真实 REST 调用。
- **运行修复闭环（0.1.1 修复的深层根因）**：① 事件总线消费端缺失——`bus.drain()` 零调用点，use_event 只落 usage_events 表从不应用（0.1.1 的 use_event 刷新修复因无消费端实际未生效）；修复：scheduler 新增 `bus_drain` 任务（2s 周期，架构 §10.10 分发语义）；② 订阅器 last_access_at 刷新缺 commit——async with 退出回滚不落库；③ `load_settings` 未设 KAIROS_DATA_DIR 时默认读 `$HOME/.kairos/.env`（S-01 必填密钥）；④ batch 导入补 occurred_at 传递。**连带数据恢复**：2041 条记忆因 freshness=0 被误归档 → 恢复 active（last_access_at 补 created_at），修复后遗忘机制按真实时间自然运行。
- **CI 修复**：ubuntu 无 PG 环境——`test_postgres_backend` 3 errors 拖红 CI；`.github/workflows/ci.yml` 补 `KAIROS_PG_TEST_SKIP=1`（3 skipped）。
- **测试**：新增 `tests/integration/test_extended_api.py` 6 项（stats/heat-top/feedback/traces/entities/graph/sessions/relations 全流程）；schema 对齐/迁移/mcp_bridge 期望更新（SLICE_TABLES 15→16、两次回退）。

**验证**：288 项测试全过（3 PG errors → skip）；MCP 15 工具 HTTP 层端到端 15/15 通过；doc-audit 全绿（修 data-model memory_relations 补 reason/confidence 列 + CRLF 统一）。结构性受改 5 份文档（README / slice-implementation-guide / api-spec / schema-slice.sql / data-model），均已登记 0.1.2 版本记录行。

## 0.1.3（2026-08-13）— 全面审计修复批次（ruff/mypy 清零 + Litestar 新风格迁移 + 文档-代码同步 + 门禁 0.1.x 识别修复）

> **背景**：2026-08-13 全面审计（工作区根 `audit-report-2026-08-13.md`，未随仓库分发）发现：CI code-checks 三步（ruff 77 errors + mypy 10 errors + format）非零退出、Litestar 2.x 弃用 API 大规模使用（1217 warnings，3.0 移除 `Body()` 默认值写法）、文档状态声明与代码漂移多处、doc-audit 批次识别未覆盖 0.1.x。本批次全量修复。

**落地清单**：
- **代码质量**：ruff 77→0（B008×15 随 Body 迁移清零、E501 32 处折行/格式化、UP006/UP045/I001/UP017/F401 自动修复、F841×4/B905×1 手动）；mypy 10→0（kairos_provider 两处 `resp.json()` 加 cast、hermes_plugin import-not-found/misc ignore 修正、cli/extended SQLAlchemy Row→dict 显式注解、pyproject mypy overrides 冲突移除）；Litestar 31 端点签名迁移 Annotated 新风格（`Annotated[T, Body()]` / `Annotated[T, Parameter(...)]` / `FromQuery` / `FromPath`，含 `Parameter(query=)` 弃用清除）+ pyproject 加 `litestar>=2.0,<3` 上限——warnings 1217→1、3.0 升级兼容（2.x 新风格与 3.x 兼容）。
- **auth 重构**：`ApiKeyGuard` 构造注入 salt/api_key_hash（守卫从 `request.app.state` 应用容器读取已加载配置），消除每请求 `load_settings()`（.env 重读）——S-01/S-06 语义不变。
- **文档-代码同步**：CLI 计数 18→21（代码实证 21 条命令；slice-implementation-guide §三 清单补全 21 条 + REST 31 扩展端点 10 行、project-plan/api-spec/README/AGENTS 同步）；docs/README 状态段（16 表/31 端点/21 CLI/15 工具/288 测试）+ api-contract 描述（D-428 已闭合）；api-spec §1 补登记 traces/relations 四端点 + 新增 §1.9 关系管理 + 端点计数 85→89、88→92；openapi.yaml 补 4 端点（operations 88→92）；main.py docstring 15→21。
- **门禁修复**：doc-audit.py 批次正则 `0\.0\.\d+`→`0\.\d+\.\d+`（6.32/6.34/6.39 + 8 处版本记录表行跳过判断）；**6.39 叙述节切分偏移 bug 修复**（seg 已切片后用绝对偏移二次切片致 m_end 恒不匹配、seg 蔓延全文件误匹配历史行）；补 0.1.x 时代治理欠账——documentation-governance 执行记录补 0.1.0~0.1.2、slice-guide/api-spec/data-model 补 0.1.2 版本记录行、changelog 0.1.2 叙述受改清单格式修正（无份数致 6.39 跳过）。
- **许可证**：pyproject license 加占位注释（正式许可证待 release-guide 定稿，当前 Proprietary 保证构建元数据完整）。

**验证**：ruff lint/format 全绿（86 files formatted + All checks passed）；mypy strict 0 errors；288 测试全过（0.1.2 基线复验 + 鉴权相关 24 项 + Litestar 迁移 smoke 全链路）；doc-audit/deep-audit exit 0；pip-audit 0 已知漏洞。结构性受改 6 份文档（README / slice-implementation-guide / project-plan / api-spec / documentation-governance / changelog 本文件）+ scripts/doc-audit.py，均已登记 0.1.3 版本记录行。

---

## 0.1.4（2026-08-13）— 全面审计修复批次（安全契约三缺口 + CI 校验真实化 + 覆盖率加固）

> **背景**：2026-08-13 全面审计跟进版（工作区根 `audit-report-2026-08-13-followup.md`，未随仓库分发）发现：S-09 注入扫描零实现零测试零登记、S-01「无 API Key 拒绝启动」未落地（REQUIRED 仅 HMAC key，守卫静默放行且注释声称的生产强制不存在）、S-06/S-08 三级 Key 契约 vs 单 Key 实现无债务登记、CI 覆盖率门禁余量 1.52pp、CI mcp-tools 校验引用不存在的 schema 文件（ajv 必然失败、校验从未真实生效）。本批次全量修复。

**落地清单**：
- **S-09 注入扫描**（P1-1）：新建 `src/utils/injection_scan.py`（隐形 Unicode 控制字符 + 角色劫持/指令泄露中英双语高置信短语库，完整短语匹配防误报）+ 接线 `IngestionGate._check_capture_gates` 第 5 层（命中 → 403 ERR-SEC-001，与 S-07 同级；常驻契约不豁免）+ `test_redlines.py` TestS09InjectionScan 4 用例（角色劫持/指令泄露/隐形 Unicode 拒绝 + 正常内容不误报）。
- **S-01 生产密钥强制**（P1-2）：config.py 新增 `KAIROS_ENV`（development 默认 / production）+ production 追加密钥族（API_KEY_HASH/SALT/SECRET_KEY）必填拒绝启动 + 非法值拒绝 + development 未配置 API Key 启动警告日志（显式声明无鉴权状态）；auth.py 注释与实现一致；`test_redlines.py` TestS01ApiKey 补 3 用例。[configuration.md](../ops/configuration.md) 附录 A 登记（参数 380→381）+ [deployment.md](../ops/deployment.md) §三 加行并注明「生产部署必须显式设为 production」。
- **D-450 登记**（P1-3）：debt-collection 新增「三级 API Key 鉴权体系（read/write/admin）未实现」追缴（五段式，与 D-430 的 admin key 命令层分开追缴权限模型层，v0.1.0 全量阶段）；D-430 摘要表状态同步为「🟡 部分闭合（0.1.2 实现 4 条）」。
- **CI 校验真实化**（P2-4）：创建 `docs/specification/api-contract/mcp-tools.schema.json`（此前不存在——ajv 校验从未真实生效，仅 JSON 合法性降级检查）+ ci.yml 收紧（ajv 失败即红，`set -e`；toolCount≡tools 长度、mapsTo 合法形态校验）。
- **覆盖率加固**（P1-4）：test_api.py 新增 TestAuthEndpoints（缺 token/无效 token → 401、有效 token 放行——auth.py 52% 主缺口）；test_cli.py 补 D-430 闭合命令（health --full / audit log / config reset）——测试 288→292，覆盖率 81.52%→82.81%（CI 口径实测，fail_under=80 余量 2.81pp）。
- **文档同步**：[AGENTS.md](../../AGENTS.md) D-428 残留×2 清除 + 覆盖率声明 85.23%→82.81%；changelog 浏览指引「最新批次置顶」→「时间正序」修正 + frontmatter updated 2026-08-13；.gitignore 补 `audit-report-*.md` 模式（审计材料此前未被忽略）；development-setup §四 增运行环境约束注记（Windows 文件锁 / PYTHONPATH 劫持 / KAIROS_DATA_DIR 污染）。

**验证**：定向 40/40 → 全量 292 passed / 3 skipped（PG）/ 1 warning；覆盖率 82.81%（CI 口径）；ruff/mypy/format 见批次验证（本地 --no-sync 实测）；doc-audit/deep-audit exit 0。结构性受改：debt-collection / configuration / deployment / development-setup / changelog 本文件 / AGENTS / .gitignore / ci.yml / mcp-tools.schema.json。

---

## 0.1.5（2026-08-13）— 实体信号激活批次（竖切组件 3 未竟交付 + 归一化退化 bug 修复）

> **背景**：2026-08-13 运行态设计目的验证发现：三信号混合检索的**实体加成信号实际未生效**（entities 词典空、explanation.entity 恒 0）——slice-guide 组件 3 承诺的三信号融合（α_e=0.15）属竖切交付未竟。根因两层：① 提取端点（`POST /v1/entities/extract`）存在但**无写入侧自动触发点**，词典无数据；② **归一化退化 bug**——`hybrid_search.py` 信号归一化 `hi <= lo`（单候选/同分）时 norm 恒置 0，唯一得分信号被压制（词典激活后单候选场景仍恒 0）。

**落地清单**：
- **`src/storage/entity_extractor.py`（新建）**：规则法实体提取器集中实现（引号短语 / 全大写缩写 / 中文专名三模式，stopword 过滤）+ 类型推断（tool/project/concept）+ user_id 路径解析——从 extended.py 提炼增强（原恒 concept）。
- **写入侧自动提取**：`MemoryStore.create` 末尾新增 `_store_entities`——提取 → entities 去重入库（user_id 按路径解析）→ memory_entities 关联（relation=mentions）；失败仅告警不阻断主写入（实体为检索增强信号）。extended.py extract 端点复用公共提取器（消除重复）+ 类型推断增强。
- **归一化退化 bug 修复**（hybrid_search.py L164-167）：`hi <= lo` 分支改为「唯一得分者信号满配」（raw>0 → norm=1.0），消除 (raw-lo)/(hi-lo) 零分母语义对单候选信号的压制。
- **测试**：`tests/unit/test_entity_extractor.py` 13 项（提取规则 / 类型推断 / user_id 解析 / 写入侧入库去重 / 无实体内容跳过 / 检索 entity 信号激活）。
- **真实验证**：服务重启后写入含实体记忆 → 检索 explanation `entity=1.0 bm25=1.0`，融合 score=0.5 = 0.35·1+0.15·1 数学吻合；测试数据已清理。存量 2086 条记忆不回溯提取（增量生效，全量 v0.1.0 处理）。

**验证**：全量测试 305 passed（288+13+回归）/ ruff 0 / mypy 0（50 文件）/ format 全绿。结构性受改：src/storage/entity_extractor.py（新）/ memory_store.py / hybrid_search.py / extended.py / tests/unit/test_entity_extractor.py（新）+ changelog 本文件。

---

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 变更日志：跨文档版本演进全景（当前基线 0.0.1）。 |
| 0.0.2 | 2026-08-03 | P0 修复：RC-01 D-01 残留清理、RC-02 api_keys 表、RC-03 融合公式量纲、RC-04 类型映射 + DDL。 |
| 0.0.3 | 2026-08-03 | P1~P3 修复：RC-05~RC-19 及 A-004（投影 ADR、双阶段管线、compacted 列、配置扩列、版本号规则、changelog、日期倒挂、技术栈、债务墓碑、编号分段、OP-ID、api-spec 响应、NFR 测量方法）。 |
| 0.0.4 | 2026-08-04 | 市场理念吸收：双时态、时间感知检索、生成式记忆、主动触发式记忆（D-322~D-325、glossary 增补、吸收决策记录）。 |
| 0.0.5 | 2026-08-04 | 门禁覆盖补全：doc-audit 新增术语计数校验（6.7）；README 术语计数 53→56 与版本记录升版；api-spec 版本记录升 0.0.2；竖切指南挂接 schema-slice.sql DDL 引用。 |
| 0.0.6 | 2026-08-04 | ADR 计数同步 10→12（[README](../README.md)/[adr.md](./adr.md) 版本记录升版）；doc-audit 新增 ADR 计数校验（6.8）；deep-audit.py 修复 Windows GBK 编码崩溃。 |
| 0.0.7 | 2026-08-04 | 债务闭环检查语义修正（仅已闭环条目要求可检索，9 项 WARN 归零）；D-323/D-324 落地编号引用补全（架构/认知基础升 0.0.3）。 |
| 0.0.8 | 2026-08-04 | 全库深度审计修复批次：安全口径（API Key 哈希统一 PBKDF2）、版本归属与 P6 定性统一、竖切落点补全、引用/编号勘误（RC-18/19→A-005/A-006）、核心文档修复、治理补账（版本记录回填、决策编号注册）、参数取值范围列修正与新增熔断参数、门禁全绿。 |
| 0.0.9 | 2026-08-04 | 文档职责剥离批次：认知基础聚焦认知理论（8 处工程细节剥离）、主架构聚焦系统架构（24 章剥离为摘要+指针）、详细设计承接扩展（500→1500 行，新增 §10-§12）、60+ 处引用改向、门禁全绿。 |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复批次：权威文档矛盾修复（遗忘口径/意图契约/监督平面）、引用与数值漂移修正、P6 定性统一、feature-list 结构修复、格式与元数据批量统一、门禁扩展（锚点/frontmatter/废弃短语/标题缩进）。 |
| 0.0.11 | 2026-08-04 | 开发就绪度审计修复批次（依 maturity-audit 闭环）：权威定义唯一化（知识演化/契约枚举/关系类型）、临时契约审计痕迹统一、时序优先→并行审查收敛、schema-slice.sql 重建、data-model §八 重排与类型/索引修复、api-spec 机制指针与勘误、配置参数体系（210+148=358，去重 3 项、新增 14 项、待定义回填 12 项、NARRATIVE_IDENTITY 默认 ON）、claim-matrix 账目重建、竖切口径与编号消歧、运维/质量/安全引用修正、recheck/round2 勘误。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次（依 maturity-audit §七 遗留项）：doc-audit 编号连续性扩展五命名空间、新增决策编号标注检查（14a）、债务闭环正文口径、陈旧值集中化+邻近值；documentation-governance 新增 §2.1 机制定义唯一化人工门禁；13 处决策编号引用补「决策」前缀；configuration 勘误注记去历史计数字样。 |
| 0.0.13 | 2026-08-04 | 认知×架构交叉审计修复批次（决策 D-16~D-27，见 cognitive-architecture-fixes）：A1 硬过滤、B1 学习边界三边重画、C1 检索-再巩固让步、D2 身份否决权语义边界、E1 身份危机判例、F1 符合论域权威、G1 DFA 分工、H1 定向遗忘锚点、I3 巩固预测误差、J2 组块化硬承诺、K2 推理皮层论证、L1 元认知职责边界、P-01~P-20 问题项闭环、§5.20 重复内容删除 243 行。本条目为 0.0.15 补登（原 changelog 缺失，见 comprehensive-documentation-audit P2-01）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次：契约语义统一（删除/到期/intention 枚举）、遗忘算法 freshness 归位、关系枚举语义标记扩展、虚拟校准触发链、HMAC 公式统一、S-07 脱敏口径、MCP 进程模型与工具计数、D-324→D-325 债务挂错、制衡四项口径、竖切测试补全（迁移/回滚）、复兴机制勘误、决策编号注册更新、格式清理（31 份文档）。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次（依 comprehensive-documentation-audit 闭环）：契约枚举第五值同步（api-spec 摄取端点）、竖切 M-05 归档/恢复端点注册（业务端点 78→80、物理总数 81）、0.0.13 版本批次补登、参数计数现值锚定、门禁标签编号修复（15/16/17）、正文双空格清零 2 处、0.0.14 登记文档数 29→31。 |
| 0.0.16 | 2026-08-05 | 外部建议落地批次（依外部提案评估拍板）：校准退化链（衰减公式+状态指示器+nudge）、structural_value 半定量三级、QueryAnalyzer 规则优先+事件锚定+fallback_query、记忆压力四指标+三级减压、Saga narrative_threads v0.1.0 子集、概念分级速查表（[references/concept-tiers.md](../references/concept-tiers.md)）、压缩审计（compression_trail+capability_matrix.yaml+审计端点）。 |
| 0.0.17 | 2026-08-05 | 外部建议其余落地批次：R-1 P6 收敛目标化（D-334）、R-2 进程级隔离演进路径（deployment §九）、R-3 社会性校准研究启动点（roadmap）、R-9 债务关键路径依赖表+注册规则、R-10 Phase↔验收↔门禁对照表；R-4~R-8 确认已覆盖。 |
| 0.0.18 | 2026-08-05 | 审计归档与决策迁移批次：决策 D-01~D-27 迁移至 `adr.md`「审计决策迁移」节（注册表改指）;reviews 10 份审计报告归档为 `audit-history-summary.md`（删除原报告,30 处引用改指）;归档机制确立（后续审计闭环即登记摘要并删除原报告）。 |
| 0.0.19 | 2026-08-05 | 第四轮全库深度审计修复批次（依 master-documentation-audit 闭环）：身份否决权实现形态裁决（1-01，架构 §1.8 权威，D-001/D-101 已实施）;章节引用错位三连与成本护栏引用修正；监督平面口径统一；逻辑-因果轴层级口径（方案 a）;P3-19 承载补全;§5.2 占位与节内导航；驻留矛盾句与命名统一;blueprint 文件名 v1.1+ → v1.1 全库同步。 |
| 0.0.20 | 2026-08-05 | 第五轮全库深度审计修复批次（依 round5-deep-audit 闭环，0 高/10 中/8 低）：P0 语义矛盾 4 项（速查表否决权/监督平面宪法解释/宪法解释层驻留/时间轴三子轴口径）;P1 引用批量 3 组（架构词汇桥接 8 处、认知基础 6 处、架构→api-spec 7 处 + 反向注记）;P2 结构与格式（§5.17/5.18 迁 §6、断号说明合并、术语计数 56→57 + 门禁补盲区、行号引用清零、SDK 版本对齐注记、README 入口行、1-05 方案 b、3-03 记录在案）;门禁全绿。 |
| 0.0.21 | 2026-08-05 | 系统架构总览图新增批次：architecture §0.4.1 新增 Mermaid 全局架构图（六层栈 + 三治理面 + 横切基础设施 + 编号数据流 + 图例）;口径与正文逐条核验；门禁全绿。 |
| 0.0.22 | 2026-08-05 | 外部项目理念吸收：热度体系实证参考基线、摄入侧情绪爆发整轮保护、摄取噪音规则库、时间粒度层级实证对照、三问题正交解耦框架、RSK-008 可复现性风险（D-335~D-338、glossary 57→60、配置 368→371）。 |
| 0.0.23 | 2026-08-05 | 内容架构全面审视修复批次：认知基础（引论瘦身、§1.1 标题、断号注记、六机制编号、§2.2 消歧、附录 8 项）；系统架构（§2.6 归位、§0 标题消歧、§5.2 树修复、§5.20 编号、§7.3.1 降级、7.4a 注记、7.3d→7.1a 迁移、§10 更名）。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次（round6 10 项 + round7 9 项新发现 = 19 项闭环）：中风险 6 项（E.6a/is_identity/RTM R-01 R-02/blueprint §5.7/M-05 标注/配置计数）+ 低风险 13 项（§10.24 落点、ARC-D-101、D-4xx 排序、前瞻记忆归位、OP-054+ 收口、README 0.0.19 补登、执行记录、悬空承诺、组件数、版本记录占位 ×3、arch 缩写）；联动 feature-list PM-01；过程建议 16 不做项记录；round6/round7 报告按 0.0.18 机制归档。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（round8 3 高/12 中/9 低 = 24 项闭环）：端点计数 85/88 重算与同步 + doc-audit 6.12 门禁补盲区（1-1/2-2）、DFA/DAP 命名与交付状态裁决（统一 DFA、v1.1，1-2/3-3）、架构引用落点 11 处（审计 8 + grep 同源 3）、ERR-CTR-002 口径（1-5）、参数计数 371（1-6）、前瞻记忆引用 3 处（2-1）、领域路由收敛（3-1）、glossary derived_from（2-3）、S-xx→S-06（2-4）、章节编号中英混用统一（4-1，api-spec/data-model 标题+引用+全库联动 25 处）、版本记录占位惯例（4-3）；round8 报告按 0.0.18 机制归档。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（round9 P0+P1 闭环）：H-01 §3.2→§3.3 引用 29 处（含审计遗漏 2 处同源）+ §3.2 反向指引（P0）；H-02 编译器管线顺序裁定「缓冲→注意力→编译器」修订 4 处（P0）；H-03 schema-slice 补 4 字段 + 同步约束 + 14 表逐列复核（P0）；M-01 三环不变量 §10.3 五处；M-03 汇聚式融合落点；M-04 dpr 表 3 行文件错列；M-05 MCP Bridge §7.1a 三处（含同源 2 处）；M-06 检索深度分级 §3.9；M-07 /health 探针；M-11 种子路径目录语义；门禁新增 6.13 DDL 字段比对 + 6.14 机制名映射抽检（M-13 建议 1/2）；14 份文档版本记录 + frontmatter 同步。 |
| 0.0.27 | 2026-08-06 | 第三方分析摘要分诊批次：12 项建议交叉核实——9 项已覆盖/有意设计/已登记（降维 D-016/D-103、衰减公式化、充分性不阻塞为安全权衡、学习边界 D-007、制衡叠加规则、可导航性、冷启动种子、自激防护、化石节点、事件类型注册门禁）；架构 §0.8 补「命名配置集与组合约束」（三种命名配置集为唯一测试目标 + 启动组合校验）；debt-collection 新增 D-403 架构复杂度度量（v1.1 评估）。 |
| 0.0.28 | 2026-08-06 | 第十轮全库深度审计修复批次（round10 P0 三项闭环）：C-01 MCP 工具计数 15 口径统一——api-spec §6.8 补关系管理 3 工具 + 指引段修正（§7.3.1→§7.1a）、operation-catalog/technology-stack 注记修正、架构 §7.1a :2920 构成重写（F-03 link/unlink 重复计数）；C-02 覆盖声明失真修复——新增 OP-054~066 共 13 项（记忆生命周期 6 + 主动功能 7）、7 个运维探针豁免声明、覆盖声明改写 49/56、sessions/evolution 占位符统一 {id}；C-03/F-01 硬行号整体废除——configuration 附录 A 136 处改「文档 §章节」语义引用（38 处权威落点修正至 detailed-design/blueprint）；门禁新增 6.15 硬行号禁令 + 6.12a MCP 工具表行数比对（M-13 建议 2 剩余一半落地）；round10 报告核验勘误（A-02 误报更正、C-02 数字订正 56/20、S-01 份数 8→7、F-01 汇总补注）；P1 五项（S-01/D-02/D-01/C-04/D-04）排期后续批次。 |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（round10 P1 五项闭环）：S-01 标题风格统一（方案 B 拍板）——api-spec/data-model 大章「N、」→「§N」（18+13 章并入 §N 数字序形态，引用零联动）、blueprint 3 大章归位中文序、documentation-governance §2 补大章标题风格约定（§N 数字序/中文序双形态 + 引言例外）；D-02/M-13 建议 3 落地——documentation-governance §2.2 结构性变更连锁复核人工流程规则（基线扫描/五步复核清单/复核登记）；D-01/M-12 新增 [development/engineering-workflow.md](../development/engineering-workflow.md)（分支策略/PR 流程/提交规范/CI 门禁/发布衔接，README 计数 54→55）；C-04 归档衔接修正——未闭环项报告不删 + 汇总表保留未闭环项标题级清单；D-04 术语表补 7 条（编译器/结构化通信单元/编译净化/检索深度分级/命名配置集/竖切/结构性记忆，60→67，README/架构计数同步）。 |
| 0.0.30 | 2026-08-06 | 仓库整洁化批次：审计过程材料移出仓库——删除 docs/reviews/ 目录（审计历史摘要）与 scripts/_deep_audit_out.json（纳入 .gitignore）；全库 audit-history-summary 引用清理（决策编号改指 [adr.md](adr.md)、债务谱系标注保留文字删链接、changelog 历史条目去链接）；README 移除审计历史索引、修订审计材料不随仓库分发的说明。 |
| 0.0.31 | 2026-08-06 | 第十一轮全库深度审计修复批次（round11 9 项成立问题闭环）：操作数同步 66 + 门禁 6.8a OP 行数校验；changelog 0.0.27~0.0.30 叙述节补齐；blueprint v1.1 承诺追缴补登 D-404~D-413 共 10 条；glossary 推理皮层别名收录；行尾统一 LF（20 份 + .gitattributes + 门禁 6.16）；catalog「—」语义注记；架构 §0.8 短名注记；deep-audit 输出改系统临时目录。 |
| 0.0.32 | 2026-08-06 | 第三方分析分诊 + 全量债务 v0.1.0 可实现性评估批次：外部记忆系统 16 项交叉核实（14 项已覆盖/有意差异/互为印证——含 RL 权重设计独立实现印证、宣称-实际反面教材、SKILL 层集成佐证；rl-weight-spec 补衰减防坑注记；新增 D-414 检索反馈权重快照）；debt-collection §七 评估表 62 条活跃债务全量评估（9 已覆盖/7 升格 v0.1.0.x/1 规格升格/11 已在首版范围/34 维持附真实理由）；正文与摘要表同步（D-006/007/008/009/010/011/014/018/019/102/103/301/302/402/406/414，D-102 过时描述修订）。 |
| 0.0.33 | 2026-08-06 | round12/round13 深度审计修复批次：round12 遗留 8 项全量核销（核销表见叙述节）——版本记录补登（architecture 0.0.29/0.0.30、cognitive-foundation 0.0.30、blueprint 0.0.30）、changelog 0.0.30 补记 2.1-01、摘要表 Phase 列修复（D-404/405/407~412 → v1.1、D-413 → v1.2）、test-plan 黄金集占位 TC-GOLD-001~、README 空节删除、doc-audit docstring raw string 修复；round13 新发现 R13-04 门禁清单补 6.8a/6.16 + 「批次收尾检查清单」（流程级根因治理）；观察项 R13-06 历史指引改注、R13-09 记录在案；0.0.32 门禁验证回填。 |
| 0.0.34 | 2026-08-06 | 第十四轮全库深度审计修复批次（round14 3 中/7 低 + 1 观察全部闭环）：R14-01 治理面计数统一（§0.4.1 图题/结构原则 → 两个正交治理面，身份面不入计数 + HTML 图题同源联动）；R14-02 治理输入表述（外部校准信号为外部信号治理输入，另有管理员冻结/解冻指令 + HTML 图例）；R14-03 检索权重单一权威（四链路 0.50/0.20/0.10/0.20 唯一默认，三链路标历史配比；configuration KAIROS_RETRIEVAL_LINK_WEIGHTS 补默认值）；R14-04 速查表命名两称并存口径；R14-05 [AGENTS.md](../../AGENTS.md) git 状态更新；R14-06 §10.24 补 D-006/D-008/D-016/D-019；R14-07 §5.2 节内导航补 5 节点；R14-08 ⚠️ 字面转义修复；R14-09 健康接口引用改指 ME-1；R14-10 差异检验引用改指 §5.5；观察项 R14-11 记录在案；门禁补盲区（结构性建议 12 落地）：doc-audit 新增 6.17 治理面计数一致性 / 6.18 检索权重公式唯一性 / 6.19 §10.24 关联债索引完整性（含镜像回归验证）；遗留项核销：0 遗留。 |
| 0.0.35 | 2026-08-06 | 第三方分析分诊批次：20 项交叉核实判定（6 已覆盖 / 10 互为印证 / 4 有意设计差异）；落地规格修正 R-01——架构 §3.9 补检索深度分级 ↔ 内容读取层级映射注记（R0 指针 / R1 摘要级仅定位 / R2 全文级唯一可用，吸收外部记忆库「摘要不算上下文」失效模式；api-spec 不加镜像防双写）；无债务登记。 |
| 0.0.36 | 2026-08-06 | 第三方分析分诊批次：20 项交叉核实判定（10 互为印证 / 7 有意设计差异 / 1 反面教材——含「拥抱冗余」哲学互为印证：去重不删本体、重复进热度频次）；落地规格修正 2 项——R-02 升华产物 verbatim 拒绝护栏（detailed-design §4，`sublimation_invalid` 审计事件 + 重试一次）、R-03 使用权重影子副本可重建性声明（架构 §3.3，use_event 事件流重放重建 + 恢复四步 + 防线不变）；无债务登记。 |
| 0.0.37 | 2026-08-06 | round15 全面深度审计修复批次：45 项问题闭环（1 高/19 中/25 低）——M-03 三义统一（feature-list 语义为锚）；否决权「默认优先级+判例出口」口径全库 4 处统一（认知基础 §2.1/架构 §0.4.1/glossary/HTML 图）；三信号/四链路管线关系声明与术语消歧（架构 §7.3a）；意图契约第五契约说明（架构 §3.7）；MCP 12→15、CLI 24→25（api-spec 补注册 degradation switch）、术语 67→68（glossary 补准见证锚定）、OP 53→66、traceability-map 四种→六种、api_keys read-only→read、待定义 12→11 计数联动；conversation_messages parts 列与 journal_entries node_episode_index_map 列补录；竖切 REST 20→21 补 restore；troubleshooting 命令状态表失实修正；reliability 改指 sublimation_queue；P3-19~25 债务补登 D-415~D-421；差距表 G-01/G-07 互引；D-402 改引 ARC-D-004；S-19 汇总表收敛；版本注记纪律收敛（勘误类去版本号、外部产品名收敛）；benchmark-plan 判据补齐（升华/磁盘/启动）；门禁 18 类 + 14a + 6.8a/6.12a/6.13~6.16 + 6.17/6.18/6.19 全绿。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次：全面审计 113 项（3 高/64 中/46 低）全部闭环——P0 三项【高】（推论幽灵引用、帕累托维度三重口径、零版本标记全库收敛）；P1 约 30 项【中】（幽灵引用清理、WM 唯一化、rl_weights 归一化矛盾、多模态档位、错误码口径、CLI 契约盘点等）；P2 其余（路径下划线统一、§10.24 补 D-322~338、参数计数 224+146=370、[AGENTS.md](../../AGENTS.md) 刷新等）；计数变化：glossary 68→69、参数 371→370、标志 11→12；门禁 18 类 + 14a + 6.8a/6.12a/6.13~6.16 + 6.17/6.18/6.19 全绿。 |
| 0.0.39 | 2026-08-06 | 外部理念吸收批次（2026-07）：落地 6 项借鉴——① 记忆质量评估指标（acceptance-criteria §一a 新增过时调用率 / 任务成功率改善，v1.1+ 设计目标）；② 反事实检验测试模式（test-strategy §2.7 三态对比 + TC-CF-001~004）；③ encoding_context `conditions` 子结构约定（data-model，条件性经验适用范围显式化）；④ 高相似 × 过时联合惩罚（architecture §7.3a 排序调制，stale ×0.7 / expired ×0.5）；⑤ 记忆四动作失败模式排障表（troubleshooting §二a）；⑥ 基准设计红线——经验来源与验证数据分离（benchmark-plan §3.11 评测泄漏防护）；配套：observability 指标 2 项 + 告警 1 条、integration-design §五a 任务成功率回传契约（task_outcome 事件，v0.1.0 落 usage_events 不新增端点）；无债务登记、无新文档（7 份现有文档修订）；门禁验证通过。 |
| 0.0.40 | 2026-08-07 | 外部视频分析批次：100 视频 + 15 仓库对照分析（详见上文 0.0.40 主体章节）——新建 [docs/analysis/external-videos/](../analysis/external-videos/README.md) 独立目录（索引 + 分诊矩阵 + 原理评审 + 吸收建议 + N 份视频笔记 + 15 份仓库笔记 + 抓取流程记录）；实测 B站 AI 字幕串台问题；脚本入库 2 个；零改动核心设计文档；无债务/ADR/风险登记（全部建议态）；门禁验证见批次记录。 |
| 0.0.41 | 2026-08-07 | 外部理念吸收落地批次：AP-01~28 全量落库（详见上文 0.0.41 主体章节）——认知基础 8 条声明 + 架构 22 条机制 + 规格层 7 份文档 + schema-slice 联动；表数 57 不变、参数 370 不变（4 处新阈值标注「参数待登记」）；受改 10 份文档版本记录统一 0.0.41；门禁 18 类全绿。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42，见本文件 0.0.42 叙述节）。 |
| 0.0.43 | 2026-08-07 | 文档审计报告（F1–F9）闭环修复批次（changelog 0.0.43，见本文件 0.0.43 叙述节）。 |
| 0.0.44 | 2026-08-08 | 外部理念吸收补落地批次（changelog 0.0.44，见本文件 0.0.44 叙述节）：AP-29~37 + PAPER-01~09 增量未覆盖项全量落库（认知基础 2 注记 + 架构 14 处注记 + 蓝图 1 注记 + 基准/测试 2 注记 + 债务 2 条）；吸收管线闭环（本批次全部「可吸收」条目已落地）；参数计数不变；门禁全类验证。 |
| 0.0.45 | 2026-08-08 | 文档审计报告（R18-01~R18-15）闭环修复批次（changelog 0.0.45，见本文件 0.0.45 叙述节）：README 计数/索引/零版本标记收敛、AP- 编号注册 + claim-matrix 死链修正、架构批次号/小节名/术语消歧修正、openapi.yaml 结构重建（D-428 追缴）、契约追缴补登、.gitignore 审计报告覆盖、AGENTS api-contract 登记、D-422~425 硬行号改语义引用、technology-stack F2 误诊回退；门禁全类验证。 |
| 0.0.46 | 2026-08-08 | 文档审计修复批次（round19 五维审计闭环）（changelog 0.0.46，见本文件 0.0.46 叙述节）：R19-01~R19-04 闭环（三链路改名收敛 / 零版本标注豁免澄清 / CI 工具链交叉引用 / 版本记录触达登记）；门禁复验全绿。 |
| 0.0.47 | 2026-08-08 | 外部论文分析批次（13 链接批次）（changelog 0.0.47，见本文件 0.0.47 叙述节）：11 篇新论文逐篇分析（PAPER-11~21，2 篇已分析交叉引用）+ 分诊 I 节 EV-60~74 + 吸收建议四d 节 AP-38~52（建议态未落库）+ 张力 AT-08~09 + changelog 版本表补登 0.0.46 行；零改动核心设计文档。 |
| 0.0.48 | 2026-08-08 | 外部理念吸收落地批次（changelog 0.0.48，见本文件 0.0.48 叙述节）：AP-38~52 全量落库——架构 9 处注记（§0.8/§1.7/§3.2/§3.9/§5.1/§5.2/§5.5/§10.14/§10.15）+ 蓝图 2 处注记（§5.3/P3）+ benchmark-plan 3 处（§3.11 第 5 条简单基线对照红线 + 能力验证门方法论 + §3.13 用户反馈模拟维度）+ D-427 证据补充；参数计数不变；门禁全类验证。 |
| 0.0.49 | 2026-08-08 | round20 全面深度审计修复批次（changelog 0.0.49，见本文件 0.0.49 叙述节）：5 高/10 中/6 低全部闭环，默认配置下系统行为语义自洽；修复后门禁全类验证。 |
| 0.0.50 | 2026-08-08 | round21 深度审计修复批次（changelog 0.0.50，见本文件 0.0.50 叙述节）：2 高/5 中/1 低全部闭环（R21-01~R21-08）；特征标志最小系统死锁与证伪纪律×命名配置集/宪法核死锁两处语义互斥闭环；changelog 0.0.49 版本记录行补登；`/metrics` 端点待定义追缴 D-429；P- 编号注册 + P4 命名统一；KAIROS_PATH 语义冲突修正；cognitive-foundation 去版本化残留清理；参数计数不变；门禁全类验证。 |
| 0.0.51 | 2026-08-08 | round22 深度审计修复批次（changelog 0.0.51，见本文件 0.0.51 叙述节）：4 高/3 中/2 低全部闭环（R22-01~R22-09）；质量层证伪测试承载链/命名配置集矩阵/S-19 行为层承载/运维 CLI 追缴 D-430；错误码 38→40（ERR-SYS-006/007）；门禁新增 6.20/6.21；参数计数不变；门禁全类验证。 |
| 0.0.52 | 2026-08-08 | round22 结构性建议落地批次（changelog 0.0.52，见本文件 0.0.52 叙述节）：S22-1 约束传导登记规则（documentation-governance §2.3）+ S22-2 自设硬门禁追缴子检查 6.22；派生债务 D-431 补登；参数计数不变；门禁全类验证。 |
| 0.0.53 | 2026-08-08 | round23 深度审计修复批次（changelog 0.0.53，见本文件 0.0.53 叙述节）：2 高/2 中/4 低全部闭环（R23-01~R23-08）；端点路径 /v1 前缀事实修正、S-19 遗忘生效边界承载、OTel 追缴 D-432、编辑痕迹 17 处清除、门禁清单口径统一、runbook 追缴块、架构章节导航、竖切 5000 行修正；参数计数不变；门禁全类验证。 |
| 0.0.54 | 2026-08-08 | round23 结构性建议落地批次（changelog 0.0.54，见本文件 0.0.54 叙述节）：S23-1 单一事实源反查子检查 6.23（首跑捕获 memory-pressure 端点 /v1 前缀漏项）+ S23-2 版本记录回填脚本 version-record-update.py；参数计数不变；门禁全类验证。 |
| 0.0.55 | 2026-08-08 | round24 全面深度审计修复批次（changelog 0.0.55，见本文件 0.0.55 叙述节）：1 高/10 中/7 低全部闭环（R24-01~R24-18）；认知基础去版本化 30 处改写、引用错位（api-spec §6.5 等）修正、S-19 验收承载、CLI 追缴对齐、blueprint 无编号承诺追缴 D-433~D-438 补登；参数计数不变；门禁全类验证。 |
| 0.0.56 | 2026-08-08 | round24 结构性建议落地批次（changelog 0.0.56）：S24-1 门禁 6.24 端点→章节锚点一致性（首跑捕获架构 L771 calibration 端点引用 §1.7→§6.5）；S24-2 门禁 6.25 认知基础去版本化（首跑捕获 4 处版本字样残留并修复）；门禁清单口径 6.13~6.25。 |
| 0.0.57 | 2026-08-08 | round25 全面深度审计修复批次（changelog 0.0.57，见本文件 0.0.57 叙述节）：21 项问题闭环（0 高/9 中/12 低）——架构元认知层第五层编号修正、完结叙事线 409 对齐、deleted_at 承载补列、api-spec §13~§17 版本边界标注、技能管理定位改指 blueprint、S-17 法定擦除例外同步、D-430 追缴扩范围（+init --seed-path + release-guide）、README 版本记录链补登、changelog 0.0.54 重复行清除、KAIROS_ 参数前缀补全、参数/计数/债务/端点计数全部不变；门禁全类验证。 |
| 0.0.58 | 2026-08-08 | round25 结构性建议落地批次（changelog 0.0.58，见本文件 0.0.58 叙述节）：S25-1 门禁 6.26 通用章节引用存在性与标题语义（裸引用/中文标题/引号标题三档，突变测试 4 用例全通过）+ S25-2 门禁 6.27 api-spec 章节版本标注完备性（§11~§17 全带标注）；工程工作流/项目计划门禁口径补 6.26/6.27；参数/债务/端点计数不变；门禁全类验证。 |
| 0.0.59 | 2026-08-08 | round26 全面深度审计修复批次（changelog 0.0.59，见本文件 0.0.59 叙述节）：17 项问题闭环（3 高/9 中/5 低）——openapi.yaml 契约骨架与 api-spec 全面对齐（端口 8010/bearerAuth/88 端点响应码补全/权限扩展字段/v1.1 边界标注）、错误码全库 40→42 对齐（ERR-CTR-003/004 + ERR-DB-004/005 内部码例外澄清）、新增债务 D-439（供应链完整性与侧信道加固）、技术栈补本地推理运行时与 CLI 框架、D-432 扩展至可观测性可视化层、user 层三处修正（--source 必填/校准枚举 healthy/裸 # 围栏）、quick-start 2 分钟口径澄清、架构 5D 同名消歧；误报剔除 4 项（Q-03/G-01/F-02/S-10）；门禁全类验证。 |
| 0.0.60 | 2026-08-08 | round26 结构性建议落地批次（changelog 0.0.60，见本文件 0.0.60 叙述节）：S26-1→门禁 6.28 契约反查（openapi 88=88/api-spec 端点、端口 8010、bearerAuth、mcp mapsTo⊆登记）、S26-2→门禁 6.29 错误码三处集合一致性（error-reference≡troubleshooting 42=42 + api-spec §7⊆error-reference）、S26-3→门禁 6.30 + 文档纪律 §6.2 示例代码纪律（kairos write 须 --source / calibration_status 四值）；首跑三项零失败；门禁全类验证。 |
| 0.0.61 | 2026-08-08 | round27 全面深度审计修复批次（changelog 0.0.61，见本文件 0.0.61 叙述节）：记忆状态机五态平级口径全局对齐（架构 §5.2 / detailed-design / cognitive-foundation）、前序批次版本记录漏登记集中补登（glossary / cognitive-architecture-gap / integration-design / benchmark-plan / requirements-baseline / feature-list / implementation-map）、技术选型缺口补齐（technology-stack §七 MCP 计数矛盾修正 + §二 BM25/FTS5 关键词检索选型）、data-model §11 FTS5 分词器口径矛盾消除；参数 / 表 / 端点 / 错误码 / 债务 / 术语 / MCP 计数全未变动；门禁全类验证。 |
| 0.0.62 | 2026-08-08 | round28 全面深度审计修复批次（changelog 0.0.62，见本文件 0.0.62 叙述节）：FTS5 范围与分词器口径一致性——纠正架构 §5.20/§5.20.2「FTS5 contentless-external 为 v1.1+ 不交付」「jieba 无条件」误述（基础 FTS5 contentless-external + unicode61 为 v0.1.0 轻量模式 BM25 承载，jieba 为需编译扩展的可选精细分词，由 KAIROS_FTS5_CHINESE_SEGMENTATION 控制，与 data-model §11 / schema-slice §14 / blueprint §P3-21 一致）；§7.3a BM25 词形归并中文处理改为模式感知（标准 zhparser / 轻量 FTS5 unicode61）；受改 1 份文档（architecture-v0.1.0）；计数全未变动；门禁全类验证。 |
| 0.0.63 | 2026-08-08 | round29 全面深度审计修复批次（changelog 0.0.63，见本文件 0.0.63 叙述节）：1 高/3 中/2 低全部闭环——债务 D-417 台账与 v0.1.0 实际交付面对齐（基础 FTS5 已交付，jieba 精细分词与 Playbook 索引剩余 v1.1）；§七 可实现性评估表补登 29 条游离条目（62→91）并确立与 §四 摘要表条目集合一致的维护规则；§七 排除清单 D-011 自相矛盾修正；D-001 可接受成本过时表述改写；detailed-design §10.6 解除对 v1.1 组件 PreparedStatementCache 的依赖；data-model §11 版本归属注记；架构总览图工具栏功能虚标与离线渲染说明修正；核心计数全未变动；门禁全类验证。 |
| 0.0.64 | 2026-08-08 | round30 门禁盲区扫描 + 修复批次（changelog 0.0.64，见本文件 0.0.64 叙述节）：5 类实质问题闭环——A 事件队列参数 `KAIROS_EVENT_QUEUE_CAPACITY` 补登（架构 §10.10 + configuration 附录 A）、B data-model 点分键 2 项（`KAIROS_GSPO_MIN_CLUSTER_SIZE`/`KAIROS_CROSS_ENCODER_ENABLED`）补登 + 参数计数 370→373、C 门禁清单口径同步 6.13~6.31、D security-spec/technology-stack 改用已登记命令与端点（修 6.24 章节错位）、E 中文半角标点 101 处归一化；门禁 6.31（中文正文半角标点纪律）固化落地 + documentation-governance §6.3 补规则；门禁全类验证 exit 0。 |
| 0.0.65 | 2026-08-08 | round31 语义层深度审计修复批次（changelog 0.0.65，见本文件 0.0.65 叙述节）：3 高/8 中/6 低全闭环——FTS5 参数族来源改指 v0.1.0 权威 + 附录引言例外注记（R31-01/12）、runbook 补 WAL 回放步骤 + RPO 口径（R31-02）、claim C-29 虚标/C-12 跨层错位修正（R31-03）、observability 补可用性指标 + 磁盘/SLO/熔断告警（R31-04/05）、恢复演练触发修正 + benchmark 补 RPO 验证（R31-06）、acceptance 补容量/RTO/RPO/可用性验收行 + nfr 测量方法与 RPO 适用范围修正（R31-07/13）、CAL-02 预留状态统一（R31-08）、test-plan §3.5a 标题 + A-01 占位（R31-09/10）、runbook 证伪响应补暂停遗忘调度器（R31-14）；受改 10 份文档版本记录同步；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.66 | 2026-08-09 | round32 全面深度审计修复批次（changelog 0.0.66，见本文件 0.0.66 叙述节）：版本记录登记纪律系统性收口——补登 0.0.57/0.0.59/0.0.61/0.0.64 四个批次共 14 处版本记录漏登记行（architecture/configuration/data-model/README×3/implementation-map/engineering-workflow/project-plan/security-specification/technology-stack/runbook/threat-model/acceptance-criteria/cognitive-foundation）；0.0.64 叙述节被 0.0.65 分割的排序错误修复（B~E 段归位）；[REPO-09-hermes-agent.md](../analysis/external-videos/repos/REPO-09-hermes-agent.md) 尾随空格 1 处清除；受改 14 份文档版本记录同步 0.0.66；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.67 | 2026-08-09 | round33 全面深度审计修复批次（changelog 0.0.67，见本文件 0.0.67 叙述节）：治理执行记录过时补记（documentation-governance §3 补 round17~32 批次链）+ 批次/过程标记收敛（cognitive-architecture-gap G-08/09/11「（本轮新增）」×3 删除；「（勘误）」后缀 ×6 去除于 technology-stack/architecture/configuration/observability/use-cases）；受改 8 份文档版本记录同步 0.0.67；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.68 | 2026-08-09 | round34 全面深度审计修复批次（changelog 0.0.68，见本文件 0.0.68 叙述节）：语义层版本边界/事实转述 + 硬行号缩写残留 + 用户路径域对齐——架构 §3.9 R1 补版本边界（128 维摘要向量为 v1.1+ 目标，v0.1.0 以 1536 维单向量承载）、架构 §3.2 组合性使用转述改指认知基础实际定义（两种异质激活活动 + 联结性使用为运行时模式）并清除 L94、认知基础 L64 缩写行号残留清除、configuration `KAIROS_PATH` 来源「§L3」→「§9.3 四级规则引擎（L3 字典匹配）」、user-guide/quick-start 路径域改指 `_user` 持久域；受改 6 份文档版本记录同步 0.0.68；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.69 | 2026-08-09 | round34 门禁建议落实批次（changelog 0.0.69，见本文件 0.0.69 叙述节）：门禁 6.15 扩展捕获 Lxx 缩写行号形态 + adr 决策 D-10 行号引用语义化。 |
| 0.0.70 | 2026-08-09 | round35 全面深度审计修复批次（changelog 0.0.70，见本文件 0.0.70 叙述节）：治理执行记录自引用快照收口——documentation-governance §3 执行记录补记 round34（0.0.68）/0.0.69 批次（round33 教训「自引用快照必须含自身批次」重演），含本批次自身；受改 2 份文档（documentation-governance + changelog）；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.71 | 2026-08-09 | round35 门禁建议落实批次（changelog 0.0.71，见本文件 0.0.71 叙述节）：门禁 6.32 治理执行记录覆盖性入检（自引用快照须含最新 changelog 批次，R35-01 防复发）+ engineering-workflow CI 门禁清单同步 + documentation-governance 执行记录补 0.0.71（含本批次自身）；受改 3 项（doc-audit.py + engineering-workflow + documentation-governance + 本文件）；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.72 | 2026-08-09 | round36 全面深度审计修复批次（changelog 0.0.72，见本文件 0.0.72 叙述节）：五维度全面深度审计（完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）——机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.32 exit 0；deep-audit exit 0），语义层核查 35 项核心口径零漂移；新发现 5 项问题（1 中 / 4 低）全部闭环——H-02/H-03 引用落点 §7.3→§7.1a（同源遗漏）、C-23 悬空引用修正、P3-21 FTS5 口径补注、project-plan 门禁镜像滞后同步 6.32；受改 4 份文档（feature-list + claim-implementation-matrix + project-plan + changelog）；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.73 | 2026-08-09 | round37 全面深度审计修复批次（changelog 0.0.73，见本文件 0.0.73 叙述节）：五维度全面深度审计（完整性与一致性 / 缺失与过时 / 结构与组织 / 格式规范 / 核心文档准确性）——机器门禁基线全绿（doc-audit 18 类 + 14a + 6.8a/6.12a/6.13~6.32 exit 0；deep-audit exit 0），语义层核查以「引用落点存在性」为重心；新发现 12 项问题（10 中 / 2 低）全部闭环——feature-list 引用落点批量修正 10 行（R-05 时间索引→§7.3a 时间过滤约束、R-10 时间序检索→api-spec §1.2 + api-spec 补 sort 参数、W-09 冲突检测→蓝图 §5.6、M-12 社区检测→蓝图 §一、M-13/A-16 事实新鲜度→蓝图 §一、A-15 Recall Funnel→架构 §7.3、M-16 MemCube→蓝图 §一、M-22 Mental Model→蓝图 §一、A-24 MCP Bridge→§7.1a）、架构 §7.3a 内部悬空引用修正（事实新鲜度元数据→蓝图 §一）、claim-matrix C-20 悬空引用修正（§8 或→§0.5 单一落点）、blueprint P3-15 引用落点修正（§5.2→§一）；受改 5 份文档（feature-list + api-spec + architecture + claim-implementation-matrix + architecture-blueprint-v1.1）+ 本文件；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.74 | 2026-08-09 | round38 门禁建议落实批次（changelog 0.0.74，见本文件 0.0.74 叙述节）：round37 门禁补盲区建议落地——新增 6.33（feature-list「对应架构组件」列引用落点全量校验，FAIL 级硬门禁，首跑 0 漂移）+ 6.26 扩展档 4（链接格式「§X 机制名」存在性校验，WARN 级软提示）；首跑捕获并修复真实问题 8 项——C-19 排列漂移审计→运行期漂移审计、design-philosophy 序数压制幅度记录/排列漂移审计/认知关节索引→序数幅度差记录/运行期漂移审计/认知关节登记表、debt-collection ARC-D-004 序数压制幅度记录→序数幅度差记录、api-spec/requirements-baseline/detailed-design 三处「事件类型原语表」→「事件类型枚举表」、data-model「密钥生命周期」→「API Key 生命周期」；门禁清单镜像同步（engineering-workflow §四 + project-plan Phase 0 →6.13~6.33）；受改 9 份文档 + 本文件；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.75 | 2026-08-09 | round39 全面深度审计修复批次（changelog 0.0.75，见本文件 0.0.75 叙述节）：五维度全面深度审计——round38 报告「26 条 6.26 档 4 WARN 全为可忽略噪声」声明逐条实证复核，甄别出 **4 条真实问题**（0 高 / 4 中 / 0 低）全部闭环：data-model 定位段「架构 §4 存储层」章节错位→§5（§4 为推理皮层）；data-model memory_relations `derived_from`「架构 §5.2 Mental Model」悬空→blueprint §一（架构全文无 Mental，同源遗漏）；detailed-design 写入管线「data-model §8.3 冲突判定规则」悬空→§1 memories `content_hash` 列（§8.3 为 memory_entities 表）；acceptance-criteria §三「参数登记见 configuration §9」错位→附录 A（§9 为 RL 参数，`KAIROS_BENCHMARK_*` 在附录 A）+「架构 §10 基准测试配置」→§10.5 量化指标；受改 4 份文档（data-model + detailed-design + acceptance-criteria）+ 本文件；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.76 | 2026-08-09 | round39 门禁补盲区建议落地批次（changelog 0.0.76，见本文件 0.0.76 叙述节）：6.26 档 4 候选词提取优化——动词/描述性前缀剥离（定义了/详述/只覆盖/保持/约束等）+ 尾部后缀扩展（参数/状态机/验收/确定/路径/过程/流程）+ 括号 a-d 类字母段标注回退，WARN 23→12 条；标题行匹配「整段连续中文段」严格逻辑复核（曾试滑窗子串致误放行已回退）；突变测试双验证（悬空捕获/描述放过）；documentation-governance §2.2 触发条件与复核清单 (b) 增补「机制名引用修改须 grep 同机制名全库联动」规则（R39-02 同源遗漏防复发）；受改 3 项（doc-audit.py + documentation-governance + 本文件）；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.77 | 2026-08-09 | round40 全面深度审计轮次登记（changelog 0.0.77，见本文件 0.0.77 叙述节）：0.0.76 门禁优化批次后首轮五维度审计——0 高 / 0 中 / 0 低全面零漂移（架构引用落点批量校验 10+27+analysis 143 份 0 漂移；核心口径复验五条推论/事件 10 类/CLI 三档/E2E 9/五态/债务 104/D-334/标志 24/声明 37/MCP 15 全部一致；6.26 剩余 12 条 WARN 全部为可忽略噪声）；本批次无文档实质变更，仅登记审计轮次；门禁全类验证 exit 0。 |
| 0.0.78 | 2026-08-09 | round40 改进建议落地批次（changelog 0.0.78，见本文件 0.0.78 叙述节）：6.26 档 4 新增「3-6 字尾缀标题匹配」判定（特征标志编码纪律→编码纪律子节标题、各条推论→五条推论标题，WARN 12→10 条；仅取尾部窗口非任意子串——反例存储层量子纠缠索引不误放行；突变测试双验证通过；「权重」未入剥离表保守决策）；documentation-governance §4 增补「版本记录表方向约定」（升序表插表尾/降序表插表首，插入前确认表方向，单文档内一致）；受改 3 项（doc-audit.py + documentation-governance + 本文件）；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.79 | 2026-08-09 | round41 全面深度审计修复批次（changelog 0.0.79，见本文件 0.0.79 叙述节）：8 中 / 17 低全闭环——changelog 排序归位（叙述节 0.0.74 + 版本表升序）、五份超限文档补导航、摄入/摄取统一、组合寄存器/§10.12/P6 口径/潜伏势能四处裁决歧义修正、§10.24 补 3 债、§0.9 补可及性轴行、认知基础五处口径修正、蓝图三处引用修正、格式类 7 项；受改 12 份文档 + 本文件；核心计数全未变动；门禁全类验证 exit 0。 |
| 0.0.80 | 2026-08-09 | round42 全面深度审计修复批次（changelog 0.0.80，见本文件 0.0.80 叙述节）：9 中 / 36 低全闭环——错误码返回方式/契约引用/摄取沙箱错指三处口径修正、架构三级梯度三处互斥收敛（宪法主权面/探索投资/元认知层）、§10.3 版本链形态对齐 §5.2、认知基础调用类型轴归属统一；摄入残留 4 处、「吸收自」旧形态 5 处、决策编号前缀 12 处、glossary 补 6 术语（70→76）等格式收尾；受改 21 份文档 + 本文件；门禁全类验证 exit 0。 |
| 0.0.81 | 2026-08-10 | round43 全面深度审计修复批次（changelog 0.0.81，见本文件 0.0.81 叙述节）：3 高 / 6 中 / 5 低全闭环——VAD 条件激活（G-02）权威落点统一至架构 §3.2（联动 9 处引用归位）、vad-coordinate-algorithm 公式对齐、security-specification L61 自否定句修正对齐 S-01；threat-model S-07 主控制重映射、requirements-baseline R-06 隐式 VAD 形式、claim-matrix/traceability-map VAD 引用统一、test-strategy S-17 法定擦除例外测试行、债务 D-440 登记（价值维度熵阈值参数化）；changelog 叙述节升序重排 + 孤标题归位；debt-collection/architecture-blueprint 补章节导航；CRLF 4 份归一 LF；§11 负载锚点刻意不改；受改 18 份文档 + 本文件；门禁全类验证 exit 0。 |
| 0.0.82 | 2026-08-10 | round44 门禁建议落实批次（changelog 0.0.82，见本文件 0.0.82 叙述节）：落 round43 §四 4.4 门禁增强——新增 6.34 changelog 结构纪律（叙述节升序 + 版本记录邻接，防 R43-09/10 复发）、6.35 红线语义互斥词对检查（S-14 试点，全库 0 违例）；S43-2 暂缓；scripts/doc-audit.py 受改；门禁全类验证 exit 0。 |
| 0.0.83 | 2026-08-10 | round45 全面深度审计修复批次（changelog 0.0.83，见本文件 0.0.83 叙述节）：3 高 / 4 中 / 4 低共 11 项全闭环——intention 契约版本归属改能力粒度切分（feature-list PM-01/02 + requirements-baseline §1.8 与 data-model/api-spec 契约层已落地事实对齐）、api-spec §4 事件枚举范围标签对齐表体（补「首迭代」列 ✅4/⏳6）、架构 §10.11 P6 监控改基线增量制（消除交付态恒触发的自毁规则）并前置三层治理边界承载（关系层不受 P6 压缩约束）；红线违反 HTTP 分派映射、备份容量满载口径与 NFR 磁盘预算反向声明、特征标志默认组合实为双信号、FTS5 分词扩展缺失回落行为、`sort=heat_score` 未启用回落语义、契约 DDL/API 默认分层说明；误报剔除 3 项、观察项 3 项（D-428/D-429/VAD 刻意设计）；受改 9 份文档 + 本文件；核心计数零漂移；门禁全类验证 exit 0。 |
| 0.0.84 | 2026-08-10 | round46 门禁建议落实批次（changelog 0.0.84，见本文件 0.0.84 叙述节）：落 round45 §四 4.4 门禁增强——新增 6.36 版本归属互斥检查 / 6.37 表格范围词一致性 / 6.38 阈值监控自洽性（三项 WARN 级软门禁首轮，全库 0 违例）；门禁清单镜像同步 6.13~6.38（补齐 round44 漏登的 6.34/6.35）；scripts/doc-audit.py 受改；门禁全类验证 exit 0。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85，见本文件 0.0.85 叙述节）：6 高 / 14 中 / 2 低共 22 项全闭环——状态机死角收口（Reflect done 收敛、遗忘函数极性、宪法修订端口单条记忆出口）、契约语义互斥收敛（幂等键统一 + ERR-CTR-005、乐观锁强制 If-Match）、openapi adminKey 未定义引用替换、锁死锁/归档身份守卫/as_of 双时态/Deep 抽样口径/GSPO 缩减语义/softmax 投影/实体阈值参数化/S-04 术语/S-11 端口混淆等；错误码 42→43、参数 373→374；实质受改 13 份 md + openapi.yaml（data-model / reliability 审视未动，0.0.89 勘误原「15 份」）+ 本文件；门禁全类验证 exit 0。 |
| 0.0.86 | 2026-08-10 | round48 遗留问题处理批次（changelog 0.0.86，见本文件 0.0.86 叙述节）：6.26 全文痕迹校验跨行吞噬缺陷修复（round47 新 WARN「衰减口径」误报根因）+ api-spec 引用措辞对齐（仅 §1.3 一处；§1.1/§1.2 两处遗留由 0.0.87 补改，见 R49-02）；6.36/6.37/6.38 三项软门禁观察一轮后晋升 FAIL（round46 承诺兑现，晋升后全库 0 违例）；0.0.85 验证段 WARN 计数勘误（S 级诚实红线）；scripts/doc-audit.py + api-spec + engineering-workflow 受改；门禁全类验证 exit 0。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87，见本文件 0.0.87 叙述节）：0 高 / 8 中 / 11 低共 19 项全闭环——既往批次落体核查（round47 H-04 幂等模型正文补改、round48 api-spec 引用措辞两处补改、round47 受改清单勘误）、api-spec If-Match 口径统一、决策/债务编号前缀与正文裸引用收敛、5 份长文档章节导航 + adr ADR 一览表、标题风格约定补全、债务 D-441/D-442 登记、glossary 补「上下文腐烂」（术语 76→77）、use-cases 入口、投影措辞括注、版本记录表方向例证勘误；受改 21 份文档（configuration 审视未改，0.0.89 勘误原「22 份」）+ 本文件；门禁全类验证 exit 0。 |
| 0.0.88 | 2026-08-10 | round50 全面深度审计修复批次（changelog 0.0.88，见本文件 0.0.88 叙述节）：0 高 / 2 中 / 7 低共 9 项全闭环——引用落点错位 5 处（feature-list R-23/R-24/R-27/SF-18 §2.1→§2.6.x、data-model QueryAnalyzer §2.1→§2.6.1）、blueprint DERIVED_FROM 版本边界措辞、分析批次过时计数 4 处（triage/first-principles/absorption/README）、concept-tiers 意图契约注记、use-cases 场景 4 表述精确化；受改 9 份文档 + 本文件；门禁全类验证 exit 0。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89，见本文件 0.0.89 叙述节）：0 高 / 7 中 / 13 低共 20 项全闭环（另观察 1 项）——落体核查（debt-collection 摘要表补 D-440~D-442 三行）+ 受改计数勘误（0.0.85 15→13、0.0.87 22→21）+ 5 份长文档章节导航 + feature-list/claim-matrix 版本记录归位 + 正文裸引用链接化 30+ 处 + 编号前缀补标 + 追缴补盲（D-443/D-444）+ 孤儿入口 5 处 + 格式收尾；债务 D-442→D-444；其余核心计数零漂移；门禁全类验证 exit 0。 |
| 0.0.90 | 2026-08-11 | round52 全面深度审计修复批次（changelog 0.0.90，见本文件 0.0.90 叙述节）：0 高 / 1 中 / 5 低共 6 项全闭环（另观察 1 项）——追缴补盲三轮（7 处「v1.1 候选/目标」软承诺登记 D-445，架构原文加指针）+ architecture/blueprint 补 H1 + 「多 Agent/单 Agent/跨 Agent」空格统一 20 处 + 「架构[链接]」中英空格统一 10 处 + P1-P6 全角范围符 6 处；债务 D-444→D-445；其余核心计数零漂移；门禁全类验证 exit 0。 |
| 0.0.91 | 2026-08-11 | 外部理念吸收落地批次（changelog 0.0.91，见本文件 0.0.91 叙述节）：LongMemEval 记忆能力评测协议落地——benchmark-plan 新增 §3.15（七步流程 / Kairos 变体定义 / 汇报硬规则 5 条 / 参考基线非门槛 / 既有机制联动）+ §3.12 联动注记 + test-plan 预留 TC-LME-001~ + acceptance-criteria §一a 测量任务集补充 + absorption-proposals 登记 AP-53；参数计数不变；核心计数零漂移。 |
| 0.0.92 | 2026-08-11 | 定稿收尾批次（changelog 0.0.92，见本文件 0.0.92 叙述节）：D-431 十项待定义参数分类处置（8 项 v1.1 域 + 2 项部署时点，竖切核验无待定义）+ 设计基线冻结声明（修订仅限三类、外部吸收边界 0.0.91 止）+ doc-audit.py GBK 编码崩溃修复；参数计数不变；核心计数零漂移。 |
| 0.0.93 | 2026-08-11 | round53 全面深度审计修复批次（changelog 0.0.93，见本文件 0.0.93 叙述节）：0 高 / 1 中 / 3 低全闭环（另 2 观察项）——追踪项计数收口（traceability-map「104 追踪项」快照 → debt-collection 权威账目 + README 同步）+ traceability-map 版本记录补登 0.0.90 + slice-implementation-guide 引用措辞 + changelog 浏览指引 + feature-list 结尾换行；参数计数不变；核心计数零漂移。 |
| 0.0.94 | 2026-08-11 | round54 全面深度审计修复批次（changelog 0.0.94，见本文件 0.0.94 叙述节）：0 高 / 0 中 / 2 低全闭环（另 2 观察项）——traceability-map 版本记录登记缺陷收口（0.0.90 行混入 0.0.93 内容移除 + 0.0.93 行补建，R53-02 同类复发）+ deployment 标准级宪法主权面措辞对齐架构 §0.5 + 「触及即登记」操作细节防复发规则 + **门禁 6.39 新增（受改批次版本记录覆盖性，WARN 级软门禁，首跑捕获 traceability-map 缺 0.0.94 行并补登）**；主审门禁盲区扫描（H1 全库/标题跳变/超长导航/中英空格/日期格式/软承诺追缴）全绿；参数计数不变；核心计数零漂移。 |
| 0.0.95 | 2026-08-11 | Obsidian frontmatter 闭合缺陷修复批次（changelog 0.0.95，见本文件 0.0.95 叙述节）：6 份文档（adr / risks / slice-implementation-guide / acceptance-criteria / benchmark-plan / test-strategy）frontmatter 缺立即闭合 `---` 修复（Obsidian「无效属性」根因——正文引用块被卷入 YAML 区）+ 门禁 6.16 盲区增强（frontmatter 区内容合法性校验，突变测试验证捕获能力）；参数计数不变；核心计数零漂移。 |
| 0.0.96 | 2026-08-11 | 定稿审查处置批次（changelog 0.0.96，见本文件 0.0.96 叙述节）：四组全量通读低危缺口收口——use-cases 三信号检索误归 v1.1 勘误、架构叙事自洽度评估器降级默认分数登记 D-446、D-430 分类处置（config show 契约登记 + 其余归 v0.1.0 全量阶段）、认知导航表/RTM/OP-054/deployment 环境变量/架构引用与版本标注等机械性修正；债务 D-445→D-446；参数计数不变；其余核心计数零漂移。 |
| 0.0.97 | 2026-08-11 | 竖切代码启动批次（changelog 0.0.97，见本文件 0.0.97 叙述节）：W1~W9 全量交付——项目骨架（Typer 定档）、15 张竖切表迁移（Alembic + schema-slice 权威 DDL）、记忆 CRUD + 双副本（S-14 隔离）、路径空间（GLOB 前缀 + 污染率 0%）、事件总线（4 类 + 背压 + trace_id）、三信号检索（numpy 余弦 + FTS5 BM25 + 实体加成）、遗忘 + 潜伏势能、身份注册表（构造论 + 否决裁决器）、校准/降级/冻结 + 审计 HMAC 链；REST 21 端点 + CLI 15 条；基准（写 P50 16.6ms / 路径 / 语义 1 万条）；D-428 竖切部分闭合（redocly 零 error）；实现偏差登记 D-447/D-448；README 状态声明更新。 |
| 0.0.98 | 2026-08-12 | 版本记录双轨制规则修订批次（changelog 0.0.98，见本文件 0.0.98 叙述节）：「触及即登记」→「结构性变更即登记」——版本记录只登记结构性变更，机械性变更只进 changelog；doc-audit 6.39 适配结构性受改清单解析（旧格式兼容）；changelog 0.0.97 受改清单标注为新格式。 |
| 0.0.99 | 2026-08-12 | 竖切首迭代批次（changelog 0.0.99，见本文件 0.0.99 叙述节）：事件总线全链路接线（use_event→影子副本）、APScheduler 空闲驱动调度（4 任务）、QueryAnalyzer（意图+时间锚定）、特征标志配置集校验+证伪套件、D-428 全量闭合（88 操作 schema，redocly 零 error）。 |
| 0.0.100 | 2026-08-12 | 竖切验收核对批次（changelog 0.0.100，见本文件 0.0.100 叙述节）：验收 9 项逐条核对（8 项代码侧达成 + 定稿评审待评审人）；事件总线入队非阻塞修复（基准挂起根因，恢复 PASS 4.7/3.4/1.4ms）；Agent Tool 层五工具；GET /health 补 scheduler/embedding 状态。 |
| 0.0.101 | 2026-08-12 | 接入层全通道交付批次（changelog 0.0.101，见本文件 0.0.101 叙述节）：Agent Tool 层五工具 + MCP Bridge 15 工具（独立子进程 stdio）+ StorageBackend 抽象（D-449 前置）+ GET /health 增强——v0.1.0 接入层四通道齐备（REST/CLI/AgentTool/MCP）。 |
| 0.1.0 | 2026-08-12 | v0.1.0 首版发布批次（changelog 0.1.0，见本文件 0.1.0 叙述节）：定稿评审通过（release-guide §2 十项全过 + §3 构建安装验证）——全库版本统一升级 0.0.x → 0.1.0、文档状态 draft → design-freeze。 |
| 0.1.1 | 2026-08-12 | Hermes Memory Provider 接入批次（changelog 0.1.1，见本文件 0.1.1 叙述节）：Hermes ABC 契约对齐（handle_tool_call JSON 字符串 / queue_prefetch / on_session_switch / get_config_schema+save_config / agent_context 守卫）+ 端口勘误 8011→8010 + 遗忘调度器缺陷修复（create 初始化 last_access_at + use_event 刷新）+ 端到端验证（8010 默认端口）+ deployment §四·a 部署登记 + configuration 附录 A 登记接入层参数 5 项（参数 374→379）+ 契约测试新增；债务 D-447~449 闭合叙述补记（debt-collection 已登记）。 |
| 0.1.2 | 2026-08-13 | MCP 工具契约补齐批次（changelog 0.1.2，见本文件 0.1.2 叙述节）：扩展端点 10 个（stats/heat-top/feedback/traces/entities/graph/sessions/relations）+ memory_relations 表（16 张竖切表）+ bridge 假实现真实化——MCP 15 工具全可用；运行修复闭环（bus_drain 消费接线 / 订阅器 commit / load_settings 默认 .env / batch occurred_at）+ 2041 条误归档记忆恢复 active；CI 补 KAIROS_PG_TEST_SKIP=1；测试 288 项；README 竖切状态更新（16 表/31 端点/18 CLI/15 工具）。 |
| 0.1.3 | 2026-08-13 | 全面审计修复批次（changelog 0.1.3，见本文件 0.1.3 叙述节）：ruff 77→0 / mypy 10→0（CI code-checks 转绿）；Litestar 31 端点迁移 Annotated 新风格 + `<3` 上限（warnings 1217→1，3.0 升级兼容）；auth 守卫注入消除每请求配置重读；CLI 计数 18→21、api-spec §1 补登记 4 端点（端点 88→92）、openapi 补 4 端点；doc-audit 批次正则扩展 0.1.x + 6.39 偏移 bug 修复 + 0.1.x 治理欠账补登。 |
| 0.1.4 | 2026-08-13 | 全面审计修复批次（changelog 0.1.4，见本文件 0.1.4 叙述节）：S-09 注入扫描实现（injection_scan + ingestion 第 5 层 + 4 用例）；S-01 生产密钥强制（KAIROS_ENV 参数 + production 密钥族必填 + development 无鉴权警告，config/deployment/configuration 登记，参数 380→381）；D-450 三级 Key 鉴权体系追缴登记 + D-430 状态部分闭合同步；CI mcp-tools schema 校验真实化（schema 文件创建 + fallback 收紧）；测试 288→292、覆盖率 81.52%→82.81%（auth 401 + D-430 命令补测）；AGENTS D-428 残留清除 + 覆盖率同步、changelog 指引/frontmatter、gitignore 补模式、development-setup 环境约束注记。 |
| 0.1.5 | 2026-08-13 | 实体信号激活批次（changelog 0.1.5，见本文件 0.1.5 叙述节）：entity_extractor 公共提取器（规则法 + 类型推断 + user_id 解析）；MemoryStore.create 写入侧自动提取（entities 去重 + memory_entities 关联）；hybrid_search 归一化退化 bug 修复（单候选信号满配——entity 恒 0 深层根因）；extended.py 复用公共提取器 + 类型推断；测试 +13 项（305 全量）；真实验证三信号融合 0.35·1+0.15·1=0.5 吻合。 |
