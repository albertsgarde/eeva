import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from eeva.interview import Interview, Interviewer, Message
from eeva.utils import Model, Prompts

from .database import Database


class NetworkModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,  # snake_case → camelCase
        populate_by_name=True,  # accept either name or alias on input
        frozen=True,  # make immutable
    )


class InterviewId(NetworkModel):
    id: int = Field()


class CreateInterviewRequest(NetworkModel):
    interviewer_system_prompt_id: str = Field()
    start_message_id: str = Field()


class CreateInterviewResponse(NetworkModel):
    interview_id: InterviewId = Field()
    messages: list[Message] = Field()


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

    @app.get("/ready")
    def ready() -> str:
        """
        Health check endpoint.
        """
        return "OK"

    @app.get("/api/prompt")
    def get_prompt(id: str) -> str:
        """
        Get a prompt by its ID.
        """
        print(f"Fetching prompt with ID: {id}")

        return prompts.get(id)

    @app.post("/api/interview")
    def create_interview(request: CreateInterviewRequest) -> CreateInterviewResponse:
        initial_message = prompts.get(request.start_message_id)
        model = Model(
            model_name="gpt-4o-mini",
            model_provider="openai",
        )
        interviewer = Interviewer(
            system_prompt=prompts.get(request.interviewer_system_prompt_id),
            model=model,
        )
        interview = Interview.initialize(interviewer, initial_message)
        interview_id = InterviewId(id=database.interviews().create(interview))
        return CreateInterviewResponse(interview_id=interview_id, messages=interview.messages)

    class GetResponseRequest(BaseModel):
        user_message: str = Field()

    @app.post("/api/interview/{interview_id}/respond")
    def respond_to_interview(interview_id: int, request: GetResponseRequest) -> list[Message]:
        """
        Respond to an interview with a message.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        interview.respond(request.user_message)
        interview_store.update(interview_id, interview)
        return interview.messages

    return app
