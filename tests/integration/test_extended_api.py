"""扩展端点集成测试（MCP 工具契约 §6.8 补齐端点）。

覆盖：stats / heat-top / feedback / traces / entities-extract / graph-search /
sessions / relations 全流程（link → query → unlink）。
"""

from __future__ import annotations

import pytest
from litestar.testing import AsyncTestClient

from src.access.server import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
async def client(memory_db):
    """无密钥测试客户端（与 test_api.py 同构）。"""
    from src.app import build_app

    settings = type(
        "S",
        (),
        {
            "get": lambda self, k, d=None: {
                "KAIROS_AUDIT_HMAC_KEY": "22" * 32,
                "KAIROS_FORGETTING_HALF_LIFE": 69,
                "KAIROS_FRESHNESS_ACTIVE_THRESHOLD": 0.3,
                "KAIROS_FRESHNESS_STALE_THRESHOLD": 0.1,
                "KAIROS_DEGRADATION_PERIOD_N": 50,
                "KAIROS_DEGRADATION_PERIOD_M": 200,
                "KAIROS_HOST": "127.0.0.1",
                "KAIROS_PORT": 8010,
            }.get(k, d)
        },
    )()
    kairos = build_app(settings, db=memory_db)
    app = create_app(kairos)
    async with AsyncTestClient(app) as c:
        yield c
    await kairos.close()


def _write_payload(
    content: str, path: str = "kairos://_user/t/ext", provenance: str = "user_input"
):
    return {"path": path, "content": content, "provenance": provenance}


@pytest.mark.asyncio
async def test_stats_and_heat_top(client: AsyncTestClient) -> None:
    """stats 聚合 + heat-top 排序（kairos_get_stats / kairos_get_hot_memories）。"""
    r = await client.post(
        "/v1/memories", json=_write_payload("扩展端点测试记忆 统计验证 内容足够长")
    )
    assert r.status_code == 201, r.text

    stats = (await client.get("/v1/memories/stats")).json()
    assert stats["total"] >= 1
    assert stats["by_state"].get("active", 0) >= 1

    hot = (await client.get("/v1/memories/heat-top?limit=5")).json()
    assert "data" in hot
    assert isinstance(hot["total"], int)


@pytest.mark.asyncio
async def test_feedback_updates_confidence_and_audits(client: AsyncTestClient) -> None:
    """feedback 更新 calibration_confidence + 审计留痕（kairos_feedback_memory）。"""
    r = await client.post(
        "/v1/memories", json=_write_payload("反馈测试记忆 内容足够长 用于可信度更新")
    )
    mem_id = r.json()["id"]

    fb = await client.post(
        f"/v1/memories/{mem_id}/feedback", json={"feedback": 0.9, "reason": "test"}
    )
    assert fb.status_code == 201, fb.text
    body = fb.json()
    assert body["status"] == "applied"
    assert body["new"] == pytest.approx(0.7 * 0.5 + 0.3 * 0.9)

    # 审计链留痕
    log = (await client.get("/v1/audit-log?limit=10")).json()
    actions = [e["action"] for e in log["logs"]]
    assert "feedback" in actions

    # 非法反馈 422
    bad = await client.post(f"/v1/memories/{mem_id}/feedback", json={"feedback": 1.5})
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_traces_records_state_history(client: AsyncTestClient) -> None:
    """traces 返回状态机轨迹（kairos_get_memory_traces——memory_states 数据源）。"""
    r = await client.post(
        "/v1/memories", json=_write_payload("轨迹测试记忆 内容足够长 生命周期验证")
    )
    mem_id = r.json()["id"]

    # 归档触发状态转换（写入 memory_states）
    ar = await client.post(f"/v1/memories/{mem_id}/archive", json={"reason": "test"})
    assert ar.status_code == 200, ar.text

    traces = (await client.get(f"/v1/memories/{mem_id}/traces")).json()
    assert traces["memory_id"] == mem_id
    states = [t["state"] for t in traces["traces"]]
    assert "archived" in states


@pytest.mark.asyncio
async def test_entities_extract_and_graph_search(client: AsyncTestClient) -> None:
    """实体提取入库 + 图谱检索（kairos_extract_entities / kairos_search_graph）。"""
    text = "Kairos 记忆系统 项目使用 SQLite 引擎，Hermes 集成采用 MCP 协议"
    ex = await client.post("/v1/entities/extract", json={"text": text})
    assert ex.status_code == 201, ex.text
    body = ex.json()
    assert body["count"] >= 1
    names = [e["name"] for e in body["entities"]]

    gs = await client.post("/v1/graph/search", json={"query": names[0], "limit": 5})
    assert gs.status_code == 201, gs.text
    assert gs.json()["hops"] >= 1


@pytest.mark.asyncio
async def test_sessions_lists_dialogue_memories(client: AsyncTestClient) -> None:
    """sessions 列表识别对话记录记忆（kairos_search_sessions）。"""
    await client.post(
        "/v1/memories",
        json=_write_payload(
            "对话记录（session-test-123）:\n用户: 测试会话内容",
            path="kairos://_user/hermes/sessions/session-test-123",
        ),
    )
    sess = (await client.get("/v1/sessions?limit=5")).json()
    ids = [s["session_id"] for s in sess["data"]]
    assert any("session-test-123" in i for i in ids)


@pytest.mark.asyncio
async def test_relations_full_flow(client: AsyncTestClient) -> None:
    """关系全流程：link → query → unlink → query 空（kairos_link/unlink/relations）。"""
    a = (await client.post("/v1/memories", json=_write_payload("关系源记忆 内容足够长 A"))).json()[
        "id"
    ]
    b = (
        await client.post("/v1/memories", json=_write_payload("关系目标记忆 内容足够长 B"))
    ).json()["id"]

    # link（必填 reason）
    lk = await client.post(
        "/v1/relations",
        json={"from_uri": a, "uris": [b], "reason": "测试关联", "relation_type": "reference"},
    )
    assert lk.status_code == 201, lk.text
    assert lk.json()["count"] == 1

    # query（outbound）
    q = (await client.get(f"/v1/relations/{a}?direction=outbound")).json()
    assert q["outbound"][0]["target_id"] == b

    # 重复 link 幂等（exists 而非 created）
    lk2 = await client.post("/v1/relations", json={"from_uri": a, "uris": [b], "reason": "重复"})
    assert lk2.json()["created"][0]["status"] == "exists"

    # unlink（软删除）
    ul = await client.delete(f"/v1/relations/{a}/{b}?relation_type=reference")
    assert ul.status_code == 200, ul.text
    assert ul.json()["removed"] == 1

    q2 = (await client.get(f"/v1/relations/{a}?direction=outbound")).json()
    assert q2["outbound"] == []

    # 必填缺失 422
    bad = await client.post("/v1/relations", json={"from_uri": a, "uris": [b]})
    assert bad.status_code == 422
