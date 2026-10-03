"""Synthetic tests; no research datasets or holdout results are used."""

import numpy as np
import pytest

from src.research.evaluation import (
    classification_metrics,
    paired_block_bootstrap,
)


def sample():
    # Two companies per round; every round contains all three classes.
    actual = np.tile(
        ["favourable", "neutral", "unfavourable"], 4
    )
    rounds = np.repeat(np.arange(6), 2)
    return actual, rounds


def test_perfect_classification():
    actual = ["favourable", "neutral", "unfavourable"]
    result = classification_metrics(actual, actual)

    assert result["macro_f1"] == 1.0
    assert result["balanced_accuracy"] == 1.0
    assert result["accuracy"] == 1.0
    assert result["confusion_matrix"] == [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]


def test_majority_prediction_has_low_macro_f1():
    result = classification_metrics(
        ["favourable", "neutral", "unfavourable"],
        ["favourable"] * 3,
    )

    assert result["accuracy"] == pytest.approx(1 / 3)
    assert result["macro_f1"] == pytest.approx(1 / 6)


@pytest.mark.parametrize(
    "actual,predicted",
    [
        ([], []),
        (["neutral"], []),
        (["invalid"], ["neutral"]),
        (["neutral"], ["invalid"]),
    ],
)
def test_invalid_labels_are_rejected(actual, predicted):
    with pytest.raises(ValueError):
        classification_metrics(actual, predicted)


def test_identical_models_have_zero_paired_difference():
    actual, rounds = sample()
    predicted = np.full(len(actual), "neutral")

    results = paired_block_bootstrap(
        actual,
        {"a": predicted, "b": predicted},
        rounds,
        comparisons=[("a", "b")],
        replicates=30,
    )
    difference = results[-1]

    assert difference["kind"] == "macro_f1_difference"
    assert difference["estimate"] == 0
    assert difference["lower_95"] == 0
    assert difference["upper_95"] == 0


def test_perfect_model_outperforms_constant_model():
    actual, rounds = sample()

    results = paired_block_bootstrap(
        actual,
        {
            "perfect": actual,
            "constant": np.full(len(actual), "neutral"),
        },
        rounds,
        comparisons=[("perfect", "constant")],
        replicates=30,
    )

    difference = results[-1]
    assert difference["estimate"] > 0
    assert difference["lower_95"] > 0
    assert difference["upper_95"] <= 1


def test_seed_makes_bootstrap_repeatable():
    actual, rounds = sample()
    predictions = {"constant": np.full(len(actual), "neutral")}

    first = paired_block_bootstrap(
        actual, predictions, rounds, replicates=30, seed=42
    )
    second = paired_block_bootstrap(
        actual, predictions, rounds, replicates=30, seed=42
    )

    assert first == second


def test_rounds_must_align_with_rows():
    actual, rounds = sample()

    with pytest.raises(ValueError, match="align"):
        paired_block_bootstrap(
            actual, {"perfect": actual}, rounds[:-1]
        )


def test_missing_round_is_rejected():
    actual, rounds = sample()
    rounds[rounds == 3] = 4

    with pytest.raises(ValueError, match="consecutive"):
        paired_block_bootstrap(actual, {"perfect": actual}, rounds)


def test_too_few_rounds_is_rejected():
    with pytest.raises(ValueError, match="Too few rounds"):
        paired_block_bootstrap(
            ["neutral", "favourable"],
            {"model": ["neutral", "favourable"]},
            [0, 1],
            block_length=3,
        )


def test_unknown_comparison_model_is_rejected():
    actual, rounds = sample()

    with pytest.raises(ValueError, match="Unknown"):
        paired_block_bootstrap(
            actual,
            {"perfect": actual},
            rounds,
            comparisons=[("perfect", "missing")],
        )


def test_companies_within_round_are_resampled_together():
    # Every round has one row of each class. Keeping the whole
    # round together preserves the constant model's macro-F1.
    actual = np.tile(
        ["favourable", "neutral", "unfavourable"], 6
    )
    rounds = np.repeat(np.arange(6), 3)

    results = paired_block_bootstrap(
        actual,
        {"constant": np.full(len(actual), "neutral")},
        rounds,
        replicates=30,
    )

    assert results[0]["lower_95"] == pytest.approx(1 / 6)
    assert results[0]["upper_95"] == pytest.approx(1 / 6)