import base64
from enum import Enum
from pathlib import Path

from openai import AsyncOpenAI
from PIL import Image

from app.core.config import get_settings
from app.core.exceptions import AppException

SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_IMAGE_DIMENSION = 2048  # px — GPT-4o vision limit


class VisionTask(str, Enum):
    OCR = "ocr"
    UNDERSTAND = "understand"
    DIAGRAM = "diagram"
    ERROR_ANALYSIS = "error_analysis"
    GENERAL = "general"


_TASK_PROMPTS: dict[VisionTask, str] = {
    VisionTask.OCR: "Extract ALL text from this image verbatim. Preserve formatting and structure.",
    VisionTask.UNDERSTAND: "Describe this image in detail. Identify key elements, context, and meaning.",
    VisionTask.DIAGRAM: (
        "Analyze this diagram. Identify: type of diagram, components, relationships, "
        "flow/data direction, and key insights."
    ),
    VisionTask.ERROR_ANALYSIS: (
        "Analyze this screenshot for errors, issues, or problems. "
        "Identify: error messages, stack traces, UI issues, and suggest fixes."
    ),
    VisionTask.GENERAL: "Analyze this image and provide a comprehensive description.",
}


def _encode_image(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type)."""
    suffix = path.suffix.lower().lstrip(".")
    media_type = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    data = base64.b64encode(path.read_bytes()).decode()
    return data, f"image/{media_type}"


def _resize_if_needed(path: Path) -> Path:
    """Resize image in-place if it exceeds GPT-4o dimension limits."""
    with Image.open(path) as img:
        if max(img.size) <= MAX_IMAGE_DIMENSION:
            return path
        img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
        img.save(path)
    return path


async def analyze_image(
    path: Path,
    task: VisionTask = VisionTask.GENERAL,
    extra_prompt: str | None = None,
) -> str:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_IMAGE_TYPES:
        raise AppException(415, f"Unsupported image type: {ext}", "UNSUPPORTED_MEDIA")

    _resize_if_needed(path)
    b64, media_type = _encode_image(path)
    prompt = _TASK_PROMPTS[task]
    if extra_prompt:
        prompt = f"{prompt}\n\nAdditional instruction: {extra_prompt}"

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}", "detail": "high"}},
                ],
            }
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""
