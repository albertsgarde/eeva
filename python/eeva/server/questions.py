from fastapi import APIRouter, HTTPException
from pydantic import Field

from eeva.question import Question, QuestionId
from eeva.utils import NetworkModel

from .database import Database


def create_router(database: Database) -> APIRouter:
    router = APIRouter()

    @router.post("/{question_id}")
    def create_question(question_id: QuestionId, question: Question):
        questions = database.questions()
        if questions.exists(question_id):
            raise HTTPException(status_code=409, detail=f"Question with id {question_id} already exists.")
        questions.create_with_id(question, question_id)
        return {"status": "created", "id": question_id}

    @router.post("")
    def create_questions(request: dict[QuestionId, Question]):
        questions = database.questions()
        for question_id in request.keys():
            if questions.exists(question_id):
                raise HTTPException(status_code=409, detail=f"Question with id {question_id} already exists.")
        for id, question in request.items():
            questions.create_with_id(question, id)
        return {"status": "created"}

    @router.get("/{question_id}")
    def get_question(question_id: QuestionId):
        questions = database.questions()
        try:
            question = questions.get(question_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Question '{question_id}' not found") from e
        return question

    class GetQuestionResponse(NetworkModel):
        id: str = Field()
        question: Question = Field()

    @router.get("")
    def get_all_questions():
        questions = database.questions()
        all_questions = questions.get_all()
        # Return as list of dicts with id and question content
        return [GetQuestionResponse(id=id, question=question) for id, question in all_questions]

    @router.delete("/{question_id}")
    def delete_question(question_id: QuestionId):
        questions = database.questions()
        if not questions.exists(question_id):
            raise HTTPException(status_code=404, detail=f"Question '{question_id}' not found")
        questions.delete(question_id)
        return {"status": "deleted"}

    @router.put("")
    def update_questions(request: dict[QuestionId, Question]):
        questions = database.questions()
        for question_id, question in request.items():
            questions.upsert(question_id, question)
        return {"status": "upserted"}

    @router.put("/{question_id}")
    def update_question(question_id: QuestionId, question: Question):
        questions = database.questions()
        questions.upsert(question_id, question)
        return {"status": "upserted", "id": question_id}

    return router
