---
title: REPO-03 仓库分析：Memorix
aliases:
  - 外部仓库分析-03
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-03 Memorix

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/AVIDS2/memorix |
| Star | 613★（任务简报口径，2026-08-07） |
| 语言/许可 | TypeScript（bun，monorepo）/ Apache 2.0 |
| 视频对应 | VID-28（BV1oxNZ6uE6G，素材级别 A——字幕匹配，声称可信） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 GitHub 失败，经 gh-proxy 镜像下载 main 分支 tarball（无 .git，无 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：「Local-first shared memory layer for AI coding agents」——项目级共享记忆（SQLite 权威存储 + Orama 全文/向量检索，LLM 形成/嵌入为可选），跨 20+ agent（Claude Code/Codex/Cursor/Windsurf/Copilot/Gemini CLI/OpenCode/OpenClaw/Hermes 等，MCP/插件/钩子/skills 接入面）；能力含观察记忆、长期 curated 记忆、代码状态/代码记忆、Git 记忆、推理记忆、知识工作区、Memory Autopilot、编排（`README.md`）。

**源码实证**：与 README **高度一致且实现充分**——`src/memory/`、`src/store/`、`src/search/`、`src/git/`、`src/codegraph/`、`src/compact/` 等均为真实实现（约 30+ 核心模块）。这是 4 个仓库中**唯一核心机制全部开源**的（对比 supermemory 闭源引擎）。

## 架构与核心机制（源码实证）

1. **记忆模型：五维独立轴**（`docs/1.3-MEMORY-ARCHITECTURE.md` + `src/memory/long-term.ts`、`long-term-types.ts`）
   - 认知类 kind：episodic / semantic / procedural
   - 作用域 scope：project / user / team
   - 状态 state：candidate / qualified / approved / archived / superseded——**candidate 不进自动上下文**，qualify 需 ≥1 证据引用（语义/程序性条目禁止成为无证据摘要），approve 为单独人工操作（审计轨迹记录）
   - 来源 source：manual / agent / hook / git / test / code-state / workflow
   - 可移植性 portability：project-bound / portable——**portable 用户项拒绝项目类证据**（跨项目传播必须用户/手动证据）
   - 检索投递纪律：Workset 只收 qualified/approved；最多 3 条、固定子预算、给 `durable:<id>` 引用而非长叙事；语义回退预算 1.8s 超时、无重试、失败静默回退关键词（`src/memory/long-term.ts`：SEMANTIC_RETRIEVAL_TIMEOUT_MS=1800、MIN_SEMANTIC_SIMILARITY=0.58）
2. **形成管道：Extract → Resolve → Evaluate 三阶段**（`src/memory/formation/`：extract.ts / resolve.ts / evaluate.ts）
   - 规则基线模式（无 LLM 也能跑）+ LLM 增强模式（可选）
   - Resolve 四决策：new / merge / evolve / discard（阈值：merge>0.75、evolve>0.60+矛盾检测、重复>0.85 丢弃，`docs/MEMORY_FORMATION_PIPELINE.md`）
   - Evaluate 产出 valueCategory：core / contextual / ephemeral + reason
   - 写入前有 admission 门控（`src/memory/admission.ts`）：hook 自动捕获为 candidate，须「当前代码引用 ≥1」才自动合格（DURABLE_AUTOMATIC_TYPES）；legacy 记录保持旧投递行为
3. **保留/遗忘引擎**（`src/memory/retention.ts`）：
   - `score = baseImportance × e^(-ageDays/retentionPeriod) × accessBoost`；accessBoost = 1+0.1×accessCount，封顶 2.0（retention.ts:185-222）
   - importance→保留期：critical 365 天 / high 180 / medium 90 / low 30（retention.ts:26-31）；类型默认重要性表（gotcha/decision/trade-off/reasoning=high，retention.ts:42-54）；乘子：hook 来源 0.5×、git 来源 1.5×、ephemeral 0.5×、core 2.0×（retention.ts:74-88）；最低 7 天
   - **免疫规则**：critical / core / accessCount≥3 / 受保护 tag（keep/pinned...）永不自动归档；probe 类型永不免疫（retention.ts:113-134）
   - 三区生命周期：active / stale（>50% 保留期未访问）/ archive-candidate（>100% 未访问且不免疫）；**归档 = 原地置 status='archived'（可逆）**，非删除（retention.ts:504-541，批处理游标式 `archiveExpiredBatch`）
4. **检索：Orama 全文 + 可选向量 + 意图先验**（`src/store/orama-store.ts`、`src/search/intent-detector.ts`、`src/search/query-expansion.ts`）
   - hybrid 相似度阈值 0.45；命令日志硬过滤（`^(Ran:|Command:|Executed:)`）+ 软降级
   - **意图检测 7 类**（why/when/how/what_changed/problem/state/general）：关键词/正则零 LLM，返回类型→boost 乘子、字段权重、chronological 偏好（intent-detector.ts:16-31）——state 类意图（resume/progress）权重最高
   - 项目亲和度（`src/store/project-affinity.ts`）：跨项目检索按项目关键词相关性加权
5. **上下文续接：压缩检查点 + Workset**（`src/memory/compaction.ts`）
   - CompactionCheckpoint（native-summary 宿主原生摘要 / preflight 标记），`buildCompactionWorkset` 默认 420 token 预算（48-2000 可配），绝不全量回放 transcript，绝不让原生摘要自动升级为持久知识
6. **Git 记忆**（`src/git/extractor.ts` + `noise-filter.ts`）：commit/diff → 工程事实（what changed/where/why matters）；噪音过滤启发式（merge 提交、低信号消息、纯 lockfile/生成文件提交，全可配置）
7. **代码记忆/新鲜度**（`src/codegraph/`、`src/memory/freshness.ts`）：代码快照版本化、文件/符号链接、新鲜度检查（引用的代码被改 → 记忆标记过期/可疑）
8. **存储**（`src/store/`）：SQLite 权威（sqlite-store.ts/sqlite-db.ts）+ Orama 索引 + JSON 兼容层（persistence-json.ts）；obs-store 观察记忆、graph-store/graph.ts 实体知识图谱、chat-store 会话、compaction-checkpoint-store

## 关键设计决策（与视频声称对照）
| 视频声称（VID-28） | 源码验证结果 |
|:--|:--|
| 「记忆跟着项目走，住在 git 项目根目录下」 | **一致**：README「The memory lives under the Git project」（`README.md`）；观察记忆 projectId 作用域；「agent 是临时工、项目记忆是固定资产」为视频转述 |
| 「四层记忆：观察/推理/git/代码」 | **基本一致（口径简化）**：观察记忆（observations）、推理记忆（`memorix_store_reasoning`、`src/cli/commands/reasoning.ts`）、Git 记忆（src/git/）、代码记忆（src/codegraph/）均存在；但实际是「多种 store + 治理管道」，且 1.3 又引入第五类 curated long-term 层——「四层」是营销口径，非完整模型 |
| 「新鲜度检查：代码被改→记忆标记过期/可疑」 | **一致**：`src/memory/freshness.ts` + codegraph 引用检查 |
| 「local first：SQLite 权威 + 本地检索，LLM 可选」 | **一致**：SQLite 权威 + Orama 本地全文（`README.md`）；formation 双模式、embedding provider 可插拔 |
| 「默认 7 个 MCP 工具，渐进披露」 | **一致**：micro profile 默认 7 工具（`CLAUDE.md` 工具表 + `src/mcp` 相关）；light/team/pro 按需打开 |
| 「autopilot 按任务类型定制简报 + 过期记忆进警示车道」 | **一致**：Memory Autopilot（`memorix context`）、task-lensed brief（bugfix/feature/release/onboarding/refactor/docs/test/general）、Workset 预算与过滤 |
| 「aroma 检索库」 | **一致（音译）**：Orama（`@orama/orama`，orama-store.ts:4-8） |
| 「git 只记录了改了什么，没记录为什么」 | **一致**：为 Git Memory 模块的设计动机（extractor.ts:3-7「Git records code changes. Memorix records engineering knowledge」） |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 记忆五维独立轴（kind/scope/state/source/portability）+ 状态机（candidate→qualified→approved→archived→superseded） | **可吸收（强）** | 五轴度量模型（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；六级辞典式排序链无标量聚合（§2.1） | 支撑：Memorix 的「轴独立+状态机」方法论与 Kairos 五轴同构；**状态轴显式化**（candidate 不进自动上下文、approve 人工+审计）是 Kairos 未显式化的治理维度 | 记忆「资格化」管道与 Kairos 见证锚定/宪法主权面（架构 §1）呼应 |
| 证据门控：qualify 需 ≥1 证据引用、无证据不得成合格记忆、portable 项拒绝项目类证据 | 可吸收 | 见证价值轴/见证锚定（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；S-14 语境自指禁令（架构 §5.5） | 支撑：证据引用计数门槛是「见证锚定」的可操作化——跨作用域传播时证据类别随行 | 可入见证锚定的实现注记 |
| 保留期参数化：importance→天数 + 来源/价值类别乘子 + 免疫规则（critical/core/访问≥3/受保护 tag） | 可吸收 | 遗忘调度器「受控优化」（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；结构性记忆不参与遗忘评估（架构 §5 is_structure） | 支撑：免疫规则=结构性记忆守护的工程化（参数化、可解释、可配置） | 注意：Memorix 免疫对象是「记忆条目」，Kairos 是「结构性拓扑」，语义有差异 |
| 全局标量分数 score = importance×e^(-age/τ)×accessBoost | 张力 | 六级链「全程无标量聚合、逐维序数比较」（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；使用价值轴（§1.1） | 挑战：指数衰减+访问增强聚合为一标量排序，丢维度信息（同 VID-12 热度值分诊）；但其**乘子语义可分解**为各轴单独评估 | 若只取其「各因子可解释、可逐项解释保留原因」（explainRetention）而弃全局排序，则兼容 |
| 记忆归属单元：project scope（记忆跟项目走） | 张力 | 主体（认知存续单元）为记忆边界（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；TeamScope 为隔离非锚定（架构 §5.20.6）；T-002 外部场景锚定（[risks.md](../../../governance/risks.md) T-002） | 未触及：归属单元（主体 vs 项目）是 Kairos 未决问题；个人系统定位下项目记忆可视为主体记忆的投影 | 与 VID-28 分诊一致（见 [笔记](../notes/VID-28-BV1oxNZ6uE6G.md) 01:46 行） |
| 意图检测 7 类先验 → 检索类型/来源加权（零 LLM） | 可吸收 | 三信号混合检索（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：意图先验是信号权重的实现级参数（why→推理类 boost、state→时序优先） | 直接可作 Kairos 三信号融合的信号权重表参照 |
| 归档=原地状态翻转（可逆、非删除） | 已覆盖 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；见证锚定主副本不可删（§5.5） | 支撑：Memorix 归档不销毁内容、可逆恢复——与 Kairos ADD-only 纪律同向 | 「archived 可逆」语义可在遗忘调度器注记中显式化 |
| 语义回退预算：1.8s 超时、无重试、失败静默降级关键词 | 可吸收 | 探索预算独立（S-12，架构 §8）；外部信号非依赖 | 支撑：远程语义检索定位为「可选增强」而非依赖，与 Kairos 外部校准非一等公民（T-002）姿态一致 | 预算/超时/降级链参数可入检索管线注记 |
| Git 记忆（commit→工程事实）+ 噪音过滤 | 张力（T-002 实例） | 外部校准源未建模为一等公民（[risks.md](../../../governance/risks.md) T-002） | 未触及：git 提交是结构化外部校准源的典型样本（事实+时间+来源可溯）；噪音过滤=校准质量门槛 | 可作为 T-002 的候选外部源形态样本 |
| 渐进披露（micro 7 工具） | 可吸收 | 检索深度分级 R0/R1/R2（架构 §3.9）是信息侧；工具面渐进披露未显式声明 | 支撑（同 VID-28） | 工具 schema 占用上下文与 CRI（认知基础 §1.9）经济性同理 |

## 可吸收增量（具体到机制/参数/接口）
1. **记忆状态机 + 证据门控**（`src/memory/long-term.ts`、`admission.ts`）：candidate/qualified/approved/archived/superseded 五态 + qualify 需证据引用计数 + approve 人工审计——「无证据不得合格、未合格不得进自动上下文」纪律可直接映射到 Kairos 见证锚定
2. **保留期参数化引擎**（`src/memory/retention.ts`）：importance→天数（365/180/90/30）+ 来源乘子（hook 0.5×/git 1.5×）+ 价值类别乘子（ephemeral 0.5×/core 2.0×）+ 免疫规则（critical/core/access≥3/受保护 tag）+ 解释器 `explainRetention`——参数集与「可解释保留原因」输出可整体吸收
3. **意图检测→检索加权表**（`src/search/intent-detector.ts`）：7 类意图 + 类型/来源/字段 boost 乘子 + 时序优先标志
4. **语义回退降级链**（`src/memory/long-term.ts`）：关键词确定性第一路由 → 1.8s 预算语义回退 → 失败静默——远程检索不得成为依赖
5. **归档批处理协议**（`retention.ts` `archiveExpiredBatch`）：游标分页、状态翻转、可逆
6. **渐进披露工具面**：micro/light/team/pro 四档工具暴露（对应 Kairos 接入层工具暴露策略）

## 存疑与未验证
- 1.3 long-term 层为较新设计（`docs/1.3-MEMORY-ARCHITECTURE.md` 自含验收标准 9 条，未逐一跑测验证——未执行）
- 「20+ agent 全覆盖」为 README 声称，实测接入面以 `docs/INTEGRATIONS.md` 支持矩阵为准（未逐项验证）
- 跨项目 portable 记忆的权限边界（拒绝项目类证据）依赖 owner/team 上下文，失败关闭声明（1.3 文档）未实测（未验证）
- promote（观察→长期）行为以文档/CLI 声明为主，端到端未运行验证（未执行）
- 观察记忆的 status 字段 legacy 兼容（无 admission 元数据的旧记录直接可投递）为显式设计取舍，语义上与「candidate 必须合格」并存，需注意两套规则并行

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
