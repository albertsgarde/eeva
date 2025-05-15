from pathlib import Path
import typing
from typing_extensions import Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from .utils import Model


class Message(BaseModel):
    interviewer: bool = Field()
    content: str = Field()

    def to_message(self) -> BaseMessage:
        return HumanMessage(content=self.content)


class Interviewer(BaseModel):
    system_prompt: str = Field()
    model: Model = Field()

    def respond(self, messages: Sequence[Message]) -> Message:
        chat = self.model.init_chat_model()
        response = chat.invoke(
            [
                SystemMessage(content=self.system_prompt),
                *[message.to_message() for message in messages],
            ]
        )
        return Message(interviewer=True, content=response.content)


class Interview(BaseModel):
    interviewer: Interviewer = Field()
    messages: list[Message] = Field()

    @staticmethod
    def initialize(interviewer: Interviewer, initial_message: str) -> "Interview":
        return Interview(
            interviewer=interviewer,
            messages=[Message(interviewer=True, content=initial_message)],
        )

    def respond(self, subject_message: str) -> Message:
        self.messages.append(Message(interviewer=False, content=subject_message))
        response = self.interviewer.respond(self.messages)
        self.messages.append(response)
        return response

    def pretty_format(self, subject_name: str) -> str:
        role_names = {True: "Interviewer", False: subject_name}
        max_name_length = max(len(name) for name in role_names.values())
        return "\n".join(
            [
                f"{f'{role_names[message.interviewer]}:':<{max_name_length + 1}} {message.content}"
                for message in self.messages
            ]
        )

    def save_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json())

    @staticmethod
    def load_from_file(path: Path) -> "Interview":
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return Interview.model_validate_json(data)


class InterviewAnalysis(BaseModel):
    "Analysis of the interview"

    analysis: str = Field(
        description="Analysis of how the interview scores on the metric"
    )
    score: float = Field(
        description="How the interview scores on the metric from 0 to 1"
    )

    def pretty_format(self) -> str:
        return f"Score: {self.score:.2f}\nAnalysis: {self.analysis}"


class Analyst(BaseModel):
    system_prompt: str = Field()
    instruction: str = Field()
    model: Model = Field()

    def analyze(self, interview: Interview, subject_name: str) -> InterviewAnalysis:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=self.instruction + "\n" + interview.pretty_format(subject_name)
            ),
        ]
        model = self.model.init_chat_model().with_structured_output(InterviewAnalysis)
        response: InterviewAnalysis = typing.cast(
            InterviewAnalysis, model.invoke(messages)
        )
        return response
