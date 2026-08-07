---
title: VID-36 视频笔记：AutoGenetic Memory 跨会话
aliases:
  - 外部视频笔记-36
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-36 AutoGenetic Memory 跨会话

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1P4Mr6LEem |
| UP主 | openJiuwen |
| 时长 | 1min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；1 分钟产品推广短片，whisper 错字多（画绘画失忆=会话失忆、上下闻窗口=上下文窗口、Swam=Swarm、Od genetic memory=AutoGenetic Memory、动能节偶=语义不明、持续眼镜=持续演化、汇报邮箱=汇报邮件、显示指令=显式指令）；全部为产品宣称，无任何技术细节/架构/代码可验证 |

## 内容提炼
### 核心论点
1. 解决「会话失忆」：Agent 上下文窗口一清空，很多系统只能从零开始，用户被迫重复信息（00:03-00:20）
2. 理念定位：不是简单把聊天记录存下来，而是让记忆**像基因一样自主生长**；Swarm 群体记忆——记忆基因跨 Agent 复制，沉淀为**组织级记忆基因库**（00:25-00:42）
3. 分层记忆体系 L0-L3：层级记忆基因片段的精准与高效构建（00:36-00:42）
4. 后台一步式处理：将零散信息进行**重放、提炼、冲突消解**，沉淀出高价值记忆（00:42-00:51）；Memory Turbo 通过语义聚类提升记忆沉淀效率；Graph Memory 将基因记忆转化为可持续演化的记忆知识图谱，让 Agent 理解记忆的长期关联（00:51-01:06）
5. 定位宣言：把 Agent 记忆从一项功能**重构为一种核心数据资产**——「Agent 正在从临时助手走向长期懂你的伙伴」（01:36-01:52）

### 关键机制
- 演示场景（9问 Swarm 接入 9问 Memory）：用户对话中提及「需要写一封项目完成的汇报邮件」，无任何显式指令下 Agent 主动提取汇报邮件、邮件落款、收件人爱好等关键信息并**按类型分层写入记忆**；开启新对话再次给同一人发邮件时无需用户重复提供，Agent 准确调用历史偏好自动完成（01:06-01:36）

### 可操作细节
- 无（1 分钟推广片，无参数/流程细节）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记忆基因跨 Agent 复制、沉淀组织级记忆库 | 00:25 | 张力 | 路径空间域隔离（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；身份面否决权（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1） | 挑战：记忆跨 Agent 复制与 Kairos 域隔离、身份面「记忆归属个人叙事」取向存在张力——组织级共享记忆需回答「谁的身份、谁的见证」 | 仅 5 秒宣称，无机制；张力判断从理念层面 |
| 分层记忆体系 L0-L3 | 00:36 | 可吸收 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 未触及：L0-L3 无定义（是层级类型还是生命周期未知），无法对照；若为层级记忆存储，与 Kairos 分级检索同向 | 宣称级，等待可验证资料 |
| 后台重放/提炼/冲突消解 → 高价值记忆 | 00:42 | 已覆盖 | 三级知识生产管道 raw→item→strategy→behavior（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.10）；差异检验（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：重放提炼≈升华管道、冲突消解≈差异检验——概念级同构，无细节 | — |
| 主动提取 + 按类型分层写入 | 01:06 | 已覆盖 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；记忆类型三分（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.2） | 支撑：演示场景与 Kairos 提取+分类写入流程一致 | 演示无证据等级 |
| Graph Memory：记忆知识图谱理解长期关联 | 00:57 | 已覆盖 | 实体知识图谱（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.2 组件） | 支撑：图化记忆长期关联与 Kairos 实体知识图谱同向 | — |
| 记忆是「核心数据资产」定位 | 01:36 | 未触及 | — | 未触及：产品定位话术，非机制 | — |

## 存疑与未验证
- 1 分钟推广片，全部宣称无可验证证据；「Swarm 群体记忆」「L0-L3」「Memory Turbo」「Graph Memory」均无定义（未验证）
- 「动能节偶」语义不明（疑为「动态结构」或转写错误），无法解读（未验证）
- 演示场景（自动提取收件人爱好、自动完成邮件发送）为官方宣传口径，未展示实际运行（未验证）
- 本视频素材级别低，仅作理念对照，不应作为证据引用

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
