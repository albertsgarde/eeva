import json
import os


def load_secrets(path: str = "secrets.json"):
    secrets = json.load(open(path))
    for key, value in secrets.items():
        os.environ[key] = value
