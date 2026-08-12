"""密钥生成与哈希工具。

权威来源：docs/security/security-specification.md §2.1 API Key 生命周期。
- KAIROS_API_KEY_HASH = PBKDF2-HMAC-SHA512(key + salt, iterations=256_000)
- 明文 API Key 仅存在于启动进程内存 / init 输出（不持久化到磁盘）
- .env 文件权限 600（Windows 尽力设置，POSIX 强制）

S-05 加盐值 SALT 轮换时保留旧盐验证已有哈希（runbook §6.1 季度口径）。
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import secrets
from pathlib import Path

# security-specification §2.1：PBKDF2-HMAC-SHA512，256,000 次迭代
PBKDF2_ITERATIONS = 256_000
# 32 字节 = 256 bit（AES-256-GCM 密钥长度 / HMAC-SHA256 密钥建议长度）
KEY_BYTES = 32
# 加盐值长度（S-05）
SALT_BYTES = 16

# 写入 .env 的密钥参数族（含哈希派生值）
_ENV_KEYS = (
    "KAIROS_API_KEY_HASH",
    "KAIROS_SALT",
    "KAIROS_SECRET_KEY",
    "KAIROS_AUDIT_HMAC_KEY",
)


def derive_api_key_hash(api_key: str, salt: str) -> str:
    """S-01/S-05：PBKDF2-HMAC-SHA512 派生 API Key 哈希（256,000 次迭代）。"""
    derived = hashlib.pbkdf2_hmac(
        "sha512",
        api_key.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(derived).decode("ascii")


def verify_api_key(api_key: str, salt: str, stored_hash: str) -> bool:
    """启动时校验（S-01）：比对派生值与存储哈希，恒定时间比较。"""
    return secrets.compare_digest(derive_api_key_hash(api_key, salt), stored_hash)


def _restrict_file_permissions(path: Path) -> None:
    """设置文件权限 600（security-specification §2.1；POSIX 生效，Windows 尽力）。"""
    with contextlib.suppress(OSError):
        # Windows 上 chmod 语义受限，忽略（ACL 由用户环境管控）
        path.chmod(0o600)


def bootstrap_keys(dotenv_path: Path) -> str:
    """生成四密钥并写入 .env（幂等：已存在且含全部密钥时跳过生成）。

    返回明文 API Key（仅本次输出）。密钥族：
    - KAIROS_API_KEY      明文 Key（仅进程内存 / 本次输出，不落盘）
    - KAIROS_API_KEY_HASH PBKDF2 派生哈希（落盘 .env）
    - KAIROS_SALT         加盐值（S-05）
    - KAIROS_SECRET_KEY   AES-256-GCM 敏感字段加密 Key（32 字节 hex）
    - KAIROS_AUDIT_HMAC_KEY 审计链 HMAC Key（32 字节 hex，S-16）
    """
    existing: dict[str, str] = {}
    if dotenv_path.is_file():
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key.strip() in _ENV_KEYS:
                    existing[key.strip()] = value.strip()

    if all(k in existing for k in _ENV_KEYS):
        # 已初始化：不重复生成（幂等），返回占位说明
        return ""

    # 生成密钥族
    api_key = secrets.token_urlsafe(KEY_BYTES)  # 明文 Key，仅内存/输出
    salt = secrets.token_hex(SALT_BYTES)
    api_key_hash = derive_api_key_hash(api_key, salt)
    secret_key = secrets.token_hex(KEY_BYTES)
    audit_hmac_key = secrets.token_hex(KEY_BYTES)

    new_values = {
        "KAIROS_API_KEY_HASH": api_key_hash,
        "KAIROS_SALT": salt,
        "KAIROS_SECRET_KEY": secret_key,
        "KAIROS_AUDIT_HMAC_KEY": audit_hmac_key,
    }
    merged = {**existing, **new_values}
    lines = "\n".join(f"{k}={v}" for k, v in merged.items()) + "\n"
    dotenv_path.write_text(lines, encoding="utf-8")
    _restrict_file_permissions(dotenv_path)
    return api_key


def hmac_sha256_hex(key_hex: str, data: bytes) -> str:
    """HMAC-SHA256（审计链完整性签名，S-16；架构 §10.10）。"""
    import hmac

    key = bytes.fromhex(key_hex)
    return hmac.new(key, data, hashlib.sha256).hexdigest()
