"""ML Predictor service for AquaShift.

Predicts per-crop yield (t/ha) and water demand (m³/ha) given
water fraction, rainfall scenario, and crop parameters.
Returns point estimates plus uncertainty ranges from the RF ensemble.
"""

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.config import MODELS_DIR
from app.core.loaders import get_crop_dict, get_scenario_dict


_models: dict[str, Any] | None = None


def _load_models() -> dict[str, Any]:
    """Load trained models (lazy singleton)."""
    global _models
    if _models is None:
        model_path = MODELS_DIR / "crop_models.joblib"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Run: python scripts/train_model.py"
            )
        _models = joblib.load(model_path)
    return _models


def predict_crop(
    crop: str,
    water_fraction: float,
    rainfall_scenario: str,
) -> dict[str, Any]:
    """Predict yield and water demand for a single crop.

    Args:
        crop: Crop name (e.g. "Paddy").
        water_fraction: Water availability as fraction of baseline (0-1.3).
        rainfall_scenario: One of Normal/Deficit/Severe Deficit/Surplus.

    Returns:
        Dict with yield_t_ha, yield_lower, yield_upper,
        water_demand_m3_ha, water_lower, water_upper.
    """
    models = _load_models()
    crops = get_crop_dict()
    scenarios = get_scenario_dict()

    if crop not in models:
        raise ValueError(f"Unknown crop: {crop}. Known: {list(models.keys())}")
    if crop not in crops:
        raise ValueError(f"Crop not in config: {crop}")
    if rainfall_scenario not in scenarios:
        raise ValueError(f"Unknown scenario: {rainfall_scenario}")

    crop_data = crops[crop]
    scenario_data = scenarios[rainfall_scenario]

    ky = crop_data["drought_sensitivity_ky"]
    rain_frac = scenario_data["rainfall_fraction"]
    yield_stress = scenario_data["yield_stress_multiplier"]

    features = np.array([[water_fraction, rain_frac, yield_stress, ky]])

    crop_models = models[crop]
    yield_model = crop_models["yield_model"]
    water_model = crop_models["water_model"]

    # Point predictions
    yield_pred = float(yield_model.predict(features)[0])
    water_pred = float(water_model.predict(features)[0])

    # Uncertainty from individual tree predictions
    yield_trees = np.array([t.predict(features)[0] for t in yield_model.estimators_])
    water_trees = np.array([t.predict(features)[0] for t in water_model.estimators_])

    yield_lower = float(np.percentile(yield_trees, 10))
    yield_upper = float(np.percentile(yield_trees, 90))
    water_lower = float(np.percentile(water_trees, 10))
    water_upper = float(np.percentile(water_trees, 90))

    return {
        "crop": crop,
        "water_fraction": water_fraction,
        "rainfall_scenario": rainfall_scenario,
        "yield_t_ha": round(yield_pred, 3),
        "yield_lower": round(yield_lower, 3),
        "yield_upper": round(yield_upper, 3),
        "water_demand_m3_ha": round(water_pred, 1),
        "water_lower": round(water_lower, 1),
        "water_upper": round(water_upper, 1),
    }


def predict_all_crops(
    water_fraction: float,
    rainfall_scenario: str,
    crops: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Predict yield and water for all (or selected) crops.

    Args:
        water_fraction: Water availability as fraction of baseline.
        rainfall_scenario: Rainfall scenario name.
        crops: Optional list of crop names. Defaults to all.

    Returns:
        List of prediction dicts, one per crop.
    """
    models = _load_models()
    crop_names = crops or list(models.keys())
    return [predict_crop(c, water_fraction, rainfall_scenario) for c in crop_names]
