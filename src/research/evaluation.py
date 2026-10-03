"""Metrics and paired round-block bootstrap for frozen predictions."""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
)


LABELS = ["favourable", "neutral", "unfavourable"]


def classification_metrics(actual, predicted):
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)

    if (
        actual.ndim != 1
        or predicted.ndim != 1
        or len(actual) == 0
        or len(actual) != len(predicted)
    ):
        raise ValueError("Labels must be nonempty aligned vectors.")

    if not np.isin(actual, LABELS).all():
        raise ValueError("Invalid actual labels.")

    if not np.isin(predicted, LABELS).all():
        raise ValueError("Invalid predicted labels.")

    return {
        "macro_f1": float(f1_score(
            actual,
            predicted,
            labels=LABELS,
            average="macro",
            zero_division=0,
        )),
        "balanced_accuracy": float(
            balanced_accuracy_score(actual, predicted)
        ),
        "accuracy": float(accuracy_score(actual, predicted)),
        "confusion_matrix": confusion_matrix(
            actual, predicted, labels=LABELS
        ).tolist(),
    }


def paired_block_bootstrap(
    actual,
    predictions,
    rounds,
    *,
    comparisons=(),
    replicates=2000,
    block_length=3,
    seed=42,
):
    """
    Resample contiguous round blocks, keeping companies together.

    Each comparison is (candidate, reference). The same sampled
    rows are used for every model within each replicate.
    """
    actual = np.asarray(actual)
    rounds = np.asarray(rounds)

    if rounds.ndim != 1 or len(rounds) != len(actual):
        raise ValueError("Rounds must align with actual labels.")

    if not predictions:
        raise ValueError("At least one prediction vector is required.")

    if replicates < 1 or block_length < 1:
        raise ValueError("Replicates and block length must be positive.")

    predictions = {
        name: np.asarray(values)
        for name, values in predictions.items()
    }

    for values in predictions.values():
        classification_metrics(actual, values)

    unique_rounds = np.unique(rounds)
    if not np.array_equal(
        unique_rounds, np.arange(len(unique_rounds))
    ):
        raise ValueError("Rounds must be consecutive integers from zero.")

    if len(unique_rounds) < block_length:
        raise ValueError("Too few rounds for the selected block length.")

    for candidate, reference in comparisons:
        if candidate not in predictions or reference not in predictions:
            raise ValueError("Unknown comparison model.")

    row_groups = [
        np.flatnonzero(rounds == number)
        for number in unique_rounds
    ]

    rng = np.random.default_rng(seed)
    draws = {
        name: np.empty(replicates)
        for name in predictions
    }

    for replicate in range(replicates):
        sampled_rounds = []

        while len(sampled_rounds) < len(unique_rounds):
            start = int(rng.integers(
                0, len(unique_rounds) - block_length + 1
            ))
            sampled_rounds.extend(
                range(start, start + block_length)
            )

        sampled_rounds = sampled_rounds[:len(unique_rounds)]
        indices = np.concatenate([
            row_groups[number] for number in sampled_rounds
        ])

        for name, values in predictions.items():
            draws[name][replicate] = f1_score(
                actual[indices],
                values[indices],
                labels=LABELS,
                average="macro",
                zero_division=0,
            )

    results = []

    def append_interval(kind, name, estimate, values):
        lower, upper = np.quantile(values, [0.025, 0.975])
        results.append({
            "kind": kind,
            "name": name,
            "estimate": float(estimate),
            "lower_95": float(lower),
            "upper_95": float(upper),
            "replicates": replicates,
            "block_length": block_length,
            "seed": seed,
        })

    point_scores = {
        name: classification_metrics(
            actual, values
        )["macro_f1"]
        for name, values in predictions.items()
    }

    for name in predictions:
        append_interval(
            "macro_f1",
            name,
            point_scores[name],
            draws[name],
        )

    for candidate, reference in comparisons:
        append_interval(
            "macro_f1_difference",
            f"{candidate} minus {reference}",
            point_scores[candidate] - point_scores[reference],
            draws[candidate] - draws[reference],
        )

    return results