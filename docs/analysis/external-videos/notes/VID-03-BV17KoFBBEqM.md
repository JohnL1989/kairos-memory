---
title: VID-03 视频笔记：Hermes Agent 记忆架构详解：四层记忆系统持久化（长期事实/完整历史/外部）
aliases:
  - 外部视频笔记-03
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-03 Hermes Agent 记忆架构详解：四层记忆系统持久化

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV17KoFBBEqM |
| UP主 | 唐国梁Tommy |
| 时长 | 23min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字（如「Hermes/Hermis」混用、「Secretal」应为 SQLite、「缭码」应为源码等） |

## 内容提炼
### 核心论点
1. Hermes 记忆分四层：当前工作记忆（本轮 conversation 的 messages）→ 内建长期记忆（`Memory.md` 环境/项目/工具/约定 + `User.md` 用户画像/偏好/沟通方式）→ 完整对话历史（State.db 消息表 + FTS5 搜索 + Gateway 的 JSONLines transcript）→ 可插拔外部 Memory Provider（00:43-01:26）
2. 长期事实与历史轨迹故意拆开：稳定事实进 Curated Memory（`Memory.md``/User.md`），完整过程进 Transcript，需要时经 Session Search 回忆；混在一起会导致长期记忆被过程信息污染，或只剩偏好描述却想不起上次怎么修的 bug（01:48-02:16）
3. 长期记忆不是实时的：Session 启动时把 Memory 内容冻结成 System Prompt Snapshot，中途 Memory 工具写入立即落盘但不刷新当前 Session 的 System Prompt，真正注入要等下次 Session 启动——为了前缀缓存稳定，宁可牺牲实时体验（02:35-04:08）
4. 子代理默认没有 memory 工具，构造时显式传 scope 参数；探索/执行可以下放给子代理，但「值不值得进长期记忆」的判断留给上级上下文（onDelegation hook 收 task 和 result）（16:51-17:45）
5. 记忆不是一个大模块而是「上下文装配线」：内建记忆经 System Prompt 常驻、外部 recall 经 API call 临时注入、历史经 session search 汇入，全部汇入当前推理回合的 API messages（13:19-13:48）

### 关键机制
- 冻结快照与缓存稳定：System Prompt 是 Session 级缓存，第一次请求前构建一次、整个 Session 复用，只有 Context Compression 才失效重建；Gateway 场景优先读 Session DB 里上一轮保存的 System Prompt 而非按磁盘最新 Memory 文件重拼（03:08-03:46）
- 克制的最小记忆操作：纯文本文件、硬字符预算（```memory.md``` 默认 2200 字符、```user.md``` 默认 1375 字符）；单条操作只有 add/replace/remove 三种；replace/remove 靠短子串匹配而非 entryID，匹配多条且内容不一致直接报错让模型说得更具体；无知识图谱、无自动 embedding，文件可手工编辑（04:17-05:23）
- 写入安全：写前在锁内重读磁盘吸收其他 session/进程变更；tempfile + os.replace 原子写回（避免覆盖写的读空窗口）；写入前 stress scanning 扫 prompt injection/角色劫持/密钥诱导/SSH 后门暗示/隐形 Unicode——因为长期记忆是持久化 prompt 入口，污染一次后每个 session 都可能被污染（05:30-06:33）
- 完整运行轨迹存储：State.db 不只存 role/content，还存 tool call id、tool name、finish reason、reasoning details 等字段——保存的是 agent 运行轨迹而非普通聊天记录，reasoning 丢弃会导致恢复时上下文断层；SQLite WAL 多读单写 + begin immediate + 随机 jitter retry + 被动 checkpoint；FTS5 虚表经 trigger 同步（06:39-08:02）
- Session Search 召回管线：FTS5 搜关键词 → 匹配消息归并到所属 session → 读 session 完整 transcript → 辅助模型做 focus summary（面向 query 定向摘要）；query 为空走 recent sessions 模式（只返回标题/预览/时间戳，几乎零 LLM 成本）；最多总结 5 个 session；delegation 产生的 child session 向上 resolve 到 parent，并把当前 session 的线性上下文整条排除——防模型把当前上下文当历史重复召回（08:54-09:53）
- 外部 Provider 生命周期抽象：provider 可声明可用性、session 初始化连接、提供静态 System Prompt block、prefetch recall、turn 结束后同步、暴露工具接口；同一时间只允许一个外部 provider 生效（防工具表膨胀/召回冲突/幻觉调用）；prefetch 用原始 user message（非加工过的），recall 结果包在 memory context 标记里临时拼到 API messages、不写入 transcript——「召回结果写回历史会造成自我污染，系统最终分不清原始事实和临时补进去的解释」（09:26-13:07）
- Flush Memories（压缩边界知识转移）：压缩/reset/会话过期前，在消息列表末尾临时追加系统风格 user message「这段上下文马上要被压缩，请优先保存值得长期记住的东西，特别是用户偏好、纠正和重复模式」→ 发起只开放 memories 工具的一次额外模型调用 → 执行写入 → 移除 flush message 痕迹；走 auxiliary client 省主链路成本；外部 provider 另有 onPreCompress 钩子（13:52-15:23）
- 压缩不覆盖历史：结束旧 session、生成带 parent session ID 的 continuation session、压缩后的消息写进去——transcript 保留、lineage 保住，session search 依赖 lineage 感知避免重复召回（15:26-15:52）
- Background Review 兜底：turns since memory 计数器连续 10 轮无写入触发，fork 轻量 review agent（沿用当前模型）在用户收到最终回复后跑，用专门 review prompt 检查「有没有本该记住却没记下来的事实」——不跟主任务抢注意力（17:47-18:56）
- 共享边界建模：私聊按 chat 隔离、群聊可 group sessions per user、thread 默认共享 session；transcript 按 session key 隔离，外部 provider 初始化可拿到 user ID/agent identity——「对话共享和长期记忆归属可以分开设计」（15:55-16:50）

### 可操作细节
- ```memory.md``` 默认 2200 字符、```user.md``` 默认 1375 字符硬上限（04:23-04:31）
- 记忆操作仅 add/replace/remove 三原语（04:36-04:38）
- Session Search 最多总结 5 个 session（09:34-09:38）
- Background Review 触发阈值默认 10 轮（18:14-18:18）
- 压缩边界以「新 session 分支」而非「覆盖」实现（15:26-15:34）
- UP 主建议的改进方向：Curated Memory 加轻量结构化元信息（Scope/来源/更新时间/置信度）；Session 内可见但不打碎 System Prompt 前缀的 Overlay 记忆层；Session Search 从摘要模式扩展出 Artifact/Command/Decisions 结构化提讯模式（20:07-20:54）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 稳定事实与完整历史分库（事实进 Curated、过程进 Transcript） | 01:48 / 10:03 | 可吸收 | 见证锚定主副本与使用权重影子副本分离（[架构](../../../foundation/architecture-v0.1.0.md) §5.1）；确定性事实归档 DFA（§5.12）；三硬一软之「激活-存储解耦」（[认知基础](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：事实性与过程性的分离与「记忆服务于认知存续」同向，过程信息不占见证锚定 | 双副本+DFA 已承载事实/过程分离，但 Kairos 未声明显式「历史轨迹独立检索通道」；可作 §5.2 组件注记 |
| 冻结 System Prompt Snapshot（写入不实时生效，保前缀缓存） | 02:35-04:08 | 已覆盖 | 编译管线第四阶段组装哈希缓存（[架构](../../../foundation/architecture-v0.1.0.md) §4.3）；契约是运行时投影（[认知基础](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：缓存稳定与成本受控是工程必要；但「写入下次 Session 才生效」的体感滞后需 Kairos 决策投影时机 | 与 VID-10 的 frozen snapshot 同源理念 |
| recall 结果不写回 transcript（防自我污染） | 12:17-12:53 | 已覆盖 | 语境自指禁令 S-14：内部信号不得作为见证锚定真实性证据来源（[架构](../../../foundation/architecture-v0.1.0.md) §5.5 第9步） | 支撑：外部理念用工程语言独立推导出与 S-14 相同的结论 | 强呼应，可作为 S-14 的工程实证注记 |
| 压缩/重置边界作为主动知识转移时刻（Flush Memories + onPreCompress） | 13:52-15:23 | 可吸收 | 三级知识生产管道 raw→验证→归档（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）；知识加工区（[架构](../../../foundation/architecture-v0.1.0.md) §5.10） | 支撑：边界事件抽提与「记忆即使用」不冲突，归档时机显式化 | Kairos 未声明「压缩前强制抽提」显式事件；可入遗忘调度器设计注记 |
| 子代理不写长期记忆（scope 限制 + onDelegation hook 上级裁决） | 16:51-17:45 | 可吸收 | 写入权限 ACL（[架构](../../../foundation/architecture-v0.1.0.md) §7.6）；探索产物置信度带 30%→50%→70%→95%（§5.5） | 支撑：写记忆授权保守化与探索预算独立（S-12）同向，探索产物需验证后才可入见证 | Kairos 有 ACL 但未声明「子代理默认禁写」策略；与 S-12/探索产物置信度带呼应 |
| 后台 Review 兜底（连续 N 轮无写入触发复盘） | 17:47-18:56 | 已覆盖 | 防抖反射执行器（[架构](../../../foundation/architecture-v0.1.0.md) §2.6.3）；元认知层监测 | 支撑：写入欠压检测是元认知监测的合理子集 | 阈值 10 轮可作参考参数；与 VID-12 离线回顾、VID-06 AutoDream 同源 |
| 同一时间仅一个外部 provider 生效（防召回冲突） | 11:21-11:44 | 张力 | 外部校准源未建模为一等公民（T-002，）；分域真理观（[认知基础](../../../foundation/cognitive-foundation.md) §C.6） | 挑战：单一 provider 限制是工程收敛策略，但 Kairos 的分域真理观允许多源校准共存 | Hermes 的 provider 生命周期抽象（可用性/连接/prefetch/sync）可作为 T-002 未来建模的形态参照 |
| 原子写回 + 写前重读磁盘（多进程安全） | 05:30-05:57 | 未触及 | Kairos 纯文档设计，无并发写入实现细节 | 未触及 | 可作存储层实现注记 |

## 存疑与未验证
- 字幕将「Hermes」与「Hermis」混用，项目名以 Hermes 为准；「Secretal」应为 SQLite、「缭码/眼镜」应为源码/演进（whisper 谐音，未验证）
- 「```memory.md``` 默认 2200 字符、```user.md``` 默认 1375 字符」为 UP 主读源码转述，未对照 Hermes 仓库源码验证（未验证）
- 「background review 默认阈值 10 轮」同上，未验证（未验证）
- 「同一时间只允许一个外部 provider 生效」为 UP 主对源码行为的转述，未验证（未验证）
- 「state.db 存 reasoning details 等字段」为 UP 主逐字段转述，未验证字段名拼写（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
