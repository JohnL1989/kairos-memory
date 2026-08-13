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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.storage.db import Database

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

# 常见技术专名白名单（混合大小写品牌/技术名——纯大写缩写规则覆盖不到，
# 词典法增强（简化版），架构 §5.2「实体词典由后台维护」的竖切手动维护形态）
_TECH_NAMES = frozenset(
    {
        "GitHub",
        "GitLab",
        "SQLite",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "MongoDB",
        "Docker",
        "Kubernetes",
        "Nginx",
        "Vite",
        "Node.js",
        "TypeScript",
        "JavaScript",
        "Python",
        "React",
        "Vue",
        "Angular",
        "OpenAI",
        "DeepSeek",
        "Kairos",
        "Hermes",
        "Litestar",
        "SQLAlchemy",
        "APScheduler",
        "Typer",
        "Pydantic",
        "FastAPI",
        "WebSocket",
        "Jupyter",
        "Obsidian",
        "HuggingFace",
        "PowerShell",
        "Chromium",
        "Firefox",
        "Ubuntu",
        "Windows",
        "macOS",
    }
)


def extract_entities(text: str, limit: int = 20) -> list[str]:
    """规则词典法实体提取（无 LLM 依赖；竖切语义内实现）。

    命中来源优先级：引号短语 → 技术专名白名单 → 连续大写英文缩写 → 中文专名
    （XX项目/系统/…）。去重保序；stopwords 过滤英文单字符/常见缩写。
    """
    found: list[str] = []
    for m in _QUOTED.findall(text):
        if m not in found:
            found.append(m)
    for name in _TECH_NAMES:
        if name in text and name not in found:
            found.append(name)
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
    if name in _TECH_NAMES:
        return "tool"  # 白名单技术专名（GitHub/SQLite/Docker 等）
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


async def store_entities_for_memory(db: Database, memory_id: str, content: str, path: str) -> int:
    """提取实体并入库存关联（写入侧自动提取与 backfill 共用）。

    返回本次新建/关联的 memory_entities 条数；0 表示无实体命中或
    关联已存在（幂等）。失败抛出异常由调用方决定阻断语义
    （写入侧 _store_entities 捕获告警；backfill 逐条跳过计数）。

    设计依据：slice-guide 组件 3（实体词典为检索侧 _entity_recall 数据源，
    词典空则实体加成恒 0）；architecture §7.3h（竖切取关键字降级侧）。
    """
    from sqlalchemy import select

    from src.storage.models import Entity, MemoryEntity, utc_now

    names = extract_entities(content)
    if not names:
        return 0
    user_id = extract_user_id(path)
    linked = 0
    async with db.session() as session:
        # 幂等：该记忆已有实体关联则跳过（backfill 可重复执行）
        existing = (
            await session.execute(
                select(MemoryEntity).where(MemoryEntity.memory_id == memory_id).limit(1)
            )
        ).scalar_one_or_none()
        if existing is not None:
            return 0
        for name in names:
            exists = (
                await session.execute(
                    select(Entity).where(Entity.name == name, Entity.user_id == user_id)
                )
            ).scalar_one_or_none()
            if exists is None:
                ent = Entity(
                    user_id=user_id,
                    name=name,
                    type=infer_type(name),
                    description="",
                )
                session.add(ent)
                await session.flush()
                entity_id = ent.id
            else:
                entity_id = exists.id
            session.add(
                MemoryEntity(
                    memory_id=memory_id,
                    entity_id=entity_id,
                    relation="mentions",
                    valid_from=utc_now(),
                )
            )
            linked += 1
        await session.commit()
    return linked
