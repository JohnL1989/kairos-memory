"""MCP Bridge（架构 §7.1a / api-spec §6.8）——MCP Server 独立子进程。

进程模型（technology-stack §七 / integration-design §七）：MCP Server 经
stdio 传输由 Agent 的 MCP Client 启动，与 Kairos 主进程通过 localhost
HTTP 通信（非主进程内嵌）。15 工具契约见 mcp-tools.json（inputSchema 已
补全，D-428 闭合）。
"""
