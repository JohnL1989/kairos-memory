"""MCP Bridge 实现（api-spec §6.8 15 工具，FastMCP Server）。

进程模型：独立子进程（stdio 传输），与 Kairos 主进程经 localhost HTTP
通信（KAIROS_MCP_BASE_URL 默认 http://127.0.0.1:8010）——工具调用转发到
主进程 REST API（与 AgentTools 语义一致：工具 → HTTP → 存储/检索组件）。

工具清单（mcp-tools.json，15 工具 = 基础工具集 12 + 关系管理 3）：
kairos_store_memory / kairos_search_memories / kairos_get_hot_memories /
kairos_search_graph / kairos_extract_entities / kairos_get_memory_traces /
kairos_feedback_memory / kairos_calibrate / kairos_get_stats /
kairos_search_sessions / kairos_tree / kairos_delete_memory /
kairos_link / kairos_unlink / kairos_relations

治理门禁：L1 权限（Bearer Key）+ L2 宪法约束 + L3 身份否决——由主进程
REST 层承载（MCP 经 HTTP 调用即继承主进程全部门禁）。
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

DEFAULT_BASE_URL = "http://127.0.0.1:8010"


class KairosMCPBridge:
    """Kairos MCP Bridge（15 工具 → 主进程 REST API 转发）。"""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_key: str | None = None) -> None:
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("KAIROS_API_KEY", "")
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=30.0,
        )

    async def _post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        resp = await self._client.post(path, json=payload or {})
        resp.raise_for_status()
        return resp.json()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # 工具实现（api-spec §6.8 工具语义）
    # ------------------------------------------------------------------

    async def store_memory(self, path: str, content: str, provenance: str, **kwargs: Any) -> Any:
        """kairos_store_memory → POST /v1/memories（S-15 provenance 必填）。"""
        payload = {"path": path, "content": content, "provenance": provenance}
        payload.update(kwargs)
        return await self._post("/v1/memories", payload)

    async def search_memories(self, query: str, **kwargs: Any) -> Any:
        """kairos_search_memories → POST /v1/memories/search（三信号混合）。"""
        return await self._post("/v1/memories/search", {"query": query, **kwargs})

    async def get_hot_memories(self, limit: int = 10) -> Any:
        """kairos_get_hot_memories → GET /v1/memories/heat-top。"""
        return await self._get("/v1/memories/heat-top", {"limit": limit})

    async def search_graph(self, query: str, limit: int = 10) -> Any:
        """kairos_search_graph → POST /v1/graph/search（实体图谱）。"""
        return await self._post("/v1/graph/search", {"query": query, "limit": limit})

    async def extract_entities(self, text: str) -> Any:
        """kairos_extract_entities → POST /v1/entities/extract。"""
        return await self._post("/v1/entities/extract", {"text": text})

    async def get_memory_traces(self, memory_id: str, limit: int = 20) -> Any:
        """kairos_get_memory_traces → 记忆生命周期轨迹（memory_states 状态机历史）。"""
        return await self._get(f"/v1/memories/{memory_id}/traces", {"limit": limit})

    async def feedback_memory(
        self, memory_id: str, feedback: str, reason: str | None = None
    ) -> Any:
        """kairos_feedback_memory → POST /v1/memories/{id}/feedback。"""
        return await self._post(
            f"/v1/memories/{memory_id}/feedback", {"feedback": feedback, "reason": reason}
        )

    async def calibrate(
        self, memory_id: str, narrative_coherence_score: float, source: str = "mcp"
    ) -> Any:
        """kairos_calibrate → POST /v1/calibrate（S-11 外部校准端口）。"""
        return await self._post(
            "/v1/calibrate",
            {
                "memory_id": memory_id,
                "narrative_coherence_score": narrative_coherence_score,
                "source": source,
            },
        )

    async def get_stats(self) -> Any:
        """kairos_get_stats → GET /v1/memories/stats。"""
        return await self._get("/v1/memories/stats")

    async def search_sessions(self, query: str, limit: int = 10) -> Any:
        """kairos_search_sessions → GET /v1/sessions。"""
        return await self._get("/v1/sessions", {"limit": limit})

    async def tree(self, path: str = "kairos://", depth: int = 2) -> Any:
        """kairos_tree → GET /v1/path/tree。"""
        return await self._get("/v1/path/tree", {"path": path, "depth": depth})

    async def delete_memory(self, memory_id: str) -> Any:
        """kairos_delete_memory → DELETE /v1/memories/{id}（契约分支删除）。"""
        resp = await self._client.delete(f"/v1/memories/{memory_id}")
        resp.raise_for_status()
        return resp.json()

    async def link(self, from_uri: str, uris: list[str], reason: str, **kwargs: Any) -> Any:
        """kairos_link → POST /v1/relations（memory_relations 表，必填 reason）。"""
        payload: dict[str, Any] = {"from_uri": from_uri, "uris": uris, "reason": reason}
        if kwargs.get("relation_type"):
            payload["relation_type"] = kwargs["relation_type"]
        if kwargs.get("confidence") is not None:
            payload["confidence"] = kwargs["confidence"]
        return await self._post("/v1/relations", payload)

    async def unlink(self, from_uri: str, to_uri: str, relation_type: str) -> Any:
        """kairos_unlink → DELETE /v1/relations/{source}/{target}（软删除留痕）。"""
        # Authorization 头已随 AsyncClient 构造注入，无需重复传
        resp = await self._client.delete(
            f"/v1/relations/{from_uri}/{to_uri}",
            params={"relation_type": relation_type},
        )
        resp.raise_for_status()
        return resp.json()

    async def relations(self, memory_id: str, direction: str = "both") -> Any:
        """kairos_relations → GET /v1/relations/{id}（inbound/outbound）。"""
        return await self._get(f"/v1/relations/{memory_id}", {"direction": direction})


def create_mcp_server() -> FastMCP:
    """创建 FastMCP Server（15 工具注册，stdio 传输）。"""
    bridge = KairosMCPBridge(base_url=os.environ.get("KAIROS_MCP_BASE_URL", DEFAULT_BASE_URL))
    mcp = FastMCP("kairos", instructions="Kairos Memory System MCP Bridge")

    @mcp.tool()
    async def kairos_store_memory(
        path: str, content: str, provenance: str, contract: str = "ondemand"
    ) -> Any:
        """存储记忆（provenance 必填，S-15；contract 五值枚举）。"""
        return await bridge.store_memory(path, content, provenance, contract=contract)

    @mcp.tool()
    async def kairos_search_memories(query: str, limit: int = 10, path: str | None = None) -> Any:
        """三信号混合检索。"""
        return await bridge.search_memories(query, limit=limit, path=path)

    @mcp.tool()
    async def kairos_get_hot_memories(limit: int = 10) -> Any:
        """热度最高记忆。"""
        return await bridge.get_hot_memories(limit=limit)

    @mcp.tool()
    async def kairos_search_graph(query: str, limit: int = 10) -> Any:
        """实体图谱检索。"""
        return await bridge.search_graph(query, limit=limit)

    @mcp.tool()
    async def kairos_extract_entities(text: str) -> Any:
        """从文本提取实体。"""
        return await bridge.extract_entities(text)

    @mcp.tool()
    async def kairos_get_memory_traces(memory_id: str, limit: int = 20) -> Any:
        """记忆生命周期历史。"""
        return await bridge.get_memory_traces(memory_id, limit=limit)

    @mcp.tool()
    async def kairos_feedback_memory(
        memory_id: str, feedback: str, reason: str | None = None
    ) -> Any:
        """可信度反馈。"""
        return await bridge.feedback_memory(memory_id, feedback, reason)

    @mcp.tool()
    async def kairos_calibrate(
        memory_id: str, narrative_coherence_score: float, source: str = "mcp"
    ) -> Any:
        """外部校准信号（S-11）。"""
        return await bridge.calibrate(memory_id, narrative_coherence_score, source)

    @mcp.tool()
    async def kairos_get_stats() -> Any:
        """记忆库报告。"""
        return await bridge.get_stats()

    @mcp.tool()
    async def kairos_search_sessions(query: str, limit: int = 10) -> Any:
        """会话搜索。"""
        return await bridge.search_sessions(query, limit=limit)

    @mcp.tool()
    async def kairos_tree(path: str = "kairos://", depth: int = 2) -> Any:
        """路径浏览。"""
        return await bridge.tree(path, depth)

    @mcp.tool()
    async def kairos_delete_memory(memory_id: str) -> Any:
        """软删除记忆（契约分支）。"""
        return await bridge.delete_memory(memory_id)

    @mcp.tool()
    async def kairos_link(
        from_uri: str, uris: list[str], reason: str, confidence: float | None = None
    ) -> Any:
        """创建有向关系边（必填 reason）。"""
        return await bridge.link(from_uri, uris, reason, confidence=confidence)

    @mcp.tool()
    async def kairos_unlink(from_uri: str, to_uri: str, relation_type: str) -> Any:
        """移除关系边。"""
        return await bridge.unlink(from_uri, to_uri, relation_type)

    @mcp.tool()
    async def kairos_relations(memory_id: str, direction: str = "both") -> Any:
        """查询关系边。"""
        return await bridge.relations(memory_id, direction)

    return mcp


def run() -> None:
    """MCP Server 入口（stdio 传输，Agent MCP Client 启动）。"""
    server = create_mcp_server()
    server.run()
