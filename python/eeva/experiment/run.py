import asyncio
import json
import logging
import os
from datetime import datetime

import numpy as np
from langchain import chat_models

from . import analysis, stats
from .analysis import AnalysisResultSet, Analyzer
from .types import (
    BaseData,
    CoupleId,
    CouplePairs,
    QuestionResponse,
    QuestionSet,
    RunConfig,
    UserId,
    UserSet,
)


def filter_questions(questions: QuestionSet, config: RunConfig) -> QuestionSet:
    exclusion_set = set().union(
        *(
            (config.data_dir / "question_sets" / f"{set_name}.txt").read_text(encoding="utf-8").splitlines()
            for set_name in config.question_exclusion_sets
        )
    )
    inclusion_set = (
        set().union(
            *(
                (config.data_dir / "question_sets" / f"{set_name}.txt").read_text(encoding="utf-8").splitlines()
                for set_name in config.question_inclusion_sets
            )
        )
        if config.question_inclusion_sets
        else None
    )

    return QuestionSet(
        {
            q_id: q
            for q_id, q in questions.items()
            if q_id not in exclusion_set and (inclusion_set is None or q_id in inclusion_set)
        }
    )


def word_count(text: str) -> int:
    return len(text.strip().split())


def answer_progress(response: QuestionResponse, examples: list[str]) -> float:
    if not examples:
        raise ValueError("No examples provided for progress calculation.")
    response_length = word_count(response.response)
    examples_length_max = np.max([word_count(example) for example in examples])
    return response_length / examples_length_max


def filter_users(
    users: UserSet, questions: QuestionSet, couple_pairs: CouplePairs, config: RunConfig
) -> tuple[UserSet, CouplePairs]:
    exclusion_set: set[UserId] = {
        UserId(line.strip())
        for set_name in config.user_exclusion_sets
        for line in (config.data_dir / "user_sets" / f"{set_name}.txt").read_text(encoding="utf-8").splitlines()
    }
    inclusion_set: set[UserId] | None = (
        {
            UserId(line.strip())
            for set_name in config.user_inclusion_sets
            for line in (config.data_dir / "user_sets" / f"{set_name}.txt").read_text(encoding="utf-8").splitlines()
        }
        if config.user_inclusion_sets
        else None
    )

    users = UserSet(
        {
            user_id: user
            for user_id, user in users.items()
            if user_id not in exclusion_set and (inclusion_set is None or user_id in inclusion_set)
        }
    )
    for user in users.values():
        language_code = user.language_code
        user.response.responses = {
            q_id: resp
            for q_id, resp in user.response.responses.items()
            if q_id in questions
            and answer_progress(resp, questions[q_id].translations[language_code].examples)
            >= config.answer_progress_minimum
        }
    users = UserSet(
        {user_id: user for user_id, user in users.items() if len(user.response.responses) >= config.num_answers_minimum}
    )
    couple_pairs = CouplePairs(
        {couple_id: (id1, id2) for couple_id, (id1, id2) in couple_pairs.items() if id1 in users and id2 in users}
    )
    couple_users = {user_id for couple in couple_pairs.values() for user_id in couple}
    users = UserSet(
        {user_id: user for user_id, user in users.items() if not config.only_couples or user_id in couple_users}
    )
    return users, couple_pairs


def run(config: RunConfig) -> None:
    with config.secrets_path.open("r") as f:
        secrets = json.load(f)
        if secrets["OPENAI_API_KEY"]:
            os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
        if secrets["ANTHROPIC_API_KEY"]:
            os.environ["ANTHROPIC_API_KEY"] = secrets["ANTHROPIC_API_KEY"]
        if secrets["GEMINI_API_KEY"]:
            os.environ["GEMINI_API_KEY"] = secrets["GEMINI_API_KEY"]

    llm = chat_models.init_chat_model(
        config.model, model_provider=config.model_provider, reasoning_effort=config.reasoning_effort
    )

    with (config.data_dir / "couples.json").open("r", encoding="utf-8") as f:
        couple_pairs_raw: CouplePairs = {
            CoupleId(couple_id): (UserId(id1), UserId(id2)) for couple_id, (id1, id2) in json.load(f).items()
        }

    with (config.data_dir / "base_data.json").open("r", encoding="utf-8") as f:
        base_data = BaseData.model_validate_json(f.read())

        questions = filter_questions(base_data.questions, config)
        logging.info(f"Loaded {len(questions)} questions after filtering from {len(base_data.questions)} total.")

        users, couple_pairs = filter_users(base_data.users, questions, couple_pairs_raw, config)
        logging.info(f"Loaded {len(users)} users after filtering from {len(base_data.users)} total.")
        removed_users = set(base_data.users.keys()) - set(users.keys())
        for removed_user in removed_users:
            logging.debug(f"Removed user {removed_user} due to filtering.")

        logging.info(f"Loaded {len(couple_pairs)} couples from {len(couple_pairs_raw)} total.")

    analyzer = Analyzer(
        identity_prompt=config.identity_prompt,
        identity_extraction_prompt=config.identity_extraction_prompt,
        explicit_cot=config.explicit_cot,
        llm=llm,
    )

    with (config.output_dir / "identity_prompt.txt").open("w", encoding="utf-8") as f:
        f.write(config.identity_prompt)

    with (config.output_dir / "identity_extraction_prompt.txt").open("w", encoding="utf-8") as f:
        f.write(config.identity_extraction_prompt)

    logging.info(f"Generating {config.num_tests} profiles per user for {len(users)} users...")
    # Synchronously get current time
    time_started = datetime.now()
    result: AnalysisResultSet = asyncio.run(
        analysis.generate_profiles(analyzer, users, config.num_tests, user_subset=None)
    )

    time_ended = datetime.now()
    logging.info(
        f"Generated profiles for {len(users)} users in {(time_ended - time_started).total_seconds():.2f} seconds."
    )

    analysis_dump_path = config.output_dir / "analysis.json"
    with analysis_dump_path.open("w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)
    logging.info(f"Wrote analysis results to {analysis_dump_path}")

    fig = stats.identity_histogram(result)
    histogram_path = config.output_dir / "identity_histogram.png"
    fig.savefig(histogram_path)
    logging.info(f"Wrote identity histogram to {histogram_path}")

    stats.analyze(result, users, couple_pairs, config)
