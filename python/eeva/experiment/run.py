import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import tabulate
from langchain import chat_models
from matplotlib.figure import Figure
from pydantic import BaseModel, Field, RootModel

from .analyzer import AnalysisResult, Analyzer
from .types import (
    BaseData,
    CoupleId,
    CouplePairs,
    QuestionResponse,
    QuestionSet,
    User,
    UserId,
    UserSet,
)


class RunConfig(BaseModel):
    secrets_path: Path = Field()
    data_dir: Path = Field()
    output_dir: Path = Field()

    model: str = Field()
    model_provider: str = Field()
    reasoning_effort: str = Field()
    identity_prompt: str = Field()
    identity_extraction_prompt: str = Field()
    explicit_cot: bool = Field()

    num_tests: int = Field(gt=0)

    question_exclusion_sets: set[str] = Field()
    question_inclusion_sets: set[str] | None = Field()

    user_exclusion_sets: set[str] = Field()
    user_inclusion_sets: set[str] | None = Field()
    only_couples: bool = Field()
    answer_progress_minimum: float = Field(ge=0)
    num_answers_minimum: int = Field(ge=1)


async def generate_user_profiles(
    analyzer: Analyzer, user_id: UserId, user: User, num_profiles: int
) -> tuple[UserId, list[AnalysisResult]]:
    tasks = []
    for _ in range(num_profiles):
        tasks.append(asyncio.create_task(analyzer.analyze(user.response)))
    profiles = await asyncio.gather(*tasks)
    return (user_id, profiles)


# Create a dict user_id -> Profile for all users in user_data using their responses to run `analyze`
# Use asyncio to run analyze concurrently for all users
async def generate_profiles(
    analyzer: Analyzer, user_data: UserSet, num_profiles: int, user_subset: set[UserId] | None
) -> dict[UserId, list[AnalysisResult]]:
    if user_subset is not None:
        user_data = UserSet({k: v for k, v in user_data.items() if k in user_subset})

    profiles: dict[UserId, list[AnalysisResult]] = {}

    async def analyze_all_users() -> None:
        tasks = []
        for user_id, user in user_data.items():
            tasks.append(asyncio.create_task(generate_user_profiles(analyzer, user_id, user, num_profiles)))
        results: list[tuple[UserId, list[AnalysisResult]]] = await asyncio.gather(*tasks)
        for user_id, user_profiles in results:
            profiles[user_id] = user_profiles

    await analyze_all_users()
    return profiles


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


class AnalysisResultSet(RootModel):
    root: dict[UserId, list[AnalysisResult]]

    def __getitem__(self, item: UserId) -> list[AnalysisResult]:
        return self.root[item]

    def __iter__(self):
        return iter(self.root.items())

    def __contains__(self, item: UserId) -> bool:
        return item in self.root

    def __len__(self) -> int:
        return len(self.root)

    def items(self):
        return self.root.items()

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()


def identity_histogram(analysis_results: AnalysisResultSet) -> Figure:
    """Create a histogram plot of identity values from analysis results.

    Returns a matplotlib figure that can be saved with fig.savefig() or displayed.
    """

    # Extract all identity values from analysis results
    identity_values = []
    for user_results in analysis_results.values():
        for result in user_results:
            identity_values.append(result.profile.identity)

    # Create histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(identity_values, bins=20, alpha=0.7, edgecolor="black")
    ax.set_xlabel("Identity Value")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Identity Values")
    ax.grid(True, alpha=0.3)

    return fig


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
    result: AnalysisResultSet = AnalysisResultSet(
        asyncio.run(generate_profiles(analyzer, users, config.num_tests, user_subset=None))
    )
    time_ended = datetime.now()
    logging.info(
        f"Generated profiles for {len(users)} users in {(time_ended - time_started).total_seconds():.2f} seconds."
    )

    analysis_dump_path = config.output_dir / "analysis.json"
    with analysis_dump_path.open("w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)
    logging.info(f"Wrote analysis results to {analysis_dump_path}")

    fig = identity_histogram(result)
    histogram_path = config.output_dir / "identity_histogram.png"
    fig.savefig(histogram_path)
    logging.info(f"Wrote identity histogram to {histogram_path}")

    user_id_list = [
        (user_id, f"{users[user_id].response.first_name} {users[user_id].response.last_name}")
        for user_id in users.keys()
    ]

    user_id_to_index = {user_id: i for i, (user_id, _) in enumerate(user_id_list)}

    couple_id_list = [couple_id for couple_id in couple_pairs.keys()]

    couples_indices = np.array(
        [
            [user_id_to_index[couple_pairs[couple_id][0]], user_id_to_index[couple_pairs[couple_id][1]]]
            for couple_id in couple_id_list
        ]
    )
    assert couples_indices.shape == (len(couple_pairs), 2), f"{couples_indices.shape}"
    assert np.all((0 <= couples_indices) & (couples_indices < len(user_id_list))), f"{couples_indices.shape}"

    identity_values = np.array([[r.profile.identity for r in result[user_id]] for user_id, _ in user_id_list])

    identity_values = np.concatenate(
        [
            np.median(identity_values, axis=1, keepdims=True),
            identity_values.mean(axis=1, keepdims=True),
            identity_values,
        ],
        axis=1,
    )
    assert identity_values.shape == (len(user_id_list), config.num_tests + 2), f"{identity_values.shape}"
    assert np.all((0 <= identity_values) & (identity_values <= 1)), f"{identity_values.shape}"

    all_dists = np.abs(
        identity_values[:, None, :] - identity_values[None, :, :]
    )  # shape (num_users, num_users, num_tests+2)
    assert all_dists.shape == (len(user_id_list), len(user_id_list), config.num_tests + 2), f"{all_dists.shape}"
    assert np.all((0 <= all_dists) & (all_dists <= 1)), f"{all_dists.shape}"

    couple_dists = all_dists[couples_indices[:, 0], couples_indices[:, 1], :]  # shape (num_couples, num_tests+2)
    assert couple_dists.shape == (len(couple_pairs), config.num_tests + 2), f"{couple_dists.shape}"
    assert np.all((0 <= couple_dists) & (couple_dists <= 1)), f"{couple_dists.shape}"

    couple_all_dists = all_dists[couples_indices, :, :]
    assert couple_all_dists.shape == (len(couple_pairs), 2, len(user_id_list), config.num_tests + 2), (
        f"{couple_all_dists.shape}"
    )

    better_than_couple_exc = couple_all_dists < couple_dists[:, None, None, :]
    better_than_couple_inc = couple_all_dists <= couple_dists[:, None, None, :]
    assert better_than_couple_exc.shape == couple_all_dists.shape, f"{better_than_couple_exc.shape}"
    assert better_than_couple_inc.shape == couple_all_dists.shape, f"{better_than_couple_inc.shape}"

    user_steps_exc = better_than_couple_exc.sum(axis=2)
    user_steps_inc = better_than_couple_inc.sum(axis=2)
    assert user_steps_exc.shape == (len(couple_pairs), 2, config.num_tests + 2), f"{user_steps_exc.shape}"
    assert user_steps_inc.shape == (len(couple_pairs), 2, config.num_tests + 2), f"{user_steps_inc.shape}"
    assert np.all(user_steps_exc >= 0), f"{user_steps_exc.shape}"
    assert np.all(user_steps_inc >= 2), f"{user_steps_inc.shape}"

    user_steps = (user_steps_exc + user_steps_inc) / 2
    assert user_steps.shape == (len(couple_pairs), 2, config.num_tests + 2), f"{user_steps.shape}"
    assert np.all(user_steps >= 1), f"{user_steps.shape}"

    user_multipliers = len(user_id_list) / 2 / (user_steps)
    assert user_multipliers.shape == (len(couple_pairs), 2, config.num_tests + 2), f"{user_multipliers.shape}"
    assert np.all(user_multipliers > 0), f"{user_multipliers.shape}"

    couple_values = identity_values[couples_indices, :]
    assert couple_values.shape == (len(couple_pairs), 2, config.num_tests + 2), f"{couple_values.shape}"

    def format_values(dists: list[float], format_value: Callable[[float], str]) -> str:
        dists_string = " ".join(format_value(s) for s in dists[:2]) + "|" + " ".join(format_value(s) for s in dists[2:])
        return f"[{dists_string}]"

    mean_value_std = np.mean(np.std(couple_values, axis=2)) * 100
    couples_report = f"Mean individual stddev: {mean_value_std:.4f}\n"
    mean_multipliers = np.mean(user_multipliers, axis=(0, 1))
    couples_report += f"Mean multipliers: {format_values(mean_multipliers, lambda x: f'{x:3.2f}')}\n"

    table_data = []
    for couple_id, dists, values, multipliers in zip(
        couple_id_list, couple_dists, couple_values, user_multipliers, strict=True
    ):
        assert dists.shape == (config.num_tests + 2,), f"{dists.shape}"
        assert values.shape == (2, config.num_tests + 2), f"{values.shape}"
        assert multipliers.shape == (2, config.num_tests + 2), f"{multipliers.shape}"

        dist_str = format_values([s * 100 for s in dists[:]], lambda x: f"{x:2.0f}")
        value_str1 = format_values([v * 100 for v in values[0, :]], lambda x: f"{x:2.0f}")
        value_str2 = format_values([v * 100 for v in values[1, :]], lambda x: f"{x:2.0f}")
        multipliers_str1 = format_values([s for s in multipliers[0, :]], lambda x: f"{x:3.1f}")
        multipliers_str2 = format_values([s for s in multipliers[1, :]], lambda x: f"{x:3.1f}")
        min_values = np.min(values, axis=1) * 100
        median_values = np.median(values[:, 2:], axis=1) * 100
        max_values = np.max(values, axis=1) * 100
        median_dist = np.median(dists[2:]) * 100

        table_data.append(
            [
                couple_id,
                f"{int(median_dist):<2}",
                dist_str,
                f"{value_str1}\n{value_str2}",
                (
                    f"[{min_values[0]:<2.0f} {median_values[0]:<2.0f} {max_values[0]:<2.0f}]\n"
                    f"[{min_values[1]:<2.0f} {median_values[1]:<2.0f} {max_values[1]:<2.0f}]"
                ),
                f"{multipliers_str1}\n{multipliers_str2}",
            ]
        )
    couples_report += tabulate.tabulate(
        table_data,
        headers=[
            "Couple",
            "Median",
            "Dists",
            "Values",
            "Min, Median, Max",
            "Multipliers",
        ],
        tablefmt="plain",
    )
    couples_report_path = config.output_dir / "couples_report.txt"
    with couples_report_path.open("w", encoding="utf-8") as f:
        f.write(couples_report + "\n")
    logging.info(f"Wrote couples report to {couples_report_path}")
