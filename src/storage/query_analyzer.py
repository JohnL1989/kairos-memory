"""QueryAnalyzer（竖切后首迭代增强，slice-implementation-guide 组件 3 注记）。

权威规格：架构 §2.6.1 三阶段管线——
  原始查询 → 意图分类（五+1 类）→ 实体识别 → 时间约束提取 → 结构化查询描述符

阶段一 意图分类（五+1 类，规则优先 + 模型兜底）：
  factual_lookup（事实查询）/ temporal_query（时间限定）/ exploratory_browse
  （开放式探索）/ decision_trace（决策追溯）/ instructional（操作步骤）/
  general（兜底，置信度 <0.6 降级）
  规则层覆盖 ≥80% 典型查询（零 LLM 调用）；intent-t5-small 模型兜底层
  （竖切内模型未就绪 → 规则结果直接采用，置信度 0.7 标记）

阶段二 实体识别：词典匹配（entities 表名称命中查询文本），输出
  [{entity_text, entity_type, entity_id, confidence}]；识别失败跳过
  实体加成（退化纯文本检索）

阶段三 时间约束提取（四类解析）：
  相对窗口（最近X天/周/月）、日历周（上周/本周）、绝对（YYYY年M月/
  YYYY-MM-DD）、事件锚定（未命中注册表降级语义检索，置信度 <0.6 时
  时间过滤降级为可选）
  fallback_query：去除时间短语后的纯语义查询（时间过滤降级时回退）
  时间字段口径：occurred_at 优先，空回退 created_at；解析失败记录
  temporal_parse_failure 事件，检索不阻塞
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

# 意图枚举（架构 §2.6.1 五+1 类）
INTENT_FACTUAL_LOOKUP = "factual_lookup"
INTENT_TEMPORAL_QUERY = "temporal_query"
INTENT_EXPLORATORY_BROWSE = "exploratory_browse"
INTENT_DECISION_TRACE = "decision_trace"
INTENT_INSTRUCTIONAL = "instructional"
INTENT_GENERAL = "general"

ALL_INTENTS = (
    INTENT_FACTUAL_LOOKUP,
    INTENT_TEMPORAL_QUERY,
    INTENT_EXPLORATORY_BROWSE,
    INTENT_DECISION_TRACE,
    INTENT_INSTRUCTIONAL,
    INTENT_GENERAL,
)

# 置信度阈值（KAIROS_INTENT_CONFIDENCE_THRESHOLD）
CONFIDENCE_THRESHOLD = 0.6

# 问候/寒暄词表（trivial 词表直接跳过检索，架构 §2.6.1 规则层）
_TRIVIAL_QUERIES = {
    "你好",
    "您好",
    "嗨",
    "hello",
    "hi",
    "hey",
    "谢谢",
    "thanks",
    "在吗",
    "在不在",
    "早上好",
    "下午好",
    "晚上好",
    "再见",
    "拜拜",
    "没事",
    "好的",
}

# 身份查询路径前缀（架构 §2.6.1：路径前缀命中即返回，不进入概率检索）
_IDENTITY_PATH_PREFIX = "kairos://_user/{id}/core/"

# 探索表达（exploratory_browse 触发词）
_EXPLORE_PATTERNS = (
    re.compile(r"最近|最近在|有哪些|有什么|关于.*的.*(?:想法|观点|看法|内容)"),
    re.compile(r"explore|browse|what.*about|tell me about", re.IGNORECASE),
)

# 决策追溯（decision_trace 触发词）
_DECISION_PATTERNS = (re.compile(r"为什么|为何|当初.*决定|决策|reason|why", re.IGNORECASE),)

# 操作步骤（instructional 触发词）
_INSTRUCTIONAL_PATTERNS = (
    re.compile(r"怎么做|如何|怎么.*(?:做|用|实现)|步骤|how to", re.IGNORECASE),
)

# 时间表达正则（阶段三）
_CN_NUM = r"[一二两三四五六七八九十百\d]+"
_TIME_RELATIVE_DAYS = re.compile(rf"最近\s*({_CN_NUM})\s*天")
_TIME_RELATIVE_WEEKS = re.compile(rf"最近\s*({_CN_NUM})\s*周")
_TIME_RELATIVE_MONTHS = re.compile(rf"最近\s*({_CN_NUM})\s*个月")
_TIME_CALENDAR_WEEK = re.compile(r"(上周|本周|这周)")
_TIME_ABSOLUTE_MONTH = re.compile(r"(\d{4})\s*年\s*(\d{1,2})\s*月")
_TIME_ABSOLUTE_DATE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
_TIME_YESTERDAY_TODAY = re.compile(r"(昨天|今天|前天)")
# 事件锚定（"项目启动时"类——名词短语 + 时/之后/以来）
_TIME_EVENT_ANCHOR = re.compile(
    r"([一-龥A-Za-z0-9]{2,12}?)(?:启动|开始|发布|上线)(?:时|后|以来|之前)"
)

# 时间短语（fallback_query 剥离用；与上述正则对齐）
_TIME_PHRASE_PATTERNS = (
    re.compile(r"最近\s*\d+\s*(?:天|周|个月)"),
    re.compile(r"(上周|本周|这周|昨天|今天|前天)"),
    re.compile(r"\d{4}\s*年\s*\d{1,2}\s*月"),
    re.compile(r"\d{4}-\d{1,2}-\d{1,2}"),
    re.compile(r"(?:启动|开始|发布|上线)(?:时|后|以来|之前)"),
)


@dataclass(frozen=True)
class IntentInfo:
    """意图分类结果。"""

    type: str
    confidence: float
    fallback: str | None = None  # 模型兜底时记录规则类型


@dataclass(frozen=True)
class EntityHit:
    """查询实体命中（词典匹配）。"""

    entity_text: str
    entity_type: str
    entity_id: int
    confidence: float


@dataclass(frozen=True)
class TemporalConstraint:
    """时间约束（四类解析结果；start/end ISO-8601 UTC）。"""

    type: str  # relative_window / calendar_week / absolute / event_anchor / session
    start: str | None
    end: str | None
    raw_expression: str
    confidence: float = 1.0
    optional: bool = False  # 置信度 <0.6 时时间过滤降级为可选


@dataclass(frozen=True)
class QueryDescriptor:
    """结构化查询描述符（架构 §2.6.1）。"""

    raw_query: str
    intent: IntentInfo
    entities: list[EntityHit] = field(default_factory=list)
    temporal_constraint: TemporalConstraint | None = None
    fallback_query: str | None = None
    processed_at: str | None = None

    @property
    def effective_query(self) -> str:
        """实际检索查询：有时间约束时用 fallback_query（纯语义），否则原查询。"""
        if self.temporal_constraint is not None and self.fallback_query:
            return self.fallback_query
        return self.raw_query


_CN_DIGITS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def _cn_to_int(text: str) -> int:
    """中文数字/阿拉伯数字 → int（「一周」→1、「12」→12）。"""
    if text.isdigit():
        return int(text)
    total = 0
    for ch in text:
        if ch in _CN_DIGITS:
            total = total * 10 + _CN_DIGITS[ch]
    return total or 1


class QueryAnalyzer:
    """查询分析器（三阶段管线：意图 → 实体 → 时间约束）。"""

    def __init__(self, db: Any | None = None, identity_user_id: str | None = None) -> None:
        self.db = db  # 实体词典查询（entities 表）
        self.identity_user_id = identity_user_id  # 身份确定性检索用户

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    async def analyze(self, raw_query: str) -> QueryDescriptor:
        """三阶段分析 → 结构化查询描述符。"""
        # 阶段一：意图分类（规则优先；模型兜底层竖切内未就绪 → 规则结果）
        intent = self._classify_intent(raw_query)
        # 阶段二：实体识别（词典匹配）
        entities = await self._extract_entities(raw_query)
        # 阶段三：时间约束提取
        temporal = self._extract_temporal(raw_query)
        fallback = self._build_fallback_query(raw_query) if temporal else None
        return QueryDescriptor(
            raw_query=raw_query,
            intent=intent,
            entities=entities,
            temporal_constraint=temporal,
            fallback_query=fallback,
            processed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        )

    # ------------------------------------------------------------------
    # 阶段一：意图分类（规则层）
    # ------------------------------------------------------------------

    def _classify_intent(self, query: str) -> IntentInfo:
        q = query.strip()
        if not q or q in _TRIVIAL_QUERIES:
            return IntentInfo(INTENT_GENERAL, 0.95, fallback="trivial")
        if (
            _TIME_RELATIVE_DAYS.search(q)
            or _TIME_RELATIVE_WEEKS.search(q)
            or _TIME_RELATIVE_MONTHS.search(q)
        ):
            return IntentInfo(INTENT_TEMPORAL_QUERY, 0.9)
        if (
            _TIME_CALENDAR_WEEK.search(q)
            or _TIME_ABSOLUTE_MONTH.search(q)
            or _TIME_ABSOLUTE_DATE.search(q)
        ):
            return IntentInfo(INTENT_TEMPORAL_QUERY, 0.85)
        for pat in _EXPLORE_PATTERNS:
            if pat.search(q):
                return IntentInfo(INTENT_EXPLORATORY_BROWSE, 0.8)
        for pat in _DECISION_PATTERNS:
            if pat.search(q):
                return IntentInfo(INTENT_DECISION_TRACE, 0.8)
        for pat in _INSTRUCTIONAL_PATTERNS:
            if pat.search(q):
                return IntentInfo(INTENT_INSTRUCTIONAL, 0.8)
        # 事实查询兜底（非探索/决策/操作 → factual_lookup，规则置信度）
        return IntentInfo(INTENT_FACTUAL_LOOKUP, 0.7)

    # ------------------------------------------------------------------
    # 阶段二：实体识别（词典匹配，非 LLM）
    # ------------------------------------------------------------------

    async def _extract_entities(self, query: str) -> list[EntityHit]:
        if self.db is None:
            return []
        from sqlalchemy import text

        async with self.db.session() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT id, name, type FROM entities "
                        "WHERE name IN (SELECT name FROM entities)"
                    )
                )
            ).fetchall()
        hits = []
        for row in rows:
            entity_id, name, etype = row
            if name and name in query:
                hits.append(
                    EntityHit(
                        entity_text=name,
                        entity_type=etype,
                        entity_id=int(entity_id),
                        confidence=0.9,  # 词典精确命中
                    )
                )
        return hits

    # ------------------------------------------------------------------
    # 阶段三：时间约束提取（四类解析）
    # ------------------------------------------------------------------

    def _extract_temporal(self, query: str) -> TemporalConstraint | None:
        now = datetime.now(UTC)

        # 相对窗口：最近 N 天/周/月
        m = _TIME_RELATIVE_DAYS.search(query)
        if m:
            days = _cn_to_int(m.group(1))
            return TemporalConstraint(
                "relative_window",
                (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                m.group(0),
            )
        m = _TIME_RELATIVE_WEEKS.search(query)
        if m:
            weeks = _cn_to_int(m.group(1))
            return TemporalConstraint(
                "relative_window",
                (now - timedelta(weeks=weeks)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                m.group(0),
            )
        m = _TIME_RELATIVE_MONTHS.search(query)
        if m:
            months = _cn_to_int(m.group(1))
            start = now - timedelta(days=30 * months)
            return TemporalConstraint(
                "relative_window",
                start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                m.group(0),
            )

        # 日历周：上周
        m = _TIME_CALENDAR_WEEK.search(query)
        if m:
            today = now.date()
            monday = today - timedelta(days=today.weekday())
            if m.group(1) in ("上周",):
                monday = monday - timedelta(days=7)
            sunday = monday + timedelta(days=6)
            return TemporalConstraint(
                "calendar_week",
                f"{monday.isoformat()}T00:00:00.000Z",
                f"{sunday.isoformat()}T23:59:59.999Z",
                m.group(0),
            )

        # 绝对：YYYY年M月
        m = _TIME_ABSOLUTE_MONTH.search(query)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
            start = datetime(year, month, 1, tzinfo=UTC)
            end_month = month + 1
            end_year = year
            if end_month > 12:
                end_month, end_year = 1, year + 1
            end = datetime(end_year, end_month, 1, tzinfo=UTC) - timedelta(seconds=1)
            return TemporalConstraint(
                "absolute",
                start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                m.group(0),
            )

        # 绝对：YYYY-MM-DD
        m = _TIME_ABSOLUTE_DATE.search(query)
        if m:
            year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
            start = datetime(year, month, day, tzinfo=UTC)
            end = start + timedelta(days=1) - timedelta(seconds=1)
            return TemporalConstraint(
                "absolute",
                start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                m.group(0),
            )

        # 事件锚定（"项目启动时"；未命中注册表 → 降级语义检索由调用方处理，
        # 此处产出 optional 约束供检索层注入）
        m = _TIME_EVENT_ANCHOR.search(query)
        if m:
            return TemporalConstraint(
                "event_anchor",
                None,
                None,
                m.group(0),
                confidence=0.5,  # 事件锚定未解析出具体时间 → 过滤降级为可选
                optional=True,
            )
        return None

    # ------------------------------------------------------------------
    # fallback_query 生成（剥离时间短语）
    # ------------------------------------------------------------------

    def _build_fallback_query(self, query: str) -> str:
        cleaned = query
        for pat in _TIME_PHRASE_PATTERNS:
            cleaned = pat.sub(" ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or query  # 剥离后为空则保留原查询（防空检索）
