"""Generate research figures from preserved holdout results."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "research/results/holdout_analysis"
OUTPUT = ROOT / "research/figures"

PRICE_NAMES = {
    "majority_class": "Majority class",
    "technical_only": "Technical rules",
    "historical_only": "Historical rules",
    "equal_weight_price": "Equal-weight rules",
    "logistic_regression": "Logistic regression",
    "random_forest": "Random forest",
}

US_NAMES = {
    "majority_class": "Majority class",
    "logistic_regression_price_only": "LR: price",
    "logistic_regression_price_plus_fundamentals": "LR: price + fundamentals",
    "logistic_regression_price_plus_fundamentals_plus_macro":
        "LR: price + fundamentals + macro",
    "random_forest_price_only": "RF: price",
    "random_forest_price_plus_fundamentals": "RF: price + fundamentals",
    "random_forest_price_plus_fundamentals_plus_macro":
        "RF: price + fundamentals + macro",
}


def save(fig, name):
    fig.savefig(OUTPUT / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def model_chart(metrics, experiment, names, title, filename):
    rows = metrics.loc[
        metrics["experiment"].eq(experiment)
        & metrics["scope"].eq("overall")
    ].sort_values("macro_f1")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    labels = rows["model"].map(names)
    bars = ax.barh(labels, rows["macro_f1"], color="#2563eb")

    ax.bar_label(bars, fmt="%.3f", padding=5, fontsize=10)
    ax.set_xlim(0, 0.55)
    ax.set_xlabel("Macro-F1")
    ax.set_title(title, loc="left", fontweight="bold", pad=15)
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, filename)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })

    metrics = pd.read_csv(INPUT / "metrics.csv")
    intervals = pd.read_csv(INPUT / "bootstrap_intervals.csv")
    confusion = pd.read_csv(INPUT / "confusion_matrices.csv")

    model_chart(
        metrics, "price", PRICE_NAMES,
        "Four-market price models — 2025 holdout (490 observations)",
        "holdout_price_models",
    )
    model_chart(
        metrics, "us", US_NAMES,
        "US feature comparisons — 2025 holdout (120 observations)",
        "holdout_us_models",
    )

    # Draw interval endpoints directly: percentile intervals need not
    # contain the original point estimate.
    differences = intervals.loc[
        intervals["kind"].eq("macro_f1_difference")
    ].copy()

    labels = {
        "random_forest minus majority_class":
            "Price RF − majority",
        "random_forest_price_plus_fundamentals minus random_forest_price_only":
            "US RF: add fundamentals",
        "random_forest_price_plus_fundamentals_plus_macro minus random_forest_price_plus_fundamentals":
            "US RF: add macro",
    }

    fig, ax = plt.subplots(figsize=(10, 4.5))
    positions = np.arange(len(differences))

    ax.hlines(
        positions,
        differences["lower_95"],
        differences["upper_95"],
        color="#2563eb",
        linewidth=3,
    )
    ax.scatter(
        differences["estimate"], positions,
        color="#0f172a", s=65, zorder=3,
    )
    ax.set_yticks(positions, differences["name"].map(labels))
    ax.invert_yaxis()
    ax.axvline(0, color="#64748b", linestyle="--", linewidth=1)
    ax.set_xlabel("Macro-F1 difference; approximate 95% interval")
    ax.set_title(
        "Paired comparisons — three-round block bootstrap",
        loc="left", fontweight="bold", pad=15,
    )
    ax.grid(axis="x", alpha=0.2)
    fig.text(
        0.5, 0.01,
        "2,000 replicates · seed 42 · only 12–13 holdout rounds",
        ha="center", fontsize=9, color="#475569",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "holdout_comparison_intervals")

    markets = [
        "India", "United States", "Singapore", "Australia"
    ]
    models = ["majority_class", "random_forest", "historical_only"]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(markets))
    width = 0.24

    for number, model in enumerate(models):
        values = []
        for market in markets:
            row = metrics.loc[
                metrics["experiment"].eq("price")
                & metrics["scope"].eq(market)
                & metrics["model"].eq(model)
            ]
            if len(row) != 1:
                raise ValueError(f"Missing market result: {market}/{model}")
            values.append(float(row["macro_f1"].iloc[0]))

        ax.bar(
            x + (number - 1) * width,
            values,
            width,
            label=PRICE_NAMES[model],
        )

    ax.set_xticks(x, markets)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Macro-F1")
    ax.set_title(
        "Market breakdown — pooled price-model evaluation",
        loc="left", fontweight="bold", pad=15,
    )
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "holdout_market_breakdown")

    class_labels = ["favourable", "neutral", "unfavourable"]
    panels = [
        ("price", "random_forest", "Pooled price random forest"),
        (
            "us",
            "random_forest_price_plus_fundamentals",
            "US random forest + fundamentals",
        ),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, (experiment, model, title) in zip(axes, panels):
        rows = confusion.loc[
            confusion["experiment"].eq(experiment)
            & confusion["scope"].eq("overall")
            & confusion["model"].eq(model)
        ]

        matrix = rows.pivot(
            index="actual", columns="predicted", values="count"
        ).reindex(index=class_labels, columns=class_labels)

        if matrix.isna().any().any():
            raise ValueError("Incomplete confusion matrix.")

        values = matrix.to_numpy(dtype=int)
        ax.imshow(values, cmap="Blues")
        for i in range(3):
            for j in range(3):
                ax.text(
                    j, i, str(values[i, j]),
                    ha="center", va="center",
                    color=(
                        "white"
                        if values[i, j] > values.max() / 2
                        else "#0f172a"
                    ),
                )

        ax.set_xticks(range(3), class_labels, rotation=30, ha="right")
        ax.set_yticks(range(3), class_labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(title, fontsize=11)

    fig.suptitle(
        "Validation-selected models — 2025 confusion matrices",
        fontweight="bold",
    )
    fig.tight_layout()
    save(fig, "holdout_confusion_matrices")

    print("Saved five figures in PNG and PDF formats:")
    for path in sorted(OUTPUT.glob("holdout_*.png")):
        print(path)


if __name__ == "__main__":
    main()