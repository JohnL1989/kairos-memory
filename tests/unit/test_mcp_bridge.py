"""MCP Bridge 单元测试（api-spec §6.8 15 工具）。

覆盖：
- 15 工具注册完整性（mcp-tools.json 契约对齐）
- 工具 → 主进程 REST 转发（httpx MockTransport 模拟）
- 鉴权头传递（Bearer Key）
- 错误传播（主进程 4xx → 工具调用异常）
"""

from __future__ import annotations

import httpx
import pytest

from src.access.mcp.bridge import KairosMCPBridge, create_mcp_server

pytestmark = pytest.mark.unit


def _mock_transport(handler):
    """构造 MockTransport：记录请求并返回预设响应。"""

    async def _handler(request: httpx.Request) -> httpx.Response:
        return handler(request)

    return httpx.MockTransport(_handler)


@pytest.fixture
def bridge():
    """MockTransport 桥接（模拟主进程 REST）。"""
    calls: list[dict] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        calls.append(
            {"method": request.method, "url": str(request.url), "headers": dict(request.headers)}
        )
        if request.url.path == "/v1/memories":
            return httpx.Response(
                201, json={"id": "mcp-1", "path": "kairos://_user/u1/memories/mcp-1", "version": 1}
            )
        if request.url.path == "/v1/memories/search":
            return httpx.Response(
                200, json={"results": [{"id": "mcp-1", "path": "p", "score": 0.9}], "total": 1}
            )
        if request.url.path == "/v1/path/tree":
            return httpx.Response(
                200, json={"tree": [{"path": "kairos://", "memory_count": 1}], "truncated": False}
            )
        return httpx.Response(404, json={"code": "ERR-DB-004", "message": "not found"})

    b = KairosMCPBridge(base_url="http://mock", api_key="test-key")
    b._client = httpx.AsyncClient(
        transport=_mock_transport(_handler),
        base_url="http://mock",
        timeout=10.0,
        headers={"Authorization": "Bearer test-key"},
    )
    return b, calls


class TestToolRegistration:
    def test_15_tools_registered(self) -> None:
        mcp = create_mcp_server()
        tools = mcp._tool_manager.list_tools()
        names = sorted(t.name for t in tools)
        expected = {
            "kairos_store_memory",
            "kairos_search_memories",
            "kairos_get_hot_memories",
            "kairos_search_graph",
            "kairos_extract_entities",
            "kairos_get_memory_traces",
            "kairos_feedback_memory",
            "kairos_calibrate",
            "kairos_get_stats",
            "kairos_search_sessions",
            "kairos_tree",
            "kairos_delete_memory",
            "kairos_link",
            "kairos_unlink",
            "kairos_relations",
        }
        assert set(names) == expected
        assert len(names) == 15  # 基础工具集 12 + 关系管理 3


class TestBridgeForwarding:
    async def test_store_memory_forwards_with_auth(self, bridge) -> None:
        b, calls = bridge
        result = await b.store_memory(
            "kairos://_user/u1/memories/", "MCP 存储记忆内容，长度足够用于测试。", "user_input"
        )
        assert result["id"] == "mcp-1"
        call = calls[0]
        assert call["url"].endswith("/v1/memories")
        assert call["headers"].get("authorization") == "Bearer test-key"

    async def test_search_memories(self, bridge) -> None:
        b, _calls = bridge
        result = await b.search_memories("检索内容")
        assert result["total"] == 1

    async def test_tree(self, bridge) -> None:
        b, _calls = bridge
        result = await b.tree("kairos://", depth=1)
        assert result["tree"][0]["path"] == "kairos://"

    async def test_error_propagation(self, bridge) -> None:
        b, _calls = bridge
        with pytest.raises(httpx.HTTPStatusError):
            await b.delete_memory("nonexistent")  # 404 → 异常


class TestMcpOnlyTools:
    async def test_link_accepts(self, bridge) -> None:
        b, _calls = bridge
        result = await b.link("m1", ["m2"], "test reason")
        assert result["status"] == "accepted"

    async def test_relations_empty(self, bridge) -> None:
        b, _calls = bridge
        result = await b.relations("m1")
        assert result["inbound"] == []
        assert result["outbound"] == []
