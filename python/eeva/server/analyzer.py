import logging
from pathlib import Path

from fastapi import APIRouter
from langchain.chat_models.base import BaseChatModel

from eeva import analyzer
from eeva.analyzer import Profile, RelationshipProfile, Response


def create_router(llm: BaseChatModel, data_path: Path) -> APIRouter:
    router = APIRouter()

    @router.post("/analyze")
    async def analyze(response: Response) -> Profile:
        logging.info(f"Analyzing response for user {response.first_name}")
        return await analyzer.analyze(response, llm, data_path)

    @router.post("/analyze-relationship")
    async def analyze_relationship(
        response1: Response, profile1: Profile, response2: Response, profile2: Profile
    ) -> RelationshipProfile:
        logging.info(f"Analyzing link for users {response1.first_name} and {response2.first_name}")
        return await analyzer.analyze_relationship(response1, profile1, response2, profile2, llm, data_path)

    return router
