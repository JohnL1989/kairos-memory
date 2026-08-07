---
title: VID-41 视频笔记：supermemory 长期记忆系统
aliases:
  - 外部视频笔记-41
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-41 supermemory 长期记忆系统

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1nS7X6hECB |
| UP主 | 码上成功的小猴 |
| 时长 | 1min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；1 分钟快速介绍，whisper 错字多（SuperPower=SuperMemory、Coco=疑为 Claude Code、开员=开源、谈明=排名、多模特=多模态、下谱=效果、比较使用=免费使用、API Keyless=API Keys 页面、照回=找回），已按语境转述；全部为产品定位介绍，无技术细节；与仓库 REPO-01（supermemory 源码实证）同主题——开源仓库为客户端/代理层，核心引擎闭源 |

## 内容提炼
### 核心论点
1. SuperMemory：GitHub 24K star 的开源记忆系统，在三个记忆评估 benchmark 上号称排名第一，专门解决「AI 工具记忆差」的问题（00:05-00:13）
2. 定位分层：如果 mem0 等 Memory 方向是「大脑记忆层」，SuperMemory 更像是「大脑的系统层」——不仅能够记事，还能获取其他外部信息和支持（00:38-00:47）
3. 能力面：可丢入用户信息、项目资料、网页、文档、邮件、PDF、图片、视频、代码等多模态内容，还能连接外部数据工具（Google Drive / Gmail / Notion / GitHub）；核心亮点 = 自动记忆提取 / 用户画像 API / 混合搜索（00:24-00:53）
4. 评估记忆系统的**定性原则**（该记得记住 / 不该记得不记 / 该忘的能够忘 / 隐私数据 / 能够准确找回 / 找回后能正确使用）——「除了看基准测试，还是要从定性原理去考虑」（01:28-01:42）

### 关键机制
- 接入方式：以 OpenCode 为例安装插件 → 官网获取 API key（有免费使用额度）→ 自动记忆提取 + 手动命令（记住/找回）（00:55-01:26）
- 视频声称 SuperMemory 解决「以前 OpenCode 的记忆没 Hermes 的好」的问题（00:13-00:19）

### 可操作细节
- 无（1 分钟介绍，无参数/流程细节）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记忆系统定性评估六问（该记得记住/不该记得不记/该忘能忘/隐私/准确找回/找回后正确使用） | 01:28 | 已覆盖 | 使用价值驱动 + 遗忘受控优化（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；「记忆即使用」 | 支撑：六问与 Kairos 核心原则逐一对应——价值判断、遗忘权衡、隐私红线、检索质量、使用闭环 | 可作为 Kairos 验收原则的产品化表述，与验收标准同族 |
| 记忆层 vs 系统层定位（记忆不只是存储，还连接外部信息源） | 00:38 | 可吸收 | 多源摄取（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3 多源摄取）；Connectors 同步模式（§5.13） | 支撑：Kairos 已有 Connectors/多源摄取设计；「系统层」定位话术与 Kairos 记忆系统横切定位一致 | 定位话术，无机制增量 |
| 多模态内容 + 外部数据工具接入 | 00:24 | 已覆盖 | 多模态消息 Part 统一接口（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3i）；资源摄取 API（§7.3e） | 支撑：Kairos 已建模多模态与外部资源摄取 | — |
| 用户画像 API（自动画像作为一等能力） | 00:49 | 可吸收 | 可配置 Profile Schema（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.14） | 支撑：Kairos 已有 Profile Schema；「画像 API 化」是产品形态增量 | 工程产品化注记 |
| 混合搜索（记忆 + RAG 多路） | 00:51 | 已覆盖 | 三信号混合检索（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；双模检索架构 Fast Context + Deep Reasoning（§7.3d） | 支撑：混合检索是 Kairos 检索层的既定方向 | — |
| 记忆差是「AI 工具」通病（OpenCode 等） | 00:13 | 未触及 | — | 未触及：产品生态观察 | — |

## 存疑与未验证
- 1 分钟快速介绍，机制全部为宣称：核心引擎实际**闭源**（REPO-01 实证开源仓库仅客户端/代理层，引擎在 api.supermemory.ai）——视频以开源项目口吻介绍，与 REPO-01 结论存在披露差异（未验证引擎侧行为）
- 「24K Star」为视频口径，REPO-01 实证 28798★（2026-08-07）——时间口径差异，量级一致
- 「三个记忆 benchmark 排名第一」为视频转述官方 README 声称（LongMemEval/LoCoMo/ConvoMem），未独立验证（未验证）
- 「每月 5 美金免费使用」「OpenCode 记忆没 Hermes 好」为 UP 主口述（未验证）
- 错字「Coco」疑为 Claude Code，无法确认（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
