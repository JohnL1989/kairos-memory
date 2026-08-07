---
title: VID-49 视频笔记：从零构建生产级 Agent Memory（第三集：记错了比忘了更危险）
aliases:
  - 外部视频笔记-49
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-49 从零构建生产级 Agent Memory（第三集：记错了比忘了更危险）

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV15L3F6pEFN |
| UP主 | 老纪的技术唠嗑局 |
| 时长 | 4min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程（字幕至 297s）；whisper 转写存在谐音错字（「Roberts-based」=rules-based、「infmam」疑似 InFinMem、「optitate」=add 操作、「三本美式」=summarize 等） |

## 内容提炼
### 核心论点
1. 记忆系统最危险的不一定是忘了，更危险的是记错了还一直拿错的东西当真：用户改了地址系统没覆盖旧地址只是新增一条，下次下单搜到旧地址一本正经地用错；接口已不可用但 agent 还召回半个月前的经验——这时候记忆不是帮忙是添乱（00:00-00:19）。
2. Policy 是 MemoryOS 的控制中枢，不是装饰：决定什么时候读、读多少、什么时候写、怎么更新、什么时候删除（00:35-00:44）。
3. 规则型 policy（rules-based）短期能跑但很快到头：用户没说「记住」只是连续三次选同一方案，是稳定偏好还是偶然？用户纠正旧信息时是 add/update/delete 还是两个版本都保留？长期交互的变化不是几条 if-else 能覆盖的（00:45-01:20）。
4. agentic memory 的关键点：把记忆操作彻底工具化（add/update/delete 与 retrieve/compress/filter），让它们进入 agent 的动作空间——模型不再只是被动接收上下文，而是像控制手臂一样决定该拿什么、该写什么、该改什么（01:42-02:20）。
5. policy 管一整条链：检索前要不要想、检索时拿多少、回答后写不写、写的时候是新增/更新/删除；policy 必须可记录、可回放、可对比，最好还能放进 sandbox 做 A/B——因为 add 错一次长期滚雪球、delete 错一次证据直接丢、retrieve 错一次眼前推理就被污染（04:08-04:38）。

### 关键机制
- 记忆工具二分：长期记忆工具 add（存新知识）/update（修正旧事实）/delete（移除过时信息），对应参数化世界的训练/微调/遗忘管理；短期记忆工具 retrieve（语义搜索并注入）/summarize（压缩对话历史）/filter（移除无关上下文），对应激活相关信息/形成抽象表征/把干扰挡在外面（02:02-02:29）。
- 分阶段训练思路（HMM 类）：先练长期记忆（判断什么值得新增、什么在修正旧信息、什么根本不该写），再练短期管理（故意塞入干扰内容练过滤/摘要），最后把长期检索和短期整理放进复杂任务一起训练——像新员工入职先学规矩再学整理桌面再进真实项目（02:38-03:11）。
- 检索协议侧（infmam 类）解决 lost in the middle：pre-think——检索前先评估 agent 内部知识够不够回答，够就减少外部检索、降低延迟；adaptive early stopping——训练策略网络判断证据置信度，够了就立刻停止检索，报告把推理速度提升 3.9 倍；write 阶段把每次外部交换变成可优化的记忆更新决策，从 SFT 过渡到 RL（03:15-04:08）。

### 可操作细节
- adaptive early stopping 取代固定 top-k：传统 RAG 固定 top-k 每次拿固定数量，不管够不够、是不是太多；策略网络按证据置信度动态停止（03:36-03:52）。
- pre-think：检索前先想一下，评估内部知识是否足够回答（03:28-03:33）。
- 用户纠正场景的决策点：系统应该 add/update/delete 还是把两个版本都保留（01:08-01:16）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记错（旧事实被当当前事实）比忘记更危险 | 00:00-00:19 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §5.5（见证→使用仲裁差异检验）+ 价值独立性公理「好用≠真实」 | 支撑：Kairos 以见证锚定主副本+差异检验防「错当真」；外部实例（地址未覆盖）正是 Kairos 逻辑因果轴要处理的旧事实复活场景 | 与 VID-50 时间轴论点呼应 |
| Policy=控制中枢（读写更新删除的时机与量） | 00:35-00:44 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §3（策略层：检索预取/契约映射/决策模式管理）+ §5（遗忘调度器） | 支撑：Kairos 策略层即读写时机与量的控制者；外部仅到概念层 | — |
| 规则 policy 不够，需模型化 policy（LLM 控制记忆工具） | 00:45-01:20 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §4（推理皮层）+ §2（元认知层） | 支撑：Kairos 由推理皮层/元认知层承担判断，非固定规则；「长期交互变化多」正是 Kairos 用契约+校准应对的问题 | — |
| 记忆操作工具化进入动作空间（agentic memory） | 01:42-02:20 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §7.1a（MCP Bridge 接入方式） | 支撑：Kairos 已设计 MCP 接入；「add/update/delete/retrieve/compress/filter 六工具」可作为记忆操作暴露面的参考清单 | 增量：工具面清单候选 |
| 用户纠正→add/update/delete vs 保留两版本 | 01:08-01:16 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.4（用户纠正自动检测）+ §7.3g（ADD-only 提取协议） | 支撑：Kairos ADD-only 追加观察+新旧事实共存（§7.3g 示例：PostgreSQL 14/16 双观察），天然回答「保留两版本还是覆盖」 | 外部问题在 Kairos 有明确答案 |
| adaptive early stopping：检索量由策略动态决定而非固定 top-k | 03:36-04:08 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §3.9（检索深度分级 R0/R1/R2） | 支撑：Kairos 已分级检索而非固定 top-k；「证据置信度够了就停」可作为分级间切换的停止条件细节 | 增量：检索预算控制细节候选 |
| delete 错一次证据直接丢 → 遗忘操作必须可回放 | 04:23-04:32 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §2.2（三硬一软：遗忘受控优化）+ [架构](../../../foundation/architecture-v0.1.0.md) §7.3g（ADD-only：不物理删除） | 支撑：Kairos ADD-only 从机制上杜绝 delete 误删证据；外部警示从反面强化 ADD-only 合理性 | 外部警示可作为 ADD-only 设计理由的引用 |

## 存疑与未验证
- 「HMM 的训练思路」（音译，可能指某具体训练方法）——「分阶段入职」式训练流程为转述，无具体论文/参数（未验证）。
- 「infmam」（疑似 InFinMem）——lost in the middle 长文档推理的检索协议（pre-think/adaptive early stopping/right），具体论文名与「3.9 倍推理速度提升」数据均未核实（未验证）。
- 「Roberts-based policy」「optitate」「三本美式」等为转写错字，按上下文校正为 rules-based/add/summarize（未验证）。
- 「adaptive early stopping 报告 3.9 倍推理速度提升」为视频转述，原始论文数据未核对（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
