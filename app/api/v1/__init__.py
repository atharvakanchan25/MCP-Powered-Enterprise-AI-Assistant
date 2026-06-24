from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.conversations import router as conv_router
from app.api.v1.documents import router as docs_router
from app.api.v1.vision import router as vision_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(conv_router)
api_router.include_router(docs_router)
api_router.include_router(vision_router)
