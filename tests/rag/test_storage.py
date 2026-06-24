import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.storage import delete_file, _safe_path


def test_safe_path_creates_owner_dir(tmp_path):
    with patch("app.rag.storage._upload_root", return_value=tmp_path):
        p = _safe_path("user-123", "document.pdf")
        assert p.parent.name == "user-123"
        assert p.suffix == ".pdf"
        assert p.parent.exists()


async def test_delete_file_removes_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("data")
    assert f.exists()
    await delete_file(str(f))
    assert not f.exists()


async def test_delete_file_missing_is_noop(tmp_path):
    # Should not raise even if file doesn't exist
    await delete_file(str(tmp_path / "nonexistent.txt"))


async def test_save_upload_file_too_large(tmp_path):
    from app.rag.storage import save_upload
    from app.core.exceptions import AppException

    mock_file = AsyncMock()
    mock_file.filename = "large.txt"
    mock_file.content_type = "text/plain"
    # Returns data larger than limit
    chunk = b"x" * (1024 * 1024)  # 1 MB per read
    call_count = 0

    async def read_side_effect(size):
        nonlocal call_count
        call_count += 1
        return chunk if call_count == 1 else b""

    mock_file.read = read_side_effect

    with patch("app.rag.storage._upload_root", return_value=tmp_path), \
         patch("app.core.config.get_settings") as mock_settings:
        mock_settings.return_value.max_upload_size_mb = 0  # 0 MB limit → immediate rejection
        mock_settings.return_value.upload_dir = str(tmp_path)
        with pytest.raises(AppException) as exc_info:
            await save_upload(mock_file, "user-123")
        assert exc_info.value.status_code == 413
