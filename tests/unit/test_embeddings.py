"""嵌入器单元测试——HashEmbedder 确定性/维度/单位向量/BLOB 编解码。

覆盖：1536 维、同文本恒等、不同文本近正交、单位范数、向量 BLOB 双向编解码、
create_embedder 工厂回落（BGE-M3 不可用 → hash）。
"""

from __future__ import annotations

import pytest

from src.utils.embeddings import (
    EMBEDDING_DIM,
    BgeM3Embedder,
    HashEmbedder,
    bytes_to_vector,
    create_embedder,
    vector_to_bytes,
)

pytestmark = pytest.mark.unit


class TestHashEmbedder:
    async def test_dimension(self) -> None:
        v = await HashEmbedder().embed("测试文本")
        assert len(v) == EMBEDDING_DIM == 1536

    async def test_deterministic(self) -> None:
        e = HashEmbedder()
        assert await e.embed("同一文本") == await e.embed("同一文本")

    async def test_unit_norm(self) -> None:
        import math

        v = await HashEmbedder().embed("归一化测试")
        norm = math.sqrt(sum(x * x for x in v))
        assert norm == pytest.approx(1.0, abs=1e-3)

    async def test_different_texts_near_orthogonal(self) -> None:
        """不同文本近正交（余弦 ~0）——伪随机方向语义。"""
        e = HashEmbedder()
        a = await e.embed("主题甲的内容")
        b = await e.embed("主题乙的内容")
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        assert abs(dot) < 0.3


class TestBlobCodec:
    def test_roundtrip(self) -> None:
        vector = [0.5, -0.25, 1.0] * (EMBEDDING_DIM // 3)
        blob = vector_to_bytes(vector)
        assert len(blob) == EMBEDDING_DIM * 4  # float32 小端
        assert bytes_to_vector(blob)[:3] == pytest.approx([0.5, -0.25, 1.0])


class TestEmbedderFactory:
    def test_default_hash(self) -> None:
        assert isinstance(create_embedder(), HashEmbedder)

    def test_bge_m3_falls_back_to_hash(self) -> None:
        # BGE-M3 模型缺失（构造 RuntimeError）→ 工厂回落 hash（D-448 留痕）
        assert isinstance(create_embedder("bge-m3"), HashEmbedder)

    def test_bge_m3_construction_requires_model(self) -> None:
        with pytest.raises(RuntimeError, match="模型缺失"):
            BgeM3Embedder(model_path="./nonexistent-model")
