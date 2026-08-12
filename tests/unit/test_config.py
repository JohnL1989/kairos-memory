"""配置加载单元测试（W1 交付物验证）。

覆盖：默认值、env 覆盖、.env 文件、S-01 必填校验、参数取值范围校验、
运行时动态覆盖校验、路径 $HOME 展开。
"""

from __future__ import annotations

import pytest

from src.config import ConfigError, load_settings, validate_runtime_override


def _env(**overrides: str) -> dict[str, str]:
    base = {
        "KAIROS_API_KEY_HASH": "h",
        "KAIROS_AUDIT_HMAC_KEY": "k",
    }
    base.update(overrides)
    return base


class TestDefaults:
    """configuration.md 默认值对齐（检索 §6.1 / 遗忘 §10 / 降级 §4）。"""

    def test_hybrid_weights_defaults(self) -> None:
        s = load_settings(_env())
        assert s.get("KAIROS_HYBRID_SEMANTIC_WEIGHT") == 0.50
        assert s.get("KAIROS_HYBRID_BM25_WEIGHT") == 0.35
        assert s.get("KAIROS_HYBRID_ENTITY_WEIGHT") == 0.15
        # 权重和恒为 1（架构 §7.3a 三信号融合）
        total = (
            s.get("KAIROS_HYBRID_SEMANTIC_WEIGHT")
            + s.get("KAIROS_HYBRID_BM25_WEIGHT")
            + s.get("KAIROS_HYBRID_ENTITY_WEIGHT")
        )
        assert total == pytest.approx(1.0)

    def test_forgetting_defaults(self) -> None:
        s = load_settings(_env())
        assert s.get("KAIROS_FORGETTING_HALF_LIFE") == 69
        assert s.get("KAIROS_FRESHNESS_ACTIVE_THRESHOLD") == 0.3
        assert s.get("KAIROS_FRESHNESS_STALE_THRESHOLD") == 0.1
        assert s.get("KAIROS_FEATURE_FORGETTING_ENGINE") is True  # 竖切内 ON

    def test_degradation_periods(self) -> None:
        s = load_settings(_env())
        assert s.get("KAIROS_DEGRADATION_PERIOD_N") == 50
        assert s.get("KAIROS_DEGRADATION_PERIOD_M") == 200

    def test_ingestion_limits(self) -> None:
        s = load_settings(_env())
        assert s.get("KAIROS_CAPTURE_MIN_LENGTH") == 10
        assert s.get("KAIROS_INPUT_LIMIT_CONTENT_BYTES") == 65536
        assert s.get("KAIROS_INPUT_LIMIT_QUERY_CHARS") == 500


class TestEnvOverride:
    def test_env_overrides_default(self) -> None:
        s = load_settings(_env(KAIROS_FORGETTING_HALF_LIFE="30"))
        assert s.get("KAIROS_FORGETTING_HALF_LIFE") == 30

    def test_bool_parsing(self) -> None:
        assert (
            load_settings(_env(KAIROS_FEATURE_FORGETTING_ENGINE="false")).get(
                "KAIROS_FEATURE_FORGETTING_ENGINE"
            )
            is False
        )
        assert load_settings(_env(KAIROS_FTS5_ENABLED="off")).get("KAIROS_FTS5_ENABLED") is False
        assert (
            load_settings(_env(KAIROS_FTS5_CHINESE_SEGMENTATION="1")).get(
                "KAIROS_FTS5_CHINESE_SEGMENTATION"
            )
            is True
        )

    def test_unknown_env_ignored(self) -> None:
        s = load_settings(_env(KAIROS_UNKNOWN_PARAM="x"))
        assert "KAIROS_UNKNOWN_PARAM" not in s.values


class TestRequiredParams:
    """S-01 启动校验：必填无默认值参数缺失 → 失败关闭。"""

    def test_missing_audit_hmac_key_rejected(self) -> None:
        with pytest.raises(ConfigError, match="KAIROS_AUDIT_HMAC_KEY"):
            load_settings({"KAIROS_API_KEY_HASH": "h"})


class TestValidation:
    def test_narrative_cycle_max_over_12_rejected(self) -> None:
        """架构 §8 / configuration §0.10：>12 拒绝启动。"""
        with pytest.raises(ConfigError, match="NARRATIVE_AUDIT_CYCLE_MAX"):
            load_settings(_env(KAIROS_NARRATIVE_AUDIT_CYCLE_MAX="13"))

    def test_narrative_cycle_max_12_allowed(self) -> None:
        s = load_settings(_env(KAIROS_NARRATIVE_AUDIT_CYCLE_MAX="12"))
        assert s.get("KAIROS_NARRATIVE_AUDIT_CYCLE_MAX") == 12

    def test_negative_half_life_rejected(self) -> None:
        with pytest.raises(ConfigError, match="FORGETTING_HALF_LIFE"):
            load_settings(_env(KAIROS_FORGETTING_HALF_LIFE="0"))

    def test_weight_out_of_range_rejected(self) -> None:
        with pytest.raises(ConfigError, match="HYBRID"):
            load_settings(_env(KAIROS_HYBRID_ENTITY_WEIGHT="1.5"))

    def test_malformed_int_rejected(self) -> None:
        with pytest.raises(ConfigError, match="解析失败"):
            load_settings(_env(KAIROS_FORGETTING_HALF_LIFE="abc"))


class TestRuntimeOverride:
    def test_valid_override(self) -> None:
        assert validate_runtime_override("KAIROS_HYBRID_ENTITY_WEIGHT", "0.20") == 0.20

    def test_unknown_param_rejected(self) -> None:
        with pytest.raises(ConfigError, match="未知参数"):
            validate_runtime_override("KAIROS_NOPE", "1")

    def test_out_of_range_rejected(self) -> None:
        with pytest.raises(ConfigError, match="HYBRID"):
            validate_runtime_override("KAIROS_HYBRID_ENTITY_WEIGHT", "2")


class TestHomeExpansion:
    def test_db_url_home_expanded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KAIROS_DB_URL", raising=False)
        s = load_settings(_env())
        # 默认 sqlite:///$HOME/.kairos/kairos.db 已展开
        assert "$HOME" not in s.get("KAIROS_DB_URL")
        assert s.get("KAIROS_DB_URL").startswith("sqlite:///")
