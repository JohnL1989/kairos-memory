---
title: REPO-05 仓库分析：OpenClaw
aliases:
  - 外部仓库分析-05
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-05 OpenClaw

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/openclaw/openclaw |
| Star | 385402★（任务简报口径，2026-08-07） |
| 语言/许可 | TypeScript（pnpm monorepo，内置插件 extensions/）/ MIT（LICENSE 存在，Copyright 2026 OpenClaw Foundation） |
| 视频对应 | VID-16（BV1YXVg69EmC，A 级）、VID-19（BV11RGX6bEdc，A 级）、VID-31（BV1rnM269ErH，A 级） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 GitHub 失败，经 gh-proxy 镜像下载 main 分支 tarball（95MB，无 .git，无 commit SHA）；版本为 tarball 抓取时点 main 分支快照（OpenClaw ≥ 2026.3.13 声明口径） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：OpenClaw 是 agent 框架（非大模型），记忆为内置能力之一——「memory-search on `MEMORY.md` + memory/*.md + indexed session transcripts」；README 主文档聚焦安装/CLI/网关，记忆细节分布在 `extensions/memory-core/` 与 `src/agents/memory-search.ts`（`README.md` 与 `extensions/CLAUDE.md` 共同定义插件边界）。

**源码实证**：记忆系统是**完整落地的一等子系统**，非营销口径——记忆索引/搜索/巩固全部开源：`extensions/memory-core/`（约 200+ 文件：索引、混合检索、dreaming、短时提升、会话回填）+ `src/agents/memory-search.ts`（配置与默认参数）+ `src/hooks/bundled/session-memory/`（会话落盘钩子）+ `src/memory/root-memory-files.ts`（`MEMORY.md` 规范）。README 对记忆着墨少属「产品文档分发」取舍，机制本身实现充分。

## 架构与核心机制（源码实证）

1. **三层记忆文件 + 一个索引引擎**
   - ```MEMORY.md```（规范名，`src/memory/root-memory-files.ts`：CANONICAL_ROOT_MEMORY_FILENAME="```MEMORY.md```"，legacy "```memory.md```"）+ ```memory/YYYY-MM-DD.md``` 每日笔记 + ```DREAMS.md```（dreaming 产物，`extensions/memory-core/src/dreaming-dreams-file.ts`：DREAMS_FILENAMES=["`DREAMS.md`","`dreams.md`"]，managed block 标记 `<!-- openclaw:dreaming:deep:start/end -->`）
   - ```MEMORY.md``` 磁盘预算默认 10000 字符（`extensions/memory-core/src/memory-budget.ts`：DEFAULT_MEMORY_FILE_MAX_CHARS，理由：低于 bootstrap 注入上限 ~12KB/文件，避免被引导预算静默截断——对应 VID-19「```memory.md``` 太大系统会自动截断」）
   - 索引源双类：`memory`（`MEMORY.md` + memory/*.md）与 `sessions`（会话转录），DEFAULT_SOURCES=["memory"]（src/agents/memory-search.ts:136）
   - **每 agent 独立 SQLite 库**：`<state>/agents/<agentId>/agent/openclaw-agent.sqlite`（src/state/openclaw-agent-db.paths.ts:20-31）——注意：**非** VID-16 口述路径 `~/.openclaw/memory/<agent_id>.sqlite`（视频路径不准确，物理隔离的事实一致）
2. **混合检索：BM25 + 向量加权融合 + 三层修正器**（extensions/memory-core/src/memory/hybrid.ts + src/agents/memory-search.ts:119-138）
   - FTS5（tokenizer 默认 unicode61、**可配 trigram** 供中日韩）+ 向量余弦；默认权重 vector 0.7 / text 0.3（DEFAULT_HYBRID_VECTOR_WEIGHT/TEXT_WEIGHT，权重归一化 src/agents/memory-search.ts:327-330）
   - 三级修正：**importance 乘子**（0.75 + imp×0.05，importance 1-10→0.80-1.25×，importance.ts）、**时间衰减**（DEFAULT_TEMPORAL_DECAY_ENABLED=true、半衰期 30 天、指数 exp(-ln2/τ×age)，temporal-decay.ts）、**MMR 去重**（默认关、λ=0.7，mmr.ts）
   - 精确路径分级 exactPathSpecificity 0-3（整路径/父路径/文件名命中跨层优先，hybrid.ts:13, 283-293）
   - 参数：minScore 0.35、maxResults 6、candidateMultiplier 4、分块 400 tokens/80 重叠（DEFAULT_CHUNK_TOKENS=400/DEFAULT_CHUNK_OVERLAP=80，src/agents/memory-search.ts:119-120）、文件变更防抖 1500ms（DEFAULT_WATCH_DEBOUNCE_MS）
   - 降级链：无嵌入 provider → FTS-only 模式；FTS 不可用 → vector-only（manager.ts:1312-1314）
3. **Dreaming 三阶段巩固（short-term promotion）**（extensions/memory-core/src/dreaming.ts + dreaming-phases.ts + short-term-promotion-*.ts）
   - 默认 cron `0 3 * * *`（凌晨 3 点）；**默认 enabled=true**（dreaming.ts:22，DEFAULT_MEMORY_DREAMING_ENABLED——与 VID-19/31「默认关闭」口径**不一致**，疑为版本差异，见存疑）
   - light（浅睡眠）：lookback 2 天、limit 100、dedupeSimilarity 0.9，源 daily/sessions/recall
   - deep（深睡眠）：minScore **0.75**、minRecallCount **3**、minUniqueQueries **3**、recencyHalfLifeDays **14**、maxAgeDays 30、maxPromotedSnippetTokens 160、maxPriorEntryLossFraction 0.25，源 daily/memory/sessions/logs/recall
   - rem：minPatternStrength 0.75，源 memory/daily/deep
   - **确定性校准评分**（dreaming.ts:43-46 注释）：3 天/3 次查询的持久事实 0.750-0.756，重复填充 0.489-0.549，高相关一次性 0.529-0.606——「时间跨度和召回次数共同决定提升资格」是**非 LLM 硬判据**（LLM 只做叙事生成）
   - 产物双模式：inline（写回 ```MEMORY.md```）/ separate（写 `DREAMS.md`），`<!-- openclaw-memory-promotion: -->` 标记管理（memory-budget.ts:21）
   - 恢复机制（deep recovery）：memory health <0.35 时从 30 天回看找回候选，confidence ≥0.97 自动写回（dreaming.ts:53-58）
4. **会话记忆闪存（memory flash 的对应实现）**（src/hooks/bundled/session-memory/handler.ts）
   - `/new` 或 `/reset` 时把会话尾部上下文保存为带时间戳的 dated memory 文件（```YYYY-MM-DD-HHmm.md```，SLUG via LLM，handler.ts:43-45 捕获上限 8MB/256 条/扫描 4096 条）
   - 压缩前钩子：`session:compact:before` 内部事件 + `before_compaction` 外部钩子（src/agents/embedded-agent-runner/compaction-hooks.ts:227-266）；压缩后强制记忆索引同步（sync.postCompactionForce）
5. **记忆工具与提示纪律**（extensions/memory-core/src/tools.ts:481, 905 + prompt-section.ts）
   - `memory_search` / `memory_get` 双工具；系统提示引导「回答先前工作/决策/日期/人/偏好前先跑 memory_search，低置信要明说查过」+ 引用（Source: path#line）
6. **嵌入提供商**：11 种后端（src/config/schema.help.models.ts:228）——openai（默认）/ openai-compatible / gemini / voyage / mistral / bedrock / deepinfra / github-copilot / lmstudio / ollama / local（GGUF，需 @openclaw/llama-cpp-provider 插件）；provider="auto" → 默认 openai（src/agents/memory-search.ts:211-216）；主+备份（fallback）双 provider 配置

## 关键设计决策（与视频声称对照）

> 视频声称细节与分诊背景见 、、。

| 视频声称 | 源码验证结果 |
|:--|:--|
| VID-16「三大搜索：FTS5+BM25 关键词 / 向量 / 混合」 | **一致且更丰富**：hybrid.ts 加权融合之上还有 importance 乘子、时间衰减、MMR、精确路径分级四层修正 |
| VID-16「七家嵌入提供商，自动检测」 | **部分一致**：11 种后端（含视频提到的 OpenAI/Voyage/Mistral/DeepInfra/Ollama/local），**无 Jina**（视频声称的 Jina 无法验证）；provider="auto" 存在但默认落到 openai，非「逐个探测 API key 选第一个可用」（见存疑） |
| VID-16「TRIGRAM 分词支持中日韩」 | **一致（可配）**：fts.tokenizer 可配 "unicode61"（默认）\| "trigram"（src/agents/memory-search.ts:69, 289；memory-schema-fts.ts 校验 tokenize=trigram case_sensitive 0） |
| VID-16「分块 400 tokens/80 重叠、修改后 1.5s 自动重索引」 | **一致**：DEFAULT_CHUNK_TOKENS=400 / DEFAULT_CHUNK_OVERLAP=80 / DEFAULT_WATCH_DEBOUNCE_MS=1500（src/agents/memory-search.ts:119-121） |
| VID-16「每 agent 独立 SQLite 记忆库 ~/.openclaw/memory/<agent_id>.sqlite」 | **核心一致、路径不符**：每 agent 独立库属实，但实际路径 `<state>/agents/<agentId>/agent/openclaw-agent.sqlite`（openclaw-agent-db.paths.ts:20-31） |
| VID-19「三层：```memory.md``` 长期 / daily notes 工作记忆（自动加载今天和昨天）/ ```dreams.md``` 背景整合」 | **基本一致（命名差异）**：```MEMORY.md```（规范名）+ `memory/YYYY-MM-DD.md`` + ``DREAMS.md` 均存在；「自动加载今天和昨天」未在索引代码中验证（索引覆盖全部 memory/*.md，加载时序见存疑） |
| VID-19「dreaming 默认关闭」 | **不一致**：DEFAULT_MEMORY_DREAMING_ENABLED=true（dreaming.ts:22）——疑为版本演进或配置层差异（见存疑） |
| VID-19/31「compaction 前静默保存重要上下文」 | **一致**：session-memory hook（/new、/reset 落盘）+ compact:before / before_compaction 钩子（compaction-hooks.ts:227-266） |
| VID-31「Dreaming 三步：浅睡眠扫描 → REM 串主题反思 → 深睡眠判断长期保留，默认凌晨 3 点」 | **一致（相位命名相反）**：light/deep/rem 三相位 cron 默认 `0 3 * * *`；视频称「默认关闭」与源码 enabled=true 不符（同上） |
| VID-31「压缩后的摘要不自动等于长期记忆，仍要判断有无长期价值」 | **一致**：deep 相位有确定性资格门槛（minScore 0.75 + 3 次召回 + 3 次唯一查询），不是「压缩即提升」 |
| VID-31「判断记忆系统五件事：写得对/找得到/用得准/改得动/忘得掉」 | **机制侧一致**：写（memory tools 原子写 + budget 拒绝）+ 找（混合检索）+ 用（记忆工具引导提示）+ 改（memory_get/工具编辑）+ 忘（时间衰减 + dreaming 提纯） |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 混合检索 = 加权融合 + importance 乘子 + 时间衰减 + MMR + 精确路径分级 | 可吸收（参数级） | 三信号混合检索（语义 0.50/BM25 0.35/实体 0.15，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）+ GSPO 聚类/MMR 去重（§7.3b/c） | 支撑：OpenClaw 的「检索后修正器链」（importance 乘子→时间衰减→MMR）是 Kairos 排序链的工程化雏形；**精确路径分级**（0-3 层）是 Kairos 未显式的检索先验 | 修正器参数（0.75+0.05×imp、半衰期 30 天、λ0.7）可入检索管线注记 |
| dreaming deep 确定性提升门槛（0.75 分 + 3 次召回 + 3 次唯一查询 + 14 天半衰期） | **可吸收（强）** | 升华管道 raw→item→strategy→behavior（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §0.4）；使用价值轴（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1） | 支撑：「提升资格 = 时间跨度 × 召回次数」是使用价值轴的**确定性可计算投影**——Kairos 升华管道目前以 LLM 判断为主，此硬判据可作为第一道资格闸门 | 注意外部是「召回次数」（使用侧），Kairos 使用价值轴语义包含但不限于召回；与见证锚定无冲突（提升不伪造证据） |
| 记忆文件磁盘预算（`MEMORY.md` 10000 字符）+ bootstrap 注入截断保护 | 已覆盖（工程细节） | Token 预算分解（架构 §9.3）；编译管线多阶段组装（§4.3） | 支撑：「预算防静默截断」与 Kairos 编译管线「注入预算明确化」同向 | 10KB/12KB 数值为工程参考 |
| 压缩前落盘钩子（compact:before / session-memory at /new） | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；激活-存储解耦（§2.2） | 支撑：与 Kairos「压缩前落盘、压缩摘要≠长期记忆」语义一致（VID-31 已分诊） | — |
| 时间衰减作用于**检索排序**（30 天半衰期，默认开） | 可吸收 | 时间轴物理衰减（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1） | 支撑：Kairos 物理衰减轴是存储侧评估；OpenClaw 证明「衰减乘子挂检索排序」的轻量做法（不动存储） | 检索侧投影与存储侧衰减可并存，互不冲突 |
| 11 家嵌入提供商 + fallback 双 provider + local GGUF 插件 | 可吸收 | v0.1.0 固定 text-embedding-3-small/BGE-M3（架构 §7.3a） | 支撑：提供商抽象 + 备份 provider 是工程可移植性需求（同 VID-16 分诊） | 「主+备份降级链」比 Kairos 当前单 provider 声明更细 |
| FTS5 trigram 中文分词（可配） | 未触及 | Kairos 无分词层声明 | 未触及：多语言检索为 v1.1+ 考虑项 | 与 §7.3a BM25 中文分词的工程细节可互参（同 VID-16） |
| 记忆工具引导提示（先搜后答、低置信明说查过、引用来源） | 已覆盖 | 编译管线（架构 §4.3）；宪法主权面人类可仲裁（§1） | 支撑：工具使用纪律写入系统提示 = Kairos 编译管线组装职责；「低置信明说」与 Kairos 认知诚实文化同向 | — |

## 可吸收增量（具体到机制/参数/接口）
1. **确定性提升资格判据**（`extensions/memory-core/src/dreaming.ts`：DEFAULT_MEMORY_DEEP_DREAMING_MIN_SCORE=0.75、MIN_RECALL_COUNT=3、MIN_UNIQUE_QUERIES=3、RECENCY_HALF_LIFE_DAYS=14、MAX_PROMOTED_SNIPPET_TOKENS=160、MAX_PRIOR_ENTRY_LOSS_FRACTION=0.25）：raw→item 提升的「时间×使用」硬门槛 + 「先验条目损失上限 25%」防单次提升稀释已有记忆——可直接入 Kairos 升华管道资格闸门
2. **检索后修正器链参数集**（`extensions/memory-core/src/memory/{importance,temporal-decay,mmr}.ts` + `src/agents/memory-search.ts:119-138`）：importance 乘子 0.75+imp×0.05、时间衰减半衰期 30 天（默认开）、MMR λ=0.7（默认关）、vector/text 权重 0.7/0.3、精确路径分级 0-3——作为 Kairos 三信号融合（§7.3a）之后的修正器链参照
3. **确定性校准评分方法**（dreaming.ts:43-46 注释的校准分布：持久事实 vs 填充 vs 一次性分离度 0.75 vs 0.49 vs 0.53）：用「校准集标定阈值」而非拍脑袋阈值——可入 Kairos 度量轴的参数标定方法
4. **memory health 恢复机制**（deep recovery：health<0.35 触发 30 天回看、confidence≥0.97 自动写回、0.90-0.97 人工确认）：遗忘调度器之后的「衰退召回」闭环参数集
5. **管理块标记协议**（`<!-- openclaw:dreaming:deep:start/end -->`、`<!-- openclaw-memory-promotion: -->`）：机器写入区域与人工内容分区共存、可原子替换——可作 Kairos 宪法主权面「机器可写区域」的落地形态

## 存疑与未验证
- **Dreaming 默认状态冲突**：源码 DEFAULT_MEMORY_DREAMING_ENABLED=true（dreaming.ts:22）vs 视频 VID-19/31「默认关闭」——可能为版本演进（tarball 为当前 main 快照），或视频基于旧版本/插件配置默认值；未核实具体版本（未验证）
- 「自动加载今天和昨天的 daily notes」：索引覆盖全部 memory/*.md（VID-19 声称的加载范围未在代码中找到「仅今天+昨天」的过滤逻辑，见 session-backfill-selection.ts 的按日选择未逐行核实——未验证）
- 提供商「自动检测 API key」：provider="auto" 解析为默认 openai（src/agents/memory-search.ts:211-216），未发现「枚举七家探测第一个可用 key」的逻辑；VID-16 声称的自动检测链可能是旧版本行为或 UI 层引导（未验证）
- Jina 提供商在源码中不存在（VID-16 声称的七家含 Jina）——可能已下线或为视频旧口径（未验证）
- 视频声称存储路径 `~/.openclaw/memory/<agent_id>.sqlite` 与源码 `<state>/agents/<agentId>/agent/openclaw-agent.sqlite` 不符（状态目录与记忆索引库为不同库，见 openclaw-runtime-sqlite.ts 未逐行核实——未验证）
- 基准数字（Star 数）为任务简报口径；tarball 无 git 元信息，commit SHA 未知（未验证）
- 未执行任何运行验证（未执行）；以上全部为静态源码阅读

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
