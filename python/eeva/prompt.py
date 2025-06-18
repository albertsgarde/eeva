from pydantic import Field

from eeva.utils import ID_PATTERN, NetworkModel


class PromptId(NetworkModel):
    id: str = Field(pattern=ID_PATTERN)

    def __str__(self) -> str:
        return self.id


class Prompt(NetworkModel):
    content: str = Field()

    def __str__(self) -> str:
        return self.content
