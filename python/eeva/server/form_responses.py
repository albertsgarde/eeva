from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from pydantic import Field

from eeva.form import FormId
from eeva.form_response import FormResponse, FormResponseId, QuestionResponse
from eeva.utils import NetworkModel

from .database import Database


def create_router(database: Database) -> APIRouter:
    router = APIRouter()

    class CreateFromFormRequest(NetworkModel):
        form_id: FormId = Field()
        subject_name: str = Field()

    class CreateFromFormResponse(NetworkModel):
        id: FormResponseId = Field()
        form_response: FormResponse = Field()

    @router.get("")
    def get_all_form_responses() -> dict[FormResponseId, FormResponse]:
        form_responses = database.form_responses()
        all_responses = form_responses.get_all()
        return {id: response for id, response in all_responses}

    @router.post("/create-from-form")
    def create_from_form(request: CreateFromFormRequest) -> CreateFromFormResponse:
        try:
            form = database.forms().get(request.form_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Form '{request.form_id}' not found") from e
        form_responses = database.form_responses()
        form_questions = []
        for question_id in form.questions:
            try:
                question = database.questions().get(question_id)
            except ValueError as e:
                raise HTTPException(status_code=500, detail=f"Question '{question_id}' not found") from e
            form_questions.append(QuestionResponse(question_id=question_id, question=question, response=""))

        form_response = FormResponse(
            form_id=request.form_id,
            responses=form_questions,
            subject_name=request.subject_name,
        )
        id = form_responses.create(form_response)
        return CreateFromFormResponse(id=id, form_response=form_response)

    @router.get("/{form_response_id}")
    def get_form_response(form_response_id: FormResponseId) -> FormResponse:
        form_responses = database.form_responses()
        try:
            form_response = form_responses.get(form_response_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Form response '{form_response_id}' not found") from e
        return form_response

    @router.put("/{form_response_id}")
    def update_form_response(form_response_id: FormResponseId, form_response: FormResponse):
        form_responses = database.form_responses()
        form_responses.upsert(form_response_id, form_response)
        return {"status": "updated", "id": form_response_id}

    @router.put("/{form_response_id}/question/{question_index}")
    def update_question_response(
        form_response_id: FormResponseId,
        question_index: Annotated[int, Field(ge=0)],
        question_response: QuestionResponse,
    ):
        form_responses = database.form_responses()

        try:
            form_response = form_responses.get(form_response_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Form response '{form_response_id}' not found") from e

        if question_index >= len(form_response.responses):
            raise HTTPException(status_code=400, detail="Invalid question index")

        new_responses = form_response.responses
        new_responses[question_index] = question_response
        new_form_response = FormResponse(
            form_id=form_response.form_id,
            responses=new_responses,
            subject_name=form_response.subject_name,
            subject_email=form_response.subject_email,
            created_at=form_response.created_at,
            modified_at=datetime.now(),
        )
        form_responses.update(form_response_id, new_form_response)

    @router.put("/{form_response_id}/subject-name")
    def update_subject_name(form_response_id: FormResponseId, subject_name: Annotated[str, Body()]):
        form_responses = database.form_responses()

        try:
            form_response = form_responses.get(form_response_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Form response '{form_response_id}' not found") from e

        new_form_response = FormResponse(
            form_id=form_response.form_id,
            responses=form_response.responses,
            subject_name=subject_name,
            subject_email=form_response.subject_email,
            created_at=form_response.created_at,
            modified_at=datetime.now(),
        )
        form_responses.update(form_response_id, new_form_response)
        return {"status": "updated", "id": form_response_id}

    return router
