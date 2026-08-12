"""路径空间单元测试（TC-R01-001~003 语义 + 路径隔离验证）。

覆盖：路径下记忆列表、树状浏览、跨路径污染率 0%（架构 §8 路径隔离声明）、
域前缀约束（架构 §3.4）。
"""

from __future__ import annotations

import pytest

from src.errors import InvalidPathError
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.path_index import PathIndex

pytestmark = pytest.mark.unit


@pytest.fixture
async def setup(memory_db) -> tuple[MemoryStore, PathIndex]:
    store = MemoryStore(memory_db)
    index = PathIndex(memory_db)
    return store, index


async def _seed(store: MemoryStore, path: str, content: str) -> None:
    await store.create(MemoryWriteInput(path=path, content=content, provenance="user_input"))


class TestPathList:
    async def test_list_under_path(self, setup) -> None:
        store, index = setup
        await _seed(store, "kairos://_user/u1/memories/", "路径列表测试内容甲，长度足够。")
        await _seed(store, "kairos://_user/u1/memories/", "路径列表测试内容乙，长度足够。")
        await _seed(store, "kairos://_user/u2/memories/", "路径列表测试内容丙，长度足够。")
        items, total = await index.list_path("kairos://_user/u1/")
        assert total == 2
        assert all(i["path"].startswith("kairos://_user/u1/") for i in items)

    async def test_list_excludes_other_domains(self, setup) -> None:
        """路径边界确定性隔离：其他域记忆不可见。"""
        store, index = setup
        await _seed(store, "kairos://_project/p1/", "项目域记忆内容测试。")
        items, total = await index.list_path("kairos://_user/u1/")
        assert total == 0 and items == []


class TestPathTree:
    async def test_tree_structure(self, setup) -> None:
        store, index = setup
        await _seed(store, "kairos://_user/u1/memories/", "树状浏览测试内容，长度足够。")
        await _seed(store, "kairos://_user/u1/memories/deep/", "树状浏览深层内容，长度足够。")
        root = await index.tree("kairos://_user/")
        assert root.path == "kairos://_user/"
        # 子节点包含 u1/
        u1 = next((c for c in root.children if c.path == "kairos://_user/u1/"), None)
        assert u1 is not None
        assert u1.memory_count >= 2


class TestPathIsolation:
    async def test_cross_path_pollution_zero(self, setup) -> None:
        """跨路径污染率 0%（架构 §8 路径隔离声明；非 S-04——S-04 为回环绑定红线）。"""
        store, index = setup
        await _seed(store, "kairos://_user/alice/memories/", "Alice 的私密记忆内容，长度足够。")
        await _seed(store, "kairos://_user/alice/memories/", "Alice 的另一条记忆内容，长度足够。")
        await _seed(store, "kairos://_user/bob/memories/", "Bob 的记忆内容，长度足够。")
        result = await index.verify_isolation("kairos://_user/alice/", "kairos://_user/bob/")
        assert result["overlap"] == 0
        assert result["pollution_rate"] == 0.0

    async def test_same_boundary_not_isolated(self, setup) -> None:
        """同边界内记忆共享可见（隔离仅跨边界）。"""
        store, index = setup
        await _seed(store, "kairos://_user/alice/memories/", "共享测试内容，长度足够。")
        result = await index.verify_isolation("kairos://_user/alice/", "kairos://_user/alice/")
        assert result["overlap"] == 1  # 同一集合自交（a ∩ b = 自身 1 条）


class TestDomainValidation:
    async def test_unknown_reserved_prefix_rejected(self, setup) -> None:
        _store, index = setup
        with pytest.raises(InvalidPathError, match="保留前缀"):
            index.validate_domain("kairos://_unknown/abc/")

    async def test_known_prefixes_accepted(self, setup) -> None:
        _store, index = setup
        for prefix in ("_user", "_project", "_session", "_scratch", "_system"):
            index.validate_domain(f"kairos://{prefix}/x/")  # 不抛异常
