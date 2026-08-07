---
title: VID-39 视频笔记：Letta（原 MemGPT）：让 AI 智能体拥有持久记忆的开源框架
aliases:
  - 外部视频笔记-39
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-39 Letta（原 MemGPT）：让 AI 智能体拥有持久记忆的开源框架

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1k65X6dExY |
| UP主 | AI技术投降派 |
| 时长 | 5min（1P） |
| 字幕来源 | B站 AI 字幕（ai-zh），抓取于 2026-08-07，内容与主题匹配度已人工核验 |
| 素材边界声明 | 完整覆盖视频全程；AI 字幕可能存在个别错字 |

## 内容提炼
### 核心论点
1. 把大模型上下文窗口当成操作系统内存来管理，用「虚拟内存」思路突破窗口瓶颈（00:08）
2. 有状态智能体：记忆持久、随使用不断成长，区别于主流 AI 助手的无状态「每次新对话一张白纸」（00:36）
3. 三层记忆：core memory（始终在上下文窗口内，相当于内存，存放用户档案/关键偏好）、archival memory（硬盘式，长期知识与对话记录）、recall memory（对话历史 + 语义搜索）（01:26）
4. memory blocks：每个记忆块是一段结构化文本（用户档案一个块、当前任务状态一个块），智能体可自主读取和修改这些块——「智能体在编辑自己的记忆」，行为完全透明可审计（03:07）

### 关键机制
- 三层架构让智能体在有限窗口内管理远超窗口大小的知识（01:21-02:04）
- sleep time compute：智能体在后台自主运行、整理和巩固记忆（01:15）
- memory blocks 自读自改 + 透明性：可随时查看智能体记住了什么、修改了什么，优于黑盒（03:10-03:33）
- agent file（AF 文件）：类似 Dockerfile，用一个配置文件声明式定义智能体完整状态——人格、记忆、工具、数据源（04:08-04:25）
- Letta EVAL 评估框架：专门测试智能体的记忆管理和长期对话能力（04:25-04:31）

### 可操作细节
- 安装：npm install -g letta-ai，终端运行 letta-code 即启动带持久记忆的智能体（02:20）
- 模型无关：OpenAI / Anthropic / Google / 本地模型，任何支持函数调用的 LLM 均可（03:36-03:48）
- 提供 Python 与 TypeScript 两个 SDK（03:48）
- 开源：GitHub 16,000+ stars（03:59）；商业版提供托管与记忆管理能力（05:22）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 三层记忆：core 常驻窗口 / archival / recall+语义搜索 | 01:26 | 已覆盖 | 三种检索配置模式（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.2）；检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；知识加工区三区域（§5.10） | 支撑 | 分层思路与 Kairos 一致，实现粒度不同 |
| sleep time compute：后台自主整理巩固记忆 | 01:15 | 可吸收 | 遗忘调度器定时扫描（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5）+ 防抖反射执行器（§2.6.3）；Kairos 未声明「低峰期巩固窗口」概念 | 支撑：与探索预算独立（S-12，架构 §8）兼容，巩固成本归维护 | 与 VID-14「梦境」同源；Kairos 可吸收为「维护期批量巩固」 |
| memory blocks：智能体自主读写/编辑自己的记忆块 | 03:07 | 张力 | 见证锚定主副本不可被无声改写（价值独立性公理，[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1；[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5）——Kairos 主副本写入口在见证锚定侧，使用侧只能累积权重 | 挑战：直接自改记忆违背「好用 ≠ 真实」的隔离 | Kairos 不采纳「直接编辑记忆」，但「记忆可读可审计」的透明性主张（03:25）可吸收 |
| agent file：声明式文件定义智能体完整状态 | 04:08 | 可吸收 | 契约是运行时投影（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）——声明式状态文件与契约思想接近 | 支撑 | Kairos 纯文档设计本身即以文档为契约 |
| 有状态 vs 无状态智能体 | 00:36 | 已覆盖 | Kairos LTM 持久化（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5）即「有状态」立场 | 支撑 | — |

## 存疑与未验证
- 「charles pecker」应为 Charles Packer（MemGPT 论文作者，音译错误，未验证）
- 「VTAAD」应为 Letta ADE（Agent Development Environment）的音译（未验证）
- 「GitHub 16,000+ stars」为视频发布时数据，未核对时间点（未验证）
- 「核心记忆始终在上下文窗口内」为视频简化口径，实际 Letta 通过工具调用在 core/archival 间移动记忆（未验证细节）
- 「AF 文件类似 Dockerfile」为 UP 主类比，Letta 官方文档细节未验证

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
