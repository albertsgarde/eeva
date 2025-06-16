from pydantic import Field

from eeva.utils import NetworkModel

PROMPT_ID_PATTERN = r"^[0-9a-zA-Z\-]+$"


class PromptId(NetworkModel):
    id: str = Field(pattern=PROMPT_ID_PATTERN)

    def __str__(self) -> str:
        return self.id


class Prompt(NetworkModel):
    id: PromptId = Field()
    content: str = Field()

    def __str__(self) -> str:
        return self.content
