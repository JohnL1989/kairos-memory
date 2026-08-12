"""接入层（架构 §7）——REST API / CLI / Agent Tool / 鉴权 / 摄取验证门禁。

模块映射（implementation-map 六、接入层）：
- api/            Litestar handler（竖切 21 端点）
- cli.py          CLI 命令
- auth.py         API Key 鉴权（read/write/admin 三级）
- ingestion.py    摄取验证门禁（捕获门控五层）
"""
