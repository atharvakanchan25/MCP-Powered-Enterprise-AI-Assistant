import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import AppException


def _upload_root() -> Path:
    p = Path(get_settings().upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_path(owner_id: str, filename: str) -> Path:
    """Construct a safe storage path under owner sub-directory."""
    owner_dir = _upload_root() / owner_id
    owner_dir.mkdir(exist_ok=True)
    suffix = Path(filename).suffix.lower()
    return owner_dir / f"{uuid.uuid4()}{suffix}"


async def save_upload(file: UploadFile, owner_id: str) -> Path:
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    dest = _safe_path(owner_id, file.filename or "upload")
    size = 0
    async with aiofiles.open(dest, "wb") as out:
        while chunk := await file.read(64 * 1024):
            size += len(chunk)
            if size > max_bytes:
                dest.unlink(missing_ok=True)
                raise AppException(413, f"File exceeds {settings.max_upload_size_mb} MB limit", "FILE_TOO_LARGE")
            await out.write(chunk)
    return dest


async def delete_file(path: str) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
