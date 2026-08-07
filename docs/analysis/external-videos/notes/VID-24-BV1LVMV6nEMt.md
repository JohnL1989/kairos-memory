---
title: VID-24 视频笔记：如何构建Agent长期记忆系统？从底层逻辑到完整工程落地
aliases:
  - 外部视频笔记-24
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-24 如何构建Agent长期记忆系统？从底层逻辑到完整工程落地

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1LVMV6nEMt |
| UP主 | 小寒说IT |
| 时长 | 127min（10P） |
| 字幕来源 | B站 AI 字幕（ai-zh），抓取于 2026-08-07，内容与主题匹配度已人工核验 |
| 素材边界声明 | 部分P字幕串台不可用：10P 中仅 6P 字幕与主题匹配（P1 开场介绍、P2 长期/短期记忆概念、P4 AI对话无关联+checkpoint、P6 查询信息工具、P7 更新状态工具、P8 context/UID 与综合案例）；P3（字幕为电车评测）、P5（字幕为歌词《如果你也听说》）、P9（字幕为日剧情侣内容）字幕串台，已人工抽查确认，跳过不采用；直播课口头演示，字幕错字极多，转述依语境修正 |

## 内容提炼
### 核心论点
1. Agent 默认没有记忆，需要显式配置：通过 `configurable/thread_id`（session id）绑定会话，再指定 checkpoint 存储才能开启记忆；未设置时每次对话完全独立、前后无任何关系（P4 00:31-02:31 / P4 05:23-06:30）
2. 短期记忆 = 一个 session 会话内多轮对话的数据共享（记住会话内状态，如用户叫什么）；长期记忆 = 跨 session 共享的外部存储，与 session id 无关（P4 07:05-07:30 / P7 14:05-15:10）
3. 短期记忆可存内存（InMemorySaver）也可存外部数据库（SQLite/MongoDB/PostgreSQL 等）——存数据库才能实现对话历史持久化、刷新页面后仍能看到历史（P6 03:06-05:33）
4. 长期记忆以命名空间（namespace 元组）+ key/value 组织：namespace 内部呈树状结构（如 user→preference→K/V），用于组织与隔离；key 在同一 namespace 内唯一，重复 put 会被覆盖（P7 16:47-19:36 / P8 00:41-02:10）
5. 综合落地案例（电商客服助手）：短期记忆存当前会话订单状态（current order id）、长期记忆存跨会话用户偏好（商品类别+喜欢商品）、中间件做上下文摘要压缩（每 10 条对过去 5 条做总结）；换新 session 后短期记忆丢失、长期记忆偏好仍保留（P8 19:08-29:23）

### 关键机制
- checkpoint 机制：`InMemorySaver`（内存）或数据库 saver，首次运行自动建表，持久化每次对话状态（P4 02:35-02:48 / P6 00:02-00:31）
- 短期记忆的两种形态：仅在本次对话内共享（内存）vs 持久化存储（数据库）——按是否需要跨进程/跨重启保留来选（P6 04:57-05:33）
- 工具内读写状态：LangGraph 的 `ToolRuntime` 提供内置工具上下文，可从 `state` 读取自定义状态（如 user level）；更新状态必须返回 `Command(update=...)` 包装的消息，而非普通字符串（P7 03:12-07:13 / P7 12:26-13:35）
- context 参数传用户上下文（如 UID）：invoke 时单独传入 context，工具内通过 `runtime.context` 拿到，再以 namespace+key 去长期记忆 store 中 get 用户信息（P8 07:50-11:36）
- 长期记忆的读写 API：`store.put(namespace, key, value)` / `store.get(namespace, key)`，value 可为任意对象（字典）（P7 15:52-18:46 / P8 00:41-01:38）
- 综合案例中工具链：get_user_info（从 context 取 UID）→ query_order（查订单，更新状态）→ update_user_preference（写长期记忆）→ get_recommendation（读长期记忆做推荐）（P8 19:08-25:34）

### 可操作细节
- 固定写法：`configurable={"thread_id": "..."}` 作为 agent.invoke 的 config 参数，thread id 即会话 id（P4 00:57-01:31）
- 开启短期记忆：创建 agent 时指定 `checkpointer`（内存或数据库 saver）；数据库 saver 需 `.setup()` 初始化（P6 00:16-00:31）
- 长期记忆创建：`InMemoryStore`（内存）或数据库 store（如 MySQL saver），同样需 setup；创建 agent 时以 `store=...` 传入（P7 15:52-16:47 / P8 05:49-06:27）
- namespace 是元组，如 `("user", "preference")`、`("users",)`，先传命名空间再传 key（P7 16:47-19:36）
- 换 session 验证方法：重启进程 + 换 thread_id，短期记忆中的 order id 查不到、长期记忆的偏好（手机类/华为 P70）仍能推荐（P8 28:26-29:23）
- 上下文压缩：中间件「每隔十条会对过去的五条做总结」（P8 25:34-25:50）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 短期记忆=会话内状态共享，长期记忆=跨会话共享存储 | P4 07:05 / P7 14:05 | 已覆盖 | WM 层承载当前加工（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.3.2）；激活-存储解耦（三硬一软，§2.2） | 支撑：二分法与 Kairos WM/长期记忆分层同构 | Kairos 无「短期记忆」词，以 WM/激活态承载 |
| thread_id+checkpoint 显式开启记忆（默认无记忆） | P4 00:31 | 已覆盖 | 记忆写入需经摄取管道与提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g），非默认全收 | 支撑：记忆不是默认吞下一切，与 Kairos 摄取防御（§7.4b）同向 | — |
| namespace 树状结构组织长期记忆（元组路径） | P7 16:47 | 已覆盖 | 路径空间 `kairos://{domain}` 前缀即域分类锚点（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.2 / §7.3a） | 支撑：namespace 元组≈路径前缀，树状组织同构 | Kairos 路径空间更正式（注册表+硬过滤） |
| 同 namespace 同 K 直接覆盖旧值 | P8 01:38 | 张力 | ADD-only 提取协议（追加观察不覆盖，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；见证锚定主副本不可无声改写（§5.5） | 挑战：KV 覆盖式更新与追加式审计留痕取向相反，无声覆盖可能丢失见证 | LangGraph store 是工程 KV 语义；Kairos 需决策覆盖/版本化边界，建议对覆盖操作显式登记 |
| 工具通过 ToolRuntime 读/写运行时状态 | P7 03:12 | 可吸收 | 契约是运行时投影（三硬一软，[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；策略层 PM 降级路径（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.6） | 支撑：工具-状态互操作是运行时投影的工程实例 | Kairos 未声明工具如何读写记忆状态，可借鉴工具契约层 |
| 中间件每 10 条摘要过去 5 条（固定节奏压缩） | P8 25:34 | 张力 | 可审计压缩（三硬一软，[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；上下文腐烂 CRI 与降级（§1.9 / [architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 挑战：固定条数触发压缩是纯工程启发式，未考虑压缩损失监控；Kairos 要求压缩可审计、CRI 驱动降级 | 固定节奏可作为工程简化，但需补可审计性与损失观测 |
| context 显式传用户身份（UID/渠道），工具据此取长期记忆 | P8 07:50 | 已覆盖 | 路径前缀+归属上下文窗口承载上下文（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9 上下文-记忆相关性声明） | 支撑：运行时显式上下文与 Kairos 上下文-记忆相关性方向一致 | 视频为工程实现，Kairos 已登记 D-328 将其升格为一等概念 |
| 电商案例：偏好写长期记忆、会话状态写短期记忆的分工 | P8 19:08 | 已覆盖 | 使用契约决定生命周期（推论二，[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1） | 支撑：什么该跨会话保留由使用契约决定 | — |

## 存疑与未验证
- 直播课口头演示，字幕错字极多且人名/专名混乱：「绘画」=会话、「龙虾」指 OpenClaw、「EAV」=.env、「DEPSC/GIPSIC」=DeepSeek、「A针」=Agent、「三彩」=session 等（未验证逐字）
- P1 为直播开场白（课程资料与抽奖活动介绍），实质技术内容极少，仅确认主题为「长期记忆与短期记忆」（未验证后续 P 之外内容）
- 讲师所述 LangChain/LangGraph API（create_agent、ToolRuntime、Command 等）形态可能随框架版本变化（未验证）
- 「每隔十条对过去的五条做总结」为讲师对中间件行为的口头描述，未展示配置细节（未验证）
- P3/P5/P9 字幕串台（电车评测/歌词/日剧），其音频内容与主题关系无法从字幕确认，已整 P 跳过（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
