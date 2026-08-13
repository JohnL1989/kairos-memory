"""main.py CLI 入口注册测试（0.1.9 批次补测）。

test_cli.py 直接调 `cli.cmd_*` 异步函数，main.py 的 Typer 注册层（170 行）
此前 0% 覆盖。本文件用 typer.testing.CliRunner 经完整命令链驱动：
- `--version` / `--help` / 子命令 `--help`：纯注册层（无 DB 依赖）
- write → read 真实链路：临时文件库（跨命令共享，验证入口接线正确）
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from src.main import app

pytestmark = pytest.mark.integration

runner = CliRunner()

# main.py 注册的全部命令/命令组（--help 必须全部可见）
ALL_COMMANDS = [
    "init",
    "write",
    "read",
    "search",
    "ls",
    "tree",
    "update",
    "forget",
    "calibrate",
    "freeze",
    "unfreeze",
    "status",
    "health",
    "mcp",
    "serve",
    "db",
    "degradation",
    "config",
    "audit",
    "seed",
]


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Kairos" in result.output


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ALL_COMMANDS:
        assert cmd in result.output, f"--help 缺少命令: {cmd}"


def test_subcommand_helps() -> None:
    """命令组与子命令 --help 均可正常渲染（注册完整性）。"""
    for args in (
        ["db", "--help"],
        ["db", "migrate", "--help"],
        ["db", "verify", "--help"],
        ["db", "backfill-entities", "--help"],
        ["degradation", "--help"],
        ["config", "--help"],
        ["audit", "--help"],
        ["seed", "--help"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, f"{args} 失败: {result.output[:200]}"


def test_write_read_flow_via_cli(tmp_path, monkeypatch) -> None:
    """完整命令链：write → read（临时文件库跨命令共享）。"""
    monkeypatch.setenv("KAIROS_DB_URL", f"sqlite:///{tmp_path / 'cli.db'}")
    monkeypatch.setenv("KAIROS_AUDIT_HMAC_KEY", "22" * 32)
    w = runner.invoke(
        app,
        [
            "write",
            "kairos://_user/u1/memories/",
            "--content",
            "CliRunner 端到端记忆内容，长度充足以通过捕获门禁。",
            "--source",
            "user_input",
        ],
    )
    assert w.exit_code == 0, f"write 失败: {w.output[:300]}"
    # 首次写入触发 Alembic 迁移，日志混入 stdout——JSON 从首个 '{' 起提取
    created = json.loads(w.output[w.output.index("{") :])
    assert created["version"] == 1

    r = runner.invoke(app, ["read", created["id"]])
    assert r.exit_code == 0, f"read 失败: {r.output[:300]}"
    detail = json.loads(r.output[r.output.index("{") :])
    assert detail["content"] == "CliRunner 端到端记忆内容，长度充足以通过捕获门禁。"
