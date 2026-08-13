"""Kairos Hermes Memory Provider 单元测试（架构 §7.1a）。

覆盖：6 生命周期钩子 HTTP 语义（prefetch 召回注入 / sync_turn / on_session_end /
on_pre_compress / on_memory_write / on_delegation / calibrate）、queue_prefetch
后台缓存、agent_context 守卫、is_available / initialize 校验、失败留痕不阻断。
"""

from __future__ import annotations

import json
import time

import httpx
import pytest

from src.access.provider import kairos_provider as provider_mod
from src.access.provider.kairos_provider import KairosMemoryProvider

pytestmark = pytest.mark.unit


def _make_provider(handler) -> KairosMemoryProvider:
    """构造 provider + MockTransport HTTP 客户端。"""
    provider = KairosMemoryProvider(base_url="http://mock", api_key="test-key")
    provider._http = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://mock", timeout=5.0
    )
    return provider


def _handler_ok(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/health":
        return httpx.Response(200, json={"status": "ok"})
    if request.url.path == "/v1/memories/search":
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "m1", "content": "相关记忆内容甲"},
                    {"id": "m2", "content": "相关记忆内容乙"},
                ]
            },
        )
    if request.url.path == "/v1/memories":
        return httpx.Response(
            201, json={"id": "p-1", "path": "kairos://_user/hermes/memories/p-1", "version": 1}
        )
    if request.url.path == "/v1/calibrate":
        return httpx.Response(200, json={"status": "accepted", "memory_id": "m1"})
    return httpx.Response(404, json={})


class TestCoreLifecycle:
    def test_is_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 隔离真实环境变量（本地可能已设 KAIROS_API_KEY，会污染断言）
        monkeypatch.setattr(provider_mod, "DEFAULT_API_KEY", "")
        monkeypatch.setattr(provider_mod, "DEFAULT_BASE_URL", "")
        assert KairosMemoryProvider(base_url="http://x", api_key="k").is_available() is True
        assert KairosMemoryProvider(base_url="", api_key="").is_available() is False

    def test_system_prompt_block(self) -> None:
        p = KairosMemoryProvider()
        assert "Kairos" in p.system_prompt_block()

    def test_prefetch_injects_context(self) -> None:
        p = _make_provider(_handler_ok)
        ctx = p.prefetch("查询相关记忆")
        assert "[Kairos 记忆]" in ctx
        assert "相关记忆内容甲" in ctx

    def test_prefetch_trivial_query_empty(self) -> None:
        p = _make_provider(_handler_ok)
        assert p.prefetch("") == ""

    def test_prefetch_failure_non_blocking(self) -> None:
        p = _make_provider(lambda req: httpx.Response(500, json={}))
        assert p.prefetch("查询") == ""  # 失败留痕不阻断

    def test_initialize_verifies_service(self) -> None:
        p = _make_provider(_handler_ok)
        p.initialize("sess-1")  # health 200 → 不抛异常

    def test_initialize_unreachable_raises(self) -> None:
        p = _make_provider(lambda req: httpx.Response(503, json={}))
        with pytest.raises(RuntimeError, match="不可达"):
            p.initialize("sess-1")


class TestLifecycleHooks:
    def test_sync_turn_writes(self) -> None:
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        p.sync_turn("用户问题", "助手回答")
        assert len(calls) == 1
        body = calls[0].read()
        import json as _json

        payload = _json.loads(body)
        assert payload["provenance"] == "system_generated"
        assert "用户问题" in payload["content"]

    def test_on_session_end_summarizes(self) -> None:
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        p.on_session_end(
            [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好，有什么可以帮你"},
            ]
        )
        assert len(calls) == 1

    def test_on_pre_compress_returns_summary(self) -> None:
        p = _make_provider(_handler_ok)
        summary = p.on_pre_compress([{"role": "user", "content": "将被压缩的对话内容"}])
        assert "将被压缩" in summary

    def test_on_memory_write_mirrors(self) -> None:
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        p.on_memory_write("create", "task-1", "外部写入的记忆内容")
        assert len(calls) == 1

    def test_on_delegation_records_subtask(self) -> None:
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        p.on_delegation("子任务描述", "子任务结果", child_session_id="sub-1")
        assert len(calls) == 1

    def test_calibrate(self) -> None:
        p = _make_provider(_handler_ok)
        result = p.calibrate("m1", 0.85)
        assert result["status"] == "accepted"


class TestToolSurface:
    def test_tool_schemas(self) -> None:
        p = KairosMemoryProvider()
        schemas = p.get_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "kairos_provider_write"

    def test_handle_tool_call_returns_json_string(self) -> None:
        """Hermes 契约：handle_tool_call 返回 JSON 字符串。"""
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        result = p.handle_tool_call("kairos_provider_write", {"content": "工具写入内容"})
        assert isinstance(result, str)
        assert json.loads(result)["id"] == "p-1"
        assert len(calls) == 1

    def test_unknown_tool(self) -> None:
        p = _make_provider(_handler_ok)
        result = p.handle_tool_call("nope", {})
        assert isinstance(result, str)
        assert "error" in json.loads(result)


class TestQueuePrefetch:
    def test_queue_prefetch_fills_cache_and_consumes(self) -> None:
        p = _make_provider(_handler_ok)
        p.queue_prefetch("后台召回查询")
        # 后台线程写缓存，轮询等待
        deadline = time.time() + 5.0
        while p._prefetch_cache is None and time.time() < deadline:
            time.sleep(0.05)
        assert p._prefetch_cache is not None
        assert "相关记忆内容甲" in p._prefetch_cache

        # prefetch 消费缓存（不发起新请求），二次调用回退同步检索
        calls: list[dict] = []

        def counting_handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories/search":
                calls.append(req)
            return _handler_ok(req)

        p._http.close()
        p._http = httpx.Client(
            transport=httpx.MockTransport(counting_handler), base_url="http://mock", timeout=5.0
        )
        p._prefetch_cache = "缓存内容"
        assert p.prefetch("查询") == "缓存内容"
        assert p._prefetch_cache is None
        assert len(calls) == 0

    def test_prefetch_falls_back_to_sync_without_cache(self) -> None:
        p = _make_provider(_handler_ok)
        ctx = p.prefetch("无缓存查询")
        assert "[Kairos 记忆]" in ctx

    def test_queue_prefetch_failure_non_blocking(self) -> None:
        p = _make_provider(lambda req: httpx.Response(500, json={}))
        p.queue_prefetch("查询")
        time.sleep(0.2)
        assert p._prefetch_cache is None  # 失败留痕，缓存保持空


class TestAgentContextGuard:
    def test_non_primary_context_skips_writes(self) -> None:
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        p.initialize("sess-cron", agent_context="cron")
        p.sync_turn("用户问题", "助手回答")
        assert len(calls) == 0  # cron 上下文不写记忆

    def test_primary_context_writes(self) -> None:
        calls: list[dict] = []

        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/v1/memories":
                calls.append(req)
            return _handler_ok(req)

        p = _make_provider(handler)
        p.initialize("sess-1", agent_context="primary")
        p.sync_turn("用户问题", "助手回答")
        assert len(calls) == 1


class TestSessionSwitch:
    def test_on_session_switch_records_and_clears_cache(self) -> None:
        p = _make_provider(_handler_ok)
        p._prefetch_cache = "旧会话缓存"
        p.on_session_switch("sess-2", parent_session_id="sess-1", reset=True)
        assert p._session_id == "sess-2"
        assert p._prefetch_cache is None

    def test_on_session_switch_no_reset_keeps_cache(self) -> None:
        p = _make_provider(_handler_ok)
        p._prefetch_cache = "缓存"
        p.on_session_switch("sess-3", parent_session_id="sess-1", reset=False)
        assert p._prefetch_cache == "缓存"


class TestConfigWizard:
    def test_get_config_schema_fields(self) -> None:
        p = KairosMemoryProvider()
        schema = {f["key"]: f for f in p.get_config_schema()}
        assert "base_url" in schema and schema["base_url"].get("secret", False) is False
        assert schema["api_key"]["secret"] is True
        assert schema["api_key"]["env_var"] == "KAIROS_API_KEY"

    def test_save_config_writes_json(self, tmp_path) -> None:
        p = KairosMemoryProvider()
        p.save_config(
            {"base_url": "http://example:8011", "api_key": "should-not-写入"}, str(tmp_path)
        )
        target = tmp_path / "kairos" / "config.json"
        assert target.is_file()
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["base_url"] == "http://example:8011"
        assert "api_key" not in data  # secret 不落盘
