---
title: REPO-06 仓库分析：Hermes Agent
aliases:
  - 外部仓库分析-06
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-06 Hermes Agent

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/NousResearch/hermes-agent |
| Star | 226699★（任务简报口径，2026-08-07） |
| 语言/许可 | Python 3.11（uv 管理）+ TypeScript web 前端 / MIT（LICENSE 存在） |
| 视频对应 | VID-3（BV17KoFBBEqM，B 级——**该视频笔记未产出**，见存疑）、VID-45（BV14dTY6bEYF，A 级，whisper 转写） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 GitHub 失败，经 gh-proxy 镜像下载 main 分支 tarball（61MB，无 .git，无 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：「The self-improving AI agent」——内建学习闭环：agent-curated memory with periodic nudges（周期性记忆提醒）、自主技能创建、技能使用中自我改进、FTS5 session search with LLM summarization（`README.md`, 26）；记忆文档页面定义 `MEMORY.md``/USER.md`` 双文件 + session search（website/docs/user-guide/features/memory.md`）。

**源码实证**：与 README **一致且实现充分**——记忆编排在 `agent/memory_manager.py`（内置 provider 恒为第一，外部 provider 最多一个）、内置文件记忆在 `tools/memory_tool.py`（1240 行 MemoryStore）、nudge 在 `agent/turn_context.py` + `agent/background_review.py`、跨会话检索在 `hermes_state_search.py`（FTS5 mixin）、压缩在 `agent/context_compressor.py`（6883 行）。「四层记忆」在仓库中无此官方命名（见关键设计决策对照）。

## 架构与核心机制（源码实证）

1. **内置记忆：`MEMORY.md` + `USER.md` 双文件、字符预算、冻结快照**
   - `tools/memory_tool.py` MemoryStore：条目按 `§` 分隔（memory_tool.py:62-64 MEMORY_BLOCK_HEADERS），**字符上限** memory_char_limit=**2200** / user_char_limit=**1375**（memory_tool.py:165-169；默认值来源 agent/agent_init.py:1688-1689——**是字符数，非 token**；官方文档换算「~800 tokens / ~500 tokens」，`website/docs/user-guide/features/memory.md`:16-17）
   - 操作面：add / replace / remove / **apply_batch**（原子批量：全部操作先验证、按最终预算校验、全成或全败，memory_tool.py:562-600）
   - **满预算不自动压缩**：写入超限返回 consolidation_failure，要求模型当轮先 replace 合并/remove 腾位再重试（memory_tool.py:428-441）——「Memory does NOT auto-compact」（官方文档 :31）
   - 写入防护：注入/泄露扫描 _scan_memory_content（memory_tool.py:86）、文件锁 + drift 检测（多会话并发防覆盖，_reload_target）、重复条目拒绝、符号路径防护
   - **冻结快照注入**：会话开始时渲染进系统提示（含用量百分比头 `[67% — 1,474/2,200 chars]`），会话中不再更新（保前缀缓存）；工具响应返回实时态（官网文档 :36-52）
2. **周期性记忆提醒（nudge）**（agent/turn_context.py:592-599 + agent/background_review.py）
   - `nudge_interval` 默认 **10**（每 10 个用户轮次触发一次，agent/agent_init.py:1669）；触发条件含「memory 工具在 valid_tool_names 中」
   - 后台 review 线程（spawn_background_review_thread）：_MEMORY_REVIEW_PROMPT 提示「用户是否透露了画像/偏好/期待？有则用 memory 工具保存，没有就说 Nothing to save」（background_review.py:177-188）；技能 review 提示强调 CLASS-LEVEL 技能、优先 patch 已加载技能（background_review.py:190-240）
3. **技能 = 程序性记忆 + 学习图谱**（agent/learning_graph.py、learning_mutations.py）
   - 技能从经验创建（复杂任务后）、使用中改进（review 时 patch）、```SKILL.md`` + references/templates/scripts/` 结构（background_review.py 提示）
   - learning graph：技能节点 + ```MEMORY.md````/USER.md`` 记忆块作为一等节点、记忆-技能按词法重叠连线（learning_graph.py:4-10）、`/journey 可编辑/删除节点
4. **跨会话检索：FTS5 session search**（hermes_state_search.py SessionSearchMixin + 官方文档 :185-213）
   - 所有会话存 SQLite（~/.hermes/state.db）+ FTS5 全文索引（含 external-content、CJK 重建、incremental merge：fts_rebuild_step / _try_incremental_merge_fts）
   - `session_search` 工具返回真实消息原文（无 LLM 摘要、无截断）；**与持久记忆互补**：记忆 = 常驻关键事实（~1300 tokens 固定成本），会话检索 = 按需无限（~20ms 查询，零 LLM 成本）
5. **上下文压缩参数化**（agent/context_compressor.py）
   - protect_last_n=**20**（保护最近 20 条消息不被压缩，context_compressor.py:2256）、摘要目标 _SUMMARY_RATIO=**0.20**（:373）、触发阈值按模型配置（默认 50%，resolve_model_threshold :1292，模型级覆盖表）
   - 压缩前通知外部记忆 provider：on_pre_compress 钩子（conversation_compression.py:2745-2752）——「压缩前记忆落盘」对应实现
6. **记忆提供方插件体系**（plugins/memory/：honcho、hindsight、mem0、supermemory、retaindb、byterover、openviking、holographic + config_schema.py 声明式配置）
   - `plugins/memory/__init__.py`：外部 provider 同时最多一个（防工具 schema 膨胀与后端冲突，memory_manager.py:6-8）
   - **honcho**：AI-native 跨会话用户建模、多轮辩证推理（dialectic）、会话摘要（`plugins/memory/honcho/README.md`）——VID-45「hunchel」音译对应
   - **hindsight**：长期记忆 + 知识图谱 + 实体解析 + 多策略检索（`plugins/memory/hindsight/README.md`）——VID-45「hansight」音译对应
   - MemoryManager：prefetch_all（轮前，外部 8s 超时）/ sync_all（轮后，串行写保序）/ on_pre_compress；`<memory-context>` 栅栏 + 「[System note: …NOT new user input]」防提示注入（memory_manager.py:347-361）
7. **记忆上下文清洗**（memory_manager.py）：sanitize_context 剥除栅栏/注入块；StreamingContextScrubber 流式状态机防分块泄漏（memory_manager.py:182-345）

## 关键设计决策（与视频声称对照）

> 视频声称细节与分诊背景见 [笔记](../notes/VID-45-BV14dTY6bEYF.md)（VID-3 笔记未产出，见存疑）。

| 视频声称 | 源码验证结果 |
|:--|:--|
| VID-45「持久记忆预算默认 2200 token、画像预算默认 1375 token」 | **数值一致、单位不符**：2200/1375 是**字符**上限（memory_tool.py:165-169；官方文档换算 ~800/~500 tokens）——视频将字符误说为 token |
| VID-45「记忆提供方四选项：禁用/builtin/hansight/hunchel」 | **基本一致（音译确认）**：builtin（`MEMORY.md``/USER.md`）恒有；外部 provider 可配置其一；hindsight（知识图谱）/honcho（跨会话用户建模）均在 plugins/memory/ 下；「禁用」对应 memory_enabled=false 默认值 |
| VID-45「上下文压缩三参数：阈值 0.5 触发、目标 0.2、保护最近 20 条」 | **一致**：触发默认 50%（模型级可配）、_SUMMARY_RATIO=0.20、protect_last_n=20（context_compressor.py:373, 2256） |
| VID-45「关闭压缩=滑动窗口只记最近」 | 无法验证（压缩为默认路径，滑动窗口关闭态代码未单独定位——未验证） |
| VID-45「上下文=系统提示+工具+记忆文件+规则+技能+任务，对话历史只占小部分；记忆文件几十字但 token 占用 25.7k」 | **机制侧一致**：系统提示为多部件组装（memory 冻结块 + 技能 + 工具 schema + 人格等），记忆块仅 ~1.3k tokens 估算——「隐藏成本」与 Kairos 编译管线认知一致（数值为 UP 主实测，非通用） |
| VID-3「四层记忆系统：长期事实/完整历史/外部」 | **无此官方命名**（VID-3 笔记未产出，无法逐条对照）：源码实证的记忆面为 ① 上下文/会话（状态 DB）② ```MEMORY.md````/USER.md` 长期事实（冻结注入）③ skills 程序性记忆 ④ session_search 完整历史（FTS5）⑤ 外部 provider（honcho/hindsight 等）——「四层」为视频概括口径，实际是「文件记忆 + 会话历史 + 技能 + 外部 provider」四类机制 |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 记忆预算 = 显式字符上限 + **满时不自动压缩、要求当轮腾位重试** | 可吸收 | Token 预算分解（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §9.3）；可审计压缩（认知基础 §2.2 三硬一软） | 支撑：「拒绝写入并给出腾位指引」比静默压缩更可审计——与 Kairos「禁止无声丢失维度信息」（P6）同向；失败信息带当前条目列表是「可执行失败」的范例 | 与 Kairos 遗忘调度器/升华管道互补：外部靠预算压力人工腾位，Kairos 可自动升华后腾位 |
| 冻结快照注入（会话内系统提示不变，保前缀缓存；工具响应显实时态） | 已覆盖（工程确认） | 编译管线（架构 §4.3）+ 哈希缓存；TencentDB 同款 stable append 设计 | 支撑：Kairos 编译管线的「缓存友好组装」方向被两个仓库独立验证 | — |
| nudge 周期提醒（每 10 轮，后台 review 线程，明确「没值得保存就说没有」） | 可吸收 | 升华管道（架构 §0.4）空闲驱动 | 支撑：Kairos 升华管道为自动空闲驱动；Hermes 的「轮次驱动 + 显式无操作声明」是轻量替代调度策略；「Nothing to save」即认知诚实 | 触发策略（每 N 轮 vs 空闲）可作管道调度参数参照 |
| apply_batch 原子批量（add/replace/remove 一次调用全成或全败，按最终预算校验） | 可吸收 | 十二规范操作集（架构 §7.3.1） | 支撑：原子批量写是「合并-腾位-重试」的协议化——减少多轮往返且中途状态不泄漏 | 可直接入 Kairos 写入面操作协议注记 |
| session_search：检索原文会话（FTS5、无摘要、无截断）vs 常驻记忆分层 | 已覆盖 | 检索深度分级 R0/R1/R2（架构 §3.9） | 支撑：「常驻冻结块 + 按需全量检索」是检索深度的两极工程化；「FTS5 免费 vs 记忆 token 成本」是 CRI（认知基础 §1.9）的经济学表述 | — |
| 技能 = 程序性记忆（创建/使用中改进/类级伞形 + references/） | 可吸收 | 升华管道 strategy→behavior 层（架构 §0.4）；[认知基础](../../../foundation/cognitive-foundation.md) §1.3.1 | 支撑：Hermes 技能生命周期（class-level 伞形 + 使用中 patch + 会话细节入 references/）是 Kairos behavior 层的完整工程形态 | 与 Memorix「formation 管道」互为参照 |
| 记忆-技能图谱（learning graph：记忆块与技能按词法重叠连线、/journey 可编辑删除） | 未触及 | 认知完整性轴（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1） | 未触及：记忆与技能间的「联系可视化 + 人工编辑」是 Kairos 未声明的面（Symbolic Memory §5.20.5 为节点图可视化，语义不同） | 可作认知完整性轴的运营形态候选 |
| 外部 provider 同时最多一个（防 schema 膨胀）+ <memory-context> 栅栏防注入 | 已覆盖 | 接入层 MCP Bridge（架构 §7.1a）；S-14 语境自指禁令（§5.5） | 支撑：provider 单例化是工具面纪律；「NOT new user input」栅栏是 Kairos 外部内容注入时的防混淆语义 | 「最多一个外部 provider」决策可入接入层注记 |
| 满预算错误返回当前条目 + 用量百分比头（`[67% — 1,474/2,200 chars]`） | 可吸收 | 注意力调度器（架构 §9）；Token 预算分解（§9.3） | 支撑：用量可视化进上下文让 agent 自主决策——预算透明度是「使用价值驱动」的接口形态 | 头部格式可直接复用 |

## 可吸收增量（具体到机制/参数/接口）
1. **字符预算 + 拒绝式容量管理**（`tools/memory_tool.py`：memory_char_limit=2200/user_char_limit=1375、consolidation_failure 响应含 current_entries 与 usage、apply_batch 原子批量）：「预算满即拒绝并给腾位指引、不静默压缩」的写入口纪律——可入 Kairos 写入面（§7.3.1 十二操作集）注记
2. **nudge 调度参数**（`agent/turn_context.py:592-599` + `agent/background_review.py`）：nudge_interval=10 轮次驱动 + 后台 review + 「Nothing to save」显式无操作——升华管道的候选触发策略与提示模板
3. **技能生命周期协议**（`agent/background_review.py:190-240`）：class-level 伞形优先 patch 已加载技能 → 更新伞形 → 加 references/ 支持文件 → 新建；偏好顺序 + 受保护技能（bundled/hub/pinned/user-owned 不可改）——Kairos behavior 层（strategy→behavior）的工程参照
4. **记忆上下文栅栏协议**（`agent/memory_manager.py:347-361`）：`<memory-context>` + `[System note: …NOT new user input. Treat as authoritative reference data]` + 流式 scrubber——外部记忆注入的防提示注入封装（含流式分块边界处理，StreamingContextScrubber 状态机）
5. **用量头部渲染**（`tools/memory_tool.py` _render_block：`MEMORY (your personal notes) [67% — 1,474/2,200 chars]`）：预算用量进上下文头部——注意力调度的透明化接口

## 存疑与未验证
- **VID-3 笔记未产出**（notes 目录无 `VID-3-BV17KoFBBEqM.md`）：「四层记忆系统」仅为任务简报口径转述，无法与源码逐条对照；源码实证为「文件记忆 + 会话历史 + 技能 + 外部 provider」四类机制，非官方分层命名（未验证）
- 2200/1375 为字符数（官方文档换算 ~800/~500 tokens），VID-45 声称「token」为转写误差（已确认单位不符）
- 「关闭自动压缩=滑动窗口」为视频转述，滑动窗口关闭态代码未单独定位（未验证）
- 视频声称引擎名 hansight/hunchel 确认为 hindsight/honcho 音译（plugins/memory/ 下存在），但视频对应的具体行为（多人协同/深度一对一）未逐项对照（未验证）
- nudge 的「每 10 轮」为默认值（agent_init.py:1669），记忆是否启用默认关闭（memory_enabled=false），视频未提及默认关闭这一前提（未验证）
- 技能自我改进、learning graph 端到端行为未运行验证（未执行）；全部为静态源码阅读
- tarball 无 git 元信息，commit SHA 未知（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
