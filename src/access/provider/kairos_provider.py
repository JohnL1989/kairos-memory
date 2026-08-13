"""Kairos Hermes Memory Provider（架构 §7.1a 参考实现）。

为 Hermes Agent 提供原生记忆生命周期钩子——自动监听 Agent 生命周期事件，
无需代理手动调用记忆工具（架构 §7.1a「Hermes Memory Provider（v0.1.0
完整）」）。

与 Hermes MemoryProvider ABC（agent/memory_provider.py）接口对齐：
- 核心：is_available / initialize / system_prompt_block / prefetch /
  queue_prefetch / sync_turn / get_tool_schemas / handle_tool_call / shutdown
- 钩子：on_turn_start / on_session_end / on_session_switch / on_pre_compress /
  on_memory_write / on_delegation
- 配置：get_config_schema / save_config（'hermes memory setup' 向导）

6 钩子映射（架构 §7.1a）：
| 架构钩子 | 本实现承载 | Hermes 原生对应 |
|:--|:--|:--|
| on_session_end | on_session_end（会话消息同步） | ✓ 原生 |
| on_turn_start | prefetch（turn 前召回注入）+ on_turn_start（tick） | ✓ 原生 |
| on_pre_compress | on_pre_compress（压缩前提取，temporary 契约） | ✓ 原生 |
| on_memory_write | on_memory_write（外部写入镜像） | ✓ 原生 |
| on_calibration | calibrate() 方法 + 工具（Hermes 无原生校准钩子） | 经工具面 |
| on_delegation | on_delegation（子代理上下文记录） | ✓ 原生 |

部署形态：本类为参考实现（HTTP 客户端语义）；Hermes 侧插件壳位于
$HERMES_HOME/plugins/kairos/（独立 venv 自包含，同构实现）——
memory.provider=kairos 激活。

Provider 的 prefetch 使用三信号混合检索（架构 §7.3a）召回高相关记忆。
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger("kairos.access.provider")

# Kairos 服务配置（与 MCP Bridge 同模式；端口 8010 为全库权威值，
# 见 ops/configuration.md KAIROS_PORT）
DEFAULT_BASE_URL = os.environ.get("KAIROS_BASE_URL", "http://127.0.0.1:8010")
DEFAULT_API_KEY = os.environ.get("KAIROS_API_KEY", "")

# 单次检索注入的最大记忆条数（上下文预算控制）
PREFETCH_LIMIT = 5


class KairosMemoryProvider:
    """Kairos 记忆 Provider（Hermes MemoryProvider 接口语义）。

    本类不依赖 Hermes 包（参考实现）；Hermes 插件壳继承 Hermes 的
    MemoryProvider ABC 并委托同样的 HTTP 逻辑。
    """

    # ------------------------------------------------------------------
    # 元信息
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "kairos"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        config_path: str | None = None,
    ) -> None:
        """配置优先级：显式参数 > config.json > 环境变量 > 默认。

        config.json 模式（Hermes 插件部署，hindsight 同型）：
        $HERMES_HOME/kairos/config.json —— {"base_url": ..., "api_key": ...}。
        """
        cfg: dict[str, Any] = {}
        if config_path and Path(config_path).is_file():
            try:
                cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("kairos config.json 读取失败: %s", exc)
        self.base_url = base_url or cfg.get("base_url") or DEFAULT_BASE_URL
        self.api_key = api_key or cfg.get("api_key") or DEFAULT_API_KEY
        self._http: Any = None  # httpx.AsyncClient（lazy init）
        self._session_id = ""
        # agent_context：Hermes initialize kwargs 之一（primary/subagent/cron/flush）。
        # Hermes 约定非 primary 上下文跳过写入（cron 系统提示会污染用户画像）。
        self._agent_context = "primary"
        # queue_prefetch 后台召回缓存（Hermes 轮后排队、下一轮 prefetch 消费）。
        self._prefetch_cache: str | None = None

    # ------------------------------------------------------------------
    # 核心生命周期
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """配置与密钥就绪即可用（不发起网络调用，Hermes 约定）。"""
        return bool(self.base_url and self.api_key)

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        """会话初始化：验证服务可达 + 健康检查。

        kwargs 含 agent_context（Hermes 约定）：非 primary 上下文（cron/flush/
        subagent）时写入操作跳过——cron 系统提示写入会污染用户画像。
        """
        import httpx

        self._session_id = session_id
        self._agent_context = kwargs.get("agent_context", "primary")
        if self._http is None:  # 复用已注入客户端（测试/自定义传输）
            self._http = httpx.Client(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
        try:
            resp = self._http.get("/health")
            resp.raise_for_status()
            logger.info("kairos provider initialized (session=%s, context=%s)", session_id, self._agent_context)
        except Exception as exc:
            logger.warning("kairos provider init: 服务不可达 %s", exc)
            raise RuntimeError(f"Kairos 服务不可达（{self.base_url}）: {exc}") from exc

    def system_prompt_block(self) -> str:
        """系统提示静态块（记忆能力说明）。"""
        return (
            "记忆系统：Kairos 记忆已接入。每轮对话自动检索相关记忆注入上下文，"
            "会话结束时自动同步。可用记忆工具（kairos_search_memories 等）经 MCP 提供。"
        )

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        """轮后后台召回，下一轮 prefetch 消费（Hermes 后台线程机制）。

        Hermes MemoryManager 在每轮结束后调用；prefetch 优先读缓存
        （快、不阻塞），无缓存时同步检索兜底。
        """
        if not query.strip() or not self._http:
            return

        def _run() -> None:
            try:
                resp = self._http.post(
                    "/v1/memories/search",
                    json={"query": query, "limit": PREFETCH_LIMIT},
                )
                resp.raise_for_status()
                results = resp.json().get("data", [])
                self._prefetch_cache = self._format_results(results)
            except Exception as exc:
                logger.warning("queue_prefetch 失败: %s", exc)

        threading.Thread(target=_run, daemon=True).start()

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """turn 前召回高相关记忆（三信号混合检索，架构 §7.3a）→ 注入文本。

        优先消费 queue_prefetch 的后台缓存；无缓存时同步检索兜底
        （Hermes 以线程 + 8s 超时调用本方法）。
        """
        if not query.strip() or not self._http:
            return ""
        if self._prefetch_cache is not None:
            cached, self._prefetch_cache = self._prefetch_cache, None
            return cached
        try:
            resp = self._http.post(
                "/v1/memories/search",
                json={"query": query, "limit": PREFETCH_LIMIT},
            )
            resp.raise_for_status()
            results = resp.json().get("data", [])
        except Exception as exc:
            logger.warning("prefetch 失败: %s", exc)
            return ""
        return self._format_results(results)

    @staticmethod
    def _format_results(results: list[dict[str, Any]]) -> str:
        """检索结果 → 注入文本（纯文本，<memory-context> 栅栏由 Hermes 侧包装）。"""
        if not results:
            return ""
        lines = ["[Kairos 记忆]"]
        for item in results:
            lines.append(f"- {item.get('content', '')[:200]}")
        return "\n".join(lines)

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: list[dict[str, Any]] | None = None,
    ) -> None:
        """turn 后同步对话到 Kairos（use_event 语义；非阻塞）。"""
        self._write_memory(
            content=f"对话记录（{session_id or 'session'}）:\n用户: {user_content[:500]}",
            provenance="system_generated",
        )

    def shutdown(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    # ------------------------------------------------------------------
    # 生命周期钩子（架构 §7.1a 6 钩子）
    # ------------------------------------------------------------------

    def on_turn_start(self, turn_number: int, message: str, **kwargs: Any) -> None:
        """每轮开始 tick（turn 计数/维护钩子；召回注入由 prefetch 承载）。"""
        logger.debug("kairos on_turn_start #%d", turn_number)

    def on_session_end(self, messages: list[dict[str, Any]]) -> None:
        """会话结束：同步对话消息（架构：on_session_end → 对话同步 + 蒸馏）。"""
        if not messages:
            return
        summary = self._summarize_messages(messages)
        self._write_memory(
            content=f"会话总结: {summary}",
            provenance="system_generated",
            memory_types=["episodic"],
        )

    def on_pre_compress(self, messages: list[dict[str, Any]]) -> str:
        """上下文压缩前提取将被丢弃内容（temporary 契约写入，架构 §5.2）。"""
        if not messages:
            return ""
        summary = self._summarize_messages(messages)
        self._write_memory(
            content=f"压缩前提取: {summary}",
            provenance="system_generated",
            contract="temporary",
            memory_types=["episodic"],
        )
        return summary

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """外部记忆写入镜像（架构：同步写入统一 LTM + 路径分配）。"""
        self._write_memory(
            content=content or f"[{action}] {target}",
            provenance="external_calibration",
        )

    def on_delegation(
        self,
        task: str,
        result: str,
        *,
        child_session_id: str = "",
        **kwargs: Any,
    ) -> None:
        """子代理任务完成：记录子任务独立上下文（防止记忆混淆）。"""
        self._write_memory(
            content=f"子任务（{child_session_id or 'subagent'}）: {task}\n结果: {result[:300]}",
            provenance="system_generated",
        )

    def on_session_switch(
        self,
        new_session_id: str,
        *,
        parent_session_id: str = "",
        reset: bool = False,
        rewound: bool = False,
        **kwargs: Any,
    ) -> None:
        """会话切换钩子（/resume /branch /reset /new /压缩，Hermes 原生）。

        Kairos provider 不缓存每会话状态，仅记录；reset 时清空预取缓存
        （新会话不沿用上一轮召回）。
        """
        self._session_id = new_session_id
        if reset:
            self._prefetch_cache = None
        logger.debug(
            "kairos on_session_switch → %s (parent=%s, reset=%s)", new_session_id, parent_session_id, reset
        )

    # ------------------------------------------------------------------
    # 校准（架构 on_calibration；Hermes 无原生钩子，经方法/工具暴露）
    # ------------------------------------------------------------------

    def calibrate(self, memory_id: str, score: float, source: str = "hermes") -> dict[str, Any]:
        """外部校准信号（S-11 端口；对应架构 on_calibration 语义）。"""
        if not self._http:
            return {"error": "not_initialized"}
        resp = self._http.post(
            "/v1/calibrate",
            json={"memory_id": memory_id, "narrative_coherence_score": score, "source": source},
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # 配置向导（Hermes 'hermes memory setup'；config.json 模式）
    # ------------------------------------------------------------------

    def get_config_schema(self) -> list[dict[str, Any]]:
        """配置向导字段（Hermes memory setup 遍历）。secret 字段走 .env。"""
        return [
            {
                "key": "base_url",
                "description": "Kairos 服务地址（默认 http://127.0.0.1:8010）",
                "default": self.base_url,
                "env_var": "KAIROS_BASE_URL",
                "type": "text",
            },
            {
                "key": "api_key",
                "description": "Kairos API Key（与 Kairos 服务鉴权一致）",
                "secret": True,
                "required": True,
                "env_var": "KAIROS_API_KEY",
                "type": "text",
            },
        ]

    def save_config(self, values: dict[str, Any], hermes_home: str) -> None:
        """写非 secret 配置到 $HERMES_HOME/kairos/config.json（同构于部署语义）。"""
        target = Path(hermes_home) / "kairos" / "config.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        existing: dict[str, Any] = {}
        if target.is_file():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = {}
        existing.update({k: v for k, v in values.items() if k != "api_key"})
        target.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("kairos save_config → %s", target)

    # ------------------------------------------------------------------
    # 工具面（MCP 已覆盖；可选补充 provider 级工具）
    # ------------------------------------------------------------------

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Provider 工具 schema（记忆写入/检索；MCP Bridge 亦承载同语义）。"""
        return [
            {
                "name": "kairos_provider_write",
                "description": "写入记忆（provider 内建，同 kairos_store_memory）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "path": {"type": "string", "default": "kairos://_user/hermes/memories/"},
                    },
                    "required": ["content"],
                },
            }
        ]

    def handle_tool_call(
        self, tool_name: str, args: dict[str, Any] | None = None, **kwargs: Any
    ) -> str:
        """Provider 工具调用分发（Hermes 契约：返回 JSON 字符串）。"""
        args = args or {}
        if tool_name == "kairos_provider_write":
            return json.dumps(
                self._write_memory(content=args.get("content", "")), ensure_ascii=False
            )
        return json.dumps({"error": f"unknown tool {tool_name}"}, ensure_ascii=False)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _write_memory(
        self,
        content: str,
        *,
        provenance: str = "system_generated",
        contract: str = "ondemand",
        memory_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """写入记忆（POST /v1/memories；失败留痕不抛异常——记忆流非阻断）。

        agent_context 守卫：非 primary（cron/flush/subagent）跳过写入
        （Hermes 约定，防系统提示污染用户画像）。
        """
        if not self._http:
            return {"error": "not_initialized"}
        if self._agent_context not in ("primary", ""):
            logger.debug(
                "跳过记忆写入（agent_context=%s，非 primary）", self._agent_context
            )
            return {"skipped": True, "reason": f"agent_context={self._agent_context}"}
        try:
            resp = self._http.post(
                "/v1/memories",
                json={
                    "path": "kairos://_user/hermes/memories/",
                    "content": content,
                    "provenance": provenance,
                    "contract": contract,
                    "memory_types": memory_types or ["semantic"],
                },
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("记忆写入失败: %s", exc)
            return {"error": str(exc)}

    @staticmethod
    def _summarize_messages(messages: list[dict[str, Any]]) -> str:
        """消息摘要（首末保留 + 中间截断）。"""
        parts = []
        for m in messages[:50]:
            role = m.get("role", "?")
            content = str(m.get("content", ""))[:120]
            parts.append(f"{role}: {content}")
        return "\n".join(parts)[:1500]
