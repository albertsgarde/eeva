import asyncio
import os
import random
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query, Request
from pydantic import Field
from sse_starlette import EventSourceResponse

from eeva.interview import Interview, Interviewer, Message
from eeva.utils import Model, NetworkModel, Prompts

from .database import Database


class InterviewId(NetworkModel):
    id: int = Field()


class CreateInterviewRequest(NetworkModel):
    interviewer_system_prompt_id: str = Field()
    start_message_id: str = Field()
    subject_name: str = Field()


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
        interviewer = Interviewer(
            system_prompt=prompts.get(request.interviewer_system_prompt_id),
            model=model,
        )
        interview = Interview.initialize(interviewer, initial_message, request.subject_name)
        interview_id = InterviewId(id=database.interviews().create(interview))
        return CreateInterviewResponse(interview_id=interview_id, messages=interview.messages)

    @app.get("/api/interview")
    def get_interviews() -> list[tuple[int, Interview]]:
        """
        Get all interviews.
        """
        interview_store = database.interviews()
        return interview_store.get_all()

    @app.get("/api/interview/{interview_id}")
    def get_interview(interview_id: int) -> Interview:
        """
        Get an interview by its ID.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        if interview is None:
            raise ValueError(f"Interview with ID {interview_id} not found.")
        return interview

    @app.get("/api/interview/{interview_id}/stream")
    async def stream_interview(request: Request, interview_id: int) -> EventSourceResponse:
        """
        Stream messages from an interview.
        """

        queue = asyncio.Queue[Interview](maxsize=1)

        def handle_interview(interview: Interview) -> None:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(interview)

        key = random.randint(0, 2**63 - 1)
        database.interviews().watch(interview_id, key, handle_interview)

        async def interview_streamer():
            try:
                yield {"data": database.interviews().get(interview_id).model_dump_json()}
                while True:
                    if await request.is_disconnected():
                        break
                    interview = await queue.get()
                    yield {"data": interview.model_dump_json()}
            finally:
                database.interviews().unwatch(interview_id, key)

        return EventSourceResponse(interview_streamer())

    @app.post("/api/interview/{interview_id}/add_message")
    def add_message(interview_id: int, interviewer: bool, content: str) -> None:
        """
        Add a message to an interview.
        """

        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        if interview is None:
            raise ValueError(f"Interview with ID {interview_id} not found.")
        interview.add_message(interviewer, content)
        interview_store.update(interview_id, interview)

    class GetResponseRequest(NetworkModel):
        interviewer_system_prompt_id: str | None = Field(default=None)
        message_index: int | None = Field(default=None, ge=0)

    @app.post("/api/interview/{interview_id}/get_response")
    def get_response(interview_id: int, request: Annotated[GetResponseRequest, Query()]) -> Message:
        """
        Get a response from the interview.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        if interview is None:
            raise ValueError(f"Interview with ID {interview_id} not found.")

        if request.interviewer_system_prompt_id is None:
            interviewer = None
        else:
            interviewer = Interviewer(
                system_prompt=prompts.get(request.interviewer_system_prompt_id),
                model=model,
            )
        return interview.get_response(interviewer, request.message_index)

    class RespondRequest(NetworkModel):
        user_message: str = Field()

    @app.post("/api/interview/{interview_id}/respond")
    def respond_to_interview(interview_id: int, request: RespondRequest) -> list[Message]:
        """
        Respond to an interview with a message.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        interview.respond(request.user_message)
        interview_store.update(interview_id, interview)
        return interview.messages

    @app.delete("/api/interview")
    def delete_interviews() -> str:
        database.interviews().clear()
        return "OK"

    return app
