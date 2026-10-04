"""Cache SEC companyfacts and build audited US annual features."""

from datetime import datetime, timezone
import hashlib
from importlib.metadata import metadata
from importlib import metadata
import json
import os
from pathlib import Path
import sys
import time

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.sec_fundamentals import build_sec_annual_features


CIKS = {
    "MSFT": "0000789019",
    "JPM": "0000019617",
    "JNJ": "0000200406",
    "XOM": "0000034088",
    "PG": "0000080424",
    "AMZN": "0001018724",
    "CAT": "0000018230",
    "NEE": "0000753308",
    "AMT": "0001053507",
    "GOOGL": "0001652044",
}

FEATURES = [
    "total_revenue",
    "profit_margin",
    "return_on_equity",
    "return_on_assets",
    "revenue_growth",
    "earnings_growth",
    "free_cash_flow",
    "forward_pe",
    "debt_to_equity",
]


def load_companyfacts(symbol, cik, directory, session):
    path = directory / f"{symbol}_companyfacts.json"
    metadata_path = directory / f"{symbol}_metadata.json"

    if not path.exists():
        response = session.get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()

        if int(payload.get("cik", -1)) != int(cik):
            raise ValueError(
                f"Unexpected company identifier for {symbol}."
            )

        path.write_bytes(response.content)

        metadata_path.write_text(
            json.dumps(
                {
                    "symbol": symbol,
                    "cik": cik,
                    "entity_name": payload.get("entityName"),
                    "retrieved_at_utc": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "source_url": response.url,
                    "sha256": hashlib.sha256(
                        response.content
                    ).hexdigest(),
                    "hash_origin": "download",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        time.sleep(0.5)

    content = path.read_bytes()
    payload = json.loads(content)

    if int(payload.get("cik", -1)) != int(cik):
        raise ValueError(
            f"Cached company identifier mismatch: {symbol}."
        )

    if not metadata_path.exists():
        raise ValueError(
            f"Missing raw-data metadata for {symbol}."
        )

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )
    actual_hash = hashlib.sha256(content).hexdigest()

    if "sha256" not in metadata:
        metadata["sha256"] = actual_hash
        metadata["hash_recorded_at_utc"] = datetime.now(
            timezone.utc
        ).isoformat()
        metadata["hash_origin"] = "existing_cache_baseline"
        metadata["entity_name"] = payload.get("entityName")
        metadata["source_url"] = metadata.get(
            "source_url", metadata.get("url")
        )

        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
    elif metadata["sha256"] != actual_hash:
        raise ValueError(
            f"Raw-data hash mismatch for {symbol}."
        )

    return payload, metadata

def main():
    user_agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not user_agent or "@" not in user_agent:
        raise ValueError(
            "Set SEC_USER_AGENT to your research name and contact email."
        )

    universe = pd.read_csv(ROOT / "research/company_universe.csv")
    us = universe.loc[universe["market"].eq("United States")]

    if len(us) != 10 or set(us["symbol"]) != set(CIKS):
        raise ValueError("US universe does not match the declared CIK mapping.")

    targets = pd.read_csv(
        ROOT / "data/interim/research/targets.csv",
        parse_dates=["observation_date"],
    )
    targets = targets.loc[targets["market"].eq("United States")]

    raw_directory = ROOT / "data/raw/research/sec"
    raw_directory.mkdir(parents=True, exist_ok=True)
    destination = ROOT / "data/interim/research"
    destination.mkdir(parents=True, exist_ok=True)
    reports = ROOT / "research/results/sec_fundamentals"
    reports.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
    })

    records = []
    provenance_rows = []
    manifests = []
    failures = []

    try:
        for company in us.itertuples(index=False):
            symbol = company.symbol
            observations = targets.loc[targets["symbol"].eq(symbol)]

            try:
                payload, metadata = load_companyfacts(
                    symbol, CIKS[symbol], raw_directory, session
                )
                manifests.append(metadata)
            except Exception as error:
                failures.append({
                    "symbol": symbol,
                    "observation_date": "",
                    "stage": "collection",
                    "error": str(error),
                })
                print(f"{symbol}: collection failed: {error}")
                continue

            successful = 0

            for row in observations.itertuples(index=False):
                date_text = row.observation_date.date().isoformat()
                record = {
                    "symbol": symbol,
                    "observation_date": date_text,
                    "split": row.split,
                    "eligible": row.eligible,
                }

                try:
                    features = build_sec_annual_features(
                        payload, date_text
                    )
                    provenance = features.pop("provenance")

                    filing_dates = [
                        fact["filed"]
                        for fact in provenance.values()
                        if fact is not None
                    ]
                    if any(filed >= date_text for filed in filing_dates):
                        raise ValueError("Filing cutoff violation.")

                    features["latest_component_filing_date"] = max(
                        filing_dates
                    )
                    record.update(features)
                    record["fundamental_available"] = True
                    successful += 1

                    for field, fact in provenance.items():
                        if fact is not None:
                            provenance_rows.append({
                                "symbol": symbol,
                                "observation_date": date_text,
                                "field": field,
                                **fact,
                            })

                except Exception as error:
                    record.update({field: None for field in FEATURES})
                    record["fundamental_available"] = False
                    failures.append({
                        "symbol": symbol,
                        "observation_date": date_text,
                        "stage": "feature_selection",
                        "error": str(error),
                    })

                records.append(record)

            print(
                f"{symbol:<8} {payload.get('entityName')} "
                f"available={successful}/{len(observations)}"
            )
    finally:
        session.close()

    dataset = pd.DataFrame(records)
    failure_report = pd.DataFrame(
        failures,
        columns=["symbol", "observation_date", "stage", "error"],
    )
    failure_report.to_csv(reports / "failures.csv", index=False)
    pd.DataFrame(manifests).to_csv(
        reports / "raw_manifest.csv", index=False
    )

    if dataset.empty:
        raise RuntimeError("No SEC feature rows generated.")

    dataset.to_csv(
        destination / "sec_annual_features.csv", index=False
    )
    pd.DataFrame(provenance_rows).to_csv(
        destination / "sec_feature_provenance.csv", index=False
    )

    # Coverage only: no target returns or predictive test metrics.
    summary_rows = []
    for (symbol, split), group in dataset.groupby(
        ["symbol", "split"], sort=False
    ):
        summary_rows.append({
            "symbol": symbol,
            "split": split,
            "observations": len(group),
            "available": int(group["fundamental_available"].sum()),
            **{
                f"{field}_available": int(group[field].notna().sum())
                for field in FEATURES
            },
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(reports / "coverage.csv", index=False)

    print("\nCoverage summary")
    print(summary.to_string(index=False))
    print(f"\nGenerated rows: {len(dataset)}")
    print(f"Failures: {len(failures)}")
    print(f"Reports: {reports}")

    if len(dataset) != len(targets) or failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()