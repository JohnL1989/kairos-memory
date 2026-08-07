---
title: Kairos 变更日志
aliases:
  - CHANGELOG
tags:
  - kairos
  - governance
  - changelog
created: 2026-07-20
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# CHANGELOG

> **定位**：按日期记录的变更日志，记录从什么变成什么。各文档内嵌的版本记录保留为文档级审计，CHANGELOG 提供跨文档的版本演进全景。

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

- **建议一·校准退化链（全部三子建议）**：架构 §1.2 虚拟校准置信度动态衰减公式化（`0.3 × exp(-λ × days)`，λ=0.02，floor 0.05，auto-dormant 60 天）；校准状态运营可视化映射（healthy/degraded/virtual/dormant 四级枚举,刻度粗于降级状态机周期,以状态机为准）；api-spec 检索响应补 `meta.calibration_status` 与 `nudge` 可选字段（subtle/noticeable/prominent 三级,非阻塞）+ `GET /v1/health/calibration` 端点;configuration 补 3 项参数（DECAY_LAMBDA/DECAY_FLOOR/AUTO_DORMANT_DAYS）。
- **建议二·认知完整性半定量轴（三级 0/1/2）**：架构 §5.2 结构性记忆守护补 structural_value 三级定义（L1 疑似:causal 引用≥2/路径高分叉/叙事线断裂风险;L2 确认:外部校准标记/手动标注/引用≥5）与遗忘调度器分级行为;data-model memories 补 structural_value/structural_value_reasons/structural_value_updated_at 三字段 + is_structure 双向同步;定位为 D-311 的 v0.1.0.x 前置台阶（衔接 D-306/D-312）;configuration 补 3 项参数。
- **建议三·QueryAnalyzer（保留架构枚举+吸收细节）**：架构 §2.6.1 补规则优先+模型兜底实现策略（规则层覆盖 ≥80% 查询零 LLM）、意图覆盖注记（身份查询由确定性检索承载、问候由摄取门禁拦截）、事件锚定解析（注册表→语义降级）与 fallback_query 字段;slice-guide 组件 3 补「竖切后首迭代实现优先级」定位。
- **建议四·记忆压力可操作化（映射 D.7 四信号）**：架构 §5.2 压力信号族补四指标量化（WM 占用率/检索失败率/冗余率/遗忘积压比）+ 三级减压动作（L1 温和/L2 中度/L3 激进,L3 标记遗忘候选不物理删除）+ 恢复条件与审计事件;api-spec 补 `GET /v1/health/memory-pressure`;configuration 补 4 项参数。
- **建议五·Saga 最小实现（复用 narrative_threads）**：架构 §5.2 补 v0.1.0 子集声明（创建/添加/检索/手动完结四操作,纯 DB 无 LLM）;api-spec §八 补 v0.1.0 子集声明与 create/members/memories 三端点;feature-list M-21 补子集注记;自动聚合/自动完结/summarize 标注 v1.1 目标。
- **建议六·概念分级速查表**：新增 [references/concept-tiers.md](../references/concept-tiers.md)（L1 10 项/L2 12 项/L3 12 项 + Mermaid 依赖图 + "如果只读三页"速览路径）;架构 §0 速查表加链接;glossary 权威声明不变。
- **建议七·压缩审计日志（债编号纠正）**：data-model memories 补 `compression_trail` JSONB（逐记忆压缩审计,为 §10.11 全局监控的逐记忆粒度展开）;新增 [references/capability_matrix.yaml](../references/capability_matrix.yaml)（版本化能力矩阵,恢复债编号纠正:D-306/D-311/D-312 认知完整性、D-313 可及性、D-301 时间逻辑-因果——非提案误引的墓碑 D-318/319）;api-spec 补 `GET /audit/compression` 与 `/summary`;检索侧维度丢失记事件总线 `retrieval_dimension_loss`（use_event payload,枚举保持 10 类,不写记忆 trail）。
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

> 依用户决策：审计问题处理完即归档,不长期保留;决策定义从审计报告迁移至治理资产。

- **决策迁移至 ADR**：决策编号 D-01~D-27 权威定义从 reviews 审计报告迁移至 [adr.md](./adr.md)「审计决策迁移」节（D-01~D-15 源自 08-03 审计批次、D-16~D-27 源自 08-04 交叉审计批次;D-06→ADR-001、D-11→ADR-011 由既有 ADR 承载,仅登记迁移关系）;documentation-governance §5 决策编号注册表定义源改指 `adr.md`。
- **审计报告归档**：新增审计历史摘要（10 轮审计汇总表 + 决策索引 + 归档机制）;删除 reviews 下 10 份审计报告（2026-08-03~08-05 各轮）——问题处置要点以 changelog 各批次为准,问题清单不再长期保留。
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

- **热度体系实证参考基线**（吸收外部热引擎与时间蒸馏实证）：认知基础 §1.1 新增「热度体系实证参考基线声明」（热度组合公式 `1.0+频次×2+新近×10+重要性加分`、层级衰减 ×0.985/0.975/0.965/0.95、父传播 `max×0.6+mean×0.3+一致性×0.1`，附 P6 边界声明与可证伪判据）；usage-load-algorithm 三.5 K-063 注记补参考基线段；detailed-design 补热度体系参考参数表。
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

## 0.0.24（2026-08-05）— 第六/七轮全库深度审计修复批次（后补登记：叙述节位于 0.0.25 之后，版本记录表序号为序）

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
- **格式纪律（9 项）**：正文「0.0.xx 勘误/新增」版本注记批量清理（去版本号保留信息内容；决策/教训/债务溯源类注记豁免——R14-11 观察项边界内）；外部产品名收敛为「外部理念吸收/第三方实证」表述；5D 混合排序废弃术语补历史沿用名注记；ERR-INPUT-004 改 409（完结叙事线拒绝新成员）；error_event 改 use_event；concept-tiers 契约英文名修正（pinned/lazy/ephemeral → permanent/ondemand/environmental/temporary）；api_keys 归类注记（非 P3 系）；「v0.1.0·x」笔误修正；TC-MEMV-001 回滚参数载体对齐 api-spec。
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
| 0.0.19 | 2026-08-05 | 第四轮全库深度审计修复批次（依 master-documentation-audit 闭环）：身份否决权实现形态裁决（1-01，架构 §1.8 权威，D-001/D-101 已实施）;章节引用错位三连与成本护栏引用修正;监督平面口径统一;逻辑-因果轴层级口径（方案 a）;P3-19 承载补全;§5.2 占位与节内导航;驻留矛盾句与命名统一;blueprint 文件名 v1.1+ → v1.1 全库同步。 |
| 0.0.20 | 2026-08-05 | 第五轮全库深度审计修复批次（依 round5-deep-audit 闭环，0 高/10 中/8 低）：P0 语义矛盾 4 项（速查表否决权/监督平面宪法解释/宪法解释层驻留/时间轴三子轴口径）;P1 引用批量 3 组（架构词汇桥接 8 处、认知基础 6 处、架构→api-spec 7 处 + 反向注记）;P2 结构与格式（§5.17/5.18 迁 §6、断号说明合并、术语计数 56→57 + 门禁补盲区、行号引用清零、SDK 版本对齐注记、README 入口行、1-05 方案 b、3-03 记录在案）;门禁全绿。 |
| 0.0.21 | 2026-08-05 | 系统架构总览图新增批次：architecture §0.4.1 新增 Mermaid 全局架构图（六层栈 + 三治理面 + 横切基础设施 + 编号数据流 + 图例）;口径与正文逐条核验;门禁全绿。 |
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
| 0.0.40 | 2026-08-07 | 外部视频分析批次：100 视频 + 15 仓库对照分析（详见上文 0.0.40 主体章节）——新建 [docs/analysis/external-videos/](../analysis/external-videos/README.md) 独立目录（索引 + 分诊矩阵 + 原理评审 + 吸收建议 + N 份视频笔记 + 15 份仓库笔记 + 抓取流程记录）；实测 B站 AI 字幕串台问题；脚本入库 2 个；零改动核心设计文档；无债务/ADR/风险登记（全部建议态）；门禁验证见批次记录。 |
| 0.0.39 | 2026-08-06 | 外部理念吸收批次（2026-07）：落地 6 项借鉴——① 记忆质量评估指标（acceptance-criteria §一a 新增过时调用率 / 任务成功率改善，v1.1+ 设计目标）；② 反事实检验测试模式（test-strategy §2.7 三态对比 + TC-CF-001~004）；③ encoding_context `conditions` 子结构约定（data-model，条件性经验适用范围显式化）；④ 高相似 × 过时联合惩罚（architecture §7.3a 排序调制，stale ×0.7 / expired ×0.5）；⑤ 记忆四动作失败模式排障表（troubleshooting §二a）；⑥ 基准设计红线——经验来源与验证数据分离（benchmark-plan §3.11 评测泄漏防护）；配套：observability 指标 2 项 + 告警 1 条、integration-design §五a 任务成功率回传契约（task_outcome 事件，v0.1.0 落 usage_events 不新增端点）；无债务登记、无新文档（7 份现有文档修订）；门禁验证通过。 |
