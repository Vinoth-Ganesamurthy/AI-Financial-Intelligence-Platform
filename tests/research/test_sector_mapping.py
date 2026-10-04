"""Tests for research-sector standardisation."""

import csv
from pathlib import Path

import pytest

from src.research.sector_mapping import (
    PLATFORM_SECTORS,
    find_unmapped_sectors,
    map_to_platform_sector,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

UNIVERSE_PATH = (
    PROJECT_ROOT
    / "research"
    / "company_universe.csv"
)


@pytest.mark.parametrize(
    ("research_sector", "expected"),
    [
        (
            "Information Technology",
            "Technology",
        ),
        (
            "Financials",
            "Financial Services",
        ),
        (
            "Health Care",
            "Healthcare",
        ),
        (
            "Materials",
            "Basic Materials",
        ),
        (
            "Consumer Discretionary",
            "Consumer Cyclical",
        ),
        (
            "Consumer Staples",
            "Consumer Defensive",
        ),
        (
            "Communication Services",
            "Communication Services",
        ),
        ("Energy", "Energy"),
        ("Industrials", "Industrials"),
        ("Real Estate", "Real Estate"),
        ("Utilities", "Utilities"),
    ],
)
def test_research_sector_mapping(
    research_sector,
    expected,
):
    assert (
        map_to_platform_sector(
            research_sector
        )
        == expected
    )


def test_mapping_ignores_case_and_whitespace():
    assert (
        map_to_platform_sector(
            "  INFORMATION   TECHNOLOGY "
        )
        == "Technology"
    )


def test_unknown_sector_returns_none():
    assert (
        map_to_platform_sector(
            "Unknown Sector"
        )
        is None
    )


def test_strict_mapping_rejects_unknown_sector():
    with pytest.raises(
        ValueError,
        match="Unsupported sector",
    ):
        map_to_platform_sector(
            "Unknown Sector",
            strict=True,
        )


def test_strict_mapping_requires_sector():
    with pytest.raises(
        ValueError,
        match="Sector is required",
    ):
        map_to_platform_sector(
            None,
            strict=True,
        )


def test_find_unmapped_sectors():
    assert find_unmapped_sectors(
        [
            "Financials",
            "Unknown Sector",
            "Another Sector",
            "Unknown Sector",
        ]
    ) == [
        "Another Sector",
        "Unknown Sector",
    ]


def test_platform_sector_values_are_valid():
    mapped_values = {
        map_to_platform_sector(sector)
        for sector in PLATFORM_SECTORS
    }

    assert mapped_values == PLATFORM_SECTORS


def test_every_universe_sector_is_mapped():
    with UNIVERSE_PATH.open(
        encoding="utf-8",
        newline="",
    ) as universe_file:
        sectors = [
            row["sector"]
            for row in csv.DictReader(
                universe_file
            )
        ]

    assert find_unmapped_sectors(
        sectors
    ) == []