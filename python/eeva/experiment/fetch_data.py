import json
import typing
from pathlib import Path
from typing import Any

import supabase
from supabase.lib.client_options import SyncClientOptions

from .types import (
    BaseData,
    LanguageCode,
    ProdProfile,
    Question,
    QuestionId,
    QuestionResponse,
    QuestionSet,
    QuestionTranslation,
    Response,
    User,
    UserId,
    UserSet,
)


def update_data(secrets_path: Path, output_path: Path):
    with secrets_path.open("r", encoding="utf-8") as f:
        secrets = json.load(f)

    sb_client = supabase.create_client(
        secrets["PROD_SUPABASE_URL_BASE"],
        secrets["PROD_SUPABASE_SERVICE_ROLE_KEY"],
        options=SyncClientOptions(auto_refresh_token=False, persist_session=False),
    )

    raw_answers = sb_client.table("user_answers").select("user_id, question_id, answer_text").execute().data
    user_answer_lists: dict[UserId, dict[str, str]] = {}
    for ans in raw_answers:
        user_answer_lists.setdefault(UserId.model_validate(ans["user_id"]), {})[ans["question_id"]] = ans["answer_text"]

    raw_user_data = (
        sb_client.table("profiles").select("user_id,first_name,last_name,hidden,profile,language_code").execute().data
    )
    users: dict[UserId, dict[str, Any]] = {}
    for user in raw_user_data:
        user_id: UserId = UserId.model_validate(user["user_id"])
        if user["hidden"] or user_id not in user_answer_lists:
            continue
        users[user_id] = {
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "profile": ProdProfile.model_validate(user["profile"]) if user["profile"] else None,
            "answers": user_answer_lists[user_id],
            "language_code": user["language_code"],
            "hidden": user["hidden"],
        }

    raw_question_data = sb_client.table("questions").select("id,active").execute().data
    question_translations = (
        sb_client.table("question_translations").select("question_id,language_code,text,examples").execute().data
    )

    questions: QuestionSet = QuestionSet(
        {question["id"]: Question(translations={}, active=question["active"]) for question in raw_question_data}
    )
    for translation in question_translations:
        question_id = QuestionId(translation["question_id"])
        language_code = LanguageCode(translation["language_code"])
        if question_id in questions:
            questions[question_id].translations[language_code] = QuestionTranslation(
                text=translation["text"],
                examples=translation["examples"],
            )
        else:
            raise ValueError(f"Missing question {question_id}")

    # Add fallback entries for missing translations
    all_question_ids = set(qid for qid in questions.keys())
    all_language_codes = set(translation["language_code"] for translation in question_translations)

    for question_id in all_question_ids:
        for language_code in all_language_codes:
            if question_id not in questions:
                raise ValueError(f"Missing question {question_id}")
            translations = questions[question_id].translations
            if language_code not in translations:
                # Try fallback to "en", then "da"
                for fallback_lang in ["en", "da"]:
                    if fallback_lang in translations:
                        translations[language_code] = translations[fallback_lang]
                        break
                else:
                    raise ValueError(
                        f"Missing translation for question {question_id} in language {language_code}, "
                        "and no fallback found."
                    )

    user_dict: dict[UserId, User] = {}
    # Build user data using the question text lookup
    for user_id, user in users.items():
        answers = user["answers"]
        responses = {}
        for question_id, answer_text in answers.items():
            question_data = questions[question_id].translations[user["language_code"]]
            responses[question_id] = {
                "question": question_data.text,
                "response": answer_text,
            }
        response = Response(
            first_name=user["first_name"],
            last_name=user["last_name"] if user["last_name"] else "",
            responses=typing.cast(dict[str, QuestionResponse], responses),
        )
        user_dict[user_id] = User(
            response=response,
            prod_profile=user["profile"],
            language_code=user["language_code"],
            hidden=user["hidden"],
        )

    user_data = UserSet(user_dict)

    base_data = BaseData(users=user_data, questions=questions)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            base_data.model_dump(),
            f,
            indent=2,
        )


if __name__ == "__main__":
    update_data(
        secrets_path=Path("secrets.json").resolve(),
        output_path=Path("data/base_data.json").resolve(),
    )
