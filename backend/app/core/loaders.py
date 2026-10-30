"""Data loaders for AquaShift.

Loads crop parameters and weather scenarios from CSV files.
Includes stubs documenting where real data sources would plug in.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import DATA_DIR


@lru_cache
def load_crops() -> pd.DataFrame:
    """Load crop parameters from crops.csv."""
    df = pd.read_csv(DATA_DIR / "crops.csv")
    return df


@lru_cache
def load_weather_scenarios() -> pd.DataFrame:
    """Load weather scenarios from weather_scenarios.csv."""
    df = pd.read_csv(DATA_DIR / "weather_scenarios.csv")
    return df


def get_crop_dict() -> dict[str, dict[str, Any]]:
    """Return crop parameters as a nested dict keyed by crop name."""
    df = load_crops()
    return df.set_index("crop").to_dict(orient="index")


def get_scenario_dict() -> dict[str, dict[str, float]]:
    """Return weather scenarios as a nested dict keyed by scenario name."""
    df = load_weather_scenarios()
    return df.set_index("scenario").to_dict(orient="index")


# ── Real data source stubs ──────────────────────────────────────────
# These document where real sources would plug in. Each stub lists:
# - Source name and URL
# - Expected schema
# - How it would replace the synthetic data

REAL_DATA_SOURCES = {
    "crop_yields": {
        "source": "data.gov.in / ICAR Crop Statistics",
        "url": "https://data.gov.in/catalog/district-wise-season-wise-crop-production-statistics",
        "schema": {
            "district": "str",
            "crop": "str",
            "season": "str (Kharif/Rabi)",
            "year": "int",
            "area_ha": "float",
            "production_tonnes": "float",
            "yield_t_ha": "float",
        },
        "replaces": "baseline_yield_t_ha in crops.csv",
    },
    "weather": {
        "source": "IMD (India Meteorological Department)",
        "url": "https://www.imd.gov.in/",
        "schema": {
            "station_id": "str",
            "date": "date",
            "rainfall_mm": "float",
            "temp_max_c": "float",
            "temp_min_c": "float",
            "humidity_pct": "float",
        },
        "replaces": "weather_scenarios.csv with actual historical distributions",
    },
    "groundwater": {
        "source": "CGWB (Central Ground Water Board)",
        "url": "https://cgwb.gov.in/",
        "schema": {
            "district": "str",
            "year": "int",
            "stage_of_extraction_pct": "float",
            "net_availability_mcm": "float",
        },
        "replaces": "default_water_budget in config with real availability",
    },
    "market_prices": {
        "source": "Agmarknet / APEDA",
        "url": "https://agmarknet.gov.in/",
        "schema": {
            "market": "str",
            "commodity": "str",
            "date": "date",
            "modal_price_inr_quintal": "float",
        },
        "replaces": "price_inr_quintal in crops.csv with market prices",
    },
    "cost_of_cultivation": {
        "source": "CACP / DES (Directorate of Economics and Statistics)",
        "url": "https://eands.dacnet.nic.in/",
        "schema": {
            "crop": "str",
            "state": "str",
            "year": "int",
            "cost_a2_fl_inr_ha": "float",
            "cost_c2_inr_ha": "float",
        },
        "replaces": "cost_cultivation_inr_ha in crops.csv",
    },
}
