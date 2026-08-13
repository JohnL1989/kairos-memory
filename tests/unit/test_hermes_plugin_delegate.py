"""hermes_plugin 适配壳委托行为测试（架构 §7.1a，0.1.9 批次补测）。

test_hermes_plugin_contract.py 用 AST 静态校验接口存在性（agent.memory_provider
为 Hermes 运行时模块，本仓库无 stub 不可导入）——静态校验不产生行覆盖。
本文件在 sys.modules 注入 mock 的 agent.memory_provider 后**动态导入**插件
壳，验证委托行为：全部方法转发 _impl（KairosMemoryProvider 参考实现）、
name 返回 "kairos"，消除 hermes_plugin 0% 覆盖缺口（第三轮审计 P2-4）。
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# 导入期注入：mock 掉 Hermes 运行时模块（agent / agent.memory_provider）
# ---------------------------------------------------------------------------

_agent_pkg = types.ModuleType("agent")
_mem_mod = types.ModuleType("agent.memory_provider")
_mem_mod.MemoryProvider = type("MemoryProvider", (), {})  # 空基类（壳仅继承不调用）
sys.modules.setdefault("agent", _agent_pkg)
sys.modules.setdefault("agent.memory_provider", _mem_mod)

from src.access.provider.hermes_plugin import KairosMemoryProvider  # noqa: E402


@pytest.fixture()
def plugin() -> KairosMemoryProvider:
    """构造适配壳并替换 _impl 为 mock（隔离参考实现的真实副作用）。"""
    p = KairosMemoryProvider()
    p._impl = MagicMock()
    return p


def test_name_is_kairos(plugin: KairosMemoryProvider) -> None:
    assert plugin.name == "kairos"


def test_core_lifecycle_delegates(plugin: KairosMemoryProvider) -> None:
    """核心生命周期方法逐一委托 _impl（参数透传）。"""
    plugin.is_available()
    plugin._impl.is_available.assert_called_once_with()

    plugin.initialize("sess-1", foo="bar")
    plugin._impl.initialize.assert_called_once_with("sess-1", foo="bar")

    plugin.system_prompt_block()
    plugin._impl.system_prompt_block.assert_called_once_with()

    plugin.prefetch("查询", session_id="sess-1")
    plugin._impl.prefetch.assert_called_once_with("查询", session_id="sess-1")

    plugin.queue_prefetch("查询", session_id="sess-1")
    plugin._impl.queue_prefetch.assert_called_once_with("查询", session_id="sess-1")

    plugin.sync_turn("u", "a", session_id="sess-1", messages=[{"role": "user", "content": "u"}])
    plugin._impl.sync_turn.assert_called_once_with(
        "u", "a", session_id="sess-1", messages=[{"role": "user", "content": "u"}]
    )

    plugin.get_tool_schemas()
    plugin._impl.get_tool_schemas.assert_called_once_with()

    plugin.handle_tool_call("kairos_search", {"query": "q"})
    plugin._impl.handle_tool_call.assert_called_once_with("kairos_search", {"query": "q"})

    plugin.shutdown()
    plugin._impl.shutdown.assert_called_once_with()


def test_lifecycle_hooks_delegate(plugin: KairosMemoryProvider) -> None:
    """生命周期钩子逐一委托 _impl。"""
    plugin.on_turn_start(3, "hello")
    plugin._impl.on_turn_start.assert_called_once_with(3, "hello")

    plugin.on_session_end([{"role": "user", "content": "x"}])
    plugin._impl.on_session_end.assert_called_once_with([{"role": "user", "content": "x"}])

    plugin.on_pre_compress([{"role": "user", "content": "x"}])
    plugin._impl.on_pre_compress.assert_called_once_with([{"role": "user", "content": "x"}])

    plugin.on_memory_write("store", "kairos://p/1", "内容", {"k": "v"})
    plugin._impl.on_memory_write.assert_called_once_with(
        "store", "kairos://p/1", "内容", {"k": "v"}
    )

    plugin.on_delegation("任务", "结果", child_session_id="child-1", extra=1)
    plugin._impl.on_delegation.assert_called_once_with(
        "任务", "结果", child_session_id="child-1", extra=1
    )

    plugin.on_session_switch("new-1", parent_session_id="p-1", reset=True, rewound=False)
    plugin._impl.on_session_switch.assert_called_once_with(
        "new-1", parent_session_id="p-1", reset=True, rewound=False
    )


def test_config_wizard_and_calibration_delegate(plugin: KairosMemoryProvider) -> None:
    """配置向导与校准方法委托 _impl。"""
    plugin.get_config_schema()
    plugin._impl.get_config_schema.assert_called_once_with()

    plugin.save_config({"k": "v"}, "C:/hermes")
    plugin._impl.save_config.assert_called_once_with({"k": "v"}, "C:/hermes")

    plugin.calibrate("m-1", 0.8, source="hermes")
    # 壳以位置参数委托（calibrate(memory_id, score, source)），断言须匹配位置形态
    plugin._impl.calibrate.assert_called_once_with("m-1", 0.8, "hermes")
