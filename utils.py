import json
import os
from pathlib import Path

from pydantic import BaseModel, Field
from langchain import chat_models


def load_secrets(path: str = "secrets.json"):
    secrets = json.load(open(path))
    for key, value in secrets.items():
        os.environ[key] = value


def output_dir() -> Path:
    return Path("output")


class Model(BaseModel):
    model_name: str = Field()
    model_provider: str = Field()

    def init_chat_model(self):
        return chat_models.init_chat_model(
            self.model_name, model_provider=self.model_provider
        )


class Prompts:
    dir: Path

    def __init__(self, dir: str | Path):
        if isinstance(dir, str):
            dir = Path(dir)
        self.dir = dir

    def get(self, prompt_name: str) -> str:
        with open(self.dir / f"{prompt_name}.txt", "r") as file:
            return file.read()
