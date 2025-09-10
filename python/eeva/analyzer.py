import typing
from pathlib import Path
from typing import Annotated

import aiofiles
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class Profile(BaseModel):
    identity: float = Field(ge=0, le=1)
    horoscope: str = Field()

    def cmp(self, other: "Profile") -> float:
        return abs(self.identity - other.identity)


class RelationshipProfile(BaseModel):
    horoscope: str = Field()


class QuestionResponse(BaseModel):
    question: str = Field()
    response: str = Field()


class Response(BaseModel):
    first_name: str = Field()
    last_name: str | None = Field()
    responses: dict[str, QuestionResponse] = Field()


ResponseSet = Annotated[dict[str, Response], Field()]

ProfileSet = Annotated[dict[str, Profile], Field()]


async def analyze(response: Response, llm: BaseChatModel, data_path: Path) -> Profile:
    async with aiofiles.open(data_path / "identity.txt", mode="r", encoding="utf-8") as f:
        identity_prompt = await f.read()
    async with aiofiles.open(data_path / "horoscope_helper.txt", mode="r", encoding="utf-8") as f:
        horoscope_helper_prompt = await f.read()
    async with aiofiles.open(data_path / "horoscope.txt", mode="r", encoding="utf-8") as f:
        horoscope_prompt = await f.read()

    class AnalyzerOutput(BaseModel):
        """ """

        identity: float = Field(ge=0, le=1, description=identity_prompt)
        horoscope_help: str = Field(description=horoscope_helper_prompt)
        horoscope: str = Field(description=horoscope_prompt)

    structured_llm = llm.with_structured_output(AnalyzerOutput)

    content = "\n".join(
        f"{question}: {question_response.response}" for question, question_response in response.responses.items()
    )

    raw_output = await structured_llm.ainvoke(
        [
            SystemMessage(content="Please analyze the identity of this set of answers."),
            HumanMessage(content=content),
        ]
    )
    if isinstance(raw_output, dict):
        output = AnalyzerOutput(**raw_output)
    elif isinstance(raw_output, AnalyzerOutput):
        output = typing.cast(AnalyzerOutput, raw_output)
    else:
        raise ValueError(f"Unexpected output type: {type(raw_output)}. Expected dict or AnalyzerOutput.")
    avg_identity = output.identity
    profile = Profile(identity=avg_identity, horoscope=output.horoscope)

    return profile


async def analyze_relationship(
    response1: Response, profile1: Profile, response2: Response, profile2: Profile, llm: BaseChatModel, data_path: Path
) -> RelationshipProfile:
    async with aiofiles.open(data_path / "relationship_horoscope.txt", mode="r", encoding="utf-8") as f:
        relationship_horoscope_prompt = await f.read()

    class AnalyzeRelationshipOutput(BaseModel):
        """ """

        relationship_horoscope: str = Field(description=relationship_horoscope_prompt)

    structured_llm = llm.with_structured_output(AnalyzeRelationshipOutput)
    content = (
        "Name and answers: "
        f"{response1.first_name},\n"
        + "\n".join(
            f"{question}: {question_response.response}" for question, question_response in response1.responses.items()
        )
        + "Name and answers: "
        f"{response2.first_name},\n"
        + "\n".join(
            f"{question}: {question_response.response}" for question, question_response in response2.responses.items()
        )
    )

    raw_output = await structured_llm.ainvoke(
        [
            HumanMessage(content=content),
        ]
    )

    if isinstance(raw_output, dict):
        output = AnalyzeRelationshipOutput(**raw_output)
    elif isinstance(raw_output, AnalyzeRelationshipOutput):
        output = typing.cast(AnalyzeRelationshipOutput, raw_output)
    else:
        raise ValueError(f"Unexpected output type: {type(raw_output)}. Expected dict or RelationshipHoroscopeOutput.")

    return RelationshipProfile(horoscope=output.relationship_horoscope)
