"""Agent Tool 层单元测试（api-spec §2 五个工具）。

覆盖：memories_write（S-15 provenance 必填）/ memories_search（检索语义）/
path_browse（树状浏览）/ memories_list_recent（最近使用排序）/
memories_merge（语义合并 + S-14 约束 + 源软删除）。
"""

from __future__ import annotations

import pytest

from src.access.tools import AgentTools
from src.app import build_app
from src.errors import MissingFieldError
from src.storage.models import Memory

pytestmark = pytest.mark.unit


def _settings():
    return type(
        "S",
        (),
        {
            "get": lambda self, k, d=None: {
                "KAIROS_AUDIT_HMAC_KEY": "22" * 32,
                "KAIROS_FORGETTING_HALF_LIFE": 69,
                "KAIROS_FRESHNESS_ACTIVE_THRESHOLD": 0.3,
                "KAIROS_FRESHNESS_STALE_THRESHOLD": 0.1,
                "KAIROS_DEGRADATION_PERIOD_N": 50,
                "KAIROS_DEGRADATION_PERIOD_M": 200,
                "KAIROS_HOST": "127.0.0.1",
                "KAIROS_PORT": 8010,
            }.get(k, d),
        },
    )()


@pytest.fixture
async def tools(memory_db):
    kairos = build_app(_settings(), db=memory_db)
    yield AgentTools(kairos)
    await kairos.close()


class TestMemoriesWrite:
    async def test_write_success(self, tools) -> None:
        result = await tools.memories_write(
            "kairos://_user/u1/memories/", "工具写入记忆内容，长度足够用于测试。", "user_input"
        )
        assert result["id"] and result["version"] == 1

    async def test_write_requires_provenance(self, tools) -> None:
        """S-15：provenance 缺失 → 422 语义。"""
        with pytest.raises(MissingFieldError, match="provenance"):
            await tools.memories_write("kairos://_user/u1/memories/", "内容足够用于测试。", "")


class TestMemoriesSearch:
    async def test_search(self, tools) -> None:
        await tools.memories_write(
            "kairos://_user/u1/memories/", "Python asyncio programming guide", "user_input"
        )
        result = await tools.memories_search("Python asyncio")
        assert result["total"] >= 1
        assert result["results"][0]["id"]

    async def test_search_with_path(self, tools) -> None:
        await tools.memories_write(
            "kairos://_user/u1/memories/", "路径过滤测试内容，长度足够用于测试。", "user_input"
        )
        result = await tools.memories_search("路径过滤", path="kairos://_user/u1/")
        assert result["total"] >= 1


class TestPathBrowse:
    async def test_browse_tree(self, tools) -> None:
        await tools.memories_write(
            "kairos://_user/u1/memories/", "树状浏览测试内容，长度足够用于测试。", "user_input"
        )
        result = await tools.path_browse("kairos://_user/", depth=2)
        assert result["nodes"]
        assert any("_user/u1" in n["path"] for n in result["nodes"])


class TestMemoriesListRecent:
    async def test_list_recent(self, tools) -> None:
        await tools.memories_write(
            "kairos://_user/u1/memories/", "最近列表测试内容，长度足够用于测试。", "user_input"
        )
        result = await tools.memories_list_recent(limit=5)
        assert result["total"] >= 1
        assert result["items"][0]["id"]


class TestMemoriesMerge:
    async def test_merge_and_soft_delete(self, tools) -> None:
        a = (
            await tools.memories_write(
                "kairos://_user/u1/memories/", "合并源甲内容，长度足够用于测试。", "user_input"
            )
        )["id"]
        b = (
            await tools.memories_write(
                "kairos://_user/u1/memories/", "合并源乙内容，长度足够用于测试。", "user_input"
            )
        )["id"]
        result = await tools.memories_merge([a, b], strategy="semantic_overlay")
        assert result["status"] == "merged"
        assert len(result["sources"]) == 2
        # 源记忆软删除（保留审计痕迹）
        async with tools.app.db.session() as session:
            for sid in (a, b):
                memory = await session.get(Memory, sid)
                assert memory is not None and memory.is_deleted == 1
        # 合并记忆可读
        merged = await tools.app.store.get(result["merged_id"])
        assert "[merged:semantic_overlay]" in merged["content"]

    async def test_merge_requires_sources(self, tools) -> None:
        with pytest.raises(MissingFieldError):
            await tools.memories_merge([])

    async def test_merge_invalid_strategy(self, tools) -> None:
        with pytest.raises(MissingFieldError):
            await tools.memories_merge(["x"], strategy="illegal")
