import logging
from typing import Callable

import numpy as np
import tabulate
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

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


def analyze_inner(
    identity_values: np.ndarray,
    couples_indices: np.ndarray,
    couples_id_list: list[str],
) -> str:
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

    all_dists = np.abs(
        identity_values[:, None, :] - identity_values[None, :, :]
    )  # shape (num_users, num_users, num_tests+2)
    assert all_dists.shape == (num_users, num_users, num_tests + 2), f"{all_dists.shape}"
    assert np.all((0 <= all_dists) & (all_dists <= 1)), f"{all_dists.shape}"

    couple_dists = all_dists[couples_indices[:, 0], couples_indices[:, 1], :]  # shape (num_couples, num_tests+2)
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

    def format_values(dists: list[float], format_value: Callable[[float], str]) -> str:
        dists_string = " ".join(format_value(s) for s in dists[:2]) + "|" + " ".join(format_value(s) for s in dists[2:])
        return f"[{dists_string}]"

    mean_value_std = np.mean(np.std(couple_values, axis=2)) * 100
    couples_report = f"Mean individual stddev: {mean_value_std:.4f}\n"
    mean_multipliers = np.reciprocal(np.mean(user_factors, axis=(0, 1)))
    couples_report += f"Average multipliers: {format_values(mean_multipliers, lambda x: f'{x:3.2f}')}\n"

    table_data = []
    for couple_id, dists, values, factors in zip(
        couples_id_list, couple_dists, couple_values, user_factors, strict=True
    ):
        assert dists.shape == (num_tests + 2,), f"{dists.shape}"
        assert values.shape == (2, num_tests + 2), f"{values.shape}"
        assert factors.shape == (2, num_tests + 2), f"{factors.shape}"
        multipliers = np.reciprocal(factors)

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
                f"{median_dist:2.0f}",
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
        ]
    )

    couples_report = analyze_inner(identity_values, couples_indices, couple_id_list)

    couples_report_path = config.output_dir / "couples_report.txt"
    with couples_report_path.open("w", encoding="utf-8") as f:
        f.write(couples_report + "\n")
    logging.info(f"Wrote couples report to {couples_report_path}")
