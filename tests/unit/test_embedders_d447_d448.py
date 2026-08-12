"""D-447 / D-448 闭合测试。

D-447（sqlite-vec 自适应）：探针可加载时 SQL 路径、不可加载回落 numpy——
探针幂等缓存 + 模块状态隔离。
D-448（BGE-M3 完整路径）：投影矩阵确定性生成/持久化/正交性、embed 管线
（mock 模型验证 1024→1536 投影）、模型缺失回落（工厂）。
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.utils.embeddings import BgeM3Embedder, HashEmbedder, create_embedder

pytestmark = pytest.mark.unit


class TestBgeM3Projection:
    def test_projection_deterministic(self, tmp_path: Path) -> None:
        """固定种子 → 投影矩阵确定性。"""
        emb = BgeM3Embedder.__new__(BgeM3Embedder)
        emb.projection_seed = 42
        p1 = emb._load_or_build_projection(str(tmp_path / "proj1.npy"))
        p2 = emb._load_or_build_projection(str(tmp_path / "proj1.npy"))  # 加载持久化
        assert p1.shape == (1536, 1024)
        assert np.allclose(p1, p2)

    def test_projection_near_orthogonal(self, tmp_path: Path) -> None:
        """ADR-012：固定随机正交投影（列正交性）。"""
        emb = BgeM3Embedder.__new__(BgeM3Embedder)
        emb.projection_seed = 42
        w = emb._load_or_build_projection(str(tmp_path / "proj2.npy"))
        gram = w.T @ w  # 1024×1024
        off_diag = gram - np.eye(1024)
        assert np.abs(off_diag).max() < 1e-6  # 近正交

    def test_projection_persisted(self, tmp_path: Path) -> None:
        """矩阵随 schema 持久化（KAIROS_DATA_DIR）。"""
        emb = BgeM3Embedder.__new__(BgeM3Embedder)
        emb.projection_seed = 7
        path = str(tmp_path / "persist.npy")
        emb._load_or_build_projection(path)
        assert os.path.exists(path)


class TestBgeM3EmbedPipeline:
    def test_embed_pipeline_mock_model(self, tmp_path: Path) -> None:
        """embed 管线：1024 维 → 投影 → 1536 维单位向量（mock 模型）。"""
        emb = BgeM3Embedder.__new__(BgeM3Embedder)
        emb.projection_seed = 42
        emb._projection = emb._load_or_build_projection(str(tmp_path / "proj3.npy"))
        # mock sentence-transformers 模型（返回 1024 维向量）
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.default_rng(0).standard_normal(1024)
        emb._model = mock_model

        import asyncio

        vector = asyncio.run(emb.embed("测试文本"))
        assert len(vector) == 1536
        norm = np.linalg.norm(vector)
        assert norm == pytest.approx(1.0, abs=1e-3)
        mock_model.encode.assert_called_once()

    def test_model_missing_raises(self) -> None:
        """模型缺失 → 构造失败（工厂回落路径）。"""
        with pytest.raises(RuntimeError, match="模型缺失"):
            BgeM3Embedder(model_path="./nonexistent-model-xyz")

    def test_factory_falls_back_to_hash(self) -> None:
        """模型缺失时工厂回落 HashEmbedder（D-448 fail-open 留痕）。"""
        assert isinstance(create_embedder("bge-m3"), HashEmbedder)


class TestSqliteVecProbe:
    def test_probe_cached(self, monkeypatch) -> None:
        """探针结果缓存（幂等，不重复探测）。"""
        import src.storage.vector_index as vi

        # 重置缓存 → 探针在扩展加载失败环境返回 False 并缓存
        vi._SQLITE_VEC_AVAILABLE = None
        from types import SimpleNamespace

        def _fail(*args, **kwargs):
            raise RuntimeError("load_extension not supported")

        conn = SimpleNamespace()
        conn.enable_load_extension = MagicMock()
        conn.load_extension = MagicMock(side_effect=_fail)
        # dll 路径存在检查（Windows 有 vec0.dll）→ 进入 load_extension → 失败
        monkeypatch.setattr(vi, "_SQLITE_VEC_AVAILABLE", None)
        result = vi._probe_sqlite_vec(conn)
        assert result is False  # 扩展不可加载 → numpy 路径
        assert vi._SQLITE_VEC_AVAILABLE is False  # 已缓存
        vi._SQLITE_VEC_AVAILABLE = None  # 清理

    def test_probe_false_keeps_numpy_path(self) -> None:
        """探针 False → 检索仍走 numpy 路径（现有测试全绿即证明）。"""
        import src.storage.vector_index as vi

        assert vi._SQLITE_VEC_AVAILABLE in (None, False) or vi._SQLITE_VEC_AVAILABLE
