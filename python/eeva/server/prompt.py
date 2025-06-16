from pathlib import Path

from fastapi import APIRouter
from pydantic import Field, ValidationError

from eeva.prompt import Prompt, PromptId
from eeva.server.database import Database
from eeva.utils import NetworkModel


class CreatePromptRequest(NetworkModel):
    prompt: Prompt = Field()


def load_default_prompts(database: Database, prompt_dir: Path):
    files = [file for file in prompt_dir.rglob("*.txt") if file.is_file()]
    ids: dict[PromptId, Path] = {}
    for file in files:
        file_name = file.name.removesuffix(".txt")
        try:
            id = PromptId(id=file_name)
        except ValidationError:
            print(f"Invalid prompt ID '{file_name}' found. File path: {file.absolute()}")
            continue
        if id in ids:
            print(f"Duplicate prompt ID '{id}'. Files: {ids[id].absolute()} and {file.absolute()}")
            continue
        ids[id] = file
    prompts = [Prompt(id=id, content=file.read_text()) for id, file in ids.items()]
    for prompt in prompts:
        if database.prompts().exists(prompt.id.id):
            print(f"Prompt with id {prompt.id} already exists in the database.")
            continue
        database.prompts().create_with_id(prompt, prompt.id.id)
        print(f"Loaded prompt: {prompt.id} - {prompt.content[:30]}...")


def create_router(database: Database) -> APIRouter:
    router = APIRouter()

    @router.post("")
    def create_prompt(request: CreatePromptRequest):
        prompts = database.prompts()
        prompt = request.prompt
        if prompts.get(prompt.id.id) is not None:
            raise ValueError(f"Prompt with id {prompt.id} already exists.")
        prompts.create_with_id(prompt, prompt.id.id)
        return {"status": "created", "id": prompt.id.id}

    @router.get("/{prompt_id}")
    def get_prompt(prompt_id: str):
        prompts = database.prompts()
        try:
            prompt = prompts.get(prompt_id)
        except ValueError:
            return {"error": f"Prompt '{prompt_id}' not found"}, 404
        return prompt

    @router.get("")
    def get_all_prompts():
        prompts = database.prompts()
        all_prompts = prompts.get_all()
        # Return as list of dicts with id and prompt content
        return [prompt.model_dump() for id, prompt in all_prompts]

    @router.delete("/{prompt_id}")
    def delete_prompt(prompt_id: str):
        prompts = database.prompts()
        # Check existence
        try:
            prompt = prompts.get(prompt_id)
        except ValueError:
            return {"error": f"Prompt '{prompt_id}' not found"}, 404
        cursor = prompts.connection.cursor()
        cursor.execute(f"DELETE FROM {prompts.table_name} WHERE id = ?", (prompt_id,))
        prompts.connection.commit()
        return {"status": "deleted", "prompt": prompt}

    @router.put("/{prompt_id}")
    def update_prompt(prompt_id: str, request: CreatePromptRequest):
        prompts = database.prompts()
        prompt = request.prompt
        try:
            prompts.get(prompt_id)
        except ValueError:
            return {"error": f"Prompt '{prompt_id}' not found"}, 404
        prompts.update(prompt_id, prompt)
        return {"status": "updated", "id": prompt_id}

    return router
