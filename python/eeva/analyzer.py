import typing
from typing import Annotated

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class Profile(BaseModel):
    identity: float = Field(ge=0, le=1)

    def cmp(self, other: "Profile") -> float:
        return abs(self.identity - other.identity)


class QuestionResponse(BaseModel):
    question: str = Field()
    response: str = Field()


Response = Annotated[dict[str, QuestionResponse], Field()]

ResponseSet = Annotated[dict[str, Response], Field()]

ProfileSet = Annotated[dict[str, Profile], Field()]


def analyze(response: Response, llm: BaseChatModel) -> Profile:
    structured_llm = llm.with_structured_output(Profile)

    content = "\n".join(f"{question}: {question_response.response}" for question, question_response in response.items())

    profile = typing.cast(
        Profile,
        structured_llm.invoke(
            [
                SystemMessage(content="How high is the identity of this set of answers on a scale from 0 to 1?"),
                HumanMessage(content=content),
            ]
        ),
    )

    return profile
