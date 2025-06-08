import typing
from datetime import datetime
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing_extensions import Sequence

from .utils import Model, NetworkModel


class Message(NetworkModel):
    interviewer: bool = Field()
    content: str = Field()
    timestamp: str = Field()

    def to_message(self) -> BaseMessage:
        return HumanMessage(content=self.content)


class Interviewer(NetworkModel):
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
        return Message(interviewer=True, content=response.content, timestamp=datetime.now().isoformat())


class Interview(NetworkModel):
    interviewer: Interviewer = Field()
    messages: list[Message] = Field()
    subject_name: str = Field()

    @staticmethod
    def initialize(interviewer: Interviewer, initial_message: str, subject_name: str) -> "Interview":
        return Interview(
            interviewer=interviewer,
            messages=[Message(interviewer=True, content=initial_message, timestamp=datetime.now().isoformat())],
            subject_name=subject_name,
        )

    def respond(self, subject_message: str) -> Message:
        self.messages.append(Message(interviewer=False, content=subject_message, timestamp=datetime.now().isoformat()))
        response = self.interviewer.respond(self.messages)
        self.messages.append(response)
        return response

    def pretty_format(self) -> str:
        role_names = {True: "Interviewer", False: self.subject_name}
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

    analysis: str = Field(description="Analysis of how the interview scores on the metric")
    score: float = Field(description="How the interview scores on the metric from 0 to 1")

    def pretty_format(self) -> str:
        return f"Score: {self.score:.2f}\nAnalysis: {self.analysis}"


class Analyst(BaseModel):
    system_prompt: str = Field()
    instruction: str = Field()
    model: Model = Field()

    def analyze(self, interview: Interview) -> InterviewAnalysis:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self.instruction + "\n" + interview.pretty_format()),
        ]
        model = self.model.init_chat_model().with_structured_output(InterviewAnalysis)
        response: InterviewAnalysis = typing.cast(InterviewAnalysis, model.invoke(messages))
        return response
