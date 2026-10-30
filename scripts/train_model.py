"""Train ML models for yield and water demand prediction.

Usage:
    python scripts/train_model.py

Trains a RandomForest ensemble per crop, saves to models/ directory.
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"


def train() -> None:
    """Train and save models for all crops."""
    MODELS_DIR.mkdir(exist_ok=True)

    training_path = DATA_DIR / "training_data.csv"
    if not training_path.exists():
        print("Training data not found. Run generate_data.py first.")
        sys.exit(1)

    df = pd.read_csv(training_path)
    print(f"Loaded {len(df)} training samples")

    features = ["water_fraction", "rainfall_fraction", "yield_stress_multiplier", "ky"]
    target_yield = "yield_t_ha"
    target_water = "water_demand_m3_ha"

    models = {}
    metrics = {}

    for crop in df["crop"].unique():
        crop_df = df[df["crop"] == crop]
        X = crop_df[features].values
        y_yield = crop_df[target_yield].values
        y_water = crop_df[target_water].values

        X_train, X_test, y_yield_train, y_yield_test = train_test_split(
            X, y_yield, test_size=0.2, random_state=SEED
        )
        _, _, y_water_train, y_water_test = train_test_split(
            X, y_water, test_size=0.2, random_state=SEED
        )

        # Yield model — ensemble of 50 trees for quantile estimation
        yield_model = RandomForestRegressor(
            n_estimators=50, random_state=SEED, max_depth=10, min_samples_leaf=5
        )
        yield_model.fit(X_train, y_yield_train)

        # Water demand model
        water_model = RandomForestRegressor(
            n_estimators=50, random_state=SEED, max_depth=10, min_samples_leaf=5
        )
        water_model.fit(X_train, y_water_train)

        # Evaluate
        y_yield_pred = yield_model.predict(X_test)
        y_water_pred = water_model.predict(X_test)

        metrics[crop] = {
            "yield_r2": round(r2_score(y_yield_test, y_yield_pred), 4),
            "yield_mae": round(mean_absolute_error(y_yield_test, y_yield_pred), 4),
            "water_r2": round(r2_score(y_water_test, y_water_pred), 4),
            "water_mae": round(mean_absolute_error(y_water_test, y_water_pred), 4),
        }

        models[crop] = {
            "yield_model": yield_model,
            "water_model": water_model,
            "features": features,
        }

        print(f"  {crop}: yield R²={metrics[crop]['yield_r2']:.3f}, "
              f"water R²={metrics[crop]['water_r2']:.3f}")

    # Save all models in a single joblib file
    model_path = MODELS_DIR / "crop_models.joblib"
    joblib.dump(models, model_path)
    print(f"\nModels saved to {model_path}")

    # Save metrics
    metrics_path = MODELS_DIR / "metrics.joblib"
    joblib.dump(metrics, metrics_path)
    print(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    train()
