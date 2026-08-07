---
title: REPO-07 仓库分析：TencentDB Agent Memory
aliases:
  - 外部仓库分析-07
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-07 TencentDB Agent Memory

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/TencentCloud/TencentDB-Agent-Memory |
| Star | 16670★（任务简报口径，2026-08-07） |
| 语言/许可 | TypeScript（OpenClaw 插件，npm @tencentdb-agent-memory/memory-tencentdb）+ Python（Hermes provider）/ MIT（LICENSE 明示「licensed under the MIT」，Copyright 2026 Tencent） |
| 视频对应 | VID-13（BV1tiuA6mENb）、VID-21（BV1V9Lp68Ey1）、VID-23（BV18kDjBxEYR）——三者笔记见 [notes/](../notes/) 对应文件，见存疑 |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 GitHub 失败，经 gh-proxy 镜像下载 main 分支 tarball（2.3MB，无 .git，无 commit SHA）；版本 0.3.6（package.json） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：「Symbolic short-term memory + layered long-term memory」——符号短时记忆（把重工具日志卸载为紧凑 Mermaid 符号，降 token 提成功率）+ 分层长期记忆（把碎片对话蒸馏为结构化 persona 与场景，拒绝平面向量堆）；基准声称：OpenClaw 集成后 token 降低 61.38%、通过率 +51.52%、PersonaMem 准确率 48%→76%（`README.md`）；「Lower layers preserve evidence; upper layers preserve structure」+「Full traceability and lossless recovery」（`README.md`）。

**源码实证**：与 README **高度一致**——L0→L1→L2→L3 管道完整落地（src/core/record/l1-extractor.ts 等 12666 行核心 + offload 3730 行）；「reject flat storage」不是口号：异质存储 + 下钻链在代码中可实现（result_ref/node_id 链路）。基准数字为 README 自述（未复现）。

## 架构与核心机制（源码实证）

1. **四层语义金字塔（长期记忆）**（`README.md` + src/core/ 目录结构）
   - L0 Conversation（原始对话，SQLite l0_conversations + l0_vec + l0_fts，src/core/store/sqlite.ts:648-700）
   - L1 Atom（原子事实，l1_records + l1_vec（vec0 向量表）+ l1_fts（FTS5 v2 schema），sqlite.ts:561-800）；类型枚举 persona/episodic/instruction（preference 折入 persona，l1-extractor.ts:516-528）
   - L2 Scenario（场景块：scene_blocks/*.md + scene_index.json，src/core/scene/scene-index.ts + scene-extractor.ts）
   - L3 Persona（`persona.md`，src/core/persona/persona-generator.ts，增量更新 + BackupManager 保留 3 份）
   - **异质存储**：底层（L0/L1）数据库全文本检索；顶层（L2/L3）人类可读 Markdown 白盒可查（`README.md`:79；`~/.openclaw/memory-tdai/` 目录结构）
2. **L1 提取管道：单次 LLM 调用 + 批量冲突检测**（src/core/record/l1-extractor.ts）
   - 质量门控（shouldExtractL1：长度/符号/提示注入过滤，l1-extractor.ts:129-135）+ 新消息 10 条/背景 5 条拆分 + 场景分割与记忆提取合并为一次 LLM JSON 调用（EXTRACT_MEMORIES_SYSTEM_PROMPT，l1-extraction.ts）
   - **批量冲突检测**（l1-dedup.ts：v4 移除 JSONL Jaccard 回退）——两级候选召回：向量召回（Tier 1，topK=5）→ FTS BM25（Tier 2 降级）→ 均不可用则跳过 dedup 直存（l1-dedup.ts:82-135）；候选池 + 单次 LLM 判断（store/merge/update/conflict 决策，l1-writer.ts）
   - 写入含 embedding（l1-writer.ts writeMemory）+ 会话上限 maxMemoriesPerSession=20（默认）
3. **L2 场景块：LLM agent 沙箱读写**（src/core/scene/scene-extractor.ts）
   - LLM 以工具模式自主读写 scene_blocks/*.md；**workspaceDir 沙箱**限定仅场景目录可见（系统文件 `checkpoint/scene_index/persona.md` 对 LLM 物理不可见，scene-extractor.ts:10-17）——提取/归档/导航同步，filename-normalizer 归一化
4. **L3 画像：增量生成 + 备份**（src/core/persona/persona-generator.ts）
   - 只取「自上次生成后变化的场景」（按 scene_index.updated > checkpoint.last_persona_time，persona-generator.ts:82-89）；first/incremental 双模式；备份 3 份防写坏
5. **触发调度（pipeline-manager.ts）**
   - L1：everyNConversations=**5**（每 5 轮）或空闲 l1IdleTimeoutSeconds=**600** 触发；warmup 指数阈值 **1→2→4→8→…→N**（新会话第 1 轮即触发 L1，doubling 直至稳态，pipeline-manager.ts:55-62）
   - L2：L1 完成后延迟触发（l2MinIntervalSeconds=900）；L3：persona.triggerEveryN=**50**（每 50 条新记忆）
   - 会话结束 flushSession 只清本会话（TdaiCore.handleSessionEnd 语义与 destroy 分离，tdai-core.ts:328-364）
6. **混合检索：BM25 + 向量 + RRF 融合、降级链、超时不阻塞**（src/core/hooks/auto-recall.ts + src/core/tools/memory-search.ts）
   - hybrid 默认：FTS5 BM25 与向量**并行**，RRF 融合（k=60，memory-search.ts:47-76）；TCVDB 后端支持服务端原生混合（nativeHybridSearch 短路，auto-recall.ts:377-384）
   - 降级链：embedding 不可用 → keyword（FTS5，无内存回退，auto-recall.ts:347-352）；FTS 不可用 → embedding-only；召回整体超时 5s → 跳过注入不阻塞对话（recall.timeoutMs=5000，auto-recall.ts:83-100）
   - **三层注入分层**：L1 记忆 = prependContext（动态，注入用户提示前缀，不破坏系统提示缓存）；L3 persona + L2 scene navigation + 工具指南 = appendSystemContext（稳定，注入系统提示尾，可缓存）（auto-recall.ts:186-219）——显式「缓存友好组装」
   - 召回预算：maxResults=5、scoreThreshold=0.3、maxCharsPerMemory/maxTotalRecallChars（0=不限制，applyRecallBudget 截断/丢弃并计数）；记忆工具调用限制每轮 ≤3 次（MEMORY_TOOLS_GUIDE，auto-recall.ts:44-48）
7. **符号短时记忆：Mermaid canvas + node_id 追踪 + 上下文卸载**（src/offload/ + ```README.md```）
   - 工具日志卸载到 refs/*.md，上下文只留 Mermaid 任务图（mmdMaxTokenRatio=0.2）；agent 按 node_id grep 取原文（result_ref 链路）；mildOffloadRatio=0.5 / aggressiveCompressRatio=0.85（上下文窗口占比触发）
   - 存储（storage.ts 664 行）、状态机（state-manager.ts）、回收（reclaimer.ts）、会话注册（session-registry.ts）
8. **双宿主适配**：OpenClaw 插件（in-process TdaiCore + OpenClawHostAdapter）与 Hermes provider（Python client.py → HTTP Gateway :8420，src/gateway/server.ts；可加 Bearer 鉴权）——HostAdapter 抽象使核心与宿主解耦（tdai-core.ts:22-33）

## 关键设计决策（与视频声称对照）

> 对应视频 VID-13/21/23 均为 C 级串台素材且笔记未产出（ 等不存在），下表仅能对照视频标题口径；完整机制以源码实证为准。

| 视频声称 | 源码验证结果 |
|:--|:--|
| VID-13/21/23「分层索引架构、跨会话记忆」（C 级串台，仅标题/元信息可信） | **方向一致**：L0-L3 语义金字塔 + 每层独立索引（FTS5/vec0）+ 跨会话（sessionKey 维度记忆+画像）均实证存在；但三层视频均为 C 级素材无字幕，无法逐条对照（见存疑） |
| README「reject flat storage」（拒绝平面向量堆） | **一致**：L0/L1 数据库 + L2/L3 Markdown 异质存储；「上保结构、下保证据」+ 下钻链（Persona → Scene → Atom → Conversation）在代码中可走通（result_ref/node_id） |
| README「lossless recovery / 全链路可追溯」 | **基本一致（工程实现）**：下钻链存在；「不可逆压缩不存在」在 L2/L3 层成立（Markdown 可读），但 L1 提取本身仍是 LLM 有损蒸馏（原子事实≠原文）——「lossless」指追溯路径而非内容无损 |
| README 基准（token −61.38%、通过率 +51.52%、PersonaMem 48%→76%） | 无法验证（README 自述，未附复现脚本逐项核验——未执行） |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| **语义金字塔 L0→L1→L2→L3（原文→原子事实→场景→画像）+ 异质存储（底库顶文）** | **可吸收（强）** | 升华管道 raw→item→strategy→behavior（[架构](../../../foundation/architecture-v0.1.0.md) §0.4）；六层架构分层 | 支撑：L0→L1 对应 raw→item（LLM 提取+冲突检测），L2→L3 对应 item→strategy/behavior（场景聚合+画像）；「底层数据库全文本 + 顶层 Markdown 白盒」与 Kairos 存储层（§5）+ 宪法主权面人类可读（§1）双面要求契合 | 外部把「场景」作为中间聚合层（L2），Kairos 无显式场景层——可作升华管道的中层结构参考 |
| **每层独立索引（FTS5 + vec0 双索引并存）** | 可吸收 | 三信号混合检索（架构 §7.3a）；双模式索引后端（pgvector/sqlite-vec） | 支撑：层内双索引 + RRF 融合是 §7.3a 的工程化；Kairos 四链路检索（§7.3a 口径）可参照「每层独立索引、层间按需下钻」 | — |
| **批量冲突检测：向量候选召回 + 单次 LLM 批量判断（store/merge/update/conflict）** | **可吸收（强）** | 见证→使用仲裁差异检验（架构 §5.5）；GSPO 聚类去重（§7.3b） | 支撑：新记忆 vs 既有记忆的「批量冲突决策」是 Kairos 差异检验（11 步）的写入侧补强——Kairos 差异检验聚焦使用权重回写，写入侧「新旧记忆冲突裁决」未显式声明 | 决策枚举（store/merge/update/conflict）可对照 §5.5 blocked/degraded/pruned/rollback 语义 |
| **L2 场景块 LLM agent 沙箱（workspaceDir 限定可见范围）** | 可吸收 | 安全红线（架构 §8 S-01~S-19）；监督平面（§1.7） | 支撑：让 LLM 直接写记忆文件但限定可见目录——「受控写面」的安全边界工程化；Kairos 监督平面可参照「写面沙箱」声明 | 与 Kairos 升华管道「LLM 判断 + 确定性落盘」分工可互参 |
| **三层注入分层（L1 动态 prepend / L3+L2 静态 append 保缓存）** | 已覆盖（工程确认） | 编译管线多阶段组装（架构 §4.3）；Token 预算分解（§9.3） | 支撑：动态/静态分面组装（Hermes 冻结快照为另一解）——两个仓库独立收敛到「缓存友好组装」 | 可入编译管线注记：按「变化频率」分面 |
| **召回超时不阻塞（5s 跳过注入）+ 工具调用限次（≤3/轮）** | 已覆盖 | 探索预算独立（S-12，架构 §8）；外部信号非依赖（T-002 姿态） | 支撑：检索失败/超时不得阻塞主流程——与 Kairos 组件降级契约（§10.17）同向 | 超时参数 5s 为工程参考 |
| **warmup 指数触发（1→2→4→8→N）+ 空闲超时触发** | 可吸收 | 升华管道空闲驱动（架构 §0.4）；探索预算独立 | 支撑：L1 触发调度（轮次 + 空闲双通道 + 新会话快速预热）比 Kairos「空闲驱动」声明更完整 | 调度参数（5 轮/600s/指数翻倍）可入升华管道调度注记 |
| **L3 画像增量生成（只处理变化场景）+ 备份 3 份** | 已覆盖 | 存储层一致性检查（架构 §5.16）；ADD-only（§7.3g） | 支撑：增量更新 + 备份是「可审计压缩」的落盘侧实践 | — |
| **活动时间双语义（点时间 timestamp / 段时间 activity_start~end）注入检索结果** | 可吸收 | 时间轴（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）物理衰减+逻辑因果双轴 | 支撑：记忆行 `(活动时间: 2025-05-01 ~ 2025-05-10)` 把「事件时段」作为一等元数据注入上下文——Kairos 时间双轴以存储侧为主，检索结果的时段渲染未声明 | 可入时间轴注记 |
| **Mermaid 符号短时记忆 + node_id 下钻** | 张力 | 上下文腐烂 CRI（认知基础 §1.9）压缩侧；检索深度分级 R0/R1/R2（架构 §3.9） | 支撑：符号图是压缩的极端形态（几百 token 承载任务态）；**挑战**：Mermaid 图质量依赖 LLM 且非标准语义，Kairos 以结构化契约（§7.0 结构化通信单元）承载任务态更稳 | 可作为 CRI 治理的激进压缩参考案例，不建议直接吸收格式 |
| **TCVDB 原生混合搜索（服务端 dense+sparse+RRF 单次调用）** | 可吸收 | 双模式索引后端（§7.3a） | 支撑：云后端把混合检索下沉服务端、省本地 embedding 调用——与 Kairos pgvector 后端演进同向 | — |

## 可吸收增量（具体到机制/参数/接口）
1. **L1 批量冲突检测协议**（`src/core/record/l1-dedup.ts`）：向量候选召回（topK=5）→ FTS 降级 → 单次 LLM 批量判断 store/merge/update/conflict；候选池 + 决策一次性返回——Kairos 写入侧（§7.3.1 十二规范操作集）「新旧记忆冲突裁决」的实现参照
2. **L2 场景聚合层**（`src/core/scene/scene-extractor.ts` + scene-index.ts）：场景块 Markdown + 索引 + 导航注入——升华管道 item→strategy 之间的中间聚合层结构参考；LLM 写面沙箱（workspaceDir=scene_blocks/）直接可入安全红线注记
3. **pipeline 触发调度参数集**（`src/utils/pipeline-manager.ts`）：everyNConversations=5 + idle 600s + warmup 1→2→4→8 指数 + L2 最小间隔 900s + L3 每 50 条——升华管道「轮次+空闲+预热」三通道调度
4. **三层注入分面协议**（`src/core/hooks/auto-recall.ts:186-219`）：动态面（L1，prepend）+ 静态面（persona/scene/tools-guide，append）+ 缓存友好声明——编译管线（§4.3）「按变化频率分面」的直接实现
5. **活动时间元数据渲染**（`src/core/hooks/auto-recall.ts` formatMemoryLine：点时间/段时间三态优雅降级）：检索结果携带时段语义的注入格式
6. **语境隔离参数**（`openclaw.plugin.json` 配置面）：offload.mildOffloadRatio=0.5/aggressiveCompressRatio=0.85/mmdMaxTokenRatio=0.2；bm25.language=zh（jieba）/en——CRI 治理与 BM25 中文分词的工程参考值

## 存疑与未验证
- VID-13/21/23 原为 C 级串台素材（后经 whisper 重转写成功），笔记已产出；「分层索引架构/跨会话记忆」部分来自任务简报转述与视频标题，逐条机制对照以笔记标注为限（未验证）
- 基准数字（token −61.38%、通过率 +51.52%、PersonaMem 48%→76%）为 README 自述（```README.md```），未附完整复现脚本逐项核验（未执行）
- 「lossless recovery」为口径表述：L1 提取本身是 LLM 有损蒸馏（原子事实≠原文），「无损」指追溯链而非内容保真——如实记录口径与实现的偏差
- warmup 指数、空闲超时等调度行为基于源码静态阅读，未运行验证（未执行）
- 插件依赖 OpenClaw/Hermes 宿主运行时，本环境未安装宿主，端到端未验证（未执行）
- tarball 无 git 元信息，commit SHA 未知（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
| 0.0.42 | 2026-08-07 | 0.0.2（0.0.42 批次）审计修复：VID-13/21/23 笔记状态更新（已产出，串台重转写成功）。 |
