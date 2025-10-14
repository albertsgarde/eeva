import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, alias_generators

ID_PATTERN = r"^[0-9a-zA-Z\-]+$"


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
