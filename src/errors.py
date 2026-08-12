"""Kairos 错误码与异常类型。

权威来源：docs/references/error-reference.md（全量内部错误码）+ api-spec §7（HTTP 级子集）。
本模块仅承载竖切端点消费的错误码；状态码按红线类型分派
（coding-conventions §三：S-01 启动拒绝 / S-02→429 / S-03→413 / S-15→422 /
S-06·S-08→403 / 其余→403 ERR-SEC-001）。
"""

from __future__ import annotations

from typing import Any


class KairosError(Exception):
    """业务错误基类：携带 HTTP 状态码与错误码。"""

    status_code: int = 500
    code: str = "ERR-SYS-001"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        body: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            body["details"] = self.details
        return body


# --- 认证（ERR-AUTH-*） ---
class AuthError(KairosError):
    status_code = 401
    code = "ERR-AUTH-001"


class AdminRequiredError(KairosError):
    status_code = 403
    code = "ERR-AUTH-004"


# --- 输入校验（ERR-INPUT-*） ---
class ContentTooLongError(KairosError):
    """S-03 超长输入 → 413（ERR-INPUT-001，64KB 上限）。"""

    status_code = 413
    code = "ERR-INPUT-001"


class InvalidPathError(KairosError):
    """ERR-INPUT-002：路径非 kairos:// 开头。"""

    status_code = 400
    code = "ERR-INPUT-002"


class PathDepthError(KairosError):
    """ERR-INPUT-003：路径深度超限（>10 层）。"""

    status_code = 422
    code = "ERR-INPUT-003"


class MissingFieldError(KairosError):
    """ERR-INPUT-004：缺少必填字段（content/path）。S-15 来源缺失亦由此承载（422）。"""

    status_code = 422
    code = "ERR-INPUT-004"


# --- 存储（ERR-DB-*） ---
class NotFoundError(KairosError):
    """ERR-DB-004：资源不存在（404，API 返回码）。"""

    status_code = 404
    code = "ERR-DB-004"


class VersionConflictError(KairosError):
    """ERR-DB-005：版本冲突（409，If-Match 与当前版本不一致，乐观锁裁决）。"""

    status_code = 409
    code = "ERR-DB-005"


# --- 安全红线（ERR-SEC-001） ---
class SecurityRedlineError(KairosError):
    """S 级红线违反（403）；细节写入审计日志。"""

    status_code = 403
    code = "ERR-SEC-001"


# --- 契约与状态（ERR-CTR-*） ---
class LockedMemoryError(KairosError):
    """ERR-CTR-003：记忆已锁定（locked_until 未到期）。"""

    status_code = 403
    code = "ERR-CTR-003"


class IntentionNotClosedError(KairosError):
    """ERR-CTR-004：intention 契约未关闭（拒绝直接删除）。"""

    status_code = 409
    code = "ERR-CTR-004"


class IdempotencyConflictError(KairosError):
    """ERR-CTR-005：幂等键冲突（同键重复提交且载荷不一致，409）。"""

    status_code = 409
    code = "ERR-CTR-005"
