"""Tests for data generation reproducibility."""

import hashlib
import sys
from pathlib import Path

# Add scripts to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_generate_data_reproducibility():
    """Running generate_data twice produces identical output."""
    from generate_data import generate

    df1 = generate()
    df2 = generate()

    csv1 = df1.to_csv(index=False)
    csv2 = df2.to_csv(index=False)

    assert csv1 == csv2, "Generated data is not reproducible"
    assert len(df1) == 5000, f"Expected 5000 rows, got {len(df1)}"

    sha1 = hashlib.sha256(csv1.encode()).hexdigest()
    sha2 = hashlib.sha256(csv2.encode()).hexdigest()
    assert sha1 == sha2


def test_generate_data_schema():
    """Generated data has expected columns and value ranges."""
    from generate_data import generate

    df = generate()

    expected_cols = [
        "crop", "water_fraction", "rainfall_scenario", "rainfall_fraction",
        "yield_stress_multiplier", "eta_etm", "yield_t_ha",
        "water_demand_m3_ha", "cost_inr_ha", "price_inr_quintal",
        "net_income_inr_ha", "calories_per_kg", "ky",
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"

    assert set(df["crop"].unique()) == {"Paddy", "Wheat", "Maize", "Pulses", "Millets"}
    assert df["yield_t_ha"].min() > 0, "Yield should be positive"
    assert df["water_demand_m3_ha"].min() > 0, "Water demand should be positive"
