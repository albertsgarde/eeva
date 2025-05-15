import os
from pathlib import Path
from fastapi import FastAPI

from identity.utils import Prompts

app = FastAPI()

prompt_dir_str = os.getenv("PROMPT_DIR")
if prompt_dir_str is None:
    raise ValueError("PROMPT_DIR environment variable is not set.")
else:
    prompt_dir = Path(prompt_dir_str).resolve()
if not prompt_dir.exists():
    raise ValueError(f"Prompt directory {prompt_dir} does not exist.")

print(f"Prompt directory: {prompt_dir.absolute()}")

prompts = Prompts(dir=prompt_dir)


@app.get("/prompt/")
def get_prompt(id: str) -> str:
    """
    Get a prompt by its ID.
    """
    print(f"Fetching prompt with ID: {id}")

    return prompts.get(id)
