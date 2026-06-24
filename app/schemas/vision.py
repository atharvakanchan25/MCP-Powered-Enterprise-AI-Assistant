from pydantic import BaseModel
from app.services.rag.vision import VisionTask


class VisionResponse(BaseModel):
    task: VisionTask
    filename: str
    analysis: str
