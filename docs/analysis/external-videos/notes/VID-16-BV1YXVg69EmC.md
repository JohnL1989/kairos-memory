---
title: VID-16 视频笔记：OpenClaw 默认记忆引擎全解析：三大搜索+七家嵌入提供商
aliases:
  - 外部视频笔记-16
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-16 OpenClaw 默认记忆引擎全解析：三大搜索+七家嵌入提供商

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1YXVg69EmC |
| UP主 | big叔大 |
| 时长 | 4min（1P） |
| 字幕来源 | B站 AI 字幕（ai-zh），抓取于 2026-08-07，内容与主题匹配度已人工核验 |
| 素材边界声明 | 完整覆盖视频全程；AI 字幕音译错字极多（「open cloud/open claw/大叔龙虾」=OpenClaw、「booting」=内置（built-in）、「EQUALI/XQUALIZE」=SQLite、「QMD」=Qdrant、「hunter」=某跨对话记忆工具 等），专名已按语境转述，无法确认者列入存疑 |

## 内容提炼
### 核心论点
1. OpenClaw 默认记忆引擎以 SQLite 为后端，为每个 agent 维护独立的记忆数据库——「你的 agent 从此有了记事本」，解决 agent 聊着聊着就忘、偏好要反复重说、重要信息无从找回的问题（00:29-00:52）
2. 提供三种搜索方式：关键词搜索（FTS5 全文索引 + BM25 评分精准匹配）、向量搜索（嵌入模型文字转向量做语义搜索）、混合搜索（关键词+向量结合取长补短，更精确更全面）（00:56-01:17）
3. 特别支持中日韩语言的 TRIGRAM 分词，中文搜索非常精准（01:20-01:22）
4. 支持七家嵌入提供商，自动检测：环境里有任一家的 API key 即自动启用向量搜索；没有 key 也不影响，关键词搜索依然可用（01:32-01:38）
5. 自动索引 + 智能更新：自动索引 `CLAUDE.md` 和 memory 目录下所有 markdown 文件（每段约 400 tokens、80 token 重叠存 SQLite）；文件修改后 1.5 秒内自动重新索引；嵌入提供商或模型变更时自动重建整个索引（02:31-02:56）

### 关键机制
- 每 agent 独立 SQLite 记忆库：存储位置 `~/.openclaw/memory/<agent_id>.sqlite`（02:42-02:48）
- 向量搜索可用性判定：按提供商列表从上到下检测，找到第一个可用的 API key 就自动启用；也可在配置文件 `agents.defaults.memory_search.provider` 手动指定（02:22-02:28）
- 本地嵌入两条路：provider=local + model_path 指向 GGUF 模型文件（需 node-llama-cpp 运行时）（01:50-01:55）
- 索引生命周期：文件修改 1.5 秒内自动重索引 → 提供商/模型变更全量重建 → 手动 `openclaw memory index --force` 强制重建（02:50-03:01）
- 降级兜底：sqlite-vec 未加载时系统自动回退到余弦相似度计算（03:35-03:38）

### 可操作细节
- 七家嵌入提供商：OpenAI（text-embedding-3-small）、Jina（多模态，可处理图片音频）、Voyage、Mistral、DeepInfra（BAAI/bge-m3）、Ollama（需手动配置，适合本地）、local（本地嵌入）（01:57-02:22）
- 分块参数：每段约 400 tokens、80 token 重叠（02:36-02:38）
- 诊断命令：`openclaw memory status` 检查 provider 配置；结果过时运行 `openclaw memory index --force`（03:22-03:33）
- 选型对照：开箱即用选内置引擎；需要重排序和查询扩展、或索引工作区外目录考虑 Qdrant；需要跨对话记忆和用户建模考虑另一工具（03:02-03:18）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 混合搜索（关键词 BM25 + 向量 + 混合取长补短） | 00:56 | 已覆盖 | 三信号混合检索（语义 0.50 + BM25 0.35 + 实体 0.15，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：OpenClaw 混合搜索是 Kairos 三信号融合的简化工程实证 | Kairos 权重化融合比简单取并更精细 |
| 自动索引 markdown 文件、文件变更 1.5s 自动重索引 | 02:31 / 02:50 | 已覆盖 | 文件系统-向量索引一致性检查（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.16） | 支撑：索引与源文件一致性是 Kairos 已登记机制 | 1.5s 具体参数为工程细节参考 |
| 每 agent 独立记忆数据库（物理隔离） | 00:44 | 可吸收 | 路径空间域隔离为逻辑隔离（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a 硬过滤边界） | 未触及：物理隔离 vs 逻辑隔离的取舍；多 agent/多租户场景可借鉴物理分库 | Kairos 单主体设计，多 agent 场景未建模 |
| 嵌入提供商可插拔（七家+本地 GGUF+自动检测） | 01:32 / 01:57 | 可吸收 | v0.1.0 固定 text-embedding-3-small/BGE-M3（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：提供商抽象层是工程可移植性需求，Kairos 未声明 | 与 §7.3a 双模式索引后端（pgvector/sqlite-vec）可合并考虑 |
| sqlite-vec 未加载自动回退余弦相似度 | 03:35 | 已覆盖 | 双模式索引后端：pgvector HNSW / sqlite-vec brute-force（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：降级兜底与 Kairos 组件降级契约（§10.17）同向 | — |
| 分块索引参数（400 tokens/80 重叠） | 02:36 | 可吸收 | Kairos 无显式分块参数声明（检索以摘要向量+全量向量分层承载，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 未触及：纯实现参数 | 实现期参考值 |
| TRIGRAM 分词支持中日韩 | 01:20 | 未触及 | Kairos 无分词层声明 | 未触及：多语言检索支持是 v1.1+ 考虑项 | 与 §7.3a BM25 中文分词的工程细节可互参 |

## 存疑与未验证
- 引擎名「booting memory engine」字幕音译存疑——结合语境应为「内置（built-in）记忆引擎」，OpenClaw 项目的默认记忆引擎确切名称无法从字幕确认（未验证）
- 「hunter」（跨对话记忆与用户建模工具）名称音译，无法确认对应工具（可能是 Mem0 等，未验证）
- 参数（400 tokens、80 token 重叠、1.5 秒、七家提供商清单）为 UP 主口述演示，未对照官方文档（未验证）
- 字幕中「XQUALIZE」「EQUALI」均指 SQLite，但引擎后端也可能为其他嵌入式库（未验证）
- 存储路径 `~/.openclaw/memory/<agent_id>.sqlite` 为 UP 主口述（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
