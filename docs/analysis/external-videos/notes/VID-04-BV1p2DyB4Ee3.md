---
title: VID-04 视频笔记：Agent记忆框架怎么选？5大Agent Memory项目工程级横向对比
aliases:
  - 外部视频笔记-04
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-04 Agent记忆框架怎么选？5大Agent Memory项目工程级横向对比

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1p2DyB4Ee3 |
| UP主 | 唐国梁Tommy |
| 时长 | 16min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字（MAM/Mem0/Leta/Rimi/MemU 等专名以字幕近似音为准） |

## 内容提炼
### 核心论点
1. Text-to-Mem：不是做一个记忆系统，而是给所有记忆系统定义一套通用操作语言——LLM 与存储之间插一层 IR（中间表示），把记忆操作收敛为 12 个原子操作、分 ENC/RET/STO 三阶段（00:52-01:40）
2. Mem0：开源社区热度最高的记忆中间件——三层架构（Memory API / LLM+向量检索逻辑层 / 存储层）+ 五个工厂模式（LLM 17 家、Embedder 11 家、VectorStore 22 种、GraphStore 4 种、Reanchor 5 种）；官方数据称比 OpenAI memory 准确率高 26%、响应快 91%、Token 省 90%（03:51-05:01）
3. Leta（原 MemGPT，2024年9月更名）：把操作系统虚拟内存思想完整搬进 Agent——Core memory（嵌在 System Prompt 每次推理可见，像 RAM）/ Archival memory（容量无限、向量检索、像磁盘）/ Recall memory（全部历史对话消息、像 OS 日志）；被驱逐的消息只是从 in-context 移到 out-of-context，可再检索，是「无损分层」（07:08-08:22）
4. Rimi（阿里 AgentScope）：文件即记忆——记忆直接存成 markdown 文件，用户打开就能看见、直接编辑、可 git 版本控制，「把记忆的控制权和透明度还给了用户」（09:48-10:13）
5. MemU：唯一主动型——24 小时常驻后台的 Bot 持续提取/整理/分类/预测用户意图并提前加载上下文；双 Agent 架构（MemUAgent 干活 + MemU Bot 只管记忆，实现仅是 asyncio.create_task 后台任务 + 共享 conversation.messages 列表）（11:15-12:15）

### 关键机制
- Text-to-Mem 12 原子操作分三阶段：ENC 阶段仅 Incode（记忆诞生）；RET 阶段 Retrieve（纯数据取回，几十毫秒）与 Summarize（完整 LLM 推理，延迟上千倍）分开——执行引擎可用完全不同的超时/缓存/降级策略；STO 阶段 9 个操作覆盖记忆生命周期（01:40-02:15）；操作统一为五元 JSON 结构：阶段/操作名/目标/参数/元数据（02:16-02:30）
- Text-to-Mem 安全双保险：元数据里 dryRun 与 confirmation 两个安全字段——危险操作要么先 dry-run 模拟一次、要么显式 confirmation，二选一强制；外层 JSON schema 校验格式、内层 Pydantic 校验业务逻辑（如 Promote 的绝对值和相对值必须恰好一个非空）——「不信任 LLM 但能兜住 LLM」（02:33-03:16）；Log 操作提供 ReadOnly/NoDelete/AppendOnly/Custom 审计模式，Reviewer 机制本质是 RBAC 风格的锁（03:18-03:35）
- Mem0 三种记忆类型：语义记忆（抽象事实性知识）、情景记忆（具体事件）、程序记忆（Agent 执行完整步骤、要求逐字保留——真正使用场景是崩溃后恢复执行状态）（05:01-05:19）
- Mem0 四个工程亮点：UUID 幻觉处理（LLM 对长 UUID 字符串会幻觉，把记忆 ID 硬射成 0/1/2 整数，LLM 只需决定「对第三条记忆执行 Update」，系统再映射回真实 UUID）；双存储并行（向量存储做语义相似搜索 + 图存储做关系推理，ThreadPoolExecutor 并行跑合并返回）；双 Prompt 策略（user memory extraction 只看用户消息、agent memory extraction 只看助手消息——防 AI 助手自我表达污染用户记忆，同时允许 AI 积累「我是一个什么样的 AI」的自我认知）；三层作用域隔离（用户/Agent/会话）（05:22-06:26）
- Mem0 成本瓶颈：每次 Add 完整模式调 2-5 次 LLM；token 随记忆规模线性增长——不适合高频实时写入，适合用户/对话维度中低频写入（06:27-06:53）
- Leta Core memory Block 三元组：Label（路径命名空间）/ Discrimination（告诉 Agent 这个 Block 干什么）/ Value（实际内容）；Limit 默认十万字符的强制压缩约束「逼迫 Agent 主动做信息蒸馏」；上下文窗口快满触发 Summarizer 默认驱逐 30% 消息写入 Recall memory（07:43-08:16）
- Leta Git Enabled Block Manager：Git 为真实来源 + PG 数据库为快速读缓存；每次记忆变更产生一次 Git Commit（携带 Agent ID/时间戳/变更原因）——不可篡改、完整历史回溯、并发安全（Git worktree 隔离修改）、每条 Commit 即审计记录；MemFS 把记忆组织成目录树（Agent 人格设定 / 用户偏好和事实知识 / 学到的技能和经验），每份记忆独立 markdown 文件（08:26-09:12）
- Leta Sleep Time Agent：用户不交互时后台持续自我改进——主 Agent 只负责推理和恢复（低延迟），每 5 步触发一次 Sleep Time Agent 读最近对话、分析更新 Memory Block；后台可用更大 Token 预算做深度反思（09:13-09:35）；代价：80 多个依赖包、数据库强依赖（09:39-09:43）
- Rimi Delta FileWatcher 增量监控：记忆文件累积到几十 KB 后每次变更全量重处理是 embedding API 巨大浪费；先检测文件是否纯追加模式，是则只处理新增部分——节省 92% API 调用；向量嵌入建在 window（窗口）上而非 content 上，因为用户查询与 window 天然语义接近（10:25-10:53）
- Rimi 性能：千问3-8B + Rimi 综合得分超过没有记忆的千问3-34B——「好的记忆系统可以让小模型打过 大模型」（11:03-11:10）
- MemU Salience Aware Memory（V1.4）：每条 MemoryItem 带 ReinforcementCount 计数器，每被检索一次加一，下次排序按强化次数加权——越常用的记忆越容易被再次召回，模拟人类「越常想到越容易想起」，UP 主称之为「给记忆加了一层肌肉记忆」；MemU 文件系统是概念隐喻（文件夹=Category、文件=MemoryItem、符号链接=交叉引用、挂载点=Resource），底层是数据库（12:19-13:08）
- 五项目定位总结：Text-to-Mem 做记忆的语言、Mem0 做记忆的中间件、Leta 做管理记忆的 Agent、Rimi 做人能看见的记忆、MemU 让记忆自己成为 Agent——「从 Agent 有记忆，到记忆本身是一个 Agent」（13:36-14:02）

### 可操作细节
- Text-to-Mem：12 原子操作 / 三阶段 / 五元 JSON 契约（01:37-02:30）
- Mem0：Add 完整模式 2-5 次 LLM 调用；五种工厂模式；ImportLLM 动态加载（无 Pancon 包不挂）（04:38-05:01）
- Leta：Core Block Limit 默认十万字符；Summarizer 默认驱逐 30% 消息；Sleep Time Agent 每 5 步触发一次（07:56-08:08 / 09:23-09:25）
- Rimi：增量检测节省 92% API 调用（10:39-10:42）
- MemU：ReinforcementCount 检索计数加权；Okamu 基准平均准确率 92.09%（13:11-13:16）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记忆操作语言化：12 原子操作 + 五元 JSON 契约 + 阶段分治 | 01:37-02:30 | 已覆盖 | 十二规范操作集（12 Canonical Operations，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3.1） | 支撑：操作集收敛与「契约是运行时投影」同向，Kairos 已有等价设计 | 差异：Text-to-Mem 以 ENC/RET/STO 三阶段显式分层，Kairos 操作集未按阶段分组；可作 §7.3.1 注记 |
| 危险操作强制 dryRun/confirmation 双保险 | 02:33-02:53 | 可吸收 | 19 条安全红线（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §8）；软删除而非物理删除 | 支撑：破坏性操作前置模拟与红线 fail-close 取向一致 | Kairos 未声明「危险操作须先 dry-run 或显式确认」的强制规则；可入红线实现注记 |
| Retrieve 与 Summarize 分离（毫秒级取回 vs LLM 推理，不同超时/降级策略） | 01:45-02:15 | 已覆盖 | 检索深度分级 R0/R1/R2，Token 成本比 0.05×/0.3×/1×（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：检索与生成解耦与 Kairos 分级检索同向 | 外部理念从「操作契约」角度提供分级依据 |
| 程序记忆逐字保留（崩溃后恢复执行状态） | 05:05-05:19 | 已覆盖 | 认知基础定义程序记忆为状态机轨迹（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.2）；确定性状态（§1.7） | 支撑：执行状态恢复是认知存续的工程等价物 | Kairos 类型学已含程序记忆（情景/语义/程序三类） |
| 双 Prompt 提取分离（用户消息/助手消息分渠道）+ 助手自我认知积累 | 05:54-06:15 | 可吸收 | 四层递进式摄取防御（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.4b）；身份面（§1） | 支撑：防助手表达污染用户记忆，与身份面「助手自我认知」可对接 | Kairos 未声明「助手侧自我记忆」独立积累通道；可作 §7.4 注记 |
| Git 版本化记忆（commit 带 Agent ID/时间戳/变更原因，可审计可回溯） | 08:26-08:59 | 已覆盖 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；可移植备份格式 .kairos（§5.15）；事件总线审计 | 支撑：不可篡改+完整历史与 Kairos 见证锚定（强一致主副本）同向 | 双存储（Git 真源+PG 读缓存）可作 Kairos 主/影子副本的存储实现参照 |
| Sleep Time Agent：后台大预算深度反思、主路径低延迟 | 09:13-09:35 | 已覆盖 | 防抖反射执行器（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §2.6.3）；探索预算独立 S-12（§8） | 支撑：后台反思成本归维护预算而非探索，与 S-12 兼容 | 与 VID-12 离线回顾、VID-03 Background Review、VID-06 AutoDream 同源理念 |
| 文件即记忆（透明可读可编辑可版本控制） | 09:48-10:13 | 可吸收 | 文件系统-向量索引一致性检查（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.16）；契约是运行时投影（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：可读性增强用户主权，与身份面/外部校准的可及性诉求同向 | Kairos 存储形态未定；Rimi 提供「透明文件」形态参照（但 Kairos 记忆有见证锚定，直接文件编辑需差异检验门禁） |
| ReinforcementCount 检索计数加权（使用越多越易召回） | 12:43-13:08 | 张力 | 使用价值轴（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；六级链「全程无标量聚合、逐维序数比较」（§2.1） | 挑战：单标量强化计数排序会丢失维度信息，与 P6 禁止聚合相抵 | 若仅作使用权重影子副本的累积信号（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5）则兼容；与 VID-12 热度值同源张力 |
| 主动预测式预取（用户未说话先加载上下文） | 11:40-11:50 | 已覆盖 | 检索预取策略（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.5）；Hermes provider prefetch recall 同源（VID-03） | 支撑：预取是检索管线优化，不改变价值裁决 | Kairos §3.5 已有预取；主动常驻 Bot 形态与「探索预算独立」需权衡后台常驻成本 |
| 小模型+记忆打败大模型（千问3-8B+记忆 > 千问3-34B） | 11:03-11:10 | 可吸收 | 记忆即使用（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1） | 支撑：为「记忆系统本身创造价值」提供实证论据 | 可作为记忆系统价值主张的外部实证引用 |

## 存疑与未验证
- 项目名均为 UP 主口语转述：Text-to-Mem（疑为 Letta/Text-to-Mem 项目）、MAM/MAMZERO（Mem0）、Lata/Leta（Letta）、Rimi（Rimi，阿里 AgentScope）、MemU（Memu）——拼写以字幕近似音为准，未逐一核对仓库（未验证）
- 「准确率高 26%、响应快 91%、Token 省 90%」为 Mem0 官方数据转述，未验证口径（未验证）
- 「千问3-8B+记忆超过千问3-34B」为 Rimi 项目性能数据转述，未验证（未验证）
- 「MemU Okamu 基准 92.09%」为 UP 主转述，未验证基准名称与口径（未验证）
- Leta「Limit 默认十万字符」「驱逐 30%」参数为 UP 主转述，未对照论文/源码验证（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
