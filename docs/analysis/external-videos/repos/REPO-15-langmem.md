---
title: REPO-15 仓库分析：LangMem（langchain-ai/langmem）
aliases:
  - 外部仓库分析-15
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-15 LangMem（langchain-ai/langmem）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/langchain-ai/langmem |
| Star | 1597★（任务简报口径，2026-08-07，未独立核对） |
| 语言/许可 | Python / MIT（LICENSE 文件，未逐行核对） |
| 视频对应 | 无（补充发现批次；独立项目核实——LangChain 官方记忆库） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone --depth 1（成功，有 .git；未记录 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：LangMem「helps agents learn and adapt from their interactions over time」——提供「tooling to extract important information from conversations, optimize agent behavior through prompt refinement, and maintain long-term memory」（`README.md`）；「functional primitives you can use with any storage system and native integration with LangGraph's storage layer」（`README.md`）。两大用法：热路径（agent 会话内用工具管理记忆）+ 后台（memory manager 自动提取/巩固/更新）（`README.md`）。

**源码实证**：核心抽象在 `src/langmem/`——`knowledge/extraction.py`（2113 行，`MemoryManager` 用 trustcall 做多轮提取）、`knowledge/tools.py`（530 行，create_manage_memory_tool / create_search_memory_tool）、`short_term/summarization.py`（860 行，RunningSummary 增量摘要）、`prompts/`（提示词优化三优化器）、`reflection.py`（后台 ReflectionExecutor）。**定位与源码一致：记忆是「LLM 驱动的状态机」——接受对话 + 当前记忆状态 → LLM 决定如何扩展/巩固 → 输出更新后的记忆状态**（`docs/docs/concepts/conceptual_guide.md`「At its core, each memory operation in LangMem follows the same pattern」）。与 Kairos 最大差异：**无时间轴、无衰减、无图结构、无真相分层**——记忆完全由 LLM 的提取判断驱动，存储只是 BaseStore 的 namespace/key/value 文档。

## 架构与核心机制（源码实证）

### A. 记忆类型与存储模式（`conceptual_guide.md`「Memory Types」）
| 类型 | 用途 | 存储模式 |
|:--|:--|:--|
| Semantic | 事实/知识（用户偏好、知识三元组） | **Collection**（无界知识文档，运行时搜索）或 **Profile**（严格 schema 单文档，最新状态） |
| Episodic | 过去经验 | Collection（对话摘要） |
| Procedural | 系统行为（核心人格、响应模式） | **Prompt rules**（系统提示词规则）或 Collection |

- Collection 更新复杂度自述（`conceptual_guide.md`：「The system must reconcile new information with previous beliefs, either deleting/invalidating or updating/consolidating existing memories... balance memory creation and consolidation」）——**与 Kairos 差异检验/ADD-only 的同类问题，但解是 LLM 裁决而非结构性协议**
- **Profile 模式**：单文档代表当前状态，新信息到达时更新现有文档而非创建新文档（`conceptual_guide.md`「Profiles」）——「只要最新状态」的显式取舍

### B. 记忆提取：`MemoryManager`（`knowledge/extraction.py:222-345`）
1. 指令（`_MEMORY_INSTRUCTIONS`，extraction.py:185-205）：**三步框架——提取与情境化（含 p(x) 概率置信度标注）/ 比较与更新（注意偏离现有记忆的新信息，合并压缩冗余，按可靠性/新近度强化，移除错误冗余，维持内部一致性）/ 综合与推理（演绎/归纳/溯因得出关于用户/agent/环境的结论）**——提示词层面的「巩固指令」
2. 机制：`create_extractor`（**trustcall 库**，extraction.py:235-243）——`enable_inserts / enable_updates / enable_deletes` 三开关 + `max_steps` 多轮迭代（i=1 后追加 `Done` 工具，extraction.py:239-243）——**LLM 自己决定 insert/update/delete 哪些记忆**，`json_doc_id` 追踪更新目标（extraction.py:255-258）
3. `Memory` schema（extraction.py:86-92）：单 content 字符串 + 「standalone episode/fact/note/preference」描述

### C. 热路径工具（`knowledge/tools.py`）
- `create_manage_memory_tool`（25 行）：agent 会话内工具——动作 create/update/delete（`actions_permitted` 可配置）；默认指令「Proactively call this tool when you: identify a new USER preference / receive an explicit USER request to remember / are working and want to record important context / identify an existing MEMORY is incorrect or outdated」（tools.py:27-33）
- `create_search_memory_tool`（362 行）：记忆检索工具
- namespace 设计：`("memories", "{langgraph_user_id}")` 运行时配置占位符（tools.py:117-125）——**per-user 命名空间即作用域隔离**

### D. 短期记忆摘要（`short_term/summarization.py`）
`RunningSummary`（53-60 行）：`summary` + `summarized_message_ids` + `last_summarized_message_id`——**running summary 技术：增量摘要，只摘要新消息，旧摘要保留**；`summarize_messages`（337 行）预处理好消息（`_preprocess_messages` 102 行、`_adjust_messages_before_summarization` 225 行——避免重复摘要、分块、控制 token）

### E. 提示词优化（`prompts/optimization.py`，行为进化的核心）
三优化器：
1. **GradientOptimizer**：反射循环（max_reflection_steps 默认 3）分析 prompt + 反馈 → 提出改进 → 单步应用
2. **MetapromptOptimizer**：元学习直接提出更新（分析 examples 模式 → 直接更新 prompt）
3. **PromptMemoryOptimizer**：从对话历史提取成功模式（learns from conversation history）
——输入 trajectories（对话+反馈）输出更好的系统提示词——**「记忆→行为」的显式通道：记忆优化 agent 的系统提示词**

### F. 后台调度（`reflection.py`）
`ReflectionExecutor`：`after_seconds` 延迟调度的任务队列（reflection.py:279-328），跨会话异步处理记忆——「后台 memory manager」的调度形态

## 关键设计决策（README 口径 vs 源码实证对照）
| README 声称 | 源码验证结果 |
|:--|:--|
| 「extract important information from conversations」 | **一致**：MemoryManager + trustcall 多轮提取（extraction.py:222-345） |
| 「optimize agent behavior through prompt refinement」 | **一致且为特色**：prompts/ 三优化器（optimization.py）——其他记忆系统少有的「记忆回写行为」通道 |
| 「works with any storage system」 | **一致**：BaseStore 抽象（namespace/key/value + search），可换 InMemory/Postgres 等（`README.md`, 62-63） |
| 「Native integration with LangGraph's Long-term Memory Store」 | **一致**：create_manage_memory_tool 直接绑定 LangGraph store（tools.py:25-33, 489-491） |
| 「maintain long-term memory」 | **部分一致**：记忆可跨会话持久；但**无时间字段、无衰减、无遗忘调度**（除 LLM 判断删除）——「长期」仅指存储持久性 |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 记忆提取三步指令（提取/比较更新/综合推理 + p(x) 置信度标注，extraction.py:185-205） | 可吸收 | 升华管道 raw→item→strategy→behavior（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）+ 差异检验（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：「注意偏离现有记忆的新信息」「移除错误冗余维持内部一致性」与 Kairos 差异检验同题；「p(x) 概率置信度」与见证锚定可信度同向 | 增量：LLM 指令层面对「更新 vs 新增」的显式决策框架（Kairos 用结构性协议 ADD-only，LangMem 用 LLM 判断——两路径对照） |
| Collection vs Profile 双存储模式（无界文档 vs 单文档最新状态，`conceptual_guide.md`） | 张力 | 契约是运行时投影（认知基础 §2.2）+ 双副本（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | **张力**：Profile 模式「新信息更新现有文档」是**覆盖式**记忆（旧信息丢失）——与 Kairos ADD-only 叠加模式（§7.3g）**直接冲突**；LangMem 以「只要最新状态」为由接受覆盖，Kairos 以「禁止无声丢失」为由拒绝覆盖 | 值得记入张力清单：外部主流实现（Profile/更新单文档）vs Kairos 结构性不覆盖——Kairos 需要持续论证覆盖的代价（LangMem 是反例的工程实证，证明覆盖在工程上是常见且可用的） |
| MemoryManager 多轮 insert/update/delete 迭代（max_steps + Done 工具，extraction.py:239-243） | 已覆盖 | ADD-only 提取协议（[架构](../../../foundation/architecture-v0.1.0.md) §7.3g）+ 差异检验（§5.5） | 支撑：多轮迭代是 LLM 侧的对账机制；Kairos 以结构性协议替代 | 注意：LangMem 的 delete 是显式 LLM 决策，Kairos 不覆盖但允许差异检验裁决——机制差异值得对照 |
| 提示词优化三优化器（Gradient/Metaprompt/PromptMemory，prompts/optimization.py） | 可吸收 | 升华管道·behavior 阶段（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）+ 宪法主权面（[认知基础](../../../foundation/cognitive-foundation.md) §1.8） | 支撑：「记忆→行为」通道（提取成功模式回写系统提示词）与 Kairos behavior 阶段同题；**张力**：LangMem 让 LLM 直接改写系统提示词（agent 自改行为），Kairos 由宪法主权面约束行为变更——需对照「行为自进化」的边界治理 | 这是与 Kairos 宪法/身份面最相关的增量 |
| RunningSummary 增量摘要（summarized_message_ids 追踪，summarization.py:53-60） | 已覆盖 | 升华管道·item 阶段（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）+ 时间轴（§1.1） | 支撑：running summary 是短期记忆巩固的标准形态；Kairos 会话级巩固可对照 | 与「记忆操作混入统一动作空间」等短期记忆机制分诊同族 |
| per-user namespace 作用域（`{langgraph_user_id}` 占位符，tools.py:117-125） | 已覆盖 | 分域真理路由（[认知基础](../../../foundation/cognitive-foundation.md) §C.6）+ 路径空间硬过滤（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：namespace = 运行时作用域绑定，与 Kairos 路径前缀同构 | 增量：运行时占位符解析机制（config 注入 → namespace 物化） |
| 记忆指令中的「SNR 最大化」「避免冗词」（extraction.py:197） | 可吸收 | 使用价值轴·信息密度（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 可审计压缩（认知基础 §2.2） | 支撑：信息密度作为提取标准与 Kairos 压缩纪律同向 | 增量：提取提示词的密度指令措辞 |
| 记忆管理工具默认触发指令（preference/request/context/outdated 四类，tools.py:27-33） | 已覆盖 | 探索预算独立（认知基础 §2.2）+ 使用价值驱动（§2.1） | 支撑：显式触发条件是「何时值得记」的工程形态 | Kairos 有更结构化的价值评估；LangMem 是启发式指令 |

## 可吸收增量（具体到机制/参数/接口）
1. **提取三步指令框架**（`knowledge/extraction.py:185-205`）：提取与情境化（p(x) 置信度）/ 比较与更新（偏离检测、合并压缩、可靠性/新近度强化、一致性维护）/ 综合与推理（演绎/归纳/溯因）——Kairos 升华管道各阶段的 LLM 指令设计参考（尤其是「偏离现有记忆」检测与差异检验的指令层表述）
2. **PromptMemoryOptimizer**（`prompts/optimization.py`）：从对话历史提取成功模式 → 应用至新提示词——「记忆→行为」通道的最轻实现；Kairos behavior 阶段（§1.10）的对照设计与宪法主权面治理边界审查
3. **RunningSummary 增量摘要实现**（`short_term/summarization.py:53-60`）：`summarized_message_ids` 集合 + `last_summarized_message_id` 指针——短期记忆巩固的增量追踪数据结构
4. **trustcall 多轮提取的工程形态**（`knowledge/extraction.py:235-243`）：insert/update/delete 开关 + max_steps 迭代 + Done 工具 + json_doc_id 追踪——LLM 记忆对账协议的实现参考（Kairos 若未来开放「LLM 主导的对账通道」可借鉴）
5. **namespace 运行时占位符**（`knowledge/tools.py:117-125`）：`("memories", "{langgraph_user_id}")` config 注入 → 作用域物化——路径空间硬过滤（架构 §7.3a）的绑定机制参考

## 存疑与未验证
- commit SHA 未记录；star 数未独立核对
- trustcall 库的提取质量与多轮迭代的实际行为未运行验证（未执行）
- prompts/ 三优化器的实际效果（Gradient vs Metaprompt vs PromptMemory 适用场景）无 benchmark 验证
- ReflectionExecutor 的调度与记忆提取的并发一致性未深读（reflection.py 细节只读了结构）
- `graph_rag.py` 为**注释掉的演示代码**（全文在注释块内）——README 未提 graph RAG，该文件不可作为能力证据（注意与 Graphiti 等区分）
- 「Native integration with LangGraph Platform」依赖 LangGraph 生态（BaseStore），脱离 LangGraph 的独立使用面未验证
- 记忆指令与 trustcall 均依赖 LLM 能力（小模型可能无法完成多轮对账）——`CLAUDE.md` 无此限制声明，但 README 未讨论模型下限

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
| 0.0.42 | 2026-08-07 | 0.0.2（0.0.42 批次）审计修复：引用占位补全。 |
