import json
import os
from pathlib import Path


def load_secrets(path: str = "secrets.json"):
    secrets = json.load(open(path))
    for key, value in secrets.items():
        os.environ[key] = value


def output_dir() -> Path:
    return Path("output")
