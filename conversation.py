from typing import Sequence
from pydantic import BaseModel, Field
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
    model: BaseChatModel = Field()

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
    role0_system_prompt: str
    role1_system_prompt: str
    role0_start_message: str

    def __init__(
        self,
        role0_system_prompt: str,
        role1_system_prompt: str,
        role0_start_message: str,
    ):
        self.role0_system_prompt = role0_system_prompt
        self.role1_system_prompt = role1_system_prompt
        self.role0_start_message = role0_start_message

    def create_conversation(self) -> "Conversation":
        return Conversation.initialize(self)


class Conversation(BaseModel):
    role0: Role = Field()
    role1: Role = Field()
    messages: list[Message] = Field()

    @staticmethod
    def initialize(
        config: ConversationConfig,
    ) -> "Conversation":
        role0 = Role(
            id=0,
            system_message=config.role0_system_prompt,
            model=chat_models.init_chat_model("gpt-4o-mini", model_provider="openai"),
        )
        role1 = Role(
            id=1,
            system_message=config.role1_system_prompt,
            model=chat_models.init_chat_model("gpt-4o-mini", model_provider="openai"),
        )
        messages = [Message(role_id=0, content=config.role0_start_message)]
        return Conversation(role0=role0, role1=role1, messages=messages)

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
        for message in self.messages:
            print(f"{message.role_id}: {message.content}")

    def analyze(
        self, role0_name: str, role1_name: str, system_prompt: str, prefix: str
    ) -> str:
        names = {0: role0_name, 1: role1_name}

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=prefix
                + "\n"
                + "\n".join(
                    [
                        f"{names[message.role_id]}: {message.content}"
                        for message in self.messages
                    ]
                )
            ),
        ]
        model = chat_models.init_chat_model("gpt-4o-mini", model_provider="openai")
        response = model.invoke(messages).content
        if isinstance(response, str):
            return response
        else:
            raise Exception("Multiple responses received")
