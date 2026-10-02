"""Select annual SEC financial facts available before an observation."""

from datetime import date
import math


ANNUAL_FORMS = {"10-K", "10-K/A"}


def _date(value):
    return date.fromisoformat(str(value)[:10])


def select_annual_fact(
    companyfacts,
    tags,
    observation_date,
    *,
    unit="USD",
    period_end=None,
    instant=False,
    preceding_period_end=None,
):
    """
    Select an annual fact filed before the observation date.

    Filing-day records are excluded because companyfacts provides
    dates rather than intraday availability timestamps.

    preceding_period_end selects a comparable prior fiscal year,
    including companies using 52/53-week fiscal calendars.
    """
    cutoff = _date(observation_date)
    required_end = (
        _date(period_end)
        if period_end is not None
        else None
    )
    reference_end = (
        _date(preceding_period_end)
        if preceding_period_end is not None
        else None
    )

    facts = companyfacts.get("facts", {}).get("us-gaap", {})
    candidates = []

    for priority, tag in enumerate(tags):
        records = (
            facts.get(tag, {})
            .get("units", {})
            .get(unit, [])
        )

        for record in records:
            if record.get("form") not in ANNUAL_FORMS:
                continue

            try:
                filed = _date(record["filed"])
                end = _date(record["end"])
                value = float(record["val"])
            except (KeyError, TypeError, ValueError):
                continue

            if (
                filed >= cutoff
                or end > cutoff
                or not math.isfinite(value)
            ):
                continue

            if required_end is not None and end != required_end:
                continue

            if reference_end is not None:
                gap = (reference_end - end).days
                if not 330 <= gap <= 380:
                    continue

            if instant:
                if record.get("start"):
                    continue
            else:
                try:
                    start = _date(record["start"])
                except (KeyError, TypeError, ValueError):
                    continue

                duration = (end - start).days
                if not 330 <= duration <= 380:
                    continue

            candidates.append(
                {
                    "tag": tag,
                    "value": value,
                    "period_end": end.isoformat(),
                    "filed": filed.isoformat(),
                    "accession": record.get("accn"),
                    "start": record.get("start"),
                    "unit": unit,
                    "_priority": priority,
                }
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item["period_end"],
            item["filed"],
            -item["_priority"],
            item["accession"] or "",
        )
    )

    selected = candidates[-1].copy()
    selected.pop("_priority")
    return selected


def ratio(numerator, denominator, *, percentage=False):
    """Return a finite ratio, or None when unavailable."""
    if numerator is None or denominator is None:
        return None

    if denominator == 0:
        return None

    value = numerator / denominator

    if percentage:
        value *= 100

    return value if math.isfinite(value) else None


def build_sec_annual_features(companyfacts, observation_date):
    """
    Build annual features using facts filed before the observation.

    ProfitLoss is a consolidated-income fallback. ROE requires
    parent shareholder income and parent shareholder equity.
    Earnings growth compares the same income tag across years.
    """
    provenance = {}

    revenue_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ]

    if str(companyfacts.get("cik", "")).lstrip("0") == "1053507":
        revenue_tags = ["Revenues"]

    revenue = select_annual_fact(
        companyfacts,
        revenue_tags,
        observation_date,
    )

    if revenue is None:
        raise ValueError(
            "No annual revenue available before observation."
        )

    end = revenue["period_end"]
    provenance["total_revenue"] = revenue

    def fetch_fact(field, tags, *, instant=False):
        fact = select_annual_fact(
            companyfacts,
            tags,
            observation_date,
            period_end=end,
            instant=instant,
        )
        provenance[field] = fact
        return fact

    def value(fact):
        return fact["value"] if fact is not None else None

    parent_income = fetch_fact(
        "parent_net_income",
        ["NetIncomeLoss"],
    )

    income_fact = parent_income
    if income_fact is None:
        income_fact = fetch_fact(
            "consolidated_profit",
            ["ProfitLoss"],
        )

    provenance["net_income"] = income_fact
    income = value(income_fact)

    equity = value(fetch_fact(
        "equity",
        ["StockholdersEquity"],
        instant=True,
    ))

    assets = value(fetch_fact(
        "assets",
        ["Assets"],
        instant=True,
    ))

    operating_cash = value(fetch_fact(
        "operating_cash_flow",
        ["NetCashProvidedByUsedInOperatingActivities"],
    ))

    capex = value(fetch_fact(
        "capital_expenditure",
        ["PaymentsToAcquirePropertyPlantAndEquipment"],
    ))

    previous_revenue = select_annual_fact(
        companyfacts,
        revenue_tags,
        observation_date,
        preceding_period_end=end,
    )

    previous_income = None
    if previous_revenue is not None and income_fact is not None:
        previous_income = select_annual_fact(
            companyfacts,
            [income_fact["tag"]],
            observation_date,
            period_end=previous_revenue["period_end"],
        )

    provenance["previous_revenue"] = previous_revenue
    provenance["previous_net_income"] = previous_income

    def growth(current, previous):
        if (
            current is None
            or previous is None
            or previous["value"] <= 0
        ):
            return None

        comparison = ratio(current, previous["value"])
        if comparison is None:
            return None

        return (comparison - 1) * 100

    return {
        "statement_period_end": end,
        "fundamental_source": "SEC companyfacts",
        "total_revenue": revenue["value"],
        "profit_margin": ratio(
            income,
            revenue["value"],
            percentage=True,
        ),
        "return_on_equity": ratio(
            value(parent_income),
            equity,
            percentage=True,
        ),
        "return_on_assets": ratio(
            income,
            assets,
            percentage=True,
        ),
        "revenue_growth": growth(
            revenue["value"],
            previous_revenue,
        ),
        "earnings_growth": growth(
            income,
            previous_income,
        ),
        "free_cash_flow": (
            operating_cash - capex
            if operating_cash is not None and capex is not None
            else None
        ),
        "forward_pe": None,
        "debt_to_equity": None,
        "provenance": provenance,
    }