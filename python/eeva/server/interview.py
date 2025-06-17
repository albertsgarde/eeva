import asyncio
import random
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import Field
from sse_starlette import EventSourceResponse

from eeva.prompt import Prompt

from ..interview import Interview, Interviewer, Message
from ..utils import Model, NetworkModel
from .database import Database
from .prompt import PromptId


class InterviewId(NetworkModel):
    id: int = Field()


class CreateInterviewRequest(NetworkModel):
    interviewer_system_prompt_id: PromptId = Field()
    start_message_id: PromptId = Field()
    subject_name: str = Field()


class CreateInterviewResponse(NetworkModel):
    interview_id: InterviewId = Field()
    messages: list[Message] = Field()


def create_router(database: Database, model: Model) -> APIRouter:
    router = APIRouter()

    @router.post("")
    def create_interview(request: CreateInterviewRequest) -> CreateInterviewResponse:
        initial_message = database.prompts().get(request.start_message_id.id)
        interviewer = Interviewer(
            system_prompt=database.prompts().get(request.interviewer_system_prompt_id.id),
            model=model,
        )
        interview = Interview.initialize(interviewer, initial_message, request.subject_name)
        interview_id = InterviewId(id=database.interviews().create(interview))
        return CreateInterviewResponse(interview_id=interview_id, messages=interview.messages)

    @router.get("")
    def get_interviews() -> list[tuple[int, Interview]]:
        """
        Get all interviews.
        """
        interview_store = database.interviews()
        return interview_store.get_all()

    @router.get("/{interview_id}")
    def get_interview(interview_id: int) -> Interview:
        """
        Get an interview by its ID.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        if interview is None:
            raise ValueError(f"Interview with ID {interview_id} not found.")
        return interview

    @router.get("/{interview_id}/stream")
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

    @router.post("/{interview_id}/add_message")
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
        interviewer_system_prompt_id: PromptId | None = Field(default=None)
        message_index: int | None = Field(default=None, ge=0)

    @router.get("/{interview_id}/get_response")
    def get_response(interview_id: int, request: Annotated[GetResponseRequest, Query()]) -> Message:
        """
        Get a response from the interview.
        """
        interview_store = database.interviews()
        prompts = database.prompts()
        interview = interview_store.get(interview_id)
        if interview is None:
            raise ValueError(f"Interview with ID {interview_id} not found.")

        if request.interviewer_system_prompt_id is None:
            interviewer = None
        else:
            interviewer = Interviewer(
                system_prompt=prompts.get(request.interviewer_system_prompt_id.id),
                model=model,
            )
        return interview.get_response(interviewer, request.message_index)

    class GetResponseCustomPromptRequest(NetworkModel):
        prompt: str = Field()
        message_index: int | None = Field(default=None, ge=0)

    @router.get("/{interview_id}/get_response_custom_prompt")
    def get_response_custom_prompt(interview_id: int, request: GetResponseCustomPromptRequest) -> Message:
        """
        Get a response from the interview using a custom system prompt.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        if interview is None:
            raise ValueError(f"Interview with ID {interview_id} not found.")

        interviewer = Interviewer(
            system_prompt=Prompt(content=request.prompt),
            model=model,
        )
        return interview.get_response(interviewer, request.message_index)

    class RespondRequest(NetworkModel):
        user_message: str = Field()

    @router.post("/{interview_id}/respond")
    def respond_to_interview(interview_id: int, request: RespondRequest) -> list[Message]:
        """
        Respond to an interview with a message.
        """
        interview_store = database.interviews()
        interview = interview_store.get(interview_id)
        interview.respond(request.user_message)
        interview_store.update(interview_id, interview)
        return interview.messages

    @router.delete("")
    def delete_interviews() -> str:
        database.interviews().clear()
        return "OK"

    return router
