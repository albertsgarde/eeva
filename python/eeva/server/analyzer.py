from fastapi import APIRouter
from langchain.chat_models.base import BaseChatModel

from eeva import analyzer
from eeva.analyzer import Profile, Response

from .database import Database


def create_router(database: Database, llm: BaseChatModel) -> APIRouter:
    router = APIRouter()

    @router.post("/analyze")
    def analyze(response: Response) -> Profile:
        return analyzer.analyze(response, llm)

    return router
