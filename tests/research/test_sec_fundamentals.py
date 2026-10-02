"""Test SEC filing cutoffs and annual-period selection."""

import pytest

from src.research.sec_fundamentals import (
    build_sec_annual_features,
    select_annual_fact,
)


def record(
    value,
    *,
    start="2019-07-01",
    end="2020-06-30",
    filed="2020-07-30",
    form="10-K",
):
    result = {
        "val": value,
        "end": end,
        "filed": filed,
        "form": form,
        "accn": f"filing-{filed}",
    }
    if start is not None:
        result["start"] = start
    return result


def payload(tags):
    return {
        "facts": {
            "us-gaap": {
                tag: {"units": {"USD": values}}
                for tag, values in tags.items()
            }
        }
    }


def test_future_restatement_is_excluded():
    facts = payload({
        "NetIncomeLoss": [
            record(100),
            record(999, filed="2021-07-29"),
        ]
    })
    selected = select_annual_fact(
        facts, ["NetIncomeLoss"], "2021-01-04"
    )
    assert selected["value"] == 100


def test_filing_day_is_conservatively_excluded():
    facts = payload({"NetIncomeLoss": [record(100)]})

    assert select_annual_fact(
        facts, ["NetIncomeLoss"], "2020-07-30"
    ) is None

    assert select_annual_fact(
        facts, ["NetIncomeLoss"], "2020-07-31"
    )["value"] == 100


def test_quarterly_amount_in_annual_filing_is_excluded():
    facts = payload({
        "NetIncomeLoss": [
            record(100),
            record(25, start="2020-04-01"),
        ]
    })
    assert select_annual_fact(
        facts, ["NetIncomeLoss"], "2021-01-04"
    )["value"] == 100


def test_latest_available_period_is_selected():
    facts = payload({
        "NetIncomeLoss": [
            record(
                80,
                start="2018-07-01",
                end="2019-06-30",
                filed="2019-07-30",
            ),
            record(100),
        ]
    })
    assert select_annual_fact(
        facts, ["NetIncomeLoss"], "2021-01-04"
    )["period_end"] == "2020-06-30"


def test_balance_sheet_fact_uses_instant():
    facts = payload({
        "Assets": [record(500, start=None)]
    })
    selected = select_annual_fact(
        facts, ["Assets"], "2021-01-04", instant=True
    )
    assert selected["value"] == 500


def test_annual_features_and_missing_fields():
    previous = {
        "start": "2018-07-01",
        "end": "2019-06-30",
        "filed": "2019-07-30",
    }
    facts = payload({
        "Revenues": [
            record(1000),
            record(800, **previous),
        ],
        "NetIncomeLoss": [
            record(100),
            record(80, **previous),
        ],
        "StockholdersEquity": [
            record(400, start=None)
        ],
        "Assets": [record(500, start=None)],
        "NetCashProvidedByUsedInOperatingActivities": [
            record(150)
        ],
        "PaymentsToAcquirePropertyPlantAndEquipment": [
            record(50)
        ],
    })

    result = build_sec_annual_features(facts, "2021-01-04")

    assert result["profit_margin"] == pytest.approx(10)
    assert result["return_on_equity"] == pytest.approx(25)
    assert result["return_on_assets"] == pytest.approx(20)
    assert result["revenue_growth"] == pytest.approx(25)
    assert result["earnings_growth"] == pytest.approx(25)
    assert result["free_cash_flow"] == 100
    assert result["forward_pe"] is None
    assert result["debt_to_equity"] is None


def test_missing_revenue_is_explicit_error():
    with pytest.raises(ValueError, match="annual revenue"):
        build_sec_annual_features(
            payload({}), "2021-01-04"
        )


def test_growth_handles_52_week_fiscal_calendar():
    facts = payload({
        "Revenues": [
            record(
                1000,
                start="2019-02-03",
                end="2020-02-01",
                filed="2020-03-01",
            ),
            record(
                800,
                start="2018-02-04",
                end="2019-02-02",
                filed="2019-03-01",
            ),
        ]
    })

    result = build_sec_annual_features(facts, "2021-01-04")
    assert result["revenue_growth"] == pytest.approx(25)


def test_amt_uses_total_revenue_not_contract_revenue():
    facts = payload({
        "Revenues": [record(11144200000)],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [
            record(756700000)
        ],
    })
    facts["cik"] = 1053507

    result = build_sec_annual_features(facts, "2021-01-04")

    assert result["total_revenue"] == 11144200000
    assert result["provenance"]["total_revenue"]["tag"] == "Revenues"
    
