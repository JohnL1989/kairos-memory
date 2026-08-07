---
title: VID-73 视频笔记：07 吐血整理的 Agent memory 设计
aliases:
  - 外部视频笔记-73
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-73 07 吐血整理的 Agent memory 设计

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1gRNF6PE48 |
| UP主 | AI_Julie |
| 时长 | 18min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字 |

## 内容提炼
### 核心论点
1. LLM 原生内存三大短板：上下文长度有限（128K），多轮对话+大量工具调用极易超限（agent 里写 100-200 个 tool 就可能超）；超长历史产生上下文飘移、模型丢失早期关键信息；新对话无记忆隔离、每次从零开始（00:38 / 01:33 / 02:17）
2. 不要把模型支持的上下文填满：它说支持 128K 你就不要去填 128K，否则必然幻觉——幻觉很多时候是设计导致的，不是模型的问题（01:56 / 02:04 / 02:11）
3. memory 系统的本质：agent 的 memories 折腾半天就是为了得到一个非常优质的 context——这就是 context engineering 的意义（01:15 / 01:24）
4. 完整分层：短会话=对话历史+工作内存；多轮跨会话用语义检索或 keyword 搜索做基础长期存储；超长周期高频工具调用用观测记忆分层压缩、分级遗忘，持续控制上下文长度同时永久沉淀关键信息（15:18 / 17:53）

### 关键机制
- 记忆体系分层：跨会话长期记忆信息 + 压缩 + 遗忘；short memory 分两层——conversation history（窗口，近 5-10 条连入 context）与 working memory（对本次会话的约束：system prompt、人设灵魂注入等关键信息，但不能太多，「什么都限制上就是一锅酱糊」）（03:18 / 03:32 / 04:02）
- working memory 特点：存储稳定不变的少量关键信息（用户姓名、需求目标、输出偏好——喜欢事实性输出还是比喻输出）；几轮/几百轮对话后仍保持固定核心事实（因为很短、设定好后有变化才更新）；轻量化适合任务持续性（05:15 / 05:49 / 06:00）
- 会话流程：用户输入 → 对话历史 message list → 判断是否超出滑动窗口（超则截断最早消息按条数保留最近 N 轮，或按 token 保留 200/2000 个）→ 常驻 system prompt 不参与截断 → 按用户输入召回 working memory（RAG 里的东西）→ 拼装成 prompt 输入 LLM（06:14 / 06:34 / 06:53）
- semantic recall 的替代：未必用 RAG——最近 keyword search 用得多：记忆存 markdown 文件、用时 keyword 搜索；或 markdown 分片存 BM25 库、搜索弹出 top-k chunk；问题在于 top-k 检索范围需反复调参（可能不够或太多）；semantic 搜索「总是搜不到最满意的东西」，markdown 写得好 keyword 效率更高（Google 搜索大部分就是 keyword，关键字往往最重要）（07:20 / 07:52 / 08:24）
- 全流程：用户输入/新会话 → 导入 working memory 高频固定信息 → query embedding 或 keyword search 去 memory/RAG 检索 top-k → 加相关历史片段 → 拼装上下文 → LLM 回答 → 每轮对话原话存向量数据库；进一步优化：每 N 轮做 summary，选择性遗忘垃圾信息——不要每轮结果都塞向量库，否则库越来越庞大、检索越来越不准（08:51 / 09:28 / 09:39）
- Observation memory（观测记忆）：模拟人类记忆+遗忘机制；人类总是适时遗忘（「遗忘了反而更豁达」）、脑容量有限必须选择性遗忘；顶级的长期记忆设计是「压缩分级存储+主动遗忘不重要信息+异步 Agent 自动处理不阻塞对话」（09:46 / 10:20）
- Observer 观测器：对话 token 超过阈值时后台异步运行——把完整对话+工具返回的海量文本精简为观测摘要，几十倍压缩 token，只保存关键事实、丢弃无效内容；system prompt 很重要：要告诉大模型丢弃无关事实、只 summary 重要信息；按 token 数压缩而不是按轮数（大模型认 token 不认轮数，一轮就可能超 2k）（10:20 / 11:00 / 11:19）
- Reflector 反射器：观测摘要累积再次超限后做二次聚合——压缩剔除过期、重复信息，合并重复的用户偏好，实现选择性遗忘；两次压缩的原因：第一次是 token 超限，第二次是检查新旧记忆的相关/重复/冲突后一起二次聚合（11:41 / 13:00 / 14:09）
- 优势清单：观测摘要稳定不变支持 prompt 缓存；异步后台执行不打断用户对话；适配工具调用返回超大文本场景；跨会话长期保留用户稳定习惯细节（12:18 / 12:36）
- 统一分层逻辑：完整原始消息 → Observer 压缩观测记录（token 超限才压缩）→ Reflector 二次聚合精简循环往复 → 关键信息沉淀、低价值遗忘；上下文负载必须持续降低，否则上下文越来越长、幻觉越来越明显（「会话聊多了 agent 越来越傻」）（15:18 / 16:01 / 16:26）

### 可操作细节
- 滑动窗口参数：按条数（近 5-10 条）或按 token（200/2000 个）（03:32 / 06:34）
- 场景-方案匹配表：短交互=只用对话历史；会话多轮长任务=对话历史+工作内存；多会话反复新建线程=加 RAG 语义搜索；超长期高频工具调用=观测记忆分层压缩（17:53）
- Observer/Reflector 阈值：token 超阈值触发压缩；摘要再次超限触发二次聚合（10:20 / 11:41）
- 检索弹出：向量库 top-k 或 keyword 或 hybrid（UP 个人偏好 keyword）（14:57 / 15:05）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 三大原生短板（超限/上下文飘移/无隔离） | 00:38 / 01:33 / 02:17 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；时间轴逻辑因果（§1.1） | 支撑：飘移=CRI 的早期信息丢失形态；无隔离=跨会话连续性缺失 | 与 VID-69 第一层补丁缺点同族 |
| Observer 观测器：token 超阈后台异步压缩、几十倍压缩只留关键事实 | 10:20 / 11:00 / 11:19 | 可吸收 | 可审计压缩硬约束（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；探索预算独立（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §8 S-12） | 支撑：后台异步不阻塞对话 = 压缩消费离线资源与探索预算独立/低峰期巩固同向；「按 token 不按轮数」是压缩触发参数 | 与 REPO-01 Dreaming 成组处理可合并吸收 |
| Reflector 二次聚合（查冲突/重复/过时后新旧一起压缩） | 11:41 / 13:00 / 14:09 | 可吸收 | 遗忘调度器（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5）；差异检验 11 步（§5.5）；分域真理观（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §C.6） | 支撑：二次聚合时的冲突检查是校准/差异检验的压缩期形态；「剔除过期/重复」落在时间轴+使用价值 | 可作为遗忘调度器「受控优化」的具体算子参照 |
| 选择性遗忘（人类适时遗忘、脑容量有限） | 09:46 / 10:15 | 已覆盖 | 遗忘调度器资源再分配（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5）；遗忘受控优化（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：遗忘是资源约束下的权衡（P4）的通俗表述 | — |
| keyword/BM25 优于 semantic（markdown 写得好效率更高） | 07:20 / 08:24 | 已覆盖 | 三信号混合检索：向量/全文/时间（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：BM25 即全文信号——外部实践独立支持「不止向量」立场 | 与 VID-72、VID-69 keyword 主张同族 |
| working memory 常驻稳定核心事实（几百轮不变） | 05:15 / 05:49 | 已覆盖 | 身份面否决权（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；可配置 Profile Schema（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.14） | 支撑：姓名/需求目标/输出偏好常驻 = 身份面/Profile 的独立实现 | — |
| 观测摘要稳定支持 prompt 缓存 | 12:18 / 12:36 | 可吸收 | 编译管线组装哈希缓存（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §4.3 第四阶段） | 支撑：摘要稳定不变是缓存命中的前提，与编译管线缓存同向 | 可作缓存层设计注记 |
| 上下文负载必须持续降低（聊多了变傻） | 16:26 / 16:47 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；注意力调度器 token 预算（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §9） | 支撑：CRI 的经验表述 | — |
| 场景-方案匹配表（短/中/长/超长） | 17:53 | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；六层架构 | 支撑：按场景选记忆方案与分级检索同构 | — |

## 存疑与未验证
- Observer/Reflector 机制为 UP 主整理的外部设计（来源未指明，可能是某记忆系统文档），未给出来源出处（未验证）
- 「观测摘要几十倍压缩 token」无基准/评测支撑（未验证）
- 「语义搜索总是搜不到最满意的东西」为 UP 实践经验，无量化对比（未验证）
- 「Long memory evaluate 行业长记忆准则测试表现优异」为转述声称，无具体测试名与数据（未验证）
- 转写错字：「偷肯」（token）、「语意解锁/语义检索」（语义检索）、「kwz色血/kwords色情」（keyword search）、「相量数据库」（向量数据库）、「disdue/争留」（蒸馏）、「reflective hash」（reflector）、「一锅酱糊」（一锅浆糊）、「大樓」（大佬）、「绘画」（会话）等，术语以语义还原

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
