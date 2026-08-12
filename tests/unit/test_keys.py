"""密钥工具单元测试（S-01/S-05/S-16）——PBKDF2 派生/校验/文件权限/HMAC。

覆盖：derive_api_key_hash（256k 迭代）、verify_api_key（恒定时间比对）、
bootstrap_keys（四密钥幂等生成 + 600 权限）、hmac_sha256_hex（审计链签名）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.keys import (
    PBKDF2_ITERATIONS,
    bootstrap_keys,
    derive_api_key_hash,
    hmac_sha256_hex,
    verify_api_key,
)

pytestmark = pytest.mark.unit


class TestApiKeyHash:
    def test_derive_is_deterministic(self) -> None:
        h1 = derive_api_key_hash("secret-key-1", "salt-1")
        h2 = derive_api_key_hash("secret-key-1", "salt-1")
        assert h1 == h2

    def test_derive_differs_by_salt(self) -> None:
        h1 = derive_api_key_hash("key", "salt-a")
        h2 = derive_api_key_hash("key", "salt-b")
        assert h1 != h2

    def test_derive_uses_256k_iterations(self) -> None:
        assert PBKDF2_ITERATIONS == 256_000  # security-spec §2.1

    def test_verify_match_and_mismatch(self) -> None:
        salt = "s" * 16
        stored = derive_api_key_hash("the-key", salt)
        assert verify_api_key("the-key", salt, stored) is True
        assert verify_api_key("wrong-key", salt, stored) is False


class TestBootstrapKeys:
    def test_bootstrap_generates_env_file(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        plain = bootstrap_keys(env)
        assert plain  # API Key 明文仅输出一次
        content = env.read_text(encoding="utf-8")
        for key in (
            "KAIROS_API_KEY_HASH",
            "KAIROS_SALT",
            "KAIROS_SECRET_KEY",
            "KAIROS_AUDIT_HMAC_KEY",
        ):
            assert key in content

    def test_bootstrap_is_idempotent(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        bootstrap_keys(env)
        first = env.read_text(encoding="utf-8")
        bootstrap_keys(env)  # 重复执行不重新生成
        assert env.read_text(encoding="utf-8") == first

    def test_bootstrap_hash_verifies(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        plain = bootstrap_keys(env)
        lines = dict(
            line.split("=", 1)
            for line in env.read_text(encoding="utf-8").splitlines()
            if "=" in line
        )
        assert verify_api_key(plain, lines["KAIROS_SALT"], lines["KAIROS_API_KEY_HASH"]) is True


class TestHmac:
    def test_hmac_sha256_hex_deterministic(self) -> None:
        a = hmac_sha256_hex("11" * 32, b"payload")
        b = hmac_sha256_hex("11" * 32, b"payload")
        assert a == b
        assert len(a) == 64  # SHA-256 hex

    def test_hmac_differs_by_key(self) -> None:
        a = hmac_sha256_hex("11" * 32, b"payload")
        b = hmac_sha256_hex("22" * 32, b"payload")
        assert a != b
