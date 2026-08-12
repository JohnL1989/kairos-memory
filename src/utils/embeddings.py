"""文本嵌入器（竖切组件 3 前置）。

权威规格：technology-stack §三（轻量模式默认 BGE-M3，原生 1024 维经固定
随机正交投影映射至 1536 维，ADR-012；标准模式 text-embedding-3-small 1536 维）。

竖切开发默认：HashEmbedder（确定性伪随机 1536 维嵌入）——零外部依赖、
CI 友好、管线正确性验证；BGE-M3 模型接入点保留（sentence-transformers），
模型未下载/不可用时回落 HashEmbedder 并告警（可用性降级 fail-open 留痕，
不阻断启动——与 configuration.md KAIROS_FTS5_CHINESE_SEGMENTATION 同模式）。
"""

from __future__ import annotations

import hashlib
import os
import struct
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# 嵌入维度（schema-slice §约定：VECTOR(1536)，DDL 以 1536 为准）
EMBEDDING_DIM = 1536


def vector_to_bytes(vector: list[float]) -> bytes:
    """VECTOR(n) BLOB：n × float32 小端紧凑排列（1536 维 = 6144 字节）。"""
    return struct.pack(f"<{len(vector)}f", *vector)


def bytes_to_vector(blob: bytes) -> list[float]:
    """BLOB → float32 列表（sqlite-vec 距离函数输入）。"""
    return list(struct.unpack(f"<{len(blob) // 4}f", blob))


class Embedder(ABC):
    """文本嵌入器抽象（Business 层仅依赖此接口，方言差异收敛于实现内）。"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """返回 1536 维单位向量。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """嵌入器标识（写入 GET /health 响应，观测一致性）。"""


class HashEmbedder(Embedder):
    """确定性伪随机嵌入（开发默认）——同一文本恒等向量，不同文本近正交。

    用途：管线正确性验证与测试（不承载语义质量）；真实语义质量由
    BGE-M3 承担（模型就绪后切换 KAIROS_EMBEDDER=bge-m3）。
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim

    @property
    def name(self) -> str:
        return "hash-deterministic"

    async def embed(self, text: str) -> list[float]:
        # 伪随机方向：以文本 SHA-256 为种子，numpy PCG64 派生标准正态向量。
        # 确定性：同文本恒等向量；不同文本近正交。numpy 派生替代逐维 SHA-256
        # （基准关键路径：1 万条嵌入预计算 + 每次查询嵌入 ~50ms → ~1ms）。
        import numpy as np

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(self.dim)
        norm = float(np.linalg.norm(vector)) or 1.0
        return [float(x) for x in (vector / norm)]


class BgeM3Embedder(Embedder):
    """BGE-M3 本地嵌入（轻量模式默认，technology-stack §三）——D-448 闭合。

    管线：sentence-transformers 加载 BGE-M3（原生 1024 维）→ 固定随机正交投影
    W ∈ R^{1536×1024} 映射至 1536 维（ADR-012；投影矩阵确定性生成并随
    schema 持久化）→ 归一化。
    依赖：sentence-transformers + torch 为可选组（`pip install kairos[bge-m3]`）；
    模型缺失/依赖缺失时构造失败 → 工厂回落 HashEmbedder（fail-open 留痕，
    D-448 升级触发条件：模型就绪后切换 KAIROS_EMBEDDER=bge-m3）。
    """

    def __init__(
        self,
        model_path: str = "./models/bge-m3",
        projection_path: str | None = None,
        projection_seed: int = 42,
    ) -> None:
        from pathlib import Path

        self.model_path = model_path
        self.projection_seed = projection_seed
        if not Path(model_path).exists():
            # 模型未就绪：构造失败 → 工厂回落 HashEmbedder（D-448 留痕）
            raise RuntimeError(f"BGE-M3 模型缺失: {model_path}")
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers 未安装（D-448：pip install kairos[bge-m3]）"
            ) from exc
        self._model = SentenceTransformer(model_path)
        self._projection = self._load_or_build_projection(projection_path)

    @property
    def name(self) -> str:
        return "bge-m3"

    async def embed(self, text: str) -> list[float]:
        """BGE-M3 嵌入 → 正交投影 1536 维 → 归一化（单位向量）。"""
        import numpy as np

        raw = self._model.encode(text, normalize_embeddings=True)  # 1024 维
        # x(1024) @ Wᵀ(1024×1536) → 1536 维（W ∈ R^{1536×1024}，ADR-012）
        vector = np.asarray(raw, dtype="<f4") @ self._projection.T
        norm = float(np.linalg.norm(vector)) or 1.0
        return [float(x) for x in (vector / norm)]

    # ------------------------------------------------------------------
    # 投影矩阵（ADR-012：固定随机正交投影，矩阵随 schema 持久化）
    # ------------------------------------------------------------------

    def _load_or_build_projection(self, projection_path: str | None) -> Any:
        """加载持久化投影矩阵；缺失时确定性生成（固定种子）并持久化。"""
        import numpy as np

        path = projection_path or os.path.join(
            os.environ.get("KAIROS_DATA_DIR", str(Path.home() / ".kairos")),
            "bge_m3_projection.npy",
        )
        if os.path.exists(path):
            return np.load(path)
        # 确定性生成：固定种子 → QR 正交化（1536×1024 列正交）
        rng = np.random.default_rng(self.projection_seed)
        w = rng.standard_normal((1536, 1024)).astype("<f4")
        q, _r = np.linalg.qr(w)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.save(path, q)
        return q


def create_embedder(kind: str = "hash") -> Embedder:
    """按配置创建嵌入器（KAIROS_EMBEDDER；未知种类回落 hash 并告警）。"""
    if kind in ("bge-m3", "bge_m3"):
        try:
            return BgeM3Embedder()
        except Exception:
            # 模型/依赖不可用 → 回落 hash（D-448 fail-open 留痕，启动日志告警）
            import logging

            logging.getLogger("kairos.utils.embeddings").warning(
                "BGE-M3 不可用（模型或依赖缺失），回落 HashEmbedder（D-448）"
            )
    return HashEmbedder()
