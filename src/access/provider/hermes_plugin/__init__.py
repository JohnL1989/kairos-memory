"""Kairos Memory Provider — Hermes Agent 插件桥接层（部署模板）。

部署：复制本目录到 $HERMES_HOME/plugins/kairos/ 后激活
（memory.provider=kairos）。通过 Kairos REST API（默认 127.0.0.1:8010）
实现跨会话记忆持久化：
- 生命周期钩子（架构 §7.1a 6 钩子）：on_session_end / prefetch+on_turn_start /
  on_pre_compress / on_memory_write / on_delegation（on_calibration 经
  calibrate 方法/工具面）
- prefetch 使用三信号混合检索（架构 §7.3a）召回高相关记忆注入上下文

环境变量：
    KAIROS_BASE_URL    Kairos 服务地址（默认 http://127.0.0.1:8010）
    KAIROS_API_KEY     API Key（与 Kairos 服务鉴权一致）
"""

from __future__ import annotations

import sys
from pathlib import Path
import os as _os
from typing import Any, Dict, List, Optional

# MemoryProvider subclass — 插件门禁检测（plugins/memory/__init__.py 扫描）
from agent.memory_provider import MemoryProvider

# Kairos 参考实现路径（与 aion-memory 同模式：sys.path 插入项目源码）
_kairos_src = Path(_os.environ.get("KAIROS_SRC", "D:/projects/kairos-memory"))  # hermes_plugin/ → kairos-memory/
if str(_kairos_src) not in sys.path:
    sys.path.insert(0, str(_kairos_src))

from src.access.provider.kairos_provider import (  # noqa: E402
    KairosMemoryProvider as _KairosImpl,
)


class KairosMemoryProvider(MemoryProvider):
    """Hermes MemoryProvider 适配壳（委托 Kairos 参考实现）。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._impl = _KairosImpl(*args, **kwargs)

    @property
    def name(self) -> str:
        return "kairos"

    # -- Core lifecycle ----------------------------------------------------

    def is_available(self) -> bool:
        return self._impl.is_available()

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        return self._impl.initialize(session_id, **kwargs)

    def system_prompt_block(self) -> str:
        return self._impl.system_prompt_block()

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        return self._impl.prefetch(query, session_id=session_id)

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        return self._impl.queue_prefetch(query, session_id=session_id)

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        return self._impl.sync_turn(
            user_content, assistant_content, session_id=session_id, messages=messages
        )

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return self._impl.get_tool_schemas()

    def handle_tool_call(
        self, tool_name: str, args: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> str:
        return self._impl.handle_tool_call(tool_name, args, **kwargs)

    def shutdown(self) -> None:
        return self._impl.shutdown()

    # -- Lifecycle hooks -----------------------------------------------------

    def on_turn_start(self, turn_number: int, message: str, **kwargs: Any) -> None:
        return self._impl.on_turn_start(turn_number, message, **kwargs)

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        return self._impl.on_session_end(messages)

    def on_pre_compress(self, messages: List[Dict[str, Any]]) -> str:
        return self._impl.on_pre_compress(messages)

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        return self._impl.on_memory_write(action, target, content, metadata)

    def on_delegation(
        self,
        task: str,
        result: str,
        *,
        child_session_id: str = "",
        **kwargs: Any,
    ) -> None:
        return self._impl.on_delegation(task, result, child_session_id=child_session_id, **kwargs)

    def on_session_switch(
        self,
        new_session_id: str,
        *,
        parent_session_id: str = "",
        reset: bool = False,
        rewound: bool = False,
        **kwargs: Any,
    ) -> None:
        return self._impl.on_session_switch(
            new_session_id,
            parent_session_id=parent_session_id,
            reset=reset,
            rewound=rewound,
            **kwargs,
        )

    # -- Config wizard（'hermes memory setup'；config.json 模式） -------------

    def get_config_schema(self) -> List[Dict[str, Any]]:
        return self._impl.get_config_schema()

    def save_config(self, values: Dict[str, Any], hermes_home: str) -> None:
        return self._impl.save_config(values, hermes_home)

    # -- Calibration（架构 on_calibration；Hermes 无原生钩子） ---------------

    def calibrate(self, memory_id: str, score: float, source: str = "hermes") -> Dict[str, Any]:
        return self._impl.calibrate(memory_id, score, source)


__all__ = ["KairosMemoryProvider"]
