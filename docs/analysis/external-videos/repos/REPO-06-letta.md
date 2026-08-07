---
title: REPO-06 仓库分析：Letta（原 MemGPT）
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

# REPO-06 Letta（原 MemGPT）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/letta-ai/letta |
| Star | 24133★（任务简报口径，2026-08-07） |
| 语言/许可 | Python（FastAPI 服务端）/ Apache License（pyproject.toml `version="0.16.8"`） |
| 视频对应 | VID-39（BV1k65X6dExY，素材级别 A） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone 超时/中断，经 gh-proxy 下载 main 分支 tarball（无 .git，无 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：「Build AI with advanced memory that can learn and self-improve over time」。**关键披露**：README 开头 NOTE 声明——「This repository contains the legacy Letta server (the API server behind the Letta V1 API and SDKs). Active development has moved to the Letta Agent repo (letta-ai/letta-code)」（`README.md`）。即：本仓库是**旧版 MemGPT 架构的服务端**，当前活跃开发（letta-code 的 agent 形态、AF 文件、Agent SDK）已迁移到新仓库——本笔记分析对象以本仓库（v0.16.8 legacy server）为主，视频声称对照时区分口径。

**源码实证**：视频所述三层记忆（core/archival/recall）、sleep time compute、memory blocks 自读自改均有真实实现（详见下节）。「agent file」在**本仓库**仅以导入/导出 schema 存在（`letta/schemas/agent_file.py` AgentSchema/FileAgentSchema），「AF 文件类似 Dockerfile」的声明式形态属新仓库（letta-code）概念，本仓库未实装。

## 架构与核心机制（源码实证，`letta/` 包）

1. **Core Memory（常驻窗口）**：
   - `Memory.blocks: List[Block]`（`letta/schemas/memory.py:68-77`）——块渲染为 `<memory_blocks>` XML（label/description/metadata/value/limit）进系统提示词（memory.py:143-173 `_render_memory_blocks_standard`），即**始终在上下文窗口内**
   - `Block`（`letta/schemas/block.py:13-85`）：`value` 文本 + `limit` 字符上限（`CORE_MEMORY_BLOCK_CHAR_LIMIT`）+ `read_only` 权限位 + `label`（human/persona/自定义）
   - **自编辑工具**（`letta/functions/function_sets/base.py`）：`core_memory_append`（246 行，追加）、`core_memory_replace`（263 行，精确字符串替换）、`rethink_memory`（283 行，整块重写）、`memory_replace`（311 行，带行号前缀防注入校验）——**智能体通过工具直接改写自己的记忆块**，视频声称属实
2. **Archival Memory（硬盘式）**：`Passage`（`letta/schemas/passage.py:35-77`：text + embedding（pgvector 下补零填充到 MAX_EMBEDDING_DIM）+ metadata + tags + archive_id）；`PassageManager.insert_passage`（`letta/services/passage_manager.py:543`）；工具 `archival_memory_insert` / `archival_memory_search`（`function_sets/base.py:164, 194`，语义相似度 + 标签过滤 + 时间范围过滤）
3. **Recall Memory（对话历史语义搜索）**：`conversation_search`（`function_sets/base.py:87-127`：「hybrid search (text + semantic similarity)」遍历历史消息，支持 roles/时间范围过滤）——recall = 对话历史 + 混合检索
4. **Sleep Time Compute（后台巩固）**：`enable_sleeptime` 开关 + `SleeptimeMultiAgentV4`（`letta/groups/sleeptime_multi_agent_v4.py`）：前台 `step()` 完成后自动调用 `run_sleeptime_agents()`（80 行）——按 `sleeptime_agent_frequency`（每 N 轮）把最近对话文本打包成 system-reminder 消息，**后台异步启动参与 agent**（`_issue_background_task` + `_participant_agent_step`，171-289 行），用 memory 工具集（`BASE_SLEEPTIME_TOOLS`：memory_replace/memory_insert/memory_rethink/memory_finish_edits，constants.py:135-143）更新记忆块——「智能体在后台自主整理巩固记忆」有完整实现链
5. **上下文窗口管理（压缩）**：`letta/services/summarizer/`（Summarizer / summarizer_sliding_window / thresholds.py `get_compaction_trigger_threshold`）——上下文超阈值触发对话摘要压缩（「虚拟内存/换页」类比的实际落点是 compaction 摘要）
6. **Git 版本化记忆（新特性）**：`letta/services/memory_repo/`（git_operations.py：git CLI 操作 + commit + 对象存储回写；block_markdown.py：块↔Markdown 文件投影）——记忆块以文件 + git commit 持久化，提供完整编辑历史
7. **存储**：PostgreSQL（alembic 迁移）+ pgvector（passage 语义索引）+ 可选 turbopuffer；`BlockManager` 管理块 CRUD

## 关键设计决策（与视频声称对照）
| 视频声称（VID-39） | 源码验证结果 |
|:--|:--|
| 「三层记忆：core 常驻窗口 / archival 硬盘式 / recall 对话历史+语义搜索」 | **一致**：三层均有实现（core=memory.py 块渲染进提示词；archival=passage.py+passage_manager；recall=conversation_search 混合检索） |
| 「core memory 始终在上下文窗口内」 | **一致（简化口径）**：块确实渲染进上下文；但智能体可用 archival_memory_insert/搜索在 core 与 archival 间搬运内容（视频存疑处亦自承此点，VID-39 笔记 59 行） |
| 「sleep time compute：后台自主运行整理巩固记忆」 | **一致**：SleeptimeMultiAgentV4 完整实现（前台 step 后异步 spawn 后台 agent，频率可控） |
| 「memory blocks：智能体自主读取和修改这些块，行为完全透明可审计」 | **部分一致**：自读自改属实（memory 工具集 + 块渲染含 chars_current/limit 元数据）；「可审计」部分——块编辑历史依赖 git-backed memory（新特性，非默认），默认模式下块被覆盖式更新，无强制审计日志 |
| 「agent file（AF 文件）：类似 Dockerfile 声明式定义完整状态」 | **不一致（仓库口径）**：本仓库仅 agent_file schema 导入/导出（agent_file.py）；「AF 文件」声明式形态属已迁移的 letta-code 新仓库（`README.md`），本仓库未实装——视频混淆了两仓库能力 |
| 「Letta EVAL 评估框架」 | **无法验证**：本仓库无 evaluation 目录（未随 tarball；无 tests/eval 框架发现）；Letta EVAL 概念归属新仓库 |
| 「模型无关，任何支持函数调用的 LLM」 | **基本一致**：llm_api 多 provider（OpenAI/Anthropic/Gemini/Ollama/本地等）；工具调用为硬依赖 |
| 「开源 16000+ stars / Python 与 TS 两个 SDK」 | **一致（star 数时效差异）**：现 24133★；Python（本仓库）+ TypeScript SDK（letta-client）存在 |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| sleep time compute：后台 agent 巩固记忆（频率可控、异步、低峰） | 可吸收 | 遗忘调度器定时扫描（[架构](../../../foundation/architecture-v0.1.0.md) §5）+ 防抖反射执行器（§2.6.3）；探索预算独立（§8） | 支撑：巩固成本归维护面、与探索预算独立兼容（同 VID-39 01:15 行分诊，[笔记](../notes/VID-39-BV1k65X6dExY.md)）；SleeptimeMultiAgentV4 的「每 N 轮 + 自上次处理点增量」是具体参数形态 | 增量：「自上次处理消息 ID 起增量巩固」（last_processed_message_id，sleeptime_multi_agent_v4.py:152）防重复巩固 |
| memory blocks 自读自改（工具直接改写记忆） | 张力 | 价值独立性公理（[认知基础](../../../foundation/cognitive-foundation.md) §2.1）；见证锚定主副本不可被无声改写（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 挑战：直接改写主副本违背「好用 ≠ 真实」隔离；Kairos 使用侧只能累积权重 | 与 VID-39 03:07 行分诊一致——不采纳「直接编辑记忆」，「记忆可读可审计」透明性主张可吸收 |
| 块级字符上限 + read_only 权限位 + 块元数据进上下文（chars_current/limit） | 可吸收 | 身份面常驻（[架构](../../../foundation/architecture-v0.1.0.md) §1）+ Token 预算分解（§9.3） | 支撑：显式限长与只读标记是常驻面的预算控制形态 | 增量：块级 read_only 标记 + 上下文内自曝当前占用（chars_current/chars_limit） |
| git 版本化记忆（块=文件 + commit 历史） | 可吸收 | 见证锚定强一致（[架构](../../../foundation/architecture-v0.1.0.md) §5.5）写后不可篡改 + 可审计压缩（[认知基础](../../../foundation/cognitive-foundation.md) §2.2 三硬一软） | 支撑：git commit 链是「编辑历史可审计」的现成工程形态——与 ADD-only 历史表同功能，但允许覆盖式编辑后仍留痕 | 增量：若未来允许使用侧受控编辑，git 式版本链是审计兜底形态；不改变「主副本不可无声改写」立场 |
| 精确字符串替换接口（memory_replace：old_string 精确匹配、拒绝行号前缀） | 可吸收 | 契约是运行时投影（[认知基础](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：最小侵入编辑接口（精确锚点替换而非整块重写）降低误改风险 | 增量：接口形态可作影子副本/使用侧受控更新的工程参考（若启用） |
| compaction 滑动窗口摘要（上下文超阈值触发） | 已覆盖 | 可审计压缩（[认知基础](../../../foundation/cognitive-foundation.md) §2.2）；升华管道 raw→item→strategy→behavior（§A.3）；知识加工区（[架构](../../../foundation/architecture-v0.1.0.md) §5.10） | 支撑：上下文窗口摘要即「压缩为稳定结构」，Kairos 升华管道语义更完整 | — |
| archival 语义检索 + recall 混合检索双通道 | 已覆盖 | 检索深度分级 R0/R1/R2（[架构](../../../foundation/architecture-v0.1.0.md) §3.9）；三信号混合检索（§7.3a） | 支撑：双通道即 Kairos 深度分级中「常驻浅检索 + 语义深检索」的分工 | — |
| 有状态 vs 无状态智能体（记忆随使用成长） | 已覆盖 | Kairos LTM 持久化（[架构](../../../foundation/architecture-v0.1.0.md) §5）即「有状态」立场 | 支撑 | 与 VID-39 00:36 行分诊一致 |

## 可吸收增量（具体到机制/参数/接口）
1. **sleep time 增量巩固协议**（`letta/groups/sleeptime_multi_agent_v4.py:132-168, 202-289`）：前台轮次后按 `sleeptime_agent_frequency` 触发；`last_processed_message_id` 记录上次处理点，只处理增量对话；后台 agent 用专用 memory 工具集（`BASE_SLEEPTIME_TOOLS`，constants.py:135-143）——Kairos 遗忘调度器可吸收「自上次处理点增量巩固」语义，避免每次全量扫描
2. **块级上下文自曝元数据**（`letta/schemas/memory.py:157-173`）：渲染时把 `chars_current`/`chars_limit`/`read_only` 写进可见上下文，让消费方（模型）自行感知预算——Kairos 身份面常驻（架构 §1）与 Token 预算分解（§9.3）的接口注记
3. **memory_replace 精确锚点编辑**（`letta/functions/function_sets/base.py:311-359`）：old_string 精确匹配 + 行号前缀拒绝（防模型把展示前缀当内容）+ 空串删除语义——最小侵入编辑接口规范
4. **git-backed memory**（`letta/services/memory_repo/git_operations.py:88-100`）：记忆=文件 + git commit + 对象存储回写——审计留痕的工程形态参照（用于「可审计」而非「可覆盖」）

## 存疑与未验证
- 本仓库 README 声明为 legacy server，活跃开发在 letta-ai/letta-code（新仓库未分析）——视频的「AF 文件」「Letta EVAL」等声称无法在本仓库验证（归属新仓库，未验证）
- Letta EVAL 评估框架在本仓库未找到（未验证；可能在新仓库或独立仓库）
- sleep time 的 `sleeptime_agent_frequency` 默认值/触发条件细节未运行验证（未执行）
- 块编辑默认模式无审计日志（除 git 模式）——「完全透明可审计」是视频乐观口径，与源码部分不符
- tarball 无 commit SHA，无法锚定具体版本（素材限制）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
