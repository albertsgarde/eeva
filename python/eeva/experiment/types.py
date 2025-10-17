from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel

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


class UserId(RootModel):
    model_config = ConfigDict(frozen=True)
    root: str = Field(pattern=ID_PATTERN)


LanguageCode = Annotated[str, Field(min_length=2, max_length=5)]


class User(BaseModel):
    response: Response = Field()
    prod_profile: ProdProfile | None = Field()
    language_code: LanguageCode = Field()
    hidden: bool = Field()


class UserSet(RootModel):
    root: dict[UserId, User]

    def __getitem__(self, item: UserId) -> User:
        return self.root[item]

    def __iter__(self):
        return iter(self.root.items())

    def __contains__(self, item: UserId) -> bool:
        return item in self.root

    def __len__(self) -> int:
        return len(self.root)

    def items(self):
        return self.root.items()

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()


class QuestionTranslation(BaseModel):
    text: str = Field()
    examples: list[str] = Field()


QuestionId = Annotated[str, Field(pattern=ID_PATTERN)]


class Question(BaseModel):
    translations: dict[LanguageCode, QuestionTranslation] = Field()
    active: bool = Field()


class QuestionSet(RootModel):
    root: dict[QuestionId, Question]

    def __getitem__(self, item: QuestionId) -> Question:
        return self.root[item]

    def __iter__(self):
        return iter(self.root.items())

    def __contains__(self, item: QuestionId) -> bool:
        return item in self.root

    def __len__(self) -> int:
        return len(self.root)

    def items(self):
        return self.root.items()

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()


CoupleId = Annotated[str, Field()]

Couple = Annotated[tuple[UserId, UserId], Field()]
CouplePairs = Annotated[dict[CoupleId, Couple], Field()]


class BaseData(BaseModel):
    users: UserSet = Field()
    questions: QuestionSet = Field()


class RunConfig(BaseModel):
    secrets_path: Path = Field()
    data_dir: Path = Field()
    output_dir: Path = Field()

    model: str = Field()
    model_provider: str = Field()
    reasoning_effort: str = Field()
    identity_prompt: str = Field()
    identity_extraction_prompt: str = Field()
    explicit_cot: bool = Field()
    system_prompt: str | None = Field()

    num_tests: int = Field(gt=0)

    question_exclusion_sets: set[str] = Field()
    question_inclusion_sets: set[str] | None = Field()

    user_exclusion_sets: set[str] = Field()
    user_inclusion_sets: set[str] | None = Field()
    only_couples: bool = Field()
    answer_progress_minimum: float = Field(ge=0)
    num_answers_minimum: int = Field(ge=1)
