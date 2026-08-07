---
title: VID-90 视频笔记：Claude Code 记忆系统设计（源码泄露分析，素材部分覆盖）
aliases:
  - 外部视频笔记-90
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-90 Claude Code 记忆系统设计

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1ZA93BtEKW |
| UP主 | 五道口纳什 |
| 时长 | 21min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | **素材部分覆盖**：视频标注 21min，但 whisper 转写仅覆盖前约 3 分钟（from 0~180 秒，末条 to=3:00），21 分钟内容的后续 18 分钟无转写；本笔记仅基于前 3 分钟内容，后续部分（召回细节、Wire Layer 展开、实验等）缺失，不作为完整视频结论使用；转写存在谐音错字（「TaxSonamay/Automemory」疑为「Taxonomy/auto memory」，「CladiCode/CladiX/Cardcode」应为「Claude Code/Claude X」，「绘画」应为「会话」） |

## 内容提炼
### 核心论点
1. Claude Code 的记忆按语义分类（Taxonomy / auto memory），四类：User（用户）、Feedback（反馈）、Projects（项目）、Reference（参考）——本质是"编程项目记忆"设计（00:32-00:47）。
2. 本地持久化：按语义分类写入 auto memory（自动记忆），写入方式是追加式（00:49-01:00）。
3. Agent loop 中的加载与注入：从记忆 MD 文件召回最相关的记忆，再经 Wire Layer（网络层=发送给远端 Claude API 的请求层，对应 API 的 system 约束/请求体）注入上下文（01:05-01:42）。
4. 写入、加载、注入整个链路都是语言模型驱动的（LLM 决定怎么写、怎么加载、以什么角色加载、怎么组织带记忆的 context），因此必须设计对应的 prompt 来避免"记忆幻觉"——因为记忆不是精确的，类似人记忆模糊不清（01:54-02:23）。

### 关键机制
- LLM 驱动的记忆写入：没有外部规则脚本决定记什么，由模型按四类语义分类自行决定写入（00:49-01:00，01:54-02:23）。
- Wire Layer 概念：记忆 MD 文件→召回→以 API 请求方式发送给远端模型，在 Claude API 层面对应 system 约束与请求体（01:05-01:42）。

### 可操作细节
- 记忆分类四类：User / Feedback / Projects / Reference（00:39-00:43）。
- 记忆存储形式：本地 markdown 文件（MD 文件），追加式写入（00:49-01:00）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记忆按语义分类（User/Feedback/Projects/Reference） | 00:32-00:47 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.2（记忆类型：三种检索配置模式）+ §1.1（五轴度量：见证/使用分类视角） | 支撑：语义分类=Kairos 类型学的一种工程切法（按内容来源切），Kairos 按使用模式+度量轴切，两者正交不冲突 | 分类维度差异可作为类型学对照 |
| 追加式写入（本地持久化） | 00:49-01:00 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3g（ADD-only 提取协议） | 支撑：与 Kairos ADD-only 同构；Claude Code 以 MD 文件实现追加，Kairos 以协议约束实现 | 强印证 |
| LLM 驱动的记忆写入/加载需防"记忆幻觉" | 01:54-02:23 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §5.5（见证→使用仲裁：差异检验 11 步）+ [认知基础](../../../foundation/cognitive-foundation.md) §C.5（真理条件与双轨） | 支撑：承认"记忆不精确"与 Kairos 见证锚定+差异检验的动机一致；Kairos 以仲裁机制而非仅靠 prompt 缓解 | 强印证 |
| Wire Layer：记忆经 API 请求层注入 | 01:05-01:42 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §4（编译管线：系统提示词多阶段动态组装）+ §4.3（采集→分类渲染→注入元数据→组装） | 支撑：Wire Layer=Kairos 编译管线的模型 API 侧视图；记忆文件→召回→注入请求体与编译管线四阶段同构 | — |

## 存疑与未验证
- **素材限制**：仅前 3 分钟有转写，后续 18 分钟（含召回算法细节、Wire Layer 展开、与 Claude X 对比等）缺失；「Claude Code 源码泄露」为 UP 主说法，未验证（未验证）。
- 「TaxSonamay」转写疑似「Taxonomy」，四类分类与官方 `CLAUDE.md`/memory 文档的对应关系未核对（未验证）。
- 「Wire Layer 对应 Claude API system 约束」为 UP 主个人术语解释，非官方命名（未验证）。
- 视频中「CladiCode 圆满泄露」转写混乱，泄露对象与时间不可考（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
