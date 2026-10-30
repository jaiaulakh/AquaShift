"""Generate synthetic training data using FAO yield-response-to-water model.

Usage:
    python scripts/generate_data.py

Produces data/training_data.csv with seeded randomness for reproducibility.
Model: Ya/Ym = 1 - Ky * (1 - ETa/ETm)
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
SAMPLES_PER_CROP = 1000

# Root paths
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Crop parameters: {name: (yield_max_t_ha, water_max_m3_ha, ky, cost_inr_ha, price_inr_quintal, cal_per_kg)}
CROPS = {
    "Paddy":  (4.5, 14000, 1.05, 45000, 2183, 3600),
    "Wheat":  (3.5,  4500, 1.00, 35000, 2275, 3400),
    "Maize":  (3.0,  5000, 1.25, 30000, 2090, 3650),
    "Pulses": (1.2,  3000, 0.60, 25000, 6600, 3400),
    "Millets":(2.0,  2500, 0.40, 20000, 2350, 3300),
}

RAINFALL_SCENARIOS = {
    "Normal":         (1.00, 1.00),
    "Deficit":        (0.75, 0.85),
    "Severe Deficit": (0.50, 0.65),
    "Surplus":        (1.20, 0.95),
}


def generate() -> pd.DataFrame:
    """Generate training data with fixed seed."""
    rng = np.random.RandomState(SEED)
    rows: list[dict] = []

    for crop_name, (ym, etm, ky, cost, price, cal) in CROPS.items():
        for _ in range(SAMPLES_PER_CROP):
            # Random water fraction: 0.2 to 1.3 (covers stress to surplus)
            water_frac = rng.uniform(0.2, 1.3)
            eta_etm = min(water_frac, 1.0)  # Can't exceed max ET

            # Pick a random rainfall scenario
            scenario_name = rng.choice(list(RAINFALL_SCENARIOS.keys()))
            rain_frac, yield_stress = RAINFALL_SCENARIOS[scenario_name]

            # FAO yield response: Ya/Ym = 1 - Ky * (1 - ETa/ETm)
            fao_ratio = max(0.0, 1.0 - ky * (1.0 - eta_etm))
            ya = ym * fao_ratio * yield_stress

            # Add noise (5% CV)
            noise = rng.normal(1.0, 0.05)
            ya = max(0.1, ya * noise)

            # Actual water demand (adjusted)
            actual_water = etm * water_frac * (1.0 + rng.normal(0, 0.03))
            actual_water = max(500, actual_water)

            # Net income per ha
            production_quintals = ya * 10  # t -> quintals
            gross_income = production_quintals * price
            net_income = gross_income - cost

            rows.append({
                "crop": crop_name,
                "water_fraction": round(water_frac, 4),
                "rainfall_scenario": scenario_name,
                "rainfall_fraction": rain_frac,
                "yield_stress_multiplier": yield_stress,
                "eta_etm": round(eta_etm, 4),
                "yield_t_ha": round(ya, 4),
                "water_demand_m3_ha": round(actual_water, 1),
                "cost_inr_ha": cost,
                "price_inr_quintal": price,
                "net_income_inr_ha": round(net_income, 0),
                "calories_per_kg": cal,
                "ky": ky,
            })

    return pd.DataFrame(rows)


def main() -> None:
    """Generate and save training data."""
    DATA_DIR.mkdir(exist_ok=True)
    out_path = DATA_DIR / "training_data.csv"

    df = generate()
    df.to_csv(out_path, index=False)

    # Print hash for reproducibility verification
    content = out_path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    print(f"Generated {len(df)} rows -> {out_path}")
    print(f"SHA256: {sha}")
    return sha


if __name__ == "__main__":
    main()
