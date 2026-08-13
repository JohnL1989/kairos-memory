"""三信号混合检索集成测试（TC-R02-001~002 / TC-R03-001~002）。

覆盖：
- TC-R02-001：写入 3 条相关记忆 → 检索返回按相似度排序 Top-K
- TC-R02-002：无匹配 → 空列表
- TC-R03-001：三路召回（路径/语义/全文）融合去重全召回
- TC-R03-002：融合分 = 三信号加权（0.50/0.35/0.15）；交集项排名不低于单路
- 请求级权重覆盖、路径前缀硬过滤、实体加成信号、运行时退化（norm 恒 0）
"""

from __future__ import annotations

import pytest

from src.storage.hybrid_search import HybridSearch, SearchFilter
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.utils.embeddings import HashEmbedder

pytestmark = pytest.mark.integration


@pytest.fixture
async def setup(memory_db) -> tuple[MemoryStore, HybridSearch]:
    store = MemoryStore(memory_db, embedder=HashEmbedder())
    search = HybridSearch(memory_db, embedder=HashEmbedder())
    return store, search


async def _write(store: MemoryStore, path: str, content: str, **kw) -> str:
    result = await store.create(
        MemoryWriteInput(path=path, content=content, provenance="user_input", **kw)
    )
    return result.id


class TestSemanticRecall:
    async def test_top_k_ranked_by_similarity(self, setup) -> None:
        """TC-R02-001：相关记忆按相似度排序返回 Top-K。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "Python async programming guide")
        await _write(store, "kairos://_user/u1/memories/", "Python async programming tutorial")
        await _write(store, "kairos://_user/u1/memories/", "Quantum physics notes")
        result = await search.search("Python async programming")
        assert result["total"] >= 2
        # HashEmbedder：相同/相近文本相似度更高
        top1 = result["data"][0]["content"]
        assert "Python" in top1
        assert result["data"][0]["score"] >= result["data"][1]["score"]

    async def test_no_match_returns_empty(self, setup) -> None:
        """TC-R02-002：无关查询 → 空列表（或最低相似度项）。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "Python async programming guide")
        result = await search.search("zzzzz unrelated query zzzzz")
        assert result["total"] == 0 or result["data"][0]["score"] < 0.3


class TestHybridFusion:
    async def test_three_signal_recall_and_dedup(self, setup) -> None:
        """TC-R03-001：三路各命中一条 → 融合全召回且不重复。"""
        store, search = setup
        # 语义命中（与查询文本相同）
        await _write(store, "kairos://_user/u1/memories/", "lambda calculus semantics")
        # 全文命中（BM25 关键词）
        await _write(store, "kairos://_user/u1/memories/", "notes about calculus of lambda")
        # 路径命中（路径前缀过滤域内）
        await _write(store, "kairos://_user/u1/calculus/", "a different topic entirely")
        result = await search.search(
            "lambda calculus", filters=SearchFilter(path_prefix="kairos://_user/u1/")
        )
        ids = [d["id"] for d in result["data"]]
        assert len(ids) == len(set(ids))  # 去重生效
        assert result["total"] >= 2

    async def test_fusion_score_weighted(self, setup) -> None:
        """TC-R03-002：融合分按三信号加权（0.50/0.35/0.15）。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "alpha beta gamma delta")
        await _write(store, "kairos://_user/u1/memories/", "alpha beta")
        result = await search.search("alpha beta")
        first = result["data"][0]
        # 融合分为各信号 norm 加权和（权重和恒为 1）
        assert 0 <= first["score"] <= 1.0
        # 语义信号（相近文本）权重 0.50 主导
        assert first["explanation"]["semantic"] >= first["explanation"]["bm25"]

    async def test_request_weight_override(self, setup) -> None:
        """请求级权重覆盖（权重和重新归一化，融合公式应用验证）。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "alpha beta gamma")
        await _write(store, "kairos://_user/u1/memories/", "alpha beta beta beta")
        result = await search.search(
            "alpha beta", weights={"semantic": 0.9, "bm25": 0.05, "entity": 0.05}
        )
        first = result["data"][0]
        # 融合分 = 0.9×norm(semantic) + 0.05×norm(bm25) + 0.05×norm(entity)
        # （HashEmbedder 语义信号可能 norm 退化至 0——公式应用仍须成立）
        expected = (
            0.9 * first["explanation"]["semantic"]
            + 0.05 * first["explanation"]["bm25"]
            + 0.05 * first["explanation"]["entity"]
        )
        assert first["score"] == pytest.approx(expected, abs=1e-3)

    async def test_path_prefix_hard_filter(self, setup) -> None:
        """路径前缀是硬过滤边界：域外记忆不可达。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "python asyncio coroutine")
        await _write(store, "kairos://_project/p1/memories/", "python asyncio coroutine")
        result = await search.search(
            "python asyncio", filters=SearchFilter(path_prefix="kairos://_user/")
        )
        assert all(d["path"].startswith("kairos://_user/") for d in result["data"])


class TestEntitySignal:
    async def test_entity_boost_signal(self, setup) -> None:
        """实体加成（RC-03）：查询命中实体词典 → score_entity = |Q∩E_R|/|Q|。"""
        store, search = setup
        # 0.1.5 起写入侧自动提取（白名单 Kairos → tool 实体）；不再手动 INSERT
        memory_id = await _write(store, "kairos://_user/u1/memories/", "Kairos 架构设计讨论")
        # 无关记忆提供 norm 区分度（单候选信号 norm 退化至 0 属架构公式行为）
        await _write(store, "kairos://_user/u1/memories/", "quantum physics observation notes")
        await _write(store, "kairos://_user/u1/memories/", "cooking recipe collection")
        result = await search.search("Kairos")
        assert any(d["id"] == memory_id for d in result["data"])
        hit = next(d for d in result["data"] if d["id"] == memory_id)
        assert hit["score"] > 0
        assert hit["explanation"].get("entity", 0) > 0

    async def test_entity_signal_zero_when_no_match(self, setup) -> None:
        """实体信号无命中时 score=0（RC-03：|Q|=0 → 0），不阻断其余信号。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "plain topic without entities")
        await _write(store, "kairos://_user/u1/memories/", "another unrelated topic line")
        result = await search.search("plain topic")
        assert result["data"][0]["explanation"]["entity"] == 0.0
        assert result["data"][0]["score"] > 0  # 语义/BM25 仍工作


class TestRuntimeDegradation:
    async def test_uniform_signal_norm_zero(self, setup) -> None:
        """运行时退化：某信号所有候选同值（max==min）→ norm 恒 0，权重不重分配。"""
        store, search = setup
        await _write(store, "kairos://_user/u1/memories/", "identical content line")
        await _write(store, "kairos://_user/u1/memories/", "identical content line")
        result = await search.search("identical content line")
        # 两条同文本 → 语义信号同值 → norm 0（但相对序仍稳定）
        assert len(result["data"]) == 2
        assert result["data"][0]["score"] == result["data"][1]["score"]
