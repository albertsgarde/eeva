import os
from pathlib import Path

from fastapi import FastAPI

from eeva.prompt import Prompts
from eeva.server import interview
from eeva.utils import Model

from .database import Database


def create_app() -> FastAPI:
    app = FastAPI()

    prompt_dir_str = os.getenv("PROMPT_DIR")
    if prompt_dir_str is None:
        raise ValueError("PROMPT_DIR environment variable is not set.")
    else:
        prompt_dir = Path(prompt_dir_str).resolve()
    if not prompt_dir.exists():
        raise ValueError(f"Prompt directory {prompt_dir} does not exist.")

    database_path_str = os.getenv("DATABASE_PATH")
    if database_path_str is None:
        raise ValueError("DATABASE_PATH environment variable is not set.")
    else:
        database_path = Path(database_path_str).resolve()

    database = Database(database_path)

    prompts = Prompts(dir=prompt_dir)

    model = Model(
        model_name="gpt-4o-mini",
        model_provider="openai",
    )

    @app.get("/ready")
    def ready() -> str:
        """
        Health check endpoint.
        """
        return "OK"

    app.include_router(interview.create_router(database, prompts, model), prefix="/api/interview")

    return app
