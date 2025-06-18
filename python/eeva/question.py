from typing import Annotated

from pydantic import Field

from eeva.utils import ID_PATTERN, NetworkModel

QuestionId = Annotated[str, Field(pattern=ID_PATTERN)]


class Question(NetworkModel):
    question: str = Field()
    example_answers: list[str] = Field()
