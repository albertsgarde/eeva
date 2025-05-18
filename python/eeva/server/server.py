import os
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from eeva.utils import Model, Prompts
from eeva.interview import Interview, Interviewer, Message
from eeva import utils

app = FastAPI()

secrets_path_str = os.getenv("SECRETS_PATH")
if secrets_path_str is None:
    raise ValueError("SECRETS_PATH environment variable is not set.")
else:
    secrets_path = Path(secrets_path_str).resolve()
if not secrets_path.exists():
    raise ValueError(f"Secrets file {secrets_path} does not exist.")

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

utils.load_secrets(secrets_path)

INTERVIEW_DIR = output_dir / "interviews"


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


class InterviewStore(BaseModel):
    interviews: dict[InterviewId, Interview] = Field()
    next_id: int = Field()

    @staticmethod
    def initialize() -> "InterviewStore":
        prev_ids = [
            file.name.removesuffix(".json")
            for file in INTERVIEW_DIR.iterdir()
            if file.name.removesuffix(".json").isnumeric()
        ]
        prev_max_id = -1 if not prev_ids else max(map(int, prev_ids))
        return InterviewStore(
            interviews={},
            next_id=prev_max_id + 1,
        )

    def _next_id(self) -> InterviewId:
        self.next_id += 1
        return InterviewId(id=self.next_id)

    def create_interview(
        self, create_interview_request: CreateInterviewRequest
    ) -> CreateInterviewResponse:
        initial_message = prompts.get(create_interview_request.start_message_id)
        model = Model(
            model_name="gpt-4o-mini",
            model_provider="openai",
        )
        interviewer = Interviewer(
            system_prompt=prompts.get(
                create_interview_request.interviewer_system_prompt_id
            ),
            model=model,
        )
        interview = Interview.initialize(interviewer, initial_message)
        interview_id = self._next_id()
        self.interviews[interview_id] = interview
        return CreateInterviewResponse(
            interview_id=interview_id, messages=interview.messages
        )


interview_store = InterviewStore.initialize()

prompts = Prompts(dir=prompt_dir)


@app.get("/api/prompt")
def get_prompt(id: str) -> str:
    """
    Get a prompt by its ID.
    """
    print(f"Fetching prompt with ID: {id}")

    return prompts.get(id)


@app.post("/api/interview")
def create_interview(request: CreateInterviewRequest) -> CreateInterviewResponse:
    return interview_store.create_interview(request)


class GetResponseRequest(BaseModel):
    message: str = Field()


@app.post("/api/interview/{interview_id}/respond")
def respond_to_interview(
    interview_id: int, request: GetResponseRequest
) -> list[Message]:
    """
    Respond to an interview with a message.
    """
    interview = interview_store.interviews[InterviewId(id=interview_id)]
    interview.respond(request.message)
    interview.save_to_file(output_dir / "interviews" / f"{interview_id}.json")
    return interview.messages


class SaveConversationRequest(BaseModel):
    conversation_name: str = Field()
    conversation: list[Message] = Field()


@app.post("/api/save_conversation")
def save_conversation(request: SaveConversationRequest) -> None:
    """
    Save the conversation to a file.
    """
    file_path = output_dir / "interviews" / (request.conversation_name + ".json")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as file:
        file.write(request.model_dump_json())
    return None
