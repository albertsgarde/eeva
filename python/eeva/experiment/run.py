import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

import numpy as np
import tabulate
from langchain import chat_models
from pydantic import BaseModel, Field, RootModel

from .analyzer import AnalysisResult, Analyzer
from .types import Couple, CoupleId, User, UserId


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
    analyzer: Analyzer, user_data: dict[UserId, User], num_profiles: int, user_subset: set[UserId] | None
) -> dict[UserId, list[AnalysisResult]]:
    if user_subset is not None:
        user_data = {k: v for k, v in user_data.items() if k in user_subset}

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

    with (config.data_dir / "user_data.json").open("r", encoding="utf-8") as f:

        class UserSetDeserializer(RootModel[dict[UserId, User]]):
            pass

        user_data = UserSetDeserializer.model_validate_json(f.read()).root

    with (config.data_dir / "couples.json").open("r", encoding="utf-8") as f:
        couple_pairs_raw: dict[CoupleId, list[UserId]] = json.load(f)
        couple_pairs: dict[CoupleId, Couple] = {k: (v[0], v[1]) for k, v in couple_pairs_raw.items()}

    analyzer = Analyzer(
        identity_prompt=config.identity_prompt,
        identity_extraction_prompt=config.identity_extraction_prompt,
        explicit_cot=config.explicit_cot,
        llm=llm,
    )

    logging.info(f"Generating {config.num_tests} profiles per user for {len(user_data)} users...")
    # Synchronously get current time
    time_started = datetime.now()
    result: dict[UserId, list[AnalysisResult]] = asyncio.run(
        generate_profiles(analyzer, user_data, config.num_tests, user_subset=None)
    )
    time_ended = datetime.now()
    logging.info(
        f"Generated profiles for {len(user_data)} users in {(time_ended - time_started).total_seconds():.2f} seconds."
    )

    analysis_dump = {key: [r.model_dump() for r in value] for key, value in result.items()}
    analysis_dump_path = config.output_dir / "analysis.json"
    with analysis_dump_path.open("w", encoding="utf-8") as f:
        json.dump(analysis_dump, f, indent=2)
    logging.info(f"Wrote analysis results to {analysis_dump_path}")

    user_id_list = [
        (user_id, f"{user_data[user_id].response.first_name} {user_data[user_id].response.last_name}")
        for user_id in user_data.keys()
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
