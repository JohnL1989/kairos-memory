---
title: PAPER-03 论文分析：Zero-Mem——为 LLM 智能体实现零 token 记忆操作
aliases:
  - 外部论文分析-03
tags:
  - kairos
  - external-videos
  - paper-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# PAPER-03 Zero-Mem: Zero-Token Memory Operations for LLM Agents（零 token 记忆操作）

## 元信息
| 项 | 值 |
|:--|:--|
| 论文 | Zero-Mem: Zero-Token Memory Operations for LLM Agents |
| 链接 | https://arxiv.org/abs/2607.29377 |
| 日期 | 2026-07-31（arXiv 提交，与 AI HOT 收录同日；检索口径另有 2026-08-03 出版一说） |
| 作者（检索口径） | Yilin Xiao、Zhehan Zhu、Yujing Zhang、Jin Chen、Zijin Hong、Luyao Zhuang、Qinggang Zhang、Shengyuan Chen、Xiaocao Ouyang、Lingfei Ren、Xiao Huang |
| 来源 | AI HOT 学术档案（`outputs/agent-memory-archive.html`）+ WebSearch 聚合（HuggingFace Daily Papers / scirate / chatpaper / Open Source For You 等） |
| 分析日期 | 2026-08-07 |
| 素材边界声明 | arxiv 域名直抓被网络策略拦截，未读原文全文；机制与数字经多来源聚合交叉核对；路由系数 ρ 公式、图构建参数、校准规则细节标注「未验证」；**代码未公开**（同行评审后 release），57.6% 与最高 F1 为作者声称，未见第三方复现（ic.work 亦指出未独立验证） |

## 核心机制（问题/方法/实验）

**问题**：常规 agent 记忆系统反复调用 LLM——总结对话、生成中间记忆记录、调解检索——这些生成式记忆操作带来**反复出现的 token 与时间成本**；且省略或合并细节会**遮蔽原始证据**。论文问：结构化记忆访问是否必须依赖生成（LLM 调用）？

**Zero-Mem 方法**：**零 token 记忆操作**——除最终问答外，记忆构建、检索、校准**均不调用 LLM、不消耗 LLM 输入/输出 token**（编码器计算另行核算）。不生成摘要，而是**保留原始交互轨迹作为唯一源记录（source of record）**，在其上构建两个互补视图：

1. **实体-上下文图（Entity-Context Graph）**：链接实体与其周围交互上下文，暴露跨会话/跨对话的关系。检索用实体对齐（余弦相似度）+ 共现激活传播 + **personalized PageRank（PPR）沿图扩散证据**（可捕获扁平相似度搜索漏掉的二、三阶邻居连接），稠密上下文匹配作兜底；
2. **时间层级（Temporal Hierarchy）**：保留对话顺序、会话边界与局部上下文，提供由粗到细的 **Episode → Window → Turn → Local** 检索路径，显式维持时序与时间局部依赖。

对每个查询：**动态权衡两个视图**（路由系数 ρ），从两视图分别检索并融合结果（查询级归一化 + ρ），产出带界上下文的去重证据集。

**确定性校准阶段（零模型调用）**：硬约束过滤候选（源/查询边界）、按主题/时间/答案类型兼容性重排、最终答案校准（归一化、抽取式截断、列表修剪）——使 reader 锚定在检索轨迹上。索引用常规 NER（非 LLM）、BM25 词法检索、BGE-M3 稠密嵌入。**仅最终问答 reader 调用 LLM**。

**实验**：长记忆与长上下文 QA 基准——**LoCoMo**（多会话对话记忆）与改进版 **HotpotQA**（上下文达 448,000 token）；对比 A-Mem、Mem0、MemoryOS、LightMem、SimpleMem、CompassMem、GAM 与长上下文检索基线。

## 关键发现与数据

| 发现 | 数据（作者声称口径，未独立验证） |
|:--|:--|
| 性能竞争 | 在消除全部记忆操作中的 LLM 调用与 token 消耗的同时达到竞争性表现（一份报告口径称最高 F1） |
| 时间成本大幅下降 | 相同最终 QA reader 与上下文预算下，记忆操作时间成本较最快基线降 **57.6%** |
| 双视图均有贡献 | 消融实验支持两个视图各自的贡献与查询依赖的协调 |
| 口径澄清 | 「零 token」= 零 LLM 生成调用；**编码器/嵌入计算另行核算**——记忆管理整体并非零成本，部署总成本仍取决于嵌入量、索引维护、存储与查询频率 |
| 开放状态 | 代码计划同行评审后在 github.com/TheMoon0815/Zero-mem 公开（截至分析时未公开）；57.6% 与性能数字为作者声称，待第三方复现 |

## 与 Kairos 的映射点

| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 「原始交互轨迹作为唯一源记录（不生成摘要）」 | 已覆盖（强印证） | [架构](../../../foundation/architecture-v0.1.0.md) §7.3g ADD-only 提取协议 + §5.5 见证锚定主副本 + [认知基础](../../../foundation/cognitive-foundation.md) §2.2 三硬一软（激活-存储解耦） | 支撑：Zero-Mem 实证「不压缩原文、轨迹为源」可行且性能竞争 | 与 Mem0 ADD-only、VID-47 原始账本互为印证（分诊矩阵 EV-09 同族，新增独立实现） |
| 「非 LLM 索引（常规 NER + BM25 + BGE-M3）」 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3f spaCy 轻量实体提取（Non-LLM NER） | 支撑：Kairos 已登记同构协议——Non-LLM 提取不损失检索端性能 | 印证记录 |
| 「三信号检索（稠密 + BM25 + 实体图）」 | 已覆盖（部分超集） | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a 三信号混合检索 | 支撑：三信号族新增独立实现；Zero-Mem 的图扩散（PPR 二/三阶邻居）超出 Kairos 实体加成覆盖面 | 图激活传播机制见增量 1 |
| 「时间层级由粗到细检索（Episode→Window→Turn→Local）」 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §3.9 检索深度分级 R0/R1/R2（按任务复杂度）+ [认知基础](../../../foundation/cognitive-foundation.md) §1.1 时间双轴 | 支撑：Kairos 深度分级按复杂度，Zero-Mem 按时间粒度——两轴正交可叠加 | 增量见下节 2 |
| 「确定性校准阶段（零 LLM 过滤/重排/答案校准）」 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §5.12 确定性事实归档 DFA + §1.7 监督平面 | 支撑：与「契约是运行时投影」「可审计」取向一致；零 LLM 校准是廉价监督形态 | 增量见下节 4 |
| 「记忆操作零 LLM token」 | 张力（工程取向） | [架构](../../../foundation/architecture-v0.1.0.md) §3.9 R2 全量级（含 cross-encoder 重排）+ §7.3d Deep Reasoning 路径（LLM 按需唤醒） | 挑战/提示：Kairos R2 与深度检索路径保留 LLM/重排成本；Zero-Mem 证明低 LLM 依赖可达竞争性能 | 工程取舍非原理冲突；检索深度分级与 LLM 唤醒频度可再平衡 |
| 「双视图查询级动态权重 ρ」 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a 融合公式 | 支撑：Kairos 三信号权重为静态参数（查询覆盖比例），Zero-Mem 为查询级动态路由 | 增量见下节 3 |

**重点回答**：与 Kairos 直接对话的是**三信号混合检索（架构 §7.3a）+ ADD-only（§7.3g）+ 非 LLM 实体提取（§7.3f）**。外部实证**支撑** Kairos——「轨迹为源不生成摘要」「检索不依赖 LLM」两条取向被独立实现且性能竞争；同时在两处给出**增量**（图激活传播检索、确定性校准阶段）。

## 可吸收增量（具体到机制/参数/设计）
1. **图激活传播检索**：实体共现激活 + personalized PageRank 沿图扩散二/三阶邻居——Kairos §7.3a 实体加成是查询覆盖比例（静态），可扩展为图扩散证据通路（需过差异检验，防谣言扩散——检索传播不得污染见证）。
2. **时间层级检索路径**：Episode → Window → Turn → Local 由粗到细，对应 Kairos 时间双轴（物理衰减+逻辑因果）的结构化检索形态，可与 R0/R1/R2 复杂度分级正交叠加（复杂度 × 时间粒度二维组合）。
3. **查询级路由系数 ρ**：动态权衡多信号/多视图权重，替代静态权重参数（对 Kairos §7.3a 融合公式的工程参数参考）。
4. **确定性校准阶段**：零 LLM 候选过滤（源/查询边界硬约束）+ 主题/时间/答案类型重排 + 答案归一化/抽取式截断/列表修剪——可与 §5.12 DFA 的确定性路径合并设计。
5. **基准方法参考**：LoCoMo + 448K 长上下文 HotpotQA 改造作为 Kairos [基准计划](../../../quality/benchmark-plan.md)的长上下文问答条目参考。

## 存疑与未验证
- 未读原文全文；ρ 公式、图构建参数、PPR 扩散步数、校准规则细节未验证
- 代码未公开（同行评审后 release）；57.6% 与「最高 F1」为作者声称，未见第三方复现（未执行）
- 「零 token」口径澄清：编码器计算另行核算、最终 QA 仍用 LLM——引用性能数字时需注明口径
- 各基线（A-Mem/Mem0/MemoryOS 等）的配置与对比设置（是否公平的 token/上下文预算）未验证

## 版本记录
| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 论文深读分析（外部视频分析批次 P1 组） |
