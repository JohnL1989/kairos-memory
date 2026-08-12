"""CLI 命令集成测试（竖切 15 条子集冒烟）——覆盖 main.py 注册与 cli.py 实现。

覆盖：write/read/search/ls/update/forget/calibrate/freeze/status/health/config show
命令全链路（经 _resolve_app 迁移 + 操作 + 关闭）。
"""

from __future__ import annotations

import pytest

from src.access import cli

pytestmark = pytest.mark.integration


@pytest.fixture
async def cli_env(memory_db, monkeypatch):
    """CLI 测试环境：memory_db 注入（_resolve_app 直接调用 build_app 用默认 DB——
    测试改用 monkeypatch 让 CLI 复用 memory_db 不可行；此处直接调 cli 模块函数并
    传临时 DB 场景由各测试自行处理（CLI 函数内部建库，测试用临时目录）。"""
    return memory_db


class TestCliCommands:
    async def test_write_read_update_flow(self, tmp_path) -> None:
        """write → read → update 全链路（路径 uuid 化 + 版本链）。"""
        import os

        os.environ["KAIROS_DB_URL"] = f"sqlite:///{tmp_path / 'c.db'}"
        os.environ.setdefault("KAIROS_AUDIT_HMAC_KEY", "22" * 32)
        created = await cli.cmd_write(
            "kairos://_user/u1/memories/",
            "CLI 测试记忆内容，长度足够用于测试。",
            source="user_input",
        )
        assert created["version"] == 1
        detail = await cli.cmd_read(created["id"])
        assert detail["content"] == "CLI 测试记忆内容，长度足够用于测试。"
        updated = await cli.cmd_update(
            created["id"], content="CLI 更新后的记忆内容，长度足够。", if_match=1
        )
        assert updated["version"] == 2

    async def test_search_and_ls(self, tmp_path) -> None:
        import os

        os.environ["KAIROS_DB_URL"] = f"sqlite:///{tmp_path / 'c2.db'}"
        os.environ.setdefault("KAIROS_AUDIT_HMAC_KEY", "22" * 32)
        await cli.cmd_write(
            "kairos://_user/u1/memories/", "Python async searchable content", source="user_input"
        )
        result = await cli.cmd_search("Python async")
        assert result["total"] >= 1
        listing = await cli.cmd_ls("kairos://_user/u1/memories/")
        assert listing["total"] >= 1

    async def test_health_and_config(self, tmp_path) -> None:
        import os

        os.environ["KAIROS_DB_URL"] = f"sqlite:///{tmp_path / 'c3.db'}"
        os.environ.setdefault("KAIROS_AUDIT_HMAC_KEY", "22" * 32)
        health = await cli.cmd_health()
        assert health["status"] == "ok"
        cfg = await cli.cmd_config_show("KAIROS_FORGETTING_HALF_LIFE")
        assert cfg["config"][0]["value"] == "69"

    async def test_forget_and_calibrate(self, tmp_path) -> None:
        import os

        os.environ["KAIROS_DB_URL"] = f"sqlite:///{tmp_path / 'c4.db'}"
        os.environ.setdefault("KAIROS_AUDIT_HMAC_KEY", "22" * 32)
        created = await cli.cmd_write(
            "kairos://_user/u1/memories/",
            "CLI 遗忘测试记忆内容，长度足够用于测试。",
            source="user_input",
        )
        cal = await cli.cmd_calibrate(created["id"], 0.8)
        assert cal["status"] == "accepted"
        deleted = await cli.cmd_forget(created["id"])
        assert deleted["status"] == "deleted"

    async def test_freeze_status_degradation(self, tmp_path) -> None:
        import os

        os.environ["KAIROS_DB_URL"] = f"sqlite:///{tmp_path / 'c5.db'}"
        os.environ.setdefault("KAIROS_AUDIT_HMAC_KEY", "22" * 32)
        frozen = await cli.cmd_freeze(60)
        assert frozen["status"] == "frozen"
        status = await cli.cmd_status()
        assert status["frozen"] is True
        switched = await cli.cmd_degradation_switch("safe_hibernation")
        assert switched["mode"] == "safe_hibernation"
        await cli.cmd_unfreeze()
