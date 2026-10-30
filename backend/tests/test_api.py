"""Contract tests for all API endpoints."""

import sys
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_health(client):
    """Health check."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config(client):
    """Config endpoint returns expected fields."""
    r = client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert "available_crops" in data
    assert len(data["available_crops"]) == 5
    assert "rainfall_scenarios" in data


def test_baseline(client):
    """Baseline returns plan and predictions."""
    r = client.get("/api/baseline")
    assert r.status_code == 200
    data = r.json()
    assert "plan" in data
    assert "predictions" in data
    assert len(data["plan"]["allocations"]) == 5


def test_predict(client):
    """Predict endpoint returns predictions."""
    r = client.post("/api/predict", json={
        "water_fraction": 0.8,
        "rainfall_scenario": "Deficit",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["predictions"]) == 5


def test_optimize(client):
    """Optimize endpoint returns plan."""
    r = client.post("/api/optimize", json={
        "land_ha": 1000,
        "water_budget_m3": 8000000,
        "water_change_pct": -20,
        "rainfall_scenario": "Normal",
    })
    assert r.status_code == 200
    data = r.json()
    assert "plan" in data
    assert "baseline" in data
    assert data["plan"]["status"] in ("optimal", "feasible_with_slack")


def test_stress_test(client):
    """Stress test endpoint returns bottlenecks."""
    r = client.post("/api/stress-test", json={
        "land_ha": 1000,
        "water_budget_m3": 8000000,
        "rainfall_scenario": "Normal",
    })
    assert r.status_code == 200
    data = r.json()
    assert "relaxed_plan" in data
    assert "bottlenecks" in data
    assert len(data["bottlenecks"]) > 0


def test_explain(client):
    """Explain endpoint returns explanation (template fallback)."""
    plan = {
        "status": "optimal",
        "allocations": [
            {"crop": "Paddy", "area_ha": 300, "area_pct": 30},
        ],
        "total_water_m3": 5000000,
        "water_budget_m3": 6400000,
        "total_income_inr": 1000000,
        "total_production_tonnes": 2000,
        "water_gap_pct": 0,
        "food_gap_pct": 0,
        "income_gap_pct": 0,
    }
    r = client.post("/api/explain", json={
        "plan": plan,
        "audience": "farmer",
        "language": "en",
    })
    assert r.status_code == 200
    data = r.json()
    assert "text" in data
    assert len(data["text"]) > 20


def test_sweep(client):
    """Sweep endpoint returns points."""
    r = client.post("/api/simulate/sweep", json={
        "land_ha": 1000,
        "water_budget_m3": 8000000,
        "rainfall_scenario": "Normal",
        "steps": 5,
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["points"]) == 5


def test_optimize_bad_input(client):
    """Bad input returns 422."""
    r = client.post("/api/optimize", json={
        "land_ha": -100,  # Invalid
    })
    assert r.status_code == 422
