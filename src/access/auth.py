"""API Key 鉴权（竖切轻量模式单 Key，S-01/S-06）。

权威规格：security-specification §2.1（KAIROS_API_KEY_HASH 单 Key 环境变量，
文件权限 600；S-01 无 Key 拒绝启动/缺 Key 401；S-06 越权拒绝）。
竖切内单 Key 即 admin 权限（write/read 分级随标准模式多 Key 引入）。

S-01 三层响应：启动缺 Key → 连接拒绝（config 启动校验，非 HTTP）；
运行时缺 Token → 401（ERR-AUTH-001）；红线违反 → 403（ERR-SEC-001）。
"""

from __future__ import annotations

from typing import Any

from litestar.connection import ASGIConnection
from litestar.handlers import BaseRouteHandler

from src.errors import AuthError


class ApiKeyGuard:
    """API Key 鉴权守卫（Bearer token 与 KAIROS_API_KEY_HASH 比对）。

    KAIROS_API_KEY_HASH 未配置时（本地开发未初始化密钥）守卫放行——
    开发便利；生产部署 S-01 启动校验强制。启动级校验见 config.load_settings。
    """

    def __init__(self, api_key_hash: str | None) -> None:
        self.api_key_hash = api_key_hash

    async def __call__(
        self, connection: ASGIConnection[Any, Any, Any, Any], _handler: BaseRouteHandler
    ) -> None:
        if not self.api_key_hash:
            return  # 未配置密钥：本地开发放行（S-01 启动级校验在配置层）
        auth = connection.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            raise AuthError("缺少 Authorization: Bearer <key> 请求头（S-01 运行时 401）")
        key = auth[len("Bearer ") :].strip()
        from src.config import load_settings

        settings = load_settings()
        salt = settings.get("KAIROS_SALT") or ""
        from src.utils.keys import verify_api_key

        if not verify_api_key(key, salt, self.api_key_hash):
            raise AuthError("API Key 无效（ERR-AUTH-001）")
