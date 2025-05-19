from pathlib import Path

from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from typing_extensions import Sequence

from .interview import Analyst, Interview, InterviewAnalysis, Interviewer, Message
from .utils import Model


class Character(BaseModel):
    name: str = Field()
    system_prompt: str = Field()
    model: Model = Field()

    def respond(self, messages: Sequence[Message]) -> str:
        chat = self.model.init_chat_model()
        response = chat.invoke(
            [
                SystemMessage(content=self.system_prompt),
                *[message.to_message() for message in messages],
            ]
        )
        return response.content


class InterviewSimulation(BaseModel):
    interview: Interview = Field()
    character: Character = Field()

    @staticmethod
    def initialize(
        interviewer: Interviewer, character: Character
    ) -> "InterviewSimulation":
        interview = Interview(interviewer=interviewer, messages=[])
        return InterviewSimulation(interview=interview, character=character)

    def advance(self, num_steps: int = 1) -> None:
        for _ in range(num_steps):
            character_message = self.character.respond(self.interview.messages)
            self.interview.respond(character_message)

    def analyze(self, analyzer: Analyst) -> InterviewAnalysis:
        return analyzer.analyze(self.interview, self.character.name)

    def print_messages(self) -> None:
        print(self.interview.pretty_format(self.character.name))

    def save_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json())

    @staticmethod
    def load_from_file(path: Path) -> "InterviewSimulation":
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return InterviewSimulation.model_validate_json(data)
