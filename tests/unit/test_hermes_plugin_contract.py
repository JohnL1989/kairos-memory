"""Hermes 插件壳接口契约测试（架构 §7.1a）。

适配壳 hermes_plugin/__init__.py 依赖 Hermes 包的 agent.memory_provider
（Kairos 项目 venv 不可导入），故用 AST 静态校验而非导入——断言 Hermes
MemoryProvider ABC 的全部方法在适配壳中存在，且 handle_tool_call 签名
遵循 Hermes 契约（tool_name + args + **kwargs → str）。

方法清单来自 Hermes agent/memory_provider.py（本机安装核对，2026-08-12）。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "src" / "access" / "provider" / "hermes_plugin"

# Hermes MemoryProvider ABC 全接口（核心 + 钩子 + 配置向导）
REQUIRED_METHODS = [
    # 核心生命周期
    "is_available",
    "initialize",
    "system_prompt_block",
    "prefetch",
    "queue_prefetch",
    "sync_turn",
    "get_tool_schemas",
    "handle_tool_call",
    "shutdown",
    # 生命周期钩子
    "on_turn_start",
    "on_session_end",
    "on_session_switch",
    "on_pre_compress",
    "on_memory_write",
    "on_delegation",
    # 配置向导
    "get_config_schema",
    "save_config",
    # Kairos 扩展（架构 on_calibration；Hermes 无原生钩子，经方法暴露）
    "calibrate",
]


def _class_method_names() -> set[str]:
    tree = ast.parse((PLUGIN_DIR / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "KairosMemoryProvider":
            return {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    raise AssertionError("hermes_plugin/__init__.py 缺少 KairosMemoryProvider 类")


def test_all_hermes_abc_methods_present() -> None:
    methods = _class_method_names()
    missing = [m for m in REQUIRED_METHODS if m not in methods]
    assert not missing, f"适配壳缺失 Hermes MemoryProvider 方法: {missing}"


def test_handle_tool_call_hermes_contract() -> None:
    """Hermes 契约：handle_tool_call(tool_name, args, **kwargs) -> str。"""
    tree = ast.parse((PLUGIN_DIR / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if not (isinstance(node, ast.ClassDef) and node.name == "KairosMemoryProvider"):
            continue
        for member in node.body:
            if not (isinstance(member, ast.FunctionDef) and member.name == "handle_tool_call"):
                continue
            arg_names = [a.arg for a in member.args.args]
            assert arg_names[:2] == ["self", "tool_name"], f"参数名不符: {arg_names}"
            assert member.args.kwarg is not None, "缺少 **kwargs"
            is_str_anno = isinstance(member.returns, ast.Name) and member.returns.id == "str"
            assert is_str_anno, "handle_tool_call 必须声明 -> str（Hermes 契约）"
            return
    raise AssertionError("未找到 handle_tool_call 定义")
