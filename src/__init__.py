"""Kairos Memory System — AI agent 记忆系统（竖切 v0.1.0-slice）。

包结构遵循 implementation-map.md 的 src/ 路径映射：
- main.py          CLI 入口（Typer）
- config.py        配置加载
- storage/         存储层（记忆 CRUD / 路径空间 / 三信号检索 / 双副本 / 身份注册表 / 遗忘）
- events/          事件总线（4 类事件）
- access/          接入层（REST API / CLI 命令 / 鉴权 / 摄取验证门禁）
- sovereignty/     宪法主权面（外部校准 / 降级状态机 / 强制冻结）
- supervision/     监督平面（审计庭 HMAC 链）
- scheduler.py     周期性任务调度（APScheduler 空闲驱动）
- utils/           工具函数
"""

__version__ = "0.1.0"
