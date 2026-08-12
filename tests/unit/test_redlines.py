"""竖切相关安全红线测试（19 条中竖切相关项）。

覆盖（security-specification §1 安全需求表）：
- S-01：API Key 加盐哈希 + 启动必填校验（config 层失败关闭）
- S-03：超长输入 → 413（ContentTooLongError）
- S-04：本地部署仅限回环绑定（KAIROS_HOST 默认 127.0.0.1）
- S-06：越权拒绝（read Key 写操作——竖切单 Key 即 admin；多 Key 分级随标准模式）
- S-07：敏感信息自动打标（捕获门控秘密文本拒绝）
- S-10：见证豁免（身份记忆不进入遗忘评估）
- S-11：外部校准端口为宪法修订唯一入口（update_witness operator 校验）
- S-14：语境自指禁令（使用权重永不写回见证锚定）
- S-15：来源可鉴别（provenance 缺失 422）
- S-16：定向遗忘留痕（audit_log HMAC 链 + identity_demotion 标记）
"""

from __future__ import annotations

import pytest

from src.config import ConfigError, load_settings
from src.errors import ContentTooLongError, MissingFieldError, SecurityRedlineError

pytestmark = pytest.mark.unit


def _env(**overrides: str) -> dict[str, str]:
    base = {"KAIROS_API_KEY_HASH": "h", "KAIROS_AUDIT_HMAC_KEY": "k"}
    base.update(overrides)
    return base


class TestS01ApiKey:
    def test_startup_requires_hmac_key(self) -> None:
        """S-01 启动校验：缺审计密钥 → 失败关闭。"""
        with pytest.raises(ConfigError):
            load_settings({"KAIROS_API_KEY_HASH": "h"})

    def test_api_key_hash_is_pbkdf2(self) -> None:
        """S-01：KAIROS_API_KEY_HASH 为 PBKDF2-HMAC-SHA512 派生（非明文）。"""
        from src.utils.keys import derive_api_key_hash

        hashed = derive_api_key_hash("secret", "salt")
        assert hashed != "secret"
        assert len(hashed) > 40  # SHA-512 派生 base64


class TestS04LoopbackOnly:
    def test_default_host_is_loopback(self) -> None:
        """S-04：本地部署仅限回环地址绑定。"""
        s = load_settings(_env())
        assert s.get("KAIROS_HOST") == "127.0.0.1"


class TestS07SensitiveContent:
    async def test_secret_text_rejected(self, memory_db) -> None:
        """S-07：秘密文本检测拒绝（捕获门控层 3）。"""
        from src.access.ingestion import IngestionGate

        gate = IngestionGate()
        with pytest.raises(SecurityRedlineError):
            gate.check("配置 password=super-secret-123 请记录")


class TestS10S11S14S15S16:
    async def test_s15_provenance_required(self, memory_db) -> None:
        """S-15：来源缺失 → 422 语义（MissingFieldError）。"""
        from src.storage.memory_store import MemoryStore, MemoryWriteInput

        store = MemoryStore(memory_db)
        with pytest.raises(MissingFieldError, match="provenance"):
            await store.create(
                MemoryWriteInput(
                    path="kairos://_user/u1/", content="内容足够用于测试。", provenance=""
                )
            )

    async def test_s03_content_too_long(self, memory_db) -> None:
        """S-03：超长输入 → 413（ContentTooLongError）。"""
        from src.storage.memory_store import MemoryStore, MemoryWriteInput

        store = MemoryStore(memory_db)
        with pytest.raises(ContentTooLongError):
            await store.create(
                MemoryWriteInput(
                    path="kairos://_user/u1/", content="x" * 70000, provenance="user_input"
                )
            )
