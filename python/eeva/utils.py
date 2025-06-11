import json
import os
from pathlib import Path

from langchain import chat_models
from pydantic import BaseModel, ConfigDict, Field, alias_generators


class NetworkModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,  # snake_case → camelCase
        populate_by_name=True,  # accept either name or alias on input
        frozen=True,  # make immutable
    )


def load_secrets(path: str | Path):
    secrets = json.load(open(path))
    for key, value in secrets.items():
        os.environ[key] = value


class Model(NetworkModel):
    model_name: str = Field()
    model_provider: str = Field()

    def init_chat_model(self):
        return chat_models.init_chat_model(self.model_name, model_provider=self.model_provider)
