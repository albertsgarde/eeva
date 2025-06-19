from typing import Annotated

from pydantic import Field

from eeva.question import QuestionId
from eeva.utils import ID_PATTERN, NetworkModel

FormId = Annotated[str, Field(pattern=ID_PATTERN)]


class Form(NetworkModel):
    questions: list[QuestionId] = Field()
