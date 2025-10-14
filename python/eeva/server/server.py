import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain import chat_models

from . import analyzer
from .logging_config import get_logger, log_exception, setup_logging


def create_app() -> FastAPI:
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting Eeva application")

    app = FastAPI()

    # Global exception handler for unhandled errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log_exception(logger, f"Unhandled exception in {request.method} {request.url.path}", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "path": str(request.url.path)})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://eeva.site"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    data_path_str = os.getenv("DATA_PATH")
    if data_path_str is None:
        logger.error("DATA_PATH environment variable is not set")
        raise ValueError("DATA_PATH environment variable is not set.")
    else:
        data_path = Path(data_path_str).resolve()

    llm = chat_models.init_chat_model("gpt-5", model_provider="openai")

    @app.get("/ready")
    def ready() -> str:
        """
        Health check endpoint.
        """
        return "OK"

    app.include_router(analyzer.create_router(llm, data_path), prefix="/api/analyzer")

    return app
