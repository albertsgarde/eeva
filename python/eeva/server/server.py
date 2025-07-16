import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain import chat_models

from eeva.utils import Model

from . import analyzer, form_responses, forms, interviews, prompts, questions
from .database import Database


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    prompts.load_default_prompts(database, prompt_dir)

    llm = chat_models.init_chat_model("gpt-4o-mini", model_provider="openai")

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

    app.include_router(prompts.create_router(database), prefix="/api/prompts")
    app.include_router(interviews.create_router(database, model), prefix="/api/interviews")
    app.include_router(questions.create_router(database), prefix="/api/questions")
    app.include_router(forms.create_router(database), prefix="/api/forms")
    app.include_router(form_responses.create_router(database), prefix="/api/form-responses")
    app.include_router(analyzer.create_router(database, llm), prefix="/api/analyzer")

    return app
