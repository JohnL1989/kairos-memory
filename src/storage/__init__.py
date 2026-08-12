"""存储层（架构 §5）——记忆 CRUD / 路径空间 / 三信号检索 / 双副本 / 身份注册表 / 遗忘。

模块映射（implementation-map 四、存储层）：
- models.py          数据模型定义（竖切 15 张表 ORM）
- memory_store.py    记忆 CRUD
- path_index.py      路径空间索引
- vector_index.py    向量索引（sqlite-vec）
- dual_copy.py       双副本管理
- identity_registry.py 身份注册表
- forgetting.py      遗忘调度器
- hybrid_search.py   三信号混合检索
"""
