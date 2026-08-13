"""接入层 Provider（架构 §7.1a Hermes Memory Provider）。

- kairos_provider.py：KairosMemoryProvider 参考实现（与 Hermes MemoryProvider
  ABC 对齐的接口 + HTTP 客户端语义）
- 部署：Hermes 插件壳位于 $HERMES_HOME/plugins/kairos/（独立 venv 自包含，
  与本参考实现同构）
"""
