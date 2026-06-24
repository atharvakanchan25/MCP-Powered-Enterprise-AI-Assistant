from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import CurrentUser
from app.rag.storage import delete_file, save_upload
from app.schemas.vision import VisionResponse
from app.services.rag.vision import VisionTask, analyze_image, SUPPORTED_IMAGE_TYPES
from app.core.exceptions import AppException
from pathlib import Path

router = APIRouter(prefix="/vision", tags=["Vision & Multimodal"])


@router.post("/analyze", response_model=VisionResponse)
async def analyze(
    user: CurrentUser,
    file: UploadFile = File(...),
    task: VisionTask = Form(VisionTask.GENERAL),
    extra_prompt: str | None = Form(None),
):
    """
    Upload an image and analyze it using GPT-4o Vision.

    Tasks:
    - **ocr** — Extract all text from the image
    - **understand** — General image understanding
    - **diagram** — Analyze architecture/flow diagrams
    - **error_analysis** — Debug screenshots with errors
    - **general** — Comprehensive description
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_IMAGE_TYPES:
        raise AppException(415, f"Unsupported image type '{ext}'. Allowed: {sorted(SUPPORTED_IMAGE_TYPES)}", "UNSUPPORTED_MEDIA")

    storage_path = await save_upload(file, str(user.id))
    try:
        analysis = await analyze_image(storage_path, task=task, extra_prompt=extra_prompt)
    finally:
        await delete_file(str(storage_path))  # Don't persist images

    return VisionResponse(task=task, filename=file.filename or "", analysis=analysis)
