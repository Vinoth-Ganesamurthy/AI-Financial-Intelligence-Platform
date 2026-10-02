"""Collect historical US FRED vintages without evaluating predictions."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import pandas as pd
import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.fred_macro import (
    SERIES,
    build_us_macro_features,
    clean_vintage_observations,
    vintage_before,
)


INPUT = ROOT / "data/interim/research/sec_annual_features.csv"
CACHE = ROOT / "data/raw/research/fred"
FEATURE_OUTPUT = ROOT / "data/interim/research/us_macro_features.csv"
REPORTS = ROOT / "research/results/fred_macro"
API_URL = "https://api.stlouisfed.org/fred/series/observations"


def save_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def fetch_vintage(session, series_id, vintage, api_key):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{series_id}_{vintage}.json"
    metadata_path = CACHE / f"{series_id}_{vintage}_metadata.json"

    if path.exists():
        if not metadata_path.exists():
            raise ValueError("Cached response has no metadata.")

        raw = path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        if hashlib.sha256(raw).hexdigest() != metadata["sha256"]:
            raise ValueError("Cached response hash mismatch.")

        if (
            metadata["series_id"] != series_id
            or metadata["vintage_date"] != vintage
        ):
            raise ValueError("Cached response identity mismatch.")

        payload = json.loads(raw)
        status = "cached"
    else:
        # Pace new requests; cache reuse makes repeat runs inexpensive.
        time.sleep(0.6)

        try:
            response = session.get(
                API_URL,
                params={
                    "api_key": api_key,
                    "file_type": "json",
                    "series_id": series_id,
                    "realtime_start": vintage,
                    "realtime_end": vintage,
                    "observation_start": "2018-01-01",
                    "observation_end": vintage,
                    "sort_order": "asc",
                    "limit": 100000,
                    "units": "lin",
                    "output_type": 1,
                },
                timeout=(10, 40),
            )
        except requests.RequestException:
            # Do not print exception URLs containing the API key.
            raise RuntimeError("FRED connection failed.") from None

        if response.status_code != 200:
            raise RuntimeError(
                f"FRED returned HTTP {response.status_code}."
            )

        payload = response.json()
        clean_vintage_observations(payload, vintage)

        # Store the response only, never the authenticated request URL.
        raw = response.content
        metadata = {
            "series_id": series_id,
            "vintage_date": vintage,
            "source_url": API_URL,
            "observation_start": "2018-01-01",
            "observation_end": vintage,
            "retrieved_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

        temporary = path.with_suffix(".json.tmp")
        temporary.write_bytes(raw)
        temporary.replace(path)
        save_json(metadata_path, metadata)
        status = "downloaded"

    clean_vintage_observations(payload, vintage)
    return payload, metadata, status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Collect one date without writing the full feature dataset.",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY is missing.")

    observations = pd.read_csv(INPUT)
    keys = ["symbol", "observation_date"]

    observations["observation_date"] = pd.to_datetime(
        observations["observation_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    if observations.duplicated(keys).any():
        raise ValueError("Duplicate SEC observation keys.")

    dates = sorted(observations["observation_date"].unique())
    if args.smoke_test:
        dates = dates[:1]

    features = []
    provenance_rows = []
    manifest = []

    with requests.Session() as session:
        for number, observation_date in enumerate(dates, start=1):
            vintage = vintage_before(observation_date)
            payloads = {}
            statuses = []

            for series_id in SERIES.values():
                payload, metadata, status = fetch_vintage(
                    session, series_id, vintage, api_key
                )
                payloads[series_id] = payload
                manifest.append(metadata)
                statuses.append(status)

            snapshot = build_us_macro_features(
                payloads, observation_date
            )
            provenance = snapshot.pop("provenance")

            matching = observations.loc[
                observations["observation_date"].eq(observation_date)
            ]

            for _, observation in matching.iterrows():
                features.append({
                    "symbol": observation["symbol"],
                    "split": observation["split"],
                    "eligible": observation["eligible"],
                    **snapshot,
                })

            for component, fact in provenance.items():
                if fact is not None:
                    provenance_rows.append({
                        "observation_date": observation_date,
                        "component": component,
                        **fact,
                    })

            available = sum(
                snapshot[field] is not None
                for field in (
                    "inflation_rate",
                    "monetary_rate",
                    "gdp_growth_rate",
                    "unemployment_rate",
                )
            )

            print(
                f"[{number:02d}/{len(dates):02d}] "
                f"{observation_date} vintage={vintage} "
                f"available={available}/4 "
                f"downloaded={statuses.count('downloaded')} "
                f"cached={statuses.count('cached')}",
                flush=True,
            )

    data = pd.DataFrame(features)
    macro_columns = [
        "inflation_rate",
        "monetary_rate",
        "gdp_growth_rate",
        "unemployment_rate",
    ]

    print(f"\nGenerated feature rows: {len(data)}")
    print("Available values:")
    print(data[macro_columns].notna().sum().to_string())

    if args.smoke_test:
        print("\nSmoke test complete; full dataset not overwritten.")
        print("No prediction performance evaluated.")
        return

    if len(data) != len(observations):
        raise ValueError("Generated row count does not match input.")

    FEATURE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    data.to_csv(FEATURE_OUTPUT, index=False)
    pd.DataFrame(provenance_rows).to_csv(
        REPORTS / "provenance.csv", index=False
    )
    pd.DataFrame(manifest).to_csv(
        REPORTS / "raw_manifest.csv", index=False
    )

    coverage = data.groupby("split")[macro_columns].agg(
        lambda column: column.notna().sum()
    )
    coverage["observations"] = data.groupby("split").size()
    coverage.reset_index().to_csv(
        REPORTS / "coverage.csv", index=False
    )

    print(f"\nFeatures saved to: {FEATURE_OUTPUT}")
    print(f"Reports saved to: {REPORTS}")
    print("No prediction performance evaluated.")


if __name__ == "__main__":
    main()