"""
Standardise research-sector names for the production
sector-aware macroeconomic scoring model.
"""

from collections.abc import Iterable


PLATFORM_SECTORS = frozenset(
    {
        "Technology",
        "Financial Services",
        "Energy",
        "Basic Materials",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Real Estate",
        "Utilities",
        "Healthcare",
        "Industrials",
        "Communication Services",
    }
)


SECTOR_ALIASES = {
    "technology": "Technology",
    "information technology": "Technology",
    "financial services": "Financial Services",
    "financials": "Financial Services",
    "energy": "Energy",
    "basic materials": "Basic Materials",
    "materials": "Basic Materials",
    "consumer cyclical": "Consumer Cyclical",
    "consumer discretionary": "Consumer Cyclical",
    "consumer defensive": "Consumer Defensive",
    "consumer staples": "Consumer Defensive",
    "real estate": "Real Estate",
    "utilities": "Utilities",
    "healthcare": "Healthcare",
    "health care": "Healthcare",
    "industrials": "Industrials",
    "communication services": (
        "Communication Services"
    ),
}


def _clean_sector_name(
    sector: str,
) -> str:
    """Normalise whitespace and letter case."""

    return " ".join(
        sector.strip().split()
    ).casefold()


def map_to_platform_sector(
    sector: str | None,
    *,
    strict: bool = False,
) -> str | None:
    """
    Map a research or provider sector to the platform
    sector used by ``SECTOR_MACRO_WEIGHTS``.

    When ``strict`` is true, missing or unsupported
    sectors raise ``ValueError``.
    """

    if sector is None or not str(sector).strip():
        if strict:
            raise ValueError(
                "Sector is required."
            )
        return None

    cleaned_sector = _clean_sector_name(
        str(sector)
    )

    mapped_sector = SECTOR_ALIASES.get(
        cleaned_sector
    )

    if mapped_sector is None and strict:
        raise ValueError(
            f"Unsupported sector: {sector}"
        )

    return mapped_sector


def find_unmapped_sectors(
    sectors: Iterable[str | None],
) -> list[str]:
    """Return unique sectors without a known mapping."""

    unmapped = {
        str(sector)
        for sector in sectors
        if map_to_platform_sector(sector) is None
    }

    return sorted(unmapped)