from pathlib import Path
import typing
from typing_extensions import Any, Sequence
from pydantic import BaseModel, Field, model_validator
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain import chat_models


class Message(BaseModel):
    role_id: int = Field()
    content: str = Field()

    def __repr__(self) -> str:
        return f"Message(role_id={self.role_id}, content={self.content})"

    def to_human_message(self) -> HumanMessage:
        return HumanMessage(content=self.content)

    def to_message(self, cur_role: int) -> BaseMessage:
        if cur_role == self.role_id:
            return self.to_human_message()
        else:
            return self.to_human_message()


class Role(BaseModel):
    id: int = Field()
    system_message: str = Field()
    model_name: str = Field()
    model_provider: str = Field()
    model: BaseChatModel = Field(exclude=True)

    @staticmethod
    def initialize(
        id: int,
        system_message: str,
        model_name: str,
        model_provider: str,
    ) -> "Role":
        return Role(
            id=id,
            system_message=system_message,
            model_name=model_name,
            model_provider=model_provider,
            model=chat_models.init_chat_model(
                model_name, model_provider=model_provider
            ),
        )

    @model_validator(mode="before")
    @classmethod
    def ensure_model(cls, data: Any) -> Any:
        data["model"] = chat_models.init_chat_model(
            data["model_name"], model_provider=data["model_provider"]
        )
        return data

    def create_history(self, messages: Sequence[Message]) -> Sequence[BaseMessage]:
        return [SystemMessage(content=self.system_message)] + [
            message.to_message(self.id) for message in messages
        ]

    def advance(self, messages: Sequence[Message]) -> Message:
        history = self.create_history(messages)
        response = self.model.invoke(history)
        if isinstance(response.content, str):
            return Message(role_id=self.id, content=response.content)
        else:
            raise Exception("Multiple responses received")


class ConversationConfig:
    role0_name: str
    role1_name: str
    role0_system_prompt: str
    role1_system_prompt: str
    role0_start_message: str

    def __init__(
        self,
        role0_system_prompt: str,
        role1_system_prompt: str,
        role0_start_message: str,
        role0_name: str = "0",
        role1_name: str = "1",
    ):
        self.role0_name = role0_name
        self.role1_name = role1_name
        self.role0_system_prompt = role0_system_prompt
        self.role1_system_prompt = role1_system_prompt
        self.role0_start_message = role0_start_message

    def create_conversation(self) -> "Conversation":
        return Conversation.initialize(self)


class ConversationAnalysis(BaseModel):
    "Analysis of the conversation"

    analysis: str = Field(
        description="Analysis of how the conversation scores on the metric"
    )
    score: float = Field(
        description="How the conversation scores on the metric from 0 to 1"
    )


class Conversation(BaseModel):
    role0: Role = Field()
    role1: Role = Field()
    role_names: dict[int, str] = Field()
    messages: list[Message] = Field()

    @staticmethod
    def initialize(
        config: ConversationConfig,
    ) -> "Conversation":
        role0 = Role.initialize(
            id=0,
            system_message=config.role0_system_prompt,
            model_name="gpt-4o-mini",
            model_provider="openai",
        )
        role1 = Role.initialize(
            id=1,
            system_message=config.role1_system_prompt,
            model_name="gpt-4o-mini",
            model_provider="openai",
        )
        messages = [Message(role_id=0, content=config.role0_start_message)]
        return Conversation(
            role0=role0,
            role1=role1,
            role_names={0: config.role0_name, 1: config.role1_name},
            messages=messages,
        )

    def advance(self, num_steps: int = 1) -> "Conversation":
        for _ in range(num_steps):
            if self.messages[-1].role_id == self.role0.id:
                message = self.role1.advance(self.messages)
            else:
                message = self.role0.advance(self.messages)
            self.messages.append(message)
        return self

    def get_messages(self) -> Sequence[Message]:
        return self.messages

    def print_messages(self) -> None:
        max_name_length = max(len(name) for name in self.role_names.values())
        for message in self.messages:
            print(
                f"{f'{self.role_names[message.role_id]}:':<{max_name_length + 1}} {message.content}"
            )

    def analyze(self, analyzer: "Analyzer") -> ConversationAnalysis:
        return analyzer.analyze(self)

    def save_to_file(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json())

    @staticmethod
    def load_from_file(path: Path) -> "Conversation":
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return Conversation.model_validate_json(data)


class Analyzer(BaseModel):
    system_prompt: str = Field()
    instruction: str = Field()

    def analyze(self, conversation: Conversation) -> ConversationAnalysis:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=self.instruction
                + "\n"
                + "\n".join(
                    [
                        f"{conversation.role_names[message.role_id]}: {message.content}"
                        for message in conversation.messages
                    ]
                )
            ),
        ]
        model = chat_models.init_chat_model(
            "gpt-4o-mini", model_provider="openai"
        ).with_structured_output(ConversationAnalysis)
        response: ConversationAnalysis = typing.cast(
            ConversationAnalysis, model.invoke(messages)
        )
        return response
