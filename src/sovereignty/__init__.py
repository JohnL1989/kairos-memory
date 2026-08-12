"""宪法主权面（架构 §1）——外部校准 / 降级状态机 / 强制冻结。

模块映射（implementation-map 一、宪法主权面）：
- calibration.py          外部校准端口（CAL-01，S-11 宪法修订唯一入口）
- degradation.py          降级状态机（三模式：保守静默/受限交叉验证/安全休眠）
- freeze.py               强制冻结/解冻（CAL-03）
"""
