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

    KAIROS_API_KEY_HASH 未配置时守卫放行——development 模式（KAIROS_ENV
    默认）的开发便利，启动时 config 已以警告日志显式声明无鉴权状态；
    production 模式（KAIROS_ENV=production）由 config 启动校验强制密钥族
    必填（S-01「无 API Key 拒绝启动」），未配置即拒绝启动、守卫不可达。

    salt/api_key_hash 于构造时注入（build_app 已加载配置），守卫调用期
    不再重读 .env——避免每请求 load_settings() 的 I/O 与解析开销。
    """

    def __init__(self, api_key_hash: str | None, salt: str = "") -> None:
        self.api_key_hash = api_key_hash
        self.salt = salt

    async def __call__(
        self, connection: ASGIConnection[Any, Any, Any, Any], _handler: BaseRouteHandler
    ) -> None:
        if not self.api_key_hash:
            return  # development 未配置密钥：守卫放行（S-01 生产强制在 config 层）
        auth = connection.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            raise AuthError("缺少 Authorization: Bearer <key> 请求头（S-01 运行时 401）")
        key = auth[len("Bearer ") :].strip()
        from src.utils.keys import verify_api_key

        if not verify_api_key(key, self.salt, self.api_key_hash):
            raise AuthError("API Key 无效（ERR-AUTH-001）")
