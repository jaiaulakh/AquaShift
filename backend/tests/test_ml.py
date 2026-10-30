"""Tests for ML predictor."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(autouse=True, scope="module")
def ensure_models():
    """Ensure training data and models exist."""
    from generate_data import main as gen_main
    gen_main()

    from train_model import train
    train()


def test_predict_crop():
    """Basic prediction returns valid structure."""
    from app.ml.predictor import predict_crop

    result = predict_crop("Paddy", 1.0, "Normal")

    assert result["crop"] == "Paddy"
    assert result["yield_t_ha"] > 0
    assert result["water_demand_m3_ha"] > 0
    assert result["yield_lower"] <= result["yield_t_ha"] <= result["yield_upper"]
    assert result["water_lower"] <= result["water_demand_m3_ha"] <= result["water_upper"]


def test_predict_all_crops():
    """Predict all crops returns 5 predictions."""
    from app.ml.predictor import predict_all_crops

    results = predict_all_crops(1.0, "Normal")
    assert len(results) == 5
    crop_names = {r["crop"] for r in results}
    assert crop_names == {"Paddy", "Wheat", "Maize", "Pulses", "Millets"}


def test_yield_monotonic_with_water():
    """Yield should not increase as water decreases."""
    from app.ml.predictor import predict_crop

    yields_paddy = []
    water_fractions = [1.0, 0.8, 0.6, 0.4, 0.3]

    for wf in water_fractions:
        result = predict_crop("Paddy", wf, "Normal")
        yields_paddy.append(result["yield_t_ha"])

    # Check monotonicity: each yield should be >= the next
    for i in range(len(yields_paddy) - 1):
        assert yields_paddy[i] >= yields_paddy[i + 1] - 0.1, (
            f"Yield increased as water decreased: "
            f"wf={water_fractions[i]}→{water_fractions[i+1]}, "
            f"yield={yields_paddy[i]:.3f}→{yields_paddy[i+1]:.3f}"
        )


def test_drought_sensitive_crops_drop_more():
    """Crops with higher Ky should lose more yield under water stress."""
    from app.ml.predictor import predict_crop

    # Millets (Ky=0.40) vs Paddy (Ky=1.05) under same water stress
    paddy_full = predict_crop("Paddy", 1.0, "Normal")["yield_t_ha"]
    paddy_low = predict_crop("Paddy", 0.4, "Normal")["yield_t_ha"]
    paddy_drop = (paddy_full - paddy_low) / paddy_full

    millet_full = predict_crop("Millets", 1.0, "Normal")["yield_t_ha"]
    millet_low = predict_crop("Millets", 0.4, "Normal")["yield_t_ha"]
    millet_drop = (millet_full - millet_low) / millet_full

    # Paddy (higher Ky) should drop proportionally more
    assert paddy_drop > millet_drop, (
        f"Paddy (Ky=1.05) should drop more than Millets (Ky=0.40): "
        f"paddy_drop={paddy_drop:.2%}, millet_drop={millet_drop:.2%}"
    )
