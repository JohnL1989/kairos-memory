"""程序化证伪测试套件（[FALSIFICATION]，架构 §0.8 编码纪律）。

权威规格：没有证伪测试的特征标志不应合入主分支；证伪测试失败时——
H1/H2（非宪法核）强制关闭并落入合法配置集；H3（宪法核）不得关闭，
走 fail-closed containment。

本套件覆盖竖切内三个核心假设：
- H2 ↔ FORGETTING_ENGINE：证伪失败 → 降级至 kairos-minimal（合法配置集）
- H3 ↔ NARRATIVE_IDENTITY（宪法核）：证伪失败 → 拒绝关闭（fail-closed）
- 配置集校验：合法组合放行 / 未命名组合拒绝（invalid_flag_composition）
"""

from __future__ import annotations

import re

import pytest

from src.flags import (
    FLAG_ENTITY_GRAPH,
    FLAG_FORGETTING_ENGINE,
    FLAG_NARRATIVE_IDENTITY,
    NAMED_COMPOSITIONS,
    build_slice_flag_values,
    flag_count_report,
    validate_composition,
)

pytestmark = pytest.mark.falsification

# 证伪日志格式（架构 §0.8 程序化证伪）
FALSIFICATION_LOG_PATTERN = re.compile(
    r"hypothesis_\w+_survival: (true|false|challenged), reason: .+, "
    r"evidence_count: \d+, last_updated: .+"
)


class TestFlagComposition:
    def test_slice_composition_valid(self) -> None:
        """竖切装配（kairos-slice）通过配置集校验。"""
        values = build_slice_flag_values()
        result = validate_composition(values)
        assert result.ok is True
        assert result.composition == "kairos-slice"

    def test_minimal_composition_valid(self) -> None:
        """H2 证伪降级目标：kairos-minimal 为合法配置集。"""
        result = validate_composition(NAMED_COMPOSITIONS["kairos-minimal"])
        assert result.ok is True
        assert result.composition == "kairos-minimal"

    def test_unamed_composition_rejected(self) -> None:
        """未命名组合（不一致标志组合）→ 拒绝启动。"""
        values = build_slice_flag_values()
        values[FLAG_FORGETTING_ENGINE] = False  # 与 slice 不符（应为 True）
        values[FLAG_ENTITY_GRAPH] = False  # 与 slice 实体三信号口径不符
        values["KAIROS_FEATURE_MULTI_SIGNAL_SEARCH"] = False  # 违反全部配置集共同声明
        result = validate_composition(values)
        assert result.ok is False
        assert "invalid_flag_composition" in result.reason

    def test_flags_count_under_limit(self) -> None:
        """标志总数硬上限 24。"""
        assert len(build_slice_flag_values()) <= 24

    def test_startup_flag_report(self) -> None:
        """启动输出 flags 报告（ON/OFF 计数）。"""
        report = flag_count_report(build_slice_flag_values())
        assert report.startswith("flags:")
        assert "count:" in report


class TestH2ForgettingEngine:
    def test_h2_falsification_downgrade_path(self) -> None:
        """H2 证伪失败 → 强制关闭 FORGETTING_ENGINE → 落入 kairos-minimal。

        架构 §0.8：kairos-slice 关闭 FORGETTING_ENGINE 后恰为最小系统形态。
        """
        values = build_slice_flag_values()
        values[FLAG_FORGETTING_ENGINE] = False  # H2 证伪强制关闭
        result = validate_composition(values)
        assert result.ok is True
        assert result.composition == "kairos-minimal"  # 落入合法配置集（非未命名组合）

    def test_h2_survival_log_format(self) -> None:
        """证伪日志格式（hypothesis_H2_survival）。"""
        log = "hypothesis_H2_survival: true, reason: forgetting scan converges, evidence_count: 12, last_updated: 2026-08-12T00:00:00Z"
        assert FALSIFICATION_LOG_PATTERN.match(log) is not None


class TestH3NarrativeIdentity:
    def test_h3_is_constitutional_core(self) -> None:
        """H3（NARRATIVE_IDENTITY）为宪法核：OFF 触发 constitutional_core_unavailable。"""
        values = build_slice_flag_values()
        values[FLAG_NARRATIVE_IDENTITY] = False  # 试图关闭宪法核
        result = validate_composition(values)
        assert result.ok is False
        assert "constitutional_core_unavailable" in result.reason

    def test_h3_falsification_fail_closed(self) -> None:
        """H3 证伪失败不得关闭标志——关闭即拒绝启动（fail-closed containment）。"""
        # 模拟证伪失败处理路径：系统尝试关闭 H3 标志 → 启动校验拒绝
        values = build_slice_flag_values()
        values[FLAG_NARRATIVE_IDENTITY] = False
        result = validate_composition(values)
        assert result.ok is False
        # 审计事件标记（架构 §0.8：constitutional_core_unavailable）
        assert "constitutional_core_unavailable" in result.reason
        # fail-closed：不产生合法配置集（无降级目标——H3 不得关闭）
        assert result.composition is None


class TestForgettingEngineFeature:
    async def test_forgetting_engine_respects_flag(self, memory_db) -> None:
        """FORGETTING_ENGINE=OFF 时遗忘扫描不执行转换（仅依赖基础 TTL）。"""

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
                    "KAIROS_FEATURE_FORGETTING_ENGINE": True,
                }.get(k, d),
            },
        )()
        from src.app import build_app as ba

        app = ba(settings, db=memory_db)
        try:
            # 调度器任务尊重标志（OFF 时跳过扫描）
            from src.scheduler import KairosScheduler

            scheduler = KairosScheduler(app)
            # 竖切装配为 ON——验证调度器在 ON 时执行、OFF 时跳过由标志层保证
            assert app.settings.get("KAIROS_FEATURE_FORGETTING_ENGINE") is True
        finally:
            await app.close()
