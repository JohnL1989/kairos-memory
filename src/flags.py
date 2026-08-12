"""特征标志与命名配置集（架构 §0.8）。

命名配置集（三种合法组合）：
- kairos-minimal：最小系统（无遗忘引擎）
- kairos-slice：竖切形态——MULTI_SIGNAL_SEARCH ON + NARRATIVE_IDENTITY ON
  + FORGETTING_ENGINE ON，其余 OFF（本仓库当前装配形态）
- kairos-full：全量形态（规划）

启动校验（架构 §0.8）：
- 标志组合不匹配任何命名配置集 → 拒绝启动，输出 invalid_flag_composition 审计事件
- 宪法核不可禁用（NARRATIVE_IDENTITY 必须 ON；关闭触发
  constitutional_core_unavailable 拒绝启动）
- 标志总数硬上限 24
- 启动输出 flags: ON/OFF, count: N/M

核心假设绑定（程序化证伪）：
- H1 ↔ FULL_VALUE_METRICS（竖切内 OFF，不适用）
- H2 ↔ FORGETTING_ENGINE（竖切内 ON）
- H3 ↔ NARRATIVE_IDENTITY（宪法核，部署须 ON；证伪失败走 fail-closed
  containment，不得关闭标志）

实现口径注记（ENTITY_GRAPH）：竖切组件 3 按三信号实现（含实体加成
0.15，entities/memory_entities 表在竖切 schema 清单）——竖切内
ENTITY_GRAPH 视为 ON（configuration 的 OFF 降级 0.60/0.40 双信号口径
适用于竖切外形态）。
"""

from __future__ import annotations

from dataclasses import dataclass

# 标志枚举（configuration §0.8 登记族）
FLAG_MULTI_SIGNAL_SEARCH = "KAIROS_FEATURE_MULTI_SIGNAL_SEARCH"
FLAG_FULL_VALUE_METRICS = "KAIROS_FEATURE_FULL_VALUE_METRICS"
FLAG_FORGETTING_ENGINE = "KAIROS_FEATURE_FORGETTING_ENGINE"
FLAG_NARRATIVE_IDENTITY = "KAIROS_FEATURE_NARRATIVE_IDENTITY"
FLAG_META_COGNITION = "KAIROS_FEATURE_META_COGNITION"
FLAG_CONSTITUTIONAL_GOVERNANCE = "KAIROS_FEATURE_CONSTITUTIONAL_GOVERNANCE"
FLAG_WM_PREPROCESSOR = "KAIROS_FEATURE_WM_PREPROCESSOR"
FLAG_ATTENTION_SCHEDULER = "KAIROS_FEATURE_ATTENTION_SCHEDULER"
FLAG_SUBLIMATION_PIPELINE = "KAIROS_FEATURE_SUBLIMATION_PIPELINE"
FLAG_GSPO_DEDUP = "KAIROS_FEATURE_GSPO_DEDUP"
FLAG_ENTITY_GRAPH = "KAIROS_FEATURE_ENTITY_GRAPH"
FLAG_CONNECTORS = "KAIROS_FEATURE_CONNECTORS"

ALL_FLAGS: tuple[str, ...] = (
    FLAG_MULTI_SIGNAL_SEARCH,
    FLAG_FULL_VALUE_METRICS,
    FLAG_FORGETTING_ENGINE,
    FLAG_NARRATIVE_IDENTITY,
    FLAG_META_COGNITION,
    FLAG_CONSTITUTIONAL_GOVERNANCE,
    FLAG_WM_PREPROCESSOR,
    FLAG_ATTENTION_SCHEDULER,
    FLAG_SUBLIMATION_PIPELINE,
    FLAG_GSPO_DEDUP,
    FLAG_ENTITY_GRAPH,
    FLAG_CONNECTORS,
)

# 竖切外标志（未在竖切参数族登记——配置校验时视为默认 OFF 不参与组合判定）
# 竖切装配只显式声明竖切相关标志，其余按 configuration 默认（OFF）

# 命名配置集（架构 §0.8；竖切装配 kairos-slice）
COMPOSITION_MINIMAL: dict[str, bool] = {
    FLAG_MULTI_SIGNAL_SEARCH: True,
    FLAG_NARRATIVE_IDENTITY: True,
    FLAG_FORGETTING_ENGINE: False,
}
COMPOSITION_SLICE: dict[str, bool] = {
    FLAG_MULTI_SIGNAL_SEARCH: True,
    FLAG_NARRATIVE_IDENTITY: True,
    FLAG_FORGETTING_ENGINE: True,
    # 竖切口径：实体加成三信号落地（slice-guide 组件 3）
    FLAG_ENTITY_GRAPH: True,
}
COMPOSITION_FULL: dict[str, bool] = {
    FLAG_MULTI_SIGNAL_SEARCH: True,
    FLAG_NARRATIVE_IDENTITY: True,
    FLAG_FORGETTING_ENGINE: True,
    FLAG_FULL_VALUE_METRICS: True,
    FLAG_META_COGNITION: True,
    FLAG_CONSTITUTIONAL_GOVERNANCE: True,
    FLAG_WM_PREPROCESSOR: True,
    FLAG_ATTENTION_SCHEDULER: True,
    FLAG_SUBLIMATION_PIPELINE: True,
    FLAG_GSPO_DEDUP: True,
    FLAG_ENTITY_GRAPH: True,
    FLAG_CONNECTORS: True,
}

NAMED_COMPOSITIONS: dict[str, dict[str, bool]] = {
    "kairos-minimal": COMPOSITION_MINIMAL,
    "kairos-slice": COMPOSITION_SLICE,
    "kairos-full": COMPOSITION_FULL,
}

# 宪法核不可禁用清单（架构 §0.8：装配后不可用 → 拒绝启动）
CONSTITUTIONAL_CORE_FLAGS: tuple[str, ...] = (FLAG_NARRATIVE_IDENTITY,)

# 核心假设绑定（H2/H3 竖切内生效；H1 竖切内 OFF 不适用）
HYPOTHESIS_FLAGS: dict[str, str] = {
    "H1": FLAG_FULL_VALUE_METRICS,
    "H2": FLAG_FORGETTING_ENGINE,
    "H3": FLAG_NARRATIVE_IDENTITY,
}

# 标志总数硬上限（架构 §0.8）
MAX_FLAG_COUNT = 24


@dataclass(frozen=True)
class FlagValidation:
    """启动校验结果。"""

    ok: bool
    composition: str | None  # 匹配的命名配置集
    reason: str | None = None


def validate_composition(flag_values: dict[str, bool]) -> FlagValidation:
    """配置集组合校验（架构 §0.8）。

    - 宪法核校验优先：NARRATIVE_IDENTITY 必须 ON（拒绝启动，不落入组合判定）
    - 标志组合与命名配置集匹配校验：不匹配 → 拒绝启动（invalid_flag_composition）
    """
    # 宪法核不可禁用
    for flag in CONSTITUTIONAL_CORE_FLAGS:
        if flag_values.get(flag, True) is False:
            return FlagValidation(
                False, None, f"constitutional_core_unavailable: {flag} 为宪法核，不得关闭"
            )
    # 命名配置集匹配
    for name, composition in NAMED_COMPOSITIONS.items():
        if all(flag_values.get(k, False) == v for k, v in composition.items()):
            return FlagValidation(True, name)
    # 显式声明的标志（非默认 OFF）与任一配置集不符
    return FlagValidation(False, None, "invalid_flag_composition: 标志组合不匹配任何命名配置集")


def flag_count_report(flag_values: dict[str, bool]) -> str:
    """启动输出：flags: ON/OFF, count: N/M（架构 §0.8）。"""
    on = [k for k, v in flag_values.items() if v]
    off = [k for k, v in flag_values.items() if not v]
    return f"flags: ON=[{','.join(on)}] OFF=[{','.join(off)}] count: {len(on)}/{len(off)}"


def build_slice_flag_values() -> dict[str, bool]:
    """竖切装配的标志值（kairos-slice 配置集；竖切外标志默认 OFF）。"""
    values = {flag: False for flag in ALL_FLAGS}
    values.update(COMPOSITION_SLICE)
    return values
