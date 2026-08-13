"""实体提取器测试（竖切组件 3 实体加成信号激活验证）。

覆盖：
- 规则提取：引号短语 / 英文缩写（含 stopword 过滤）/ 中文专名
- 类型推断：tool / project / concept
- user_id 路径解析
- 写入侧自动提取：entities 去重入库 + memory_entities 关联（MemoryStore.create）
- 检索侧实体信号：查询命中词典 → explanation.entity > 0（三信号融合生效）
"""

from __future__ import annotations

import pytest

from src.storage.entity_extractor import (
    extract_entities,
    extract_user_id,
    infer_type,
)

pytestmark = pytest.mark.unit


class TestExtractRules:
    def test_quoted_phrase(self) -> None:
        assert "持续记忆协议" in extract_entities("「持续记忆协议」是核心设计。")

    def test_en_acronym(self) -> None:
        """全大写缩写提取（SQLite 混合大小写不在纯大写规则内——规则法局限）。"""
        names = extract_entities("Kairos 使用 SQLite + FTS5 实现检索。")
        assert "FTS5" in names
        assert "SQLite" not in names  # 混合大小写品牌名不在竖切规则内

    def test_en_stopword_filtered(self) -> None:
        """英文单字符/常见缩写（AI/OK/ID）不视为实体。"""
        names = extract_entities("AI 与 OK 是常见词，ID 也不是实体。")
        assert "AI" not in names
        assert "OK" not in names

    def test_cn_proper(self) -> None:
        names = extract_entities("Kairos 记忆系统采用三信号混合检索。")
        assert "记忆系统" in names

    def test_dedupe_ordered(self) -> None:
        names = extract_entities("「FTS5」与「FTS5」重复引用，SQLite 与 SQLite。")
        assert names.count("FTS5") == 1
        assert names == ["FTS5"]  # 引号短语提取，其余无纯大写/中文专名


class TestInferType:
    def test_tool(self) -> None:
        assert infer_type("FTS5") == "tool"
        assert infer_type("SQL") == "tool"

    def test_project(self) -> None:
        assert infer_type("Kairos 记忆系统") == "project"
        assert infer_type("灵枢工作台项目") == "project"

    def test_concept(self) -> None:
        assert infer_type("持续记忆协议") == "concept"
        assert infer_type("「任意短语」") == "concept"
        # 混合大小写品牌名（SQLite）不在纯大写规则内 → 归 concept（规则法局限，诚实标注）
        assert infer_type("SQLite") == "concept"


class TestExtractUserId:
    def test_normal_path(self) -> None:
        assert extract_user_id("kairos://_user/hermes/memories/abc") == "hermes"

    def test_fallback(self) -> None:
        assert extract_user_id("kairos://_system/seeds/identity") == "default"


class TestWriteSideExtraction:
    """写入侧自动提取：MemoryStore.create 后 entities/memory_entities 有数据。"""

    async def test_create_populates_entities(self, memory_db) -> None:
        from src.storage.memory_store import MemoryStore, MemoryWriteInput

        store = MemoryStore(memory_db)
        result = await store.create(
            MemoryWriteInput(
                path="kairos://_user/hermes/memories/",
                content="「持续记忆协议」由 Kairos 记忆系统与 FTS5 共同实现，SQLite 存储。",
                provenance="user_input",
            )
        )
        assert result.id
        from sqlalchemy import select

        from src.storage.models import Entity, MemoryEntity

        async with memory_db.session() as session:
            entities = (await session.execute(select(Entity))).scalars().all()
            assert len(entities) >= 3  # 持续记忆协议 / 记忆系统 / FTS5(+SQLite)
            names = {e.name for e in entities}
            assert "持续记忆协议" in names
            assert "FTS5" in names
            links = (
                (
                    await session.execute(
                        select(MemoryEntity).where(MemoryEntity.memory_id == result.id)
                    )
                )
                .scalars()
                .all()
            )
            assert len(links) >= 1
            assert all(link.relation == "mentions" for link in links)

    async def test_no_entity_content_skips(self, memory_db) -> None:
        from src.storage.memory_store import MemoryStore, MemoryWriteInput

        store = MemoryStore(memory_db)
        await store.create(
            MemoryWriteInput(
                path="kairos://_user/hermes/memories/",
                content="今天天气不错，记录了这条普通内容。",
                provenance="user_input",
            )
        )
        from sqlalchemy import func, select

        from src.storage.models import Entity

        async with memory_db.session() as session:
            count = (await session.execute(select(func.count()).select_from(Entity))).scalar()
            assert count == 0  # 无实体命中不产生垃圾条目

    async def test_search_entity_signal_active(self, memory_db) -> None:
        """检索侧实体信号：词典命中 → explanation.entity > 0（三信号融合生效）。"""
        from src.storage.hybrid_search import HybridSearch, SearchFilter
        from src.storage.memory_store import MemoryStore, MemoryWriteInput

        store = MemoryStore(memory_db)
        await store.create(
            MemoryWriteInput(
                path="kairos://_user/hermes/memories/",
                content="「持续记忆协议」是 Kairos 记忆系统的核心设计，由 SQLite 承载。",
                provenance="user_input",
            )
        )
        search = HybridSearch(memory_db)
        result = await search.search(
            "持续记忆协议 记忆系统",
            limit=5,
            filters=SearchFilter(path_prefix="kairos://_user/hermes/"),
        )
        hits = result.get("data") or []
        assert hits, "检索应命中刚写入的记忆"
        top = hits[0]
        explanation = top.get("explanation") or {}
        assert explanation.get("entity", 0) > 0, f"实体信号应 >0，实际 {explanation}"
