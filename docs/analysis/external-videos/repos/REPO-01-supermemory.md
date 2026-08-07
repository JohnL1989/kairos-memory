---
title: REPO-01 仓库分析：Supermemory
aliases:
  - 外部仓库分析-01
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-01 Supermemory

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/supermemoryai/supermemory |
| Star | 28798★（任务简报口径，2026-08-07） |
| 语言/许可 | TypeScript（bun/turbo monorepo）/ MIT |
| 视频对应 | VID-66（BV1QJ7z6CES8，素材级别 C——字幕串台，视频声称不可作为证据，本笔记仅仓库实证） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 GitHub 失败，经 gh-proxy 镜像下载 main 分支 tarball（无 .git，无 commit SHA 可标注）；镜像内容与官方仓库的一致性未逐一校验（低等级证据） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：「State-of-the-art memory and context engine for AI」——自动从对话抽取事实、构建用户画像、处理知识更新与矛盾、自动遗忘过期信息、混合检索（RAG+Memory）、连接器（Google Drive/Gmail/Notion/GitHub）、多模态抽取（PDF/OCR/视频转写/代码）。声称 **#1 on LongMemEval/LoCoMo/ConvoMem 三大基准**、95% Recall@15、99.4% 上下文压缩、~50ms 用户画像（`README.md`, 356-366）。

**源码实证**：开源仓库是 **Turbo monorepo，全部为客户端/代理/文档层**，核心记忆引擎**不在本仓库**：
- `apps/web` — Next.js 前端（`apps/web/app/api/` 仅 emails/og/onboarding 三个内部路由，无 v3/v4 引擎接口）
- `apps/mcp` — MCP 服务器（Cloudflare Worker），全部工具为**薄代理**：`apps/mcp/src/server/client/index.ts:162` 硬编码 `apiUrl = "https://api.supermemory.ai"`；`tools/save-memory.ts`、`tools/add-memory.ts`、`tools/search-memory.ts` 等均只做参数校验后转发
- `apps/browser-extension`、`apps/raycast-extension` — 客户端注入（content scripts 注入 ChatGPT/Claude/Gemini 页面）
- `packages/memory-graph` + `apps/memory-graph-playground` — 图谱**可视化画布**（canvas 渲染/simulation/version-chain），非引擎本体
- `packages/agent-framework-python`、`packages/tools` — SDK 与框架封装（Vercel AI SDK/LangChain 等）
- `skills/supermemory`、`apps/docs` — 使用文档与营销级架构描述
- `CLAUDE.md` 声称的 `IngestContentWorkflow`、wrangler 绑定（Hyperdrive/AI/KV/Workflows）在仓库内**未找到对应源码**；README 声称的本地二进制 `supermemory-server`（`npx supermemory local`）源码也不在本仓库

**结论**：README 口径的「引擎」为闭源托管服务（api.supermemory.ai）；开源面 = 客户端协议 + 文档。引擎机制只能从官方文档反推（文档也是声称，非实现）。

## 架构与核心机制（源码实证）

开源面可实证的机制：

1. **MCP 工具面**（`apps/mcp/src/server/tools/` + `apps/mcp/src/server/client/index.ts`）：`memory`（save-memory/add-memory，写后状态 queued）、`recall`（search-memory，hybrid 模式，limit/threshold 参数）、`context`（resources/profile.ts + prompts/context.ts，注入用户画像+近期活动）、`forget`、`list-documents`、`memory-graph`、`guided-save` 等
2. **forget 两段式删除协议**（`client/index.ts:195-254`）：先按内容精确匹配删除；404 后回退——`search(0.85 相似度阈值)` → 取命中记忆删除。这是开源代码中唯一完整的「遗忘」实现，其余遗忘（时间过期/矛盾解决/噪音过滤）均为文档声称
3. **container tag 作用域**（`apps/mcp/src/server/container-tag.ts`、`client/index.ts:321-347`）：记忆/文档按 containerTag 隔离，profile 按 containerTag 独立维护——多租户隔离原语
4. **渐进披露**（`apps/mcp/src/server/space-state.ts`、`space.ts`）：工具/资源按 space（app 等）条件暴露

引擎侧机制（仅文档声称，`apps/docs/concepts/graph-memory.mdx`、`user-profiles.mdx`、`memory-vs-rag.mdx`、`skills/supermemory/references/architecture.md`）：
- **知识图谱三类关系**：Updates（新事实取代旧事实，isLatest 标记，历史保留）、Extends（细节丰富）、Derives（跨记忆推断新事实）
- **记忆类型**：Facts（持久至更新）/ Preferences（重复强化）/ Episodes（过期衰减）
- **自动遗忘**：时间过期（临时事实到期）、矛盾（更新获胜）、噪音过滤
- **Dreaming**：`dreaming: "dynamic"`（相关文档成组处理形成连贯单元）vs `"instant"`（单文档立即入图）
- **用户画像**：static（长期稳定事实）+ dynamic（近期活动）+ buckets（按主题分类，分类器受 bucket 描述约束）
- **记忆不是 RAG**：RAG 检索文档块（无状态），Memory 追踪用户事实的时间演化——两者默认同时跑

## 关键设计决策（与视频声称对照）

| 视频声称 | 源码验证结果 |
|:--|:--|
| VID-66「登顶三大记忆基准（LongMemEval/LoCoMo/ConvoMem）」 | **无法验证**：为 README 厂商自述（`README.md`），benchmark 结果在外部研究页，开源仓库无评测代码与数据 |
| VID-66 其余声称（若字幕存续） | **不适用**：VID-66 为 C 级串台素材，无可用字幕内容可对照（见 [笔记](../notes/VID-66-BV1QJ7z6CES8.md)） |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| Updates/Extends/Derives 关系 + isLatest 版本化（历史保留、最新优先） | 可吸收 | 见证锚定主副本 + ADD-only 协议新旧观察并存（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；双副本差异检验（§5.5） | 支撑：显式「更新」关系是 ADD-only 之上的一等语义，检索时只取 isLatest 而历史留审计——与 Kairos「新旧并存、真相裁决走校准」兼容 | 关系型更新语义可作为 ADD-only 之上的查询投影 |
| static/dynamic 画像分工（常驻 vs 按需；非字面匹配事实进 profile 不进 search） | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；身份面常驻、Profile Schema 可配置（§5.14）；「search 依赖问对问题」的缺陷论证（`user-profiles.md`x）与 Kairos 身份面否决权（认知基础 §2.1）同向 | 支撑 | 「画像应常驻、检索应按需」的分工论证可入注记 |
| 自动遗忘三分法：时间过期/矛盾更新/噪音过滤 | 已覆盖 | 遗忘调度器「受控优化」（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；时间轴物理衰减+逻辑因果双轴（§1.1）；差异检验处理矛盾（架构 §5.5） | 支撑：三分法恰好落在 Kairos 时间轴（过期）+ 校准/见证（矛盾）+ 使用价值（噪音） | 引擎闭源，机制不可审计——「声称的遗忘」与「实现的遗忘」无法区分 |
| Dreaming dynamic 成组处理（非单条写入） | 可吸收 | 探索预算独立（S-12，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §8）；离线巩固批次 | 支撑：成组处理与低峰期批量巩固同向 | 「单条立即入图 vs 成组动态」的模式开关可作为巩固批次参数 |
| forget 两段式协议（精确→0.85 相似度兜底） | 可吸收 | 遗忘调度器（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5）未声明删除语义 | 未触及：删除是 Kairos 边缘操作，其「先精确后近似」的兜底链是工程细节 | 唯一可实证的引擎侧协议 |
| **引擎闭源**：基准/性能/机制全部不可审计 | 张力 | Kairos 可审计压缩硬约束（认知基础 §2.2）+ 监督平面审计庭（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §1） | 挑战：不可审计的「黑盒记忆」与 Kairos 审计立场的根本张力；也印证「认证无源码实证=低等级证据」纪律 | 对 Kairos 是反面案例，非吸收项 |

## 可吸收增量（具体到机制/参数/接口）
1. **forget 两段式删除协议**（`apps/mcp/src/server/client/index.ts:195-254`）：先精确匹配（404 兜底）→ 相似度阈值（0.85）检索 → 删除命中项；作为 Kairos 遗忘调度器删除语义的实现参照（参数：SIMILARITY_THRESHOLD=0.85、检索 top-k=5）
2. **画像 static/dynamic 双桶 + buckets 分类器约束**（`apps/docs/concepts/user-profiles.mdx`）：bucket 描述约束分类器（「仅显式第一人称偏好，排除推断特征」）——防止画像抽取过度推断，呼应 VID-12 视频「画像 prompt 过细反效果」（见 [笔记](../notes/VID-12-BV1Z1jJ6cEVE.md) 31:25）
3. **container tag 检索隔离原语**：记忆/画像/文档统一按容器作用域隔离（`apps/mcp/src/server/container-tag.ts`），可作为 Kairos TeamScope（架构 §5.20.6）之上的轻量作用域投影
4. **Dreaming 模式开关**（dynamic/instant）：巩固批次的「成组 vs 单条」可配置化

## 存疑与未验证
- 核心引擎（事实抽取/矛盾解决/自动遗忘/画像合成）**闭源**，全部机制描述为文档声称，无源码可验证——本笔记所有引擎侧条目均标注「文档声称」
- 三大基准 #1、95% Recall@15、99.4% 压缩、50ms 画像、SMFS 3.0× token 节省：README 自述，仓库无评测复现代码（未验证）
- 本地二进制 `supermemory-server` 与 `IngestContentWorkflow` 在本仓库无源码（未验证其存在形态）
- `packages/memory-graph` 为可视化而非引擎，勿被「memory-graph」命名误导

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
| 0.0.42 | 2026-08-07 | 0.0.2（0.0.42 批次）审计修复：VID-66 笔记状态更新（已产出）。 |
