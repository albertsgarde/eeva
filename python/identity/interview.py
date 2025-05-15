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


class Character(BaseModel):
    name: str = Field()
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
        return Message(interviewer=False, content=response.content)


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
    character: Character = Field()
    interviewer: Interviewer = Field()
    messages: list[Message] = Field()

    @staticmethod
    def initialize(character: Character, interviewer: Interviewer) -> "Interview":
        return Interview(character=character, interviewer=interviewer, messages=[])

    def advance(self, num_steps: int = 1) -> None:
        for _ in range(num_steps):
            if len(self.messages) == 0 or not self.messages[-1].interviewer:
                response = self.interviewer.respond(self.messages)
            else:
                response = self.character.respond(self.messages)
            self.messages.append(response)

    def print_messages(self) -> None:
        role_names = {True: "Interviewer", False: self.character.name}
        max_name_length = max(len(name) for name in role_names.values())
        for message in self.messages:
            print(
                f"{f'{role_names[message.interviewer]}:':<{max_name_length + 1}} {message.content}"
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


class Analyst(BaseModel):
    system_prompt: str = Field()
    instruction: str = Field()
    model: Model = Field()

    def analyze(self, interview: Interview) -> InterviewAnalysis:
        role_names = {True: "Interviewer", False: interview.character.name}
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=self.instruction
                + "\n"
                + "\n".join(
                    [
                        f"{role_names[message.interviewer]}: {message.content}"
                        for message in interview.messages
                    ]
                )
            ),
        ]
        model = self.model.init_chat_model().with_structured_output(InterviewAnalysis)
        response: InterviewAnalysis = typing.cast(
            InterviewAnalysis, model.invoke(messages)
        )
        return response
