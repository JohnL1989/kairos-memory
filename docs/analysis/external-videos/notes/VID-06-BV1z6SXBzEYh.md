---
title: VID-06 视频笔记：Claude Code 六维记忆体系深度解析
aliases:
  - 外部视频笔记-06
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-06 Claude Code 六维记忆体系深度解析

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1z6SXBzEYh |
| UP主 | 唐国梁Tommy |
| 时长 | 25min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字（`CLAUDE.md``/CLOUD.md` 混用、Memory/Memories 混用、AutoDream/Autodream、KROS/CHRONOS 模式等） |

## 内容提炼
### 核心论点
1. Claude Code 记忆体系分六个维度：指令记忆（```CLAUDE.md``` 多层优先级静态指令加载系统）/ 短期记忆（当前会话完整对话历史，内存中未压缩）/ 工作记忆（当前任务进度、偏好、响应状态）/ 长期记忆（磁盘 Markdown 文件分层知识库引擎，按用户画像/行为反馈/项目上下文/外部引用四类组织）/ 摘要记忆（Session Memory：后台子代理持续维护会话笔记，压缩时直接用这份笔记替代临时摘要）/ 休眠重塑记忆（AutoDream：满足时间+会话数条件后自动整合、清理、合并、去矛盾）（00:50-02:25）
2. 信息边界定义极严格：只有四类信息值得记（User 用户画像 / Feedback 行为反馈 / Project 项目上下文 / Reference 外部指针），代码模式、架构分析、文件路径、git 历史、调试方案「全都不存」——因为它们可以从代码本身推导出来，「代码就是最权威的来源，存一份副本只会过时、产生矛盾」（07:05-08:41）
3. 反馈记忆不仅记录做错还要记录做对：只记录错误会让模型过度保守，「记录成功的反馈是告诉 AI 这种做法是对的，以后继续这样」（07:24-07:42）
4. 记忆不是简单 System Prompt 注入，而是双轨注入：指令记忆走对话消息通道（第一条 user metamessage + System Reminder 标签，不在 System Prompt 数组里），行为规范（记忆类型/保存/召回操作指令）走 System Prompt Section 通道——两者缓存策略独立、Token 预算分配灵活（05:14-06:24）
5. AutoDream 模拟人类睡眠重塑：双重门控（距上次整合 ≥24 小时且期间至少 5 个不同会话产生新记忆）+ 四阶段（Orient 定向探索 → Gather 信息收集 → Consolidate 整合 → Prune and Index 修剪索引）+ CAS 锁机制（12:30-14:43）

### 关键机制
- ```CLAUDE.md``` 四层优先级：Manage（企业级 .claude 目录，全局策略）< User（home 目录私有全局）< Project（项目根目录，入库团队共享）< Local（`.local.md` 私有不入库）；加载顺序：从 CWD 向根目录遍历收集后反转顺序处理——「离当前工作目录越近的规则文件加载越靠后，模型对它的关注度越高，最后加载的规则优先级最高」（03:04-04:10）
- 三种扩展机制：@include 递归包含（最多五层深度+循环检测）；条件规则（Front Matter PATS 路径条件 + Picomatch Glob 语法，只在访问特定路径时生效）；嵌套记忆附件（工具访问 CWD 子目录文件时自动加载目录链上的额外规则）——「不是一股脑全部加载，而是有选择性、按需、分层注入」（04:14-05:09）
- 长期记忆存储：home 目录 .claude/projects，按 git 仓库根路径清理化后作子目录名；worktree 共享同一记忆目录（用 canonical git root 而非普通 root）；两层结构——`Memory.md` 纯索引文件（每行链接+一句话摘要 ≤150 字符，整个文件 ≤200 行 25KB）+ 具体记忆文件（Front Matter：名称/描述/类型）（06:42-09:06）
- 动态相关性召回（Prefetch）：每轮对话开始异步预取（与模型响应并行，不阻塞主流程）——扫描记忆目录所有 Markdown 只读前 30 行 Front Matter 提取描述，用 Claude Sonnet 做旁路查询判断哪些记忆最相关；约束：最多返回 5 篇、不确定就不选、已展示过的过滤、最近使用过的工具相关文档压低优先级防污染——「把选择相关记忆当成一个独立的 AI 决策任务，而不是传统关键词匹配或向量检索」（09:17-10:13）
- 记忆新鲜度系统：召回记忆标注年龄用自然语言（今天/昨天/47 天前）而非绝对时间戳——模型不擅长日期计算，「47 天前」比日期更能触发成就性推理；超过一天附带警告「记忆是时间快照不是实时状态，引用之前要先验证」——「记忆说某个东西存在不等于它现在还存在」（10:16-10:47）
- 自动记忆提取（extract memories）：每轮对话后主代理不自己写记忆（会干扰对话流），后台 fork 子代理回顾最近对话提取值得长期保留的信息；互斥设计：若主代理最近已直接修改记忆文件，子代理跳过本次提取只推进游标（避免双写冲突）；子代理两回合策略（第一轮并行发所有读请求、第二轮并行发所有写请求——文件编辑工具要求先读后写，最大化并行）；轮次上限 5 轮、禁止调查验证（不 grep 源码、不 git log、不确认 pattern 存在）防验证兔子洞；工具权限：可读任意文件、可 grep，但写操作只能针对记忆目录内路径，不能执行写入性 shell 命令、不能调 MCP 工具、不能触发其他 agent（10:51-12:26）
- AutoDream 四阶段：Orient（浏览记忆目录看有哪些文件、索引有没有重复主题）→ Gather（查看最近日志、检查与代码库当前状态矛盾的旧记忆，只用精确搜索词不作宽泛扫描）→ Consolidate（新信息合并到已有主题文件而非创建近似副本；相对日期转绝对日期；被推翻的旧事实直接删除而非标注过时）→ Prune and Index（`Memory.md` 保持 200 行内、索引 ≤150 字符、删陈旧指针、压缩冗长条目解决矛盾）（13:08-14:09）
- AutoDream 锁机制：锁文件修改时间=上次整合时间、内容=持有者 PID；CAS 竞争检测（写 PID 后读回，发现不是自己 PID 说明另一进程同时获取锁，先写的退让）；整合出错回滚（修改时间回退到之前的值保证下次触发）（14:11-14:43）
- Session Memory（会话级持续记忆）：对话超 10 万 token 触发压缩前，后台子代理持续维护 Session `Memory.md`（固定章节：会话标题/当前工作状态/任务规格/涉及关键文件和函数/工作流步骤/遇到的错误和修正）；触发双阈值（上下文总 token 达最小值 + 自上次更新以来足够 token 增长或工具调用）；压缩时直接用已维护笔记而非临时生成摘要——「渐进式维护的摘要质量更高，不是压缩那一刻临时生成的」（14:47-16:05）
- Calculate Messages to Keep Index 算法：从上次压缩位置计算未压缩部分 token 量，不够最小阈值向前扩展但不能超过最大阈值、不能回退到上一压缩边界之前；保留边界遵守 API 不变量——每个 tool_use 必须有对应 tool_result，压缩边界不能切在 tool 调用对中间否则 API 报错；流式响应分段的消息要确保 thinking block 关联性不被破坏（16:05-16:56）
- 团队同步记忆：远端 API 跨栈同步数据库，team 子目录（私有+团队两套并存）；服务端优先（pull 时服务器覆盖本地、push 只上传内容哈希变化的条目）；删除不传播（本地删团队记忆文件下次 pull 恢复，避免一人误删影响整个团队）（17:01-17:36）
- 安全两道防线：路径防护防 Symlink 逃逸（恶意仓库在团队记忆目录放指向 ~/.ssh 的符号链接；Path.resolve 字符串级规范化 + realpath 文件系统级解析；悬垂 symlink 直接拒绝——readfile 会跟随 symlink 在目标位置创建文件；URL 编码路径遍历和 Unicode 全角字符攻击都考虑）；敏感数据审查（写团队记忆和同步推送前正则+关键词过滤 GitHub PAT/AWS Access Token 等，一旦检测到直接拦截）——「团队共享的特性，安全性必须比个人特性高一个等级」（17:41-18:49）
- 三层独立缓存：Get Memory Files 的 memorize 缓存（Memory 文件解析结果：读盘/Front Matter/@include/剥离 HTML 注释，只在第一次调用执行）；Get User Contexts 的 memorize 缓存（拼接后用户上下文对象，含最终 `CLAUDE.md` 字符串和当前日期）；System Prompt Section cache（Map 按 Section 名缓存，Load Memory Prompt 结果整个会话只算一次）；三层缓存清除互不联动（clear/compact 清全部三层、memory 斜杠命令只清第一层）；代码中无 `CLAUDE.md` 热重载——会话中途手动改磁盘 `CLAUDE.md` 在缓存清除前模型看不到，唯一文件系统 watcher 监控团队同步状态而非项目根 `CLAUDE.md`；「热重载引入复杂一致性、行为不可预测，宁牺牲实时性也要保证确定性」（20:17-22:04）
- Feature Flag 三级开关：远程下发的 flag（AutoDream 触发间隔、Session Memory token 阈值、extract memories 轮次节流可远程调整不发布新版本，用于灰度 AB 测试）；编译式 flag（团队记忆、CRONOS 模式、记忆遥测构建时决定）；环境变量（完全禁用自动记忆、覆盖记忆路径的本地覆盖）（22:06-23:01）

### 可操作细节
- `Memory.md`：≤200 行、25KB，每行索引 ≤150 字符（08:51-08:55 / 13:52-13:56）
- Prefetch：每轮最多返回 5 篇；只读前 30 行 Front Matter（09:47-09:51）
- AutoDream 门控：≥24 小时 + ≥5 个不同会话产生新记忆（12:39-12:45）
- extract memories 子代理：轮次上限 5 轮、两回合读写并行策略（11:37-11:58）
- Session Memory 压缩触发：对话超 10 万 token（14:55-14:58）
- 相对日期必须转绝对日期（如「下周五」→「2026年4月10日」）（08:01-08:09）
- Agent 持久记忆作用域：Global 跨仓库共享 / Project 入库团队共享 / Local 本机独享；支持 JSON 快照迁移（18:53-19:22）
- CRONOS 日志模式：追加式日志 + `Memory.md` 只读 + 夜间 Dream 整理；System Prompt 给路径模式而非写死日期（避免午夜日期翻转缓存失效）（19:24-20:15）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 六维记忆分层（静态规则/短期/工作/长期/摘要/休眠重塑） | 00:50-02:25 | 已覆盖 | 六层架构 + WM 层（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §6）；宪法主权面（§1）；遗忘调度器（§5） | 支撑：分层边界清晰与 Kairos 架构同构 | 「摘要记忆」维度（持续维护的会话笔记）是 Kairos 未显式建模的层，可作 WM 层注记 |
| 「可从代码推导的信息不存」（代码就是最权威来源） | 08:17-08:33 | 已覆盖 | 契约是运行时投影（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；确定性事实归档（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.12） | 支撑：可推导信息不入记忆与 Kairos 存储最小化、运行时投影同向 | 与 VID-10「该扔的/该缓存的/该存的」三分类同源 |
| 反馈记忆记录成功（不仅纠正，防过度保守） | 07:24-07:42 | 可吸收 | 用户纠正自动检测（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.4）；校准信号（外部校准端口） | 支撑：正向确认防过度保守，与「使用价值驱动」同向 | Kairos 侧重纠正检测，正向确认未显式建模为反馈类型；可入 §7.4 注记 |
| 双轨注入（用户指令走消息通道 vs 稳定行为规范走 System Prompt Section） | 05:14-06:24 | 已覆盖 | 编译管线多阶段动态组装 + 组装哈希缓存（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §4.3） | 支撑：可变内容与稳定内容分离注入与 Kairos 编译管线同构 | Kairos 编译器（认知基础 §1.8）已有动态组装；双通道实现细节可作参照 |
| 动态相关性召回用轻量 LLM 旁路决策（不确定就不选、已展示过滤） | 09:17-10:13 | 已覆盖 | 三信号混合检索 + 5D 混合排序（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；MMR 去重（§7.3c） | 支撑：检索决策独立化与 Kairos QueryAnalyzer/策略层同向 | 「不确定就不选」的拒绝机制可作检索门禁注记 |
| 自然语言年龄标注 + 「记忆是时间快照不是实时状态」警告 | 10:16-10:47 | 可吸收 | 时间轴（物理衰减+逻辑因果双轴）（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；上下文腐烂 CRI（§1.9） | 支撑：时间性显式化与 Kairos 时间轴同向；「引用前先验证」与见证锚定一致 | Kairos 未声明「召回时附带时效警告」机制；可入检索元数据注记 |
| AutoDream 双重门控 + 四阶段整合 + CAS 锁/回滚 | 12:30-14:43 | 已覆盖 | 防抖反射执行器（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §2.6.3）；遗忘调度器（§5）；探索预算独立 S-12（§8） | 支撑：整合归维护预算、门控防高频触发与 Kairos 调度模型一致 | 门控参数（24h/5 会话）可作参考值；CAS 锁为多实例实现细节 |
| 被推翻旧事实直接删除而非标注过时 | 13:41-13:46 | 矛盾 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；持久归档阶段更新需版本化而非覆盖（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.10） | 挑战：物理删除破坏审计与回溯，与 Kairos「见证锚定不可覆盖、版本化更新」直接冲突；也损失「去年此时什么是真的」的时间旅行能力（VID-10） | 不采纳物理删除；Kairos 以 superseded 标记+软删除承载「被推翻」语义 |
| 压缩边界遵守 tool_use/tool_result API 配对不变量 | 16:24-16:48 | 可吸收 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）驱动压缩；WM 层（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §6） | 未触及：Kairos 纯文档未声明压缩边界完整性约束 | 工程细节，Kairos 实现阶段可吸收为压缩器契约 |
| 团队记忆「删除不传播」（防一人误删影响团队） | 17:28-17:36 | 已覆盖 | TeamScope 多租户隔离（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.20.6 P3-17）；外部校准共享治理 | 支撑：共享面写入保守化与 Kairos 身份/宪法面一致 | 可入 §5.20.6 注记 |
| Symlink 逃逸防护 + 敏感数据过滤（共享面安全等级更高） | 17:41-18:49 | 已覆盖 | 19 条安全红线（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §8）；写入权限 ACL（§7.6） | 支撑：与 Kairos 红线体系同向 | 具体攻击面（symlink/悬垂链接/URL 编码/全角字符）可入红线实现注记 |
| 三层缓存互不联动 + 拒绝热重载（宁牺牲实时性保证确定性） | 20:17-22:04 | 已覆盖 | 编译管线组装哈希缓存（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §4.3） | 支撑：确定性优先与 Kairos 编译缓存同向 | 张力点：Kairos「契约是运行时投影」若取运行时热更新语义则与此取舍不同——需 Kairos 决策投影时机（同 VID-03 冻结快照） |
| Feature Flag 三级开关（远程/编译式/环境变量） | 22:06-23:01 | 已覆盖 | 核心假设与特征标志（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §0.8） | 支撑：Kairos §0.8 已有特征标志工程语义 | 三级分类（远程灰度/编译总开关/环境覆盖）可作 §0.8 实现参照 |
| CRONOS 日志模式：追加式日志 + 路径模式避免日期缓存失效 | 19:24-20:15 | 可吸收 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g） | 支撑：长生命周期会话下 ADD-only 日志化与 Kairos ADD-only 同向 | 「System Prompt 不写死日期」是编译管线的缓存一致性细节，可作 §4.3 注记 |

## 存疑与未验证
- 字幕将 `CLAUDE.md` 与 `CLOUD.md`、Memory 与 Memories、CLAUDE Code 与 Cloud Code 混用，正名为 Claude Code / `CLAUDE.md`（未验证）
- 「Manage 层级在 EDC（企业级 .claude 目录）」的「EDC」一词字幕音近，具体目录名未验证（未验证）
- 「AutoDream」「extract memories」「Session Memory」「CRONOS 模式」等模块名为 UP 主对 Claude Code 源码的转述命名，非官方文档名称（未验证）
- 「KROS/CRONOS 日志模式」字幕两种音都有，模式官方名称未验证（未验证）
- 「Gloatbook 远程下发 flag」字幕音近（疑为 LaunchDarkly 或类似平台），平台名称未验证（未验证）
- 「对话超 10 万 token 触发压缩」为 UP 主转述默认阈值，未验证（未验证）
- 视频结尾的 Feature Flag 体系（远程调整 AutoDream 间隔等）为 UP 主对源码的推断性描述，未验证（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
