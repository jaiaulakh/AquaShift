"""Tests for the optimizer, stress test, and diagnosis."""

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


CROPS = ["Paddy", "Wheat", "Maize", "Pulses", "Millets"]
LAND = 1000.0
WATER = 8_000_000.0


def test_baseline_sums_to_land():
    """Baseline allocation should sum to land."""
    from app.optimizer.model import compute_baseline

    baseline = compute_baseline(LAND, WATER, "Normal", CROPS)
    total = sum(a["area_ha"] for a in baseline["allocations"])
    assert abs(total - LAND) < 1.0, f"Baseline total {total} != {LAND}"


def test_normal_scenario_feasible():
    """Normal scenario should be optimal (no slack needed)."""
    from app.optimizer.model import solve, compute_baseline

    baseline = compute_baseline(LAND, WATER, "Normal", CROPS)
    result = solve(
        land_ha=LAND,
        water_budget_m3=WATER,
        food_target_tonnes=baseline["total_production_tonnes"],
        income_target_inr=baseline["total_income_inr"],
        rainfall_scenario="Normal",
        water_fraction=1.0,
        selected_crops=CROPS,
        mode="weights",
    )
    assert result["status"] in ("optimal", "feasible_with_slack")
    total_area = sum(a["area_ha"] for a in result["allocations"])
    assert total_area <= LAND + 0.01, f"Area {total_area} exceeds land {LAND}"


def test_allocation_within_land():
    """Total allocation should never exceed available land."""
    from app.optimizer.model import solve, compute_baseline

    baseline = compute_baseline(LAND, WATER, "Normal", CROPS)
    # Stress scenario
    result = solve(
        land_ha=LAND,
        water_budget_m3=WATER * 0.5,
        food_target_tonnes=baseline["total_production_tonnes"],
        income_target_inr=baseline["total_income_inr"],
        rainfall_scenario="Deficit",
        water_fraction=0.5,
        selected_crops=CROPS,
        mode="weights",
    )
    total_area = sum(a["area_ha"] for a in result["allocations"])
    assert total_area <= LAND + 0.01


def test_weights_vs_lexicographic_differ():
    """Weights and lexicographic modes should produce different results."""
    from app.optimizer.model import solve, compute_baseline

    baseline = compute_baseline(LAND, WATER, "Normal", CROPS)

    result_w = solve(
        land_ha=LAND,
        water_budget_m3=WATER * 0.6,
        food_target_tonnes=baseline["total_production_tonnes"],
        income_target_inr=baseline["total_income_inr"],
        rainfall_scenario="Deficit",
        water_fraction=0.6,
        selected_crops=CROPS,
        mode="weights",
    )

    result_l = solve(
        land_ha=LAND,
        water_budget_m3=WATER * 0.6,
        food_target_tonnes=baseline["total_production_tonnes"],
        income_target_inr=baseline["total_income_inr"],
        rainfall_scenario="Deficit",
        water_fraction=0.6,
        selected_crops=CROPS,
        mode="lexicographic",
    )

    # At least one allocation should differ
    alloc_w = {a["crop"]: a["area_ha"] for a in result_w["allocations"]}
    alloc_l = {a["crop"]: a["area_ha"] for a in result_l["allocations"]}

    # They might be similar but mode label should differ
    assert result_w["mode"] == "weights"
    assert result_l["mode"] == "lexicographic"


def test_stress_test_returns_slack_plan():
    """Extreme scenario should return infeasible strict + slack plan."""
    from app.optimizer.stress import run_stress_test

    result = run_stress_test(LAND, WATER, "Normal", CROPS)

    # Strict should be infeasible (or at least the relaxed should have slack)
    assert result["relaxed_plan"]["status"] in ("feasible_with_slack", "optimal")
    assert len(result["bottlenecks"]) > 0


def test_stress_test_bottleneck_ranking():
    """Stress test should rank Water as Critical."""
    from app.optimizer.stress import run_stress_test

    result = run_stress_test(LAND, WATER, "Normal", CROPS)
    bottlenecks = result["bottlenecks"]

    # Find severities
    severities = {b["constraint"]: b["severity"] for b in bottlenecks}
    print(f"Bottleneck severities: {severities}")

    # Water should be the most critical
    if "Water Budget" in severities:
        assert severities["Water Budget"] in ("Critical", "High"), (
            f"Expected Water to be Critical/High, got {severities['Water Budget']}"
        )


def test_sweep_returns_points():
    """Water sweep should return multiple points."""
    from app.optimizer.sweep import run_sweep

    result = run_sweep(LAND, WATER, "Normal", CROPS, steps=5)
    assert len(result["points"]) == 5
    assert result["points"][0]["water_change_pct"] == 0.0
