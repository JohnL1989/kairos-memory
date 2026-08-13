"""S-09 常驻契约注入扫描（security-specification §1：prompt injection / 角色劫持 /
后门 / 隐形 Unicode）。

权威规格：security-specification S-09（L+P 红线，design-freeze）——
「常驻契约写入前注入扫描」，验证方法「含注入 payload 写入 → 拒绝」。

检测面：
1. 隐形 Unicode 控制字符（零宽字符 / RTL 覆盖 / bidi isolates / BOM）——
   S-09 明确列出的载体，常用于注入文本中隐藏指令或绕过展示层审查
2. 角色劫持 / 后门指令（中英双语高置信完整短语）——「你现在是系统」、
   "you are now"、"reveal your system prompt" 等，命中即判定注入意图

误报控制：仅匹配**完整短语**（不匹配子串），模式库保持克制——正常
记忆内容（如用户讨论「prompt injection 攻击」本身）不触发；命中返回
原因列表供审计留痕。

插入点：IngestionGate._check_capture_gates 第 6 层（ingestion.py），
与 S-07 秘密文本检测同级；豁免路径（temporary 契约 / 高信用源）与
既有门控语义一致——常驻契约（S-09 对象）不豁免、必然过扫描。
"""

from __future__ import annotations

import re

# 隐形 Unicode 控制字符（S-09 明确列出的注入载体）：
#   U+200B/200C/200D 零宽空格/连接符/断字符；U+2066~2069 bidi isolates；
#   U+202D/202E 左右覆盖；U+FEFF 零宽不换行空格（BOM）
_INVISIBLE_UNICODE_RE = re.compile(r"[\u200b-\u200d\u2066-\u2069\u202d\u202e\ufeff]")

# 角色劫持 / 后门指令（高置信完整短语；仅匹配短语级，不做子串误报）
_INJECTION_PHRASES: tuple[re.Pattern[str], ...] = (
    # 英文：角色重写
    re.compile(r"\byou are now (?:a |the )?(?:system|assistant|gpt|ai)", re.IGNORECASE),
    re.compile(r"\byou (?:have been|are) replaced", re.IGNORECASE),
    re.compile(r"\byou are not (?:an |the )?ai", re.IGNORECASE),
    re.compile(r"\bact as (?:a |the )?system", re.IGNORECASE),
    # 英文：指令泄露
    re.compile(
        r"\b(?:print|reveal|show|output|display) "
        r"(?:your|the|my) (?:system|original|hidden) (?:prompt|instructions)",
        re.IGNORECASE,
    ),
    re.compile(r"\bshow (?:your|the) instructions", re.IGNORECASE),
    re.compile(r"\brepeat (?:everything|all|the prompt) above", re.IGNORECASE),
    re.compile(
        r"\bignore (?:all )?(?:previous|prior|earlier) "
        r"(?:instructions|prompts|messages) (?:and|and follow) (?:only|just)",
        re.IGNORECASE,
    ),
    # 中文：角色重写
    re.compile(r"(?:现在|此刻)你(?:已经)?(?:是|成为)(?:一个)?(?:系统|助手|AI|机器人)"),
    re.compile(r"(?:你被|已)替换(?:成|为)"),
    re.compile(r"你不是(?:一个)?(?:AI|人工智能|助手)"),
    re.compile(r"你(?:现在)?扮演(?:一个)?(?:系统|管理员|上帝)"),
    # 中文：指令泄露
    re.compile(
        r"(?:输出|打印|显示|泄露|透露)(?:你的|系统的|隐藏的)(?:系统提示|指令|提示词|prompt)"
    ),
    re.compile(r"(?:重复|复述)(?:上面|以上)(?:所有|全部)?(?:内容|指令|提示)"),
)


def scan_injection(content: str) -> list[str]:
    """扫描内容中的注入载体，返回命中原因列表（空列表 = 通过）。

    命中任一检测面即返回对应原因（供 S-16 审计留痕 / 错误 details）。
    """
    hits: list[str] = []
    if _INVISIBLE_UNICODE_RE.search(content):
        hits.append("invisible_unicode")
    for pattern in _INJECTION_PHRASES:
        if pattern.search(content):
            hits.append("injection_phrase")
            break  # 同一内容命中短语类仅记一次
    return hits
