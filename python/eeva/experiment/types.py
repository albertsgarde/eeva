from typing import Annotated, Awaitable, Callable

from pydantic import BaseModel, Field

from ..utils import ID_PATTERN


class Profile(BaseModel):
    identity: float = Field(ge=0, le=1)


class ProdProfile(BaseModel):
    identity: float = Field(ge=0, le=1)
    horoscope: str = Field()

    def cmp(self, other: "ProdProfile") -> float:
        return abs(self.identity - other.identity)


class QuestionResponse(BaseModel):
    question: str = Field()
    response: str = Field()


class Response(BaseModel):
    first_name: str = Field()
    last_name: str = Field()
    responses: dict[str, QuestionResponse] = Field()


UserId = Annotated[str, Field(pattern=ID_PATTERN)]


class User(BaseModel):
    response: Response = Field()
    prod_profile: ProdProfile | None = Field()


CoupleId = Annotated[str, Field()]

Couple = Annotated[tuple[UserId, UserId], Field()]
CouplePairs = Annotated[dict[CoupleId, Couple], Field()]


Analyzer = Callable[[Response], Awaitable[Profile]]
