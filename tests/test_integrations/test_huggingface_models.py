from __future__ import annotations

import pytest
from pathlib import Path

from src.integrations import huggingface_models
from src.integrations.huggingface_models import HuggingFaceModelManager


def test_download_success_tracks_revision(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_download(
        repo_id: str,
        revision: str,
        cache_dir: str,
        local_files_only: bool = False,
    ) -> str:
        path = Path(cache_dir) / "downloaded"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(huggingface_models, "snapshot_download", fake_download)
    manager = HuggingFaceModelManager(cache_dir=str(tmp_path))
    path, rev = manager.download_model("test/model", revision="123")
    assert rev == "123"
    assert Path(path).exists()
    version_file = tmp_path / "test__model" / "revision.txt"
    assert version_file.read_text() == "123"


def test_download_failure_uses_cached_revision(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    cached_dir = tmp_path / "test__model"
    cached_dir.mkdir()
    (cached_dir / "revision.txt").write_text("456")

    def fake_download(
        repo_id: str,
        revision: str,
        cache_dir: str,
        local_files_only: bool = False,
    ) -> str:
        if revision == "456" and local_files_only:
            path = Path(cache_dir) / "cached"
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
        raise Exception("download failed")

    monkeypatch.setattr(huggingface_models, "snapshot_download", fake_download)
    manager = HuggingFaceModelManager(cache_dir=str(tmp_path))
    path, rev = manager.download_model("test/model", revision="999")
    assert rev == "456"
    assert Path(path).exists()


def test_download_failure_uses_fallback_revision(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_download(
        repo_id: str,
        revision: str,
        cache_dir: str,
        local_files_only: bool = False,
    ) -> str:
        if revision == "fallback":
            path = Path(cache_dir) / "fallback"
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
        raise Exception("download failed")

    monkeypatch.setattr(huggingface_models, "snapshot_download", fake_download)
    manager = HuggingFaceModelManager(cache_dir=str(tmp_path))
    path, rev = manager.download_model(
        "test/model", revision="999", fallback_revision="fallback"
    )
    assert rev == "fallback"
    assert Path(path).exists()
    version_file = tmp_path / "test__model" / "revision.txt"
    assert version_file.read_text() == "fallback"
