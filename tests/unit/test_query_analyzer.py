"""QueryAnalyzer 单元测试（首迭代 3，架构 §2.6.1）。

覆盖：
- 意图分类五+1 类（事实/时间/探索/决策/操作/general 兜底 + trivial 词表）
- 时间约束四类解析（相对窗口/日历周/绝对/事件锚定）+ fallback_query 剥离
- 事件锚定 optional 降级（置信度 <0.6 → 时间过滤可选）
- 实体词典匹配
- 检索管线集成：时间锚定注入 time_range（occurred_at 优先、空回退 created_at）
"""

from __future__ import annotations

from datetime import UTC

import pytest

from src.storage.query_analyzer import (
    INTENT_DECISION_TRACE,
    INTENT_EXPLORATORY_BROWSE,
    INTENT_FACTUAL_LOOKUP,
    INTENT_GENERAL,
    INTENT_INSTRUCTIONAL,
    INTENT_TEMPORAL_QUERY,
    QueryAnalyzer,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def analyzer() -> QueryAnalyzer:
    return QueryAnalyzer()


class TestIntentClassification:
    async def test_trivial_query_general(self, analyzer) -> None:
        for q in ("你好", "谢谢", "hi", "在吗"):
            d = await analyzer.analyze(q)
            assert d.intent.type == INTENT_GENERAL

    async def test_temporal_queries(self, analyzer) -> None:
        for q in ("最近一周的讨论", "上周的记录", "2026年7月的内容"):
            d = await analyzer.analyze(q)
            assert d.intent.type == INTENT_TEMPORAL_QUERY

    async def test_exploratory(self, analyzer) -> None:
        d = await analyzer.analyze("关于记忆系统有哪些想法")
        assert d.intent.type == INTENT_EXPLORATORY_BROWSE

    async def test_decision_trace(self, analyzer) -> None:
        d = await analyzer.analyze("当初为什么选择 SQLite")
        assert d.intent.type == INTENT_DECISION_TRACE

    async def test_instructional(self, analyzer) -> None:
        d = await analyzer.analyze("如何接入事件总线")
        assert d.intent.type == INTENT_INSTRUCTIONAL

    async def test_factual_default(self, analyzer) -> None:
        d = await analyzer.analyze("Kairos 的三信号权重是多少")
        assert d.intent.type == INTENT_FACTUAL_LOOKUP
        assert d.intent.confidence >= 0.6


class TestTemporalExtraction:
    async def test_relative_days(self, analyzer) -> None:
        d = await analyzer.analyze("最近7天关于 asyncio 的内容")
        tc = d.temporal_constraint
        assert tc is not None and tc.type == "relative_window"
        assert tc.start is not None and tc.end is not None
        # fallback_query 剥离时间短语
        assert "最近7天" not in d.fallback_query
        assert "asyncio" in d.fallback_query

    async def test_relative_months(self, analyzer) -> None:
        d = await analyzer.analyze("最近3个月的进展")
        assert d.temporal_constraint is not None
        assert d.temporal_constraint.type == "relative_window"

    async def test_calendar_week(self, analyzer) -> None:
        d = await analyzer.analyze("上周的会议记录")
        tc = d.temporal_constraint
        assert tc is not None and tc.type == "calendar_week"
        assert tc.start and tc.end

    async def test_absolute_month(self, analyzer) -> None:
        d = await analyzer.analyze("2026年7月的总结")
        tc = d.temporal_constraint
        assert tc is not None and tc.type == "absolute"
        assert tc.start == "2026-07-01T00:00:00.000Z"
        assert tc.end.startswith("2026-07-31T")

    async def test_absolute_date(self, analyzer) -> None:
        d = await analyzer.analyze("2026-08-01 的记录")
        tc = d.temporal_constraint
        assert tc is not None and tc.type == "absolute"

    async def test_event_anchor_optional(self, analyzer) -> None:
        """事件锚定：未解析出具体时间 → optional（时间过滤降级为可选）。"""
        d = await analyzer.analyze("项目启动时的决策")
        tc = d.temporal_constraint
        assert tc is not None and tc.type == "event_anchor"
        assert tc.optional is True
        assert tc.confidence < 0.6
        # optional 约束不注入硬过滤
        assert "项目" in d.fallback_query

    async def test_no_temporal(self, analyzer) -> None:
        d = await analyzer.analyze("Python 异步编程")
        assert d.temporal_constraint is None
        assert d.fallback_query is None
        assert d.effective_query == "Python 异步编程"


class TestEntityExtraction:
    async def test_dictionary_match(self, memory_db, analyzer) -> None:
        from src.storage.models import Entity

        analyzer.db = memory_db
        async with memory_db.session() as session:
            session.add(Entity(user_id="u1", name="Kairos", type="project"))
            await session.commit()
        d = await analyzer.analyze("Kairos 的记忆架构")
        assert any(e.entity_text == "Kairos" and e.entity_type == "project" for e in d.entities)

    async def test_no_match(self, analyzer) -> None:
        d = await analyzer.analyze("无实体查询内容")
        assert d.entities == []


class TestSearchIntegration:
    async def test_time_range_filters_recall(self, memory_db) -> None:
        """时间锚定注入检索：occurred_at 在窗口外不召回。"""
        from src.storage.hybrid_search import HybridSearch
        from src.storage.memory_store import MemoryStore, MemoryWriteInput
        from src.utils.embeddings import HashEmbedder

        store = MemoryStore(memory_db, embedder=HashEmbedder())
        search = HybridSearch(memory_db, embedder=HashEmbedder(), analyzer=QueryAnalyzer(memory_db))
        # 旧记忆（occurred_at 30 天前）
        from datetime import datetime, timedelta

        past = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        created_old = await store.create(
            MemoryWriteInput(
                path="kairos://_user/u1/memories/",
                content="历史 asyncio 讨论内容，长度足够用于测试。",
                provenance="user_input",
                occurred_at=past,
            )
        )
        # 新记忆（默认 now）
        created_new = await store.create(
            MemoryWriteInput(
                path="kairos://_user/u1/memories/",
                content="最近的 asyncio 讨论内容，长度足够用于测试。",
                provenance="user_input",
            )
        )
        # 「最近7天」→ 时间过滤：旧记忆不召回
        result = await search.search("最近7天 asyncio 讨论")
        ids = {d["id"] for d in result["data"]}
        assert created_new.id in ids
        assert created_old.id not in ids  # 时间硬过滤生效

    async def test_no_analyzer_passthrough(self, memory_db) -> None:
        from src.storage.hybrid_search import HybridSearch
        from src.utils.embeddings import HashEmbedder

        search = HybridSearch(memory_db, embedder=HashEmbedder())  # 无 analyzer
        result = await search.search("普通查询内容测试")
        assert result["total"] >= 0  # 正常返回（passthrough）
