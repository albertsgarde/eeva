from fastapi import APIRouter, HTTPException
from pydantic import Field

from eeva.form import Form, FormId
from eeva.question import QuestionId
from eeva.utils import NetworkModel

from .database import Database


def find_missing_questions(database: Database, form: Form) -> list[QuestionId]:
    questions = database.questions()
    return [question_id for question_id in form.questions if not questions.exists(question_id)]


def create_router(database: Database) -> APIRouter:
    router = APIRouter()

    @router.post("/{form_id}")
    def create_form(form_id: FormId, form: Form):
        forms = database.forms()
        if forms.exists(form_id):
            raise HTTPException(status_code=409, detail=f"Form with id {form_id} already exists.")
        forms.create_with_id(form, form_id)
        return {"status": "created", "id": form_id}

    @router.get("/{form_id}")
    def get_form(form_id: FormId) -> Form:
        forms = database.forms()
        try:
            form = forms.get(form_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Form '{form_id}' not found") from e
        return form

    class GetFormResponse(NetworkModel):
        id: FormId = Field()
        form: Form = Field()

    @router.get("")
    def get_all_forms() -> list[GetFormResponse]:
        forms = database.forms()
        all_forms = forms.get_all()
        return [GetFormResponse(id=id, form=form) for id, form in all_forms]

    @router.delete("/{form_id}")
    def delete_form(form_id: FormId):
        forms = database.forms()
        if not forms.exists(form_id):
            raise HTTPException(status_code=404, detail=f"Form '{form_id}' not found")
        forms.delete(form_id)
        return {"status": "deleted"}

    @router.put("/{form_id}")
    def update_form(form_id: FormId, form: Form):
        forms = database.forms()
        missing_questions = find_missing_questions(database, form)
        if missing_questions != []:
            raise HTTPException(
                status_code=400,
                detail=f"Form contains questions that do not exist: {missing_questions}",
            )
        forms.upsert(form_id, form)
        return {"status": "upserted", "id": form_id}

    return router
