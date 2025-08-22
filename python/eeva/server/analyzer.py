from pathlib import Path

from fastapi import APIRouter
from langchain.chat_models.base import BaseChatModel

from eeva import analyzer
from eeva.analyzer import Profile, Response

from .database import Database


def create_router(database: Database, llm: BaseChatModel, data_path: Path) -> APIRouter:
    router = APIRouter()

    @router.post("/analyze")
    async def analyze(response: Response) -> Profile:
        return await analyzer.analyze(response, llm, data_path)

    return router
