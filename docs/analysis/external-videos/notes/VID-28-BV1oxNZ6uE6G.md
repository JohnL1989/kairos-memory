---
title: VID-28 视频笔记：换会话就失忆？Memorix：AI 编程助手的记忆，该跟着项目走
aliases:
  - 外部视频笔记-28
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-28 换会话就失忆？Memorix：AI 编程助手的记忆，该跟着项目走

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1oxNZ6uE6G |
| UP主 | AI技术投降派 |
| 时长 | 11min（1P） |
| 字幕来源 | B站 AI 字幕（ai-zh），抓取于 2026-08-07，内容与主题匹配度已人工核验 |
| 素材边界声明 | 完整覆盖视频全程；AI 字幕存在音译错字（「memories x」=Memorix、「get it」=git、「aroma」为检索库名），已按语境转述 |

## 内容提炼
### 核心论点
1. AI 编程助手的「金鱼记忆」根子不在模型，在于记忆被锁死在一个 agent 的一个聊天窗口里——换会话全忘、换工具更惨（00:50）
2. 记忆应该跟着项目走，不住在聊天窗口或工具里，而是住在 git 项目根目录下：agent 是临时工、项目记忆是固定资产，换哪个 agent 都能查固定资产台账（01:46 / 02:09）
3. 四层记忆各答一类问题：观察记忆（事实/坑/实现细节——这个功能怎么工作）、推理记忆（决策理由——当时为什么这么选，最值钱，因为决策理由最容易消失在旧聊天记录里）、git 记忆（谁改了什么——最近改了什么）、代码记忆（记忆关联具体文件符号+新鲜度检查——现在该先看哪段代码）（03:49）
4. memory autopilot（记忆自动驾驶）：新会话丢一句任务，它不把所有记忆一股脑塞入，而是按任务性质挑定制简报（修 bug 给测试文件+复现步骤、发布给 package/changelog、新人给文档+入口、重构给架构决策记录），过期/无关记忆进「警示车道」不淹没提示词，并直接建议先读哪几个文件（05:12）
5. 渐进披露（progressive disclosure）：默认只暴露 7 个 MCP 工具，light/team/pro 模式按需打开——因为 MCP 工具越多，上下文的 schema 定义占得越满，留给真实任务的空间越少，agent 反而变笨（08:34）

### 关键机制
- 跨 agent 共享：Memorix 把自己做成 MCP 服务（Anthropic 开放标准），任何支持 MCP 的 agent 一条命令接入，覆盖 20+ 主流 agent（02:44-03:20）
- 新鲜度检查：一条记忆指向的代码如果已被修改，这条记忆被标记为过期或可疑，防止 agent 拿着过时记忆瞎指挥（04:54-05:08）
- autopilot 的简报配方按任务类型定制（05:21-05:56）；过期与任务无关记忆过滤进「警示车道」（05:57-06:06）
- local first：SQLite 是权威存储，本地全文+向量检索（aroma 库），LLM 参与记忆形成和向量化是可选增强——不配 API key 也能跑，配了质量更好；数据不出本机解决公司代码保密合规焦虑（06:16-07:10）
- 超出记忆本身的能力：orchestrate 多 agent 编排（拆大任务分给多个 worker，各自独立 git worktree 防覆盖，干完合并回主分支）、本地 dashboard（端口 3211）、自带终端编程 agent（08:03-08:30）

### 可操作细节
- 安装：memories setup <agent名> --global，一条命令接入（03:05-03:17）
- 项目数据：NPM 包名 memorix，月下载 2700+，GitHub 559 stars，最新版 1.1.13，Apache 2.0（03:25-03:41）
- 四档模式：micro（默认，7 个工具）/ light（完整单机记忆面）/ team（多 agent 协调工具）/ pro（全开+老接口兼容）（08:37-08:53）
- 使用场景判断：多 agent 混用者、长周期项目（半年到一年）、团队协作是刚需；周末写脚本/做 demo 加这层属过度工程（09:41-10:20）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记忆跟着项目走：仓库级锚定、agent 可替换 | 01:46 | 张力 | Kairos 以主体（认知存续单元）为记忆边界（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；TeamScope 多租户（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.20.6）提供归属单元但语义是隔离非锚定 | 未触及：记忆归属单元（主体 vs 项目）是 Kairos 未决问题，与外部场景锚定张力 T-002（[risks.md](../../../governance/risks.md) T-002）相关 | 若 Kairos 服务编程场景可考虑项目级视图投影；个人系统定位下项目记忆是主体记忆的投影 |
| 推理记忆：决策理由是最值钱的一层（为什么这么决定） | 04:12 | 已覆盖 | 认知完整性轴：反例锚点、死胡同路径的拓扑占位价值，结构性记忆守护（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5，标记 is_structure 不参与遗忘评估） | 支撑：决策理由类记忆与认知完整性轴同向 | Kairos 未将「决策理由」列为显式记忆类型，可在轴下显式化（可吸收点） |
| 新鲜度检查：记忆指向的实体被改→标记过期/可疑 | 04:54 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；freshness 三阈值（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5 遗忘调度器）；ADD-only 协议新旧观察并存（§7.3g） | 支撑 | 记忆与源码实体的关联检查可入 Kairos 接入层注记 |
| 渐进披露：默认 7 工具、复杂度按需打开 | 08:34 | 可吸收 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）是信息侧渐进披露；工具面/能力面渐进披露未显式声明 | 支撑：工具 schema 占用上下文与 Kairos 上下文腐烂经济性同理 | 可吸收至接入层工具暴露策略 |
| 记忆会累积噪音，工具给能力给不了判断 | 10:49 | 已覆盖 | 遗忘调度器「受控优化」（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）+ 元认知层监测（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §2）即主动打理职责 | 支撑：印证 Kairos 需主动治理机制而非只依赖检索 | 「反复出现的模式值得 promote 成永久 skill」与 Kairos 能力转化机制（认知基础 §1.3.1）呼应 |

## 存疑与未验证
- 「memories x」为项目 Memorix 的音译，拼写可能不准（未验证）
- 「aroma」检索库、「better SQL i S3」（better-sqlite3）为音译，实际库名未验证
- 下载量 2700+/559 stars/v1.1.13 为视频发布时数据，时间点未核对（未验证）
- 「20 多个主流 agent 全覆盖」为 UP 主转述，实际支持列表未验证
- 默认 7 个 MCP 工具的具体清单视频未给出（未验证）
- 「git 只记录了改了什么，没记录为什么这么改」为 UP 主观点陈述，准确（可复核 git 语义），但作为 Memorix 设计动机的表述为视频口径

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
