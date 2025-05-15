import os
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

from identity.utils import Prompts

app = FastAPI()

output_dir_str = os.getenv("OUTPUT_DIR")
if output_dir_str is None:
    raise ValueError("OUTPUT_DIR environment variable is not set.")
else:
    output_dir = Path(output_dir_str).resolve()
if not output_dir.exists():
    raise ValueError(f"Output directory {output_dir} does not exist.")

prompt_dir_str = os.getenv("PROMPT_DIR")
if prompt_dir_str is None:
    raise ValueError("PROMPT_DIR environment variable is not set.")
else:
    prompt_dir = Path(prompt_dir_str).resolve()
if not prompt_dir.exists():
    raise ValueError(f"Prompt directory {prompt_dir} does not exist.")

prompts = Prompts(dir=prompt_dir)


@app.get("/api/prompt")
def get_prompt(id: str) -> str:
    """
    Get a prompt by its ID.
    """
    print(f"Fetching prompt with ID: {id}")

    return prompts.get(id)


class Message(BaseModel):
    host: bool
    name: str


class AddConversationRequest(BaseModel):
    conversation_name: str
    conversation: list[Message]


@app.post("/api/save_conversation")
def save_conversation(request: AddConversationRequest) -> None:
    """
    Save the conversation to a file.
    """
    file_path = output_dir / "interviews" / (request.conversation_name + ".json")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as file:
        file.write(request.model_dump_json())
    return None
