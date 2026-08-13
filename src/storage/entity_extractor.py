"""实体提取器（竖切组件 3 实体加成数据源）。

权威规格：
- slice-implementation-guide 组件 3：实体加成简化方案——实体提取用关键词/
  规则匹配（详细设计 §9.3 spaCy 简化版），不启用 LLM 实体提取（Deep 模式
  不在竖切）
- architecture §7.3h 实体抽取双策略：竖切取「关键字降级」侧（无 LLM 依赖）

用法：
- extract_entities(text)    → 规则提取实体名列表（引号短语 / 英文缩写 / 中文专名）
- infer_type(name)         → 实体类型推断（project / tool / concept，entities 表枚举）
- extract_user_id(path)    → 从记忆路径解析 user_id（kairos://_user/{uid}/...）

写入侧自动提取接入点：MemoryStore.create（memory_store.py `_store_entities`）——
写入后提取入库（entities 去重 + memory_entities 关联），激活三信号中实体加成
信号（此前词典为空导致 score_entity 恒 0，属竖切交付未竟）。
"""

from __future__ import annotations

import re

# 规则实体提取模式（竖切语义内；与 extended.py extract 端点同源，集中于此）
_QUOTED = re.compile(r"[「“]([^」”]{2,30})[」”]")
_EN_ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,10}\b")
_CN_PROPER = re.compile(
    r"[\u4e00-\u9fff]{2,12}(?:项目|系统|协议|框架|模型|引擎|平台|服务|工具|数据库|网络|记忆|文档|目录)"
)

# 类型推断：中文专名后缀 → project（工程实体）或 concept（概念实体）
_PROJECT_SUFFIXES = ("项目", "系统", "引擎", "平台", "服务", "数据库", "网络")
_CONCEPT_SUFFIXES = ("协议", "框架", "模型", "工具", "记忆", "文档", "目录")

# 英文缩写例外（常见词非实体）
_EN_STOPWORDS = frozenset({"I", "AI", "OK", "TV", "PC", "IP", "ID"})


def extract_entities(text: str, limit: int = 20) -> list[str]:
    """规则词典法实体提取（无 LLM 依赖；竖切语义内实现）。

    命中来源优先级：引号短语 → 连续大写英文缩写 → 中文专名（XX项目/系统/…）。
    去重保序；stopwords 过滤英文单字符/常见缩写。
    """
    found: list[str] = []
    for m in _QUOTED.findall(text):
        if m not in found:
            found.append(m)
    for m in _EN_ACRONYM.findall(text):
        if m in _EN_STOPWORDS:
            continue
        if m not in found:
            found.append(m)
    for m in _CN_PROPER.findall(text):
        if m not in found:
            found.append(m)
    return found[:limit]


def infer_type(name: str) -> str:
    """实体类型推断（entities 表 type 枚举：project / people / concept / tool）。

    规则：英文缩写（全大写）→ tool；中文专名含项目/系统/引擎/平台/服务/数据库
    /网络后缀 → project；含协议/框架/模型/工具/记忆/文档/目录后缀 → concept；
    引号短语/其余 → concept。
    """
    if name.isupper() and len(name) >= 2 and any(ch.isdigit() or ch.isascii() for ch in name):
        return "tool"
    if name.endswith(_PROJECT_SUFFIXES):
        return "project"
    if name.endswith(_CONCEPT_SUFFIXES):
        return "concept"
    return "concept"


def extract_user_id(path: str) -> str:
    """从记忆路径解析 user_id（kairos://_user/{user_id}/... 形态）。

    解析失败回退 "default"（与 extract 端点默认口径一致）。
    """
    m = re.match(r"kairos://_user/([^/]+)/", path)
    if m and m.group(1):
        return m.group(1)
    return "default"
