import json
import logging
from typing import Callable

import numpy as np
import tabulate
from beartype import beartype
from jaxtyping import Float, UInt, jaxtyped
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from numpy import ndarray
from pydantic import BaseModel

from .analysis import AnalysisResultSet
from .types import CouplePairs, RunConfig, UserSet


def identity_histogram(analysis_results: AnalysisResultSet) -> Figure:
    """Create a histogram plot of identity values from analysis results.

    Returns a matplotlib figure that can be saved with fig.savefig() or displayed.
    """

    # Extract all identity values from analysis results
    identity_values = []
    for user_results in analysis_results.values():
        for result in user_results.analysis_results:
            identity_values.append(result.profile.identity)

    # Create histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(identity_values, bins=20, alpha=0.7, edgecolor="black")
    ax.set_xlabel("Identity Value")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Identity Values")
    ax.grid(True, alpha=0.3)

    return fig


class CouplesReport(BaseModel):
    mean_individual_stddev: float
    average_multipliers: list[float]
    median_distances: list[float]
    all_distances: list[list[float]]
    user_values: list[tuple[list[float], list[float]]]
    minimum_values: list[tuple[float, float]]
    median_values: list[tuple[float, float]]
    maximum_values: list[tuple[float, float]]
    user_multipliers: list[tuple[list[float], list[float]]]

    @jaxtyped(typechecker=beartype)
    @staticmethod
    def from_data(
        identity_values: Float[ndarray, "num_users num_tests"],
        couples_indices: UInt[ndarray, "num_couples 2"],
    ) -> "CouplesReport":
        (num_users, num_tests) = identity_values.shape
        (num_couples, _) = couples_indices.shape

        identity_values = np.concatenate(
            [
                np.median(identity_values, axis=1, keepdims=True),
                identity_values.mean(axis=1, keepdims=True),
                identity_values,
            ],
            axis=1,
        )
        assert identity_values.shape == (num_users, num_tests + 2), f"{identity_values.shape}"
        assert np.all((0 <= identity_values) & (identity_values <= 1)), f"{identity_values.shape}"

        assert couples_indices.shape == (num_couples, 2), f"{couples_indices.shape}"
        assert np.all((0 <= couples_indices) & (couples_indices < num_users)), f"{couples_indices.shape}"

        all_dists = np.abs(identity_values[:, None, :] - identity_values[None, :, :])
        assert all_dists.shape == (num_users, num_users, num_tests + 2), f"{all_dists.shape}"
        assert np.all((0 <= all_dists) & (all_dists <= 1)), f"{all_dists.shape}"

        couple_dists = all_dists[couples_indices[:, 0], couples_indices[:, 1], :]
        assert couple_dists.shape == (num_couples, num_tests + 2), f"{couple_dists.shape}"
        assert np.all((0 <= couple_dists) & (couple_dists <= 1)), f"{couple_dists.shape}"

        couple_all_dists = all_dists[couples_indices, :, :]
        assert couple_all_dists.shape == (num_couples, 2, num_users, num_tests + 2), f"{couple_all_dists.shape}"

        better_than_couple_exc = couple_all_dists < couple_dists[:, None, None, :]
        better_than_couple_inc = couple_all_dists <= couple_dists[:, None, None, :]
        assert better_than_couple_exc.shape == couple_all_dists.shape, f"{better_than_couple_exc.shape}"
        assert better_than_couple_inc.shape == couple_all_dists.shape, f"{better_than_couple_inc.shape}"

        user_steps_exc = better_than_couple_exc.sum(axis=2)
        user_steps_inc = better_than_couple_inc.sum(axis=2)
        assert user_steps_exc.shape == (num_couples, 2, num_tests + 2), f"{user_steps_exc.shape}"
        assert user_steps_inc.shape == (num_couples, 2, num_tests + 2), f"{user_steps_inc.shape}"
        assert np.all(user_steps_exc >= 0), f"{user_steps_exc.shape}"
        assert np.all(user_steps_inc >= 2), f"{user_steps_inc.shape}"

        user_steps = (user_steps_exc + user_steps_inc) / 2
        assert user_steps.shape == (num_couples, 2, num_tests + 2), f"{user_steps.shape}"
        assert np.all(user_steps >= 1), f"{user_steps.shape}"

        user_factors = user_steps / (float(num_users) / 2)
        assert user_factors.shape == (num_couples, 2, num_tests + 2), f"{user_factors.shape}"
        assert np.all(user_factors > 0), f"{user_factors.shape}"

        couple_values = identity_values[couples_indices, :]
        assert couple_values.shape == (num_couples, 2, num_tests + 2), f"{couple_values.shape}"

        mean_value_std = np.mean(np.std(couple_values[:, :, 2:], axis=2)) * 100
        mean_multipliers = np.reciprocal(np.mean(user_factors, axis=(0, 1)))
        user_multipliers = np.reciprocal(user_factors)

        min_values = np.min(couple_values, axis=2)
        median_values = np.median(couple_values, axis=2)
        max_values = np.max(couple_values, axis=2)

        return CouplesReport(
            mean_individual_stddev=mean_value_std,
            average_multipliers=mean_multipliers.tolist(),
            median_distances=np.median(couple_dists[:, 2:], axis=1).tolist(),
            all_distances=[d.tolist() for d in couple_dists],
            user_values=[(v1.tolist(), v2.tolist()) for v1, v2 in couple_values],
            minimum_values=[(m1, m2) for m1, m2 in min_values],
            median_values=[(m1, m2) for m1, m2 in median_values],
            maximum_values=[(m1, m2) for m1, m2 in max_values],
            user_multipliers=[(m1.tolist(), m2.tolist()) for m1, m2 in user_multipliers],
        )

    @staticmethod
    def format_values(dists: list[float], format_value: Callable[[float], str]) -> str:
        dists_string = " ".join(format_value(s) for s in dists[:2]) + "|" + " ".join(format_value(s) for s in dists[2:])
        return f"[{dists_string}]"

    def report(self, couples_id_list: list[str]) -> str:
        couples_report = f"Mean individual stddev: {self.mean_individual_stddev:.4f}\n"
        couples_report += (
            f"Average multipliers: {CouplesReport.format_values(self.average_multipliers, lambda x: f'{x:3.2f}')}\n"
        )

        table_data = []
        for couple_id, dists, (user1_values, user2_values), (user1_multipliers, user2_multipliers), (
            user1_min,
            user2_min,
        ), (user1_median, user2_median), (user1_max, user2_max) in zip(
            couples_id_list,
            self.all_distances,
            self.user_values,
            self.user_multipliers,
            self.minimum_values,
            self.median_values,
            self.maximum_values,
            strict=True,
        ):
            dist_str = CouplesReport.format_values([s * 100 for s in dists[:]], lambda x: f"{x:2.0f}")
            value_str1 = CouplesReport.format_values([v * 100 for v in user1_values], lambda x: f"{x:2.0f}")
            value_str2 = CouplesReport.format_values([v * 100 for v in user2_values], lambda x: f"{x:2.0f}")
            multipliers_str1 = CouplesReport.format_values([s for s in user1_multipliers], lambda x: f"{x:3.1f}")
            multipliers_str2 = CouplesReport.format_values([s for s in user2_multipliers], lambda x: f"{x:3.1f}")
            median_dist = np.median(dists[2:]) * 100

            table_data.append(
                [
                    couple_id,
                    f"{median_dist:2.0f}",
                    dist_str,
                    f"{value_str1}\n{value_str2}",
                    (
                        f"[{user1_min * 100:<2.0f} {user1_median * 100:<2.0f} {user1_max * 100:<2.0f}]\n"
                        f"[{user2_min * 100:<2.0f} {user2_median * 100:<2.0f} {user2_max * 100:<2.0f}]"
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
        return couples_report


def analyze(analysis_results: AnalysisResultSet, users: UserSet, couple_pairs: CouplePairs, config: RunConfig) -> None:
    """Compute and log statistics from the analysis results."""

    user_id_list = [
        (user_id, f"{users[user_id].response.first_name} {users[user_id].response.last_name}")
        for user_id in users.keys()
    ]

    identity_values = np.array(
        [[r.profile.identity for r in analysis_results[user_id].analysis_results] for user_id, _ in user_id_list]
    )
    assert identity_values.shape == (len(user_id_list), config.num_tests), f"{identity_values.shape}"

    user_id_to_index = {user_id: i for i, (user_id, _) in enumerate(user_id_list)}

    couple_id_list = [couple_id for couple_id in couple_pairs.keys()]

    couples_indices = np.array(
        [
            [user_id_to_index[couple_pairs[couple_id][0]], user_id_to_index[couple_pairs[couple_id][1]]]
            for couple_id in couple_id_list
        ],
        dtype=np.uint32,
    )

    couples_report = CouplesReport.from_data(identity_values, couples_indices)
    report_text = couples_report.report(couple_id_list)

    couples_report_json_path = config.output_dir / "couples_report.json"
    with couples_report_json_path.open("w", encoding="utf-8") as f:
        json.dump(couples_report.model_dump(), f, indent=2, ensure_ascii=False)
    couples_report_path = config.output_dir / "couples_report.txt"
    with couples_report_path.open("w", encoding="utf-8") as f:
        f.write(report_text + "\n")
    logging.info(f"Wrote couples report to {couples_report_path}")
