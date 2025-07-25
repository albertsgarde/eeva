from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import Field, ValidationError

from eeva.prompt import Prompt, PromptId
from eeva.utils import NetworkModel

from .database import Database


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
    prompts = [(id, Prompt(content=file.read_text(encoding="utf-8"))) for id, file in ids.items()]
    for id, prompt in prompts:
        if database.prompts().exists(id.id):
            print(f"Prompt with id {id} already exists in the database.")
            continue
        database.prompts().create_with_id(prompt, id.id)
        print(f"Loaded prompt: {id} - {prompt.content[:30]}...")


class CreatePromptRequest(NetworkModel):
    id: PromptId = Field()
    prompt: Prompt = Field()


def create_router(database: Database) -> APIRouter:
    router = APIRouter()

    @router.post("")
    def create_prompt(request: CreatePromptRequest):
        prompts = database.prompts()
        id = request.id
        prompt = request.prompt
        if prompts.exists(id.id):
            raise ValueError(f"Prompt with id {id.id} already exists.")
        prompts.create_with_id(prompt, id.id)
        return {"status": "created", "id": id.id}

    @router.get("/{prompt_id}")
    def get_prompt(prompt_id: str):
        prompts = database.prompts()
        try:
            prompt = prompts.get(prompt_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found") from e
        return prompt

    @router.get("")
    def get_all_prompts():
        prompts = database.prompts()
        all_prompts = prompts.get_all()
        # Return as list of dicts with id and prompt content
        return [{"id": id, "prompt": prompt.model_dump()} for id, prompt in all_prompts]

    @router.delete("/{prompt_id}")
    def delete_prompt(prompt_id: str):
        prompts = database.prompts()
        # Check existence
        if not prompts.exists(prompt_id):
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
        prompts.delete(prompt_id)
        return {"status": "deleted"}

    @router.put("/{prompt_id}")
    def update_prompt(prompt_id: str, request: CreatePromptRequest):
        prompts = database.prompts()
        prompt = request.prompt
        if not prompts.exists(prompt_id):
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
        prompts.update(prompt_id, prompt)
        return {"status": "updated", "id": prompt_id}

    return router
