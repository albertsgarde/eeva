from datetime import datetime
from typing import Annotated

from pydantic import Field

from eeva.form import FormId
from eeva.question import Question, QuestionId
from eeva.utils import NetworkModel

FormResponseId = Annotated[int, Field(ge=0)]  # Assuming FormResponseId is a non-negative integer


class QuestionResponse(NetworkModel):
    question_id: QuestionId = Field()
    question: Question = Field()
    response: str = Field()


class FormResponse(NetworkModel):
    form_id: FormId = Field()
    responses: list[QuestionResponse]
    subject_name: str = Field()
    subject_email: str | None = Field(default=None)
    created_at: datetime = Field(default=datetime.now())
    modified_at: datetime = Field(default=datetime.now())
