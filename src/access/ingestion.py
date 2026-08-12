"""摄取验证门禁（架构 §7.3 捕获门控五层）。

捕获门控五层（子代理提取：需求描述为四类，架构原文为五层）：
  1. 琐碎文本过滤   — 预设 trivial 词表（区分 zh/en）→ 拒绝写入
  2. 上下文标记清理 — [Memory]/[SuperMemory] 等 AI 记忆上下文标记剥离 → 标记清除后进入下一层
  3. 秘密文本检测   — regex 匹配 api_key/token/secret/password/private_key 紧邻冒号+值 → 拒绝，S-07
  4. 维护提示过滤   — 匹配维护提示模式（review the conversation above / reply with ok）→ 拒绝
  5. 硬长度上限     — 超配置硬上限 → 拒绝（S-03 → 413）

拒绝操作写入事件总线（标记 capture_rejected + 原因）——事件总线 W4 接入后启用。
豁免条件（架构 §7.3）：临时契约记忆和显式用户高信用源可跳过验证环（竖切内
由调用方显式传入 skip_capture_gate 声明豁免原因）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.errors import ContentTooLongError, SecurityRedlineError

# 1. 琐碎文本词表（架构 §7.3：ok/yes/thanks/收到/明白/好的等 30+ 表达，区分 zh/en）
TRIVIAL_PHRASES_EN = {
    "ok",
    "okay",
    "yes",
    "yeah",
    "yep",
    "no",
    "nope",
    "thanks",
    "thank you",
    "thx",
    "fine",
    "good",
    "great",
    "sure",
    "got it",
    "understood",
    "i see",
    "hi",
    "hello",
    "hey",
    "bye",
    "goodbye",
    "lol",
    "haha",
    "nothing",
    "n/a",
    "done",
    "noted",
    "roger",
    "copy that",
    "sounds good",
    "no problem",
    "no worries",
    "will do",
    "gotcha",
}
TRIVIAL_PHRASES_ZH = {
    "好的",
    "好",
    "收到",
    "明白",
    "知道了",
    "了解",
    "可以",
    "嗯",
    "哦",
    "哦哦",
    "谢谢",
    "感谢",
    "再见",
    "拜拜",
    "哈哈",
    "嘻嘻",
    "没事",
    "没问题",
    "不错",
    "挺好",
    "行",
    "嗯嗯",
    "是的",
    "对",
    "不",
    "没有",
    "没啥",
    "随便",
    "再看看",
    "继续",
}
_TRIVIAL_ALL = TRIVIAL_PHRASES_EN | TRIVIAL_PHRASES_ZH

# 2. 上下文标记（架构 §7.3：[Memory]/[SuperMemory] 等 AI 记忆上下文标记）
_MEMORY_TAG_PATTERN = re.compile(
    r"\[(?:memory|supermemory|memories?|context|system message|instructions?)\]", re.IGNORECASE
)

# 3. 秘密文本检测（S-07）：敏感键名紧邻冒号 + 值
_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|token|secret|password|passwd|private[_-]?key|access[_-]?key|"
    r"client[_-]?secret|authorization|bearer)\s*[:=]\s*\S+"
)

# 4. 维护提示过滤（架构 §7.3：维护提示模式）
_MAINTENANCE_PATTERNS = (
    re.compile(r"review the conversation above", re.IGNORECASE),
    re.compile(r"reply with ok and nothing else", re.IGNORECASE),
    re.compile(r"summarize the conversation", re.IGNORECASE),
    re.compile(r"ignore (?:all )?(?:previous|prior) instructions", re.IGNORECASE),
)


@dataclass(frozen=True)
class CaptureVerdict:
    """捕获门控判定结果。"""

    accepted: bool
    reason: str | None = None  # 拒绝原因（拒绝写入事件总线标记 capture_rejected + reason）
    cleaned_content: str | None = None  # 上下文标记剥离后的内容（剥离后进入下一层）


class IngestionGate:
    """摄取验证门禁（捕获门控五层，顺序执行）。"""

    def __init__(
        self,
        min_length: int = 10,
        max_content_bytes: int = 65536,
        *,
        allow_skip: bool = True,
    ) -> None:
        # KAIROS_CAPTURE_MIN_LENGTH / KAIROS_INPUT_LIMIT_CONTENT_BYTES（configuration §6/§7）
        self.min_length = min_length
        self.max_content_bytes = max_content_bytes
        self.allow_skip = allow_skip

    # ------------------------------------------------------------------
    # 对外入口
    # ------------------------------------------------------------------

    def check(
        self,
        content: str,
        *,
        skip_reason: str | None = None,
        contract: str | None = None,
    ) -> CaptureVerdict:
        """执行捕获门控五层。

        skip_reason：豁免原因声明（架构 §7.3 豁免条件——临时契约记忆和显式
        用户高信用源；竖切内由调用方显式声明，未声明豁免原因不生效）。
        contract='temporary' 且声明豁免原因时跳过验证环（架构 §7.3 豁免条件）。
        """
        if skip_reason:
            if self.allow_skip and contract == "temporary":
                # 豁免：临时契约记忆可跳过验证环（需备注豁免原因）
                return CaptureVerdict(accepted=True, cleaned_content=content)
            if self.allow_skip and skip_reason.startswith("high_trust_source"):
                return CaptureVerdict(accepted=True, cleaned_content=content)
            # 声明了豁免原因但不满足豁免条件 → 视为无效豁免，继续常规检查
        return self._check_capture_gates(content)

    # ------------------------------------------------------------------
    # 捕获门控五层
    # ------------------------------------------------------------------

    def _check_capture_gates(self, content: str) -> CaptureVerdict:
        # 1. 琐碎文本过滤
        stripped = content.strip()
        if not stripped or stripped.lower() in _TRIVIAL_ALL:
            return CaptureVerdict(accepted=False, reason="trivial_content")

        # 2. 上下文标记清理（剥离后进入下一层）
        cleaned = _MEMORY_TAG_PATTERN.sub("", content).strip()

        # 3. 秘密文本检测（S-07 敏感信息自动打标 + 拒绝）
        if _SECRET_PATTERN.search(cleaned):
            raise SecurityRedlineError(
                "捕获门控拒绝：检测到疑似敏感信息（api key/token/password 等，S-07）",
                details={"gate": "secret_detection"},
            )

        # 4. 维护提示过滤
        for pattern in _MAINTENANCE_PATTERNS:
            if pattern.search(cleaned):
                return CaptureVerdict(accepted=False, reason="maintenance_prompt")

        # 5. 硬长度上限（S-03 → 413 ERR-INPUT-001）
        if len(cleaned.encode("utf-8")) > self.max_content_bytes:
            raise ContentTooLongError(
                f"内容超过 {self.max_content_bytes} 字节硬上限（S-03）",
                details={"gate": "length_limit", "max_bytes": self.max_content_bytes},
            )

        # 最小长度（KAIROS_CAPTURE_MIN_LENGTH；低于阈值的琐碎/噪声不捕获）
        if len(cleaned) < self.min_length:
            return CaptureVerdict(accepted=False, reason="below_min_length")

        return CaptureVerdict(accepted=True, cleaned_content=cleaned)
