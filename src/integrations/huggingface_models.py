import logging
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    from huggingface_hub import snapshot_download  # type: ignore
except Exception as exc:  # pragma: no cover
    snapshot_download = None  # type: ignore
    _import_error = exc


class HuggingFaceModelManager:
    """Manage model downloads with caching and version tracking."""

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self._logger = logging.getLogger(__name__)
        self.cache_dir = Path(
            cache_dir
            or os.getenv("HF_HOME")
            or (Path.home() / ".cache" / "huggingface")
        )
        if snapshot_download is None:  # pragma: no cover
            message = f"huggingface_hub library missing: {_import_error}"
            raise ImportError(message)

    def _model_dir(self, model_id: str) -> Path:
        safe_name = model_id.replace("/", "__")
        return self.cache_dir / safe_name

    def _revision_file(self, model_id: str) -> Path:
        return self._model_dir(model_id) / "revision.txt"

    def _write_revision(self, model_id: str, revision: str) -> None:
        model_dir = self._model_dir(model_id)
        model_dir.mkdir(parents=True, exist_ok=True)
        self._revision_file(model_id).write_text(revision)

    def _read_revision(self, model_id: str) -> Optional[str]:
        try:
            return self._revision_file(model_id).read_text().strip()
        except FileNotFoundError:
            return None

    def download_model(
        self,
        model_id: str,
        revision: str = "main",
        fallback_revision: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Download a model with caching and fallback handling.

        Returns the local path and the revision used.
        """

        try:
            path = snapshot_download(
                repo_id=model_id,
                revision=revision,
                cache_dir=str(self.cache_dir),
            )
            self._write_revision(model_id, revision)
            return path, revision
        except Exception as exc:  # pragma: no cover
            self._logger.warning(
                "Failed to download model %s revision %s: %s",
                model_id,
                revision,
                exc,
            )
            cached_revision = self._read_revision(model_id)
            if cached_revision:
                try:
                    path = snapshot_download(
                        repo_id=model_id,
                        revision=cached_revision,
                        cache_dir=str(self.cache_dir),
                        local_files_only=True,
                    )
                    self._logger.info(
                        "Using cached revision %s for model %s",
                        cached_revision,
                        model_id,
                    )
                    return path, cached_revision
                except Exception as cache_exc:  # pragma: no cover
                    self._logger.warning(
                        "Failed to load cached revision %s for model %s: %s",
                        cached_revision,
                        model_id,
                        cache_exc,
                    )
            if fallback_revision:
                try:
                    path = snapshot_download(
                        repo_id=model_id,
                        revision=fallback_revision,
                        cache_dir=str(self.cache_dir),
                    )
                    self._write_revision(model_id, fallback_revision)
                    self._logger.info(
                        "Using fallback revision %s for model %s",
                        fallback_revision,
                        model_id,
                    )
                    return path, fallback_revision
                except Exception as fallback_exc:  # pragma: no cover
                    self._logger.error(
                        "Fallback revision %s failed for model %s: %s",
                        fallback_revision,
                        model_id,
                        fallback_exc,
                    )
            raise
