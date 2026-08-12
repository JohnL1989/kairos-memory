"""Kairos 配置加载（竖切子集）。

权威来源：docs/ops/configuration.md（全量 227 项正文参数 + 附录 A 147 项）。
本模块仅承载竖切（v0.1.0-slice）消费的参数子集；参数名、默认值、取值范围
均以 configuration.md 为唯一事实源，本模块不自行发明参数。

加载顺序（configuration.md §1）：
    环境变量（KAIROS_*） > .env 文件 > 内置默认值
运行时动态配置（config 表 scope=dynamic/override）在 storage 层接入后
叠加覆盖（W3 起）。

启动校验（S-01 失败关闭）：
    - KAIROS_AUDIT_HMAC_KEY 必填（无默认值，审计链 HMAC 密钥）
    - KAIROS_NARRATIVE_AUDIT_CYCLE_MAX > 12 拒绝启动（架构 §8 风险警告）
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 常量与参数定义
# ---------------------------------------------------------------------------

_ENV_PREFIX = "KAIROS_"

# 各参数定义：(环境变量名, 默认值, 类型, 取值范围/说明)
# 来源：configuration.md 对应章节（检索 §6.1 / 摄入 §6 / 遗忘 §10 / 身份 §0.10 /
#       降级 §4 / 安全 §2.1 / FTS5 附录 A）
_PARAM_SPECS: dict[str, tuple[Any, type, str]] = {
    # 存储
    "KAIROS_DB_URL": ("sqlite:///$HOME/.kairos/kairos.db", str, "数据库连接串（轻量模式 SQLite）"),
    # 检索（configuration §6.1 三信号混合检索）
    "KAIROS_HYBRID_SEMANTIC_WEIGHT": (0.50, float, "语义信号权重（α_s）"),
    "KAIROS_HYBRID_BM25_WEIGHT": (0.35, float, "BM25 信号权重（α_b）"),
    "KAIROS_HYBRID_ENTITY_WEIGHT": (0.15, float, "实体加成权重（α_e）"),
    "KAIROS_HYBRID_CANDIDATE_POOL_SIZE": (100, int, "语义检索召回候选池大小"),
    # 摄取验证门禁（configuration §6/§7）
    "KAIROS_CAPTURE_MIN_LENGTH": (10, int, "捕获最小内容长度"),
    "KAIROS_INPUT_LIMIT_CONTENT_BYTES": (65536, int, "content 字段最大长度（字节）"),
    "KAIROS_INPUT_LIMIT_QUERY_CHARS": (500, int, "query 字段最大字符数"),
    # 遗忘（configuration §10；freshness 单曲线，竖切组件 4）
    "KAIROS_FORGETTING_HALF_LIFE": (69, int, "遗忘半衰期（天）"),
    "KAIROS_FRESHNESS_ACTIVE_THRESHOLD": (0.3, float, "活跃记忆 freshness 下限"),
    "KAIROS_FRESHNESS_STALE_THRESHOLD": (0.1, float, "归档记忆 freshness 下限"),
    "KAIROS_FEATURE_FORGETTING_ENGINE": (True, bool, "遗忘调度器特征标志（竖切内 ON）"),
    # 身份注册表（configuration §0.10）
    "KAIROS_NARRATIVE_AUDIT_CYCLE_MAX": (5, int, "叙事连贯性审计周期最大值（>12 拒绝启动）"),
    # 降级状态机（configuration §4，他律性降级契约）
    "KAIROS_DEGRADATION_PERIOD_N": (50, int, "保守静默模式触发阈值（调度周期）"),
    "KAIROS_DEGRADATION_PERIOD_M": (200, int, "受限交叉验证模式触发阈值（调度周期）"),
    # 安全（security-specification §2.1 / deployment §三；S-01 启动校验）
    "KAIROS_API_KEY_HASH": (None, str, "API Key 哈希（轻量模式单 Key，文件权限 600）"),
    "KAIROS_AUDIT_HMAC_KEY": (None, str, "审计链 HMAC 密钥（必填，无默认值）"),
    # 安全密钥族（security-specification §2.1：S-05 加盐 / S-07 AES-256-GCM 加密）
    "KAIROS_SALT": (None, str, "API Key 加盐值（S-05，PBKDF2 派生输入）"),
    "KAIROS_SECRET_KEY": (None, str, "敏感字段加密密钥（S-07，AES-256-GCM 32 字节 hex）"),
    # FTS5（data-model §11；附录 A 基础参数族为 v0.1.0 已交付）
    "KAIROS_FTS5_ENABLED": (True, bool, "FTS5 全文索引开关"),
    "KAIROS_FTS5_TOKENIZER": ("unicode61", str, "FTS5 分词器（unicode61；jieba 需编译扩展）"),
    "KAIROS_FTS5_CHINESE_SEGMENTATION": (
        True,
        bool,
        "精细中文分词（扩展缺失时回落 unicode61 并告警）",
    ),
    "KAIROS_FTS5_OPTIMIZE_INTERVAL": (3600, int, "FTS5 索引优化间隔（秒）"),
    # 服务
    "KAIROS_HOST": ("127.0.0.1", str, "服务监听地址（S-04 本地回环绑定）"),
    "KAIROS_PORT": (8010, int, "服务监听端口（api-spec 基础 URL http://localhost:8010）"),
    "KAIROS_DATA_DIR": ("$HOME/.kairos", str, "数据目录（数据库/日志/密钥文件）"),
}


def _expand_home(path: str) -> str:
    """展开 $HOME 占位符（Windows 下亦支持）。"""
    home = Path.home().as_posix()
    return path.replace("$HOME", home)


def _parse_bool(raw: str) -> bool:
    lowered = raw.strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"非法布尔值: {raw!r}")


def _parse_value(name: str, raw: str) -> Any:
    _default, typ, _desc = _PARAM_SPECS[name]
    if typ is bool:
        return _parse_bool(raw)
    if typ is int:
        return int(raw)
    if typ is float:
        return float(raw)
    return raw


def _validate(name: str, value: Any) -> None:
    """参数取值校验（configuration.md 取值范围）。"""
    if name == "KAIROS_NARRATIVE_AUDIT_CYCLE_MAX" and value > 12:
        raise ConfigError(
            f"{name}={value} 超出安全上限（>12 将导致身份否决权在两次审计之间实质失效），"
            "拒绝启动（架构 §8 风险警告，configuration §0.10）"
        )
    if name == "KAIROS_FORGETTING_HALF_LIFE" and value <= 0:
        raise ConfigError(f"{name} 必须为正整数（configuration §10）")
    if name.startswith("KAIROS_HYBRID_") and name.endswith("_WEIGHT") and not 0 <= value <= 1:
        raise ConfigError(f"{name} 必须在 [0,1] 区间（configuration §6.1）")
    if name == "KAIROS_CAPTURE_MIN_LENGTH" and value < 0:
        raise ConfigError(f"{name} 必须 ≥0（configuration §6）")


class ConfigError(Exception):
    """配置加载/校验失败（S-01 失败关闭：配置非法即拒绝启动）。"""


# ---------------------------------------------------------------------------
# 竖切参数族声明（供 API/CLI 列出可用参数）
# ---------------------------------------------------------------------------

# 竖切消费的参数名集合（config 表运行时动态覆盖亦限此集合）
SLICE_PARAM_NAMES: tuple[str, ...] = tuple(_PARAM_SPECS.keys())

# 必填无默认值参数（启动校验缺值即失败关闭，S-01）
REQUIRED_PARAMS: tuple[str, ...] = ("KAIROS_AUDIT_HMAC_KEY",)

# 特征标志参数族（configuration §0.8 竖切与特征标志）
FEATURE_FLAGS: tuple[str, ...] = ("KAIROS_FEATURE_FORGETTING_ENGINE",)


@dataclass(frozen=True)
class Settings:
    """竖切配置快照（不可变；启动时加载一次，运行时动态覆盖见 config 表）。"""

    values: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        try:
            return self.values[name]
        except KeyError:
            raise AttributeError(name) from None

    def get(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)

    @property
    def db_path(self) -> Path:
        """解析后的 SQLite 数据库文件路径（轻量模式）。"""
        url = self.values["KAIROS_DB_URL"]
        prefix = "sqlite:///"
        if not url.startswith(prefix):
            raise ConfigError(f"轻量模式仅支持 sqlite:/// 连接串，当前: {url}")
        return Path(url[len(prefix) :])


def load_settings(env: dict[str, str] | None = None, dotenv_path: Path | None = None) -> Settings:
    """加载配置：内置默认 < .env 文件 < 环境变量（KAIROS_* 前缀）。

    dotenv 行格式：`KAIROS_X=value`，支持 `#` 注释与空行；
    不调用第三方库（configuration.md 未指定 dotenv 实现，保持零依赖）。
    """
    raw: dict[str, str] = {}

    # 0. 环境变量源（.env 候选路径判定与覆盖合并共用；os.environ 为 _Environ，满足 Mapping）
    env_map: Mapping[str, str] = env if env is not None else os.environ

    # 1. 内置默认值（str 形态统一处理，便于 env 覆盖语义一致）
    for name, (default, _typ, _desc) in _PARAM_SPECS.items():
        if default is not None:
            raw[name] = str(default)

    # 2. .env 文件（显式路径 > KAIROS_DATA_DIR > 默认数据目录 $HOME/.kairos）
    candidates: list[Path] = []
    if dotenv_path is not None:
        candidates.append(dotenv_path)
    else:
        data_dir = env_map.get("KAIROS_DATA_DIR")
        if data_dir:
            candidates.append(Path(_expand_home(data_dir)) / ".env")
        elif env is None:
            # 从 os.environ 读取时（真实运行），与 _PARAM_SPECS 中
            # KAIROS_DATA_DIR 默认值（$HOME/.kairos）保持一致：未显式设置
            # KAIROS_DATA_DIR 仍读取默认数据目录的 .env，否则必填密钥
            # （S-01）缺失。显式传入 env dict（测试/嵌入场景）不读默认
            # .env——保持环境完全隔离语义。
            candidates.append(Path.home() / ".kairos" / ".env")
    for path in candidates:
        if path and path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                if key.startswith(_ENV_PREFIX):
                    raw[key] = value.strip()

    # 3. 环境变量（最高优先级）
    for key, value in env_map.items():
        if key.startswith(_ENV_PREFIX) and key in _PARAM_SPECS:
            raw[key] = value

    # 4. 类型解析 + 校验
    values: dict[str, Any] = {}
    for name in _PARAM_SPECS:
        default, _typ, _desc = _PARAM_SPECS[name]
        if name not in raw:
            if name in REQUIRED_PARAMS:
                raise ConfigError(
                    f"必填参数缺失: {name}（S-01 启动校验——审计链 HMAC 密钥无默认值，"
                    "见 security-specification §2.1 / deployment §三）"
                )
            values[name] = default
            continue
        try:
            value = _parse_value(name, raw[name])
        except ValueError as exc:
            raise ConfigError(f"参数 {name} 解析失败: {exc}") from exc
        _validate(name, value)
        values[name] = value

    # 5. 路径展开（$HOME 占位符）
    for name in ("KAIROS_DB_URL", "KAIROS_DATA_DIR"):
        if isinstance(values[name], str):
            values[name] = _expand_home(values[name])

    return Settings(values=values)


def validate_runtime_override(name: str, raw_value: str) -> Any:
    """运行时动态覆盖校验（PATCH /v1/config / kairos config set）。

    仅接受竖切参数族内的参数名；解析与取值校验复用启动逻辑。
    """
    if name not in _PARAM_SPECS:
        raise ConfigError(f"未知参数: {name}（仅接受竖切参数族 {len(_PARAM_SPECS)} 项）")
    try:
        value = _parse_value(name, raw_value)
    except ValueError as exc:
        raise ConfigError(f"参数 {name} 解析失败: {exc}") from exc
    _validate(name, value)
    return value


# 环境变量名合法性（配置键规范：KAIROS_ + UPPER_SNAKE）
_CONFIG_KEY_RE = re.compile(r"^KAIROS_[A-Z][A-Z0-9_]*$")
