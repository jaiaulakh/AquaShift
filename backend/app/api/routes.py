"""API routes for AquaShift."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.loaders import get_crop_dict, get_scenario_dict, load_crops
from app.ml.predictor import predict_all_crops
from app.optimizer.model import solve, compute_baseline
from app.optimizer.stress import run_stress_test
from app.optimizer.sweep import run_sweep
from app.llm.explain import explain_plan
from app.models.schemas import (
    ScenarioInput,
    PredictRequest,
    ExplainRequest,
    SweepRequest,
    OptimizationResult,
    StressTestResult,
    ConfigResponse,
    BaselineResponse,
    ExplainResult,
    SweepResult,
)

router = APIRouter(prefix="/api")

# Simple in-memory cache
_cache: dict[str, Any] = {}


def _cache_key(prefix: str, **kwargs: Any) -> str:
    """Generate a cache key from parameters."""
    parts = [prefix] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return "|".join(str(p) for p in parts)


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Return application configuration for frontend."""
    settings = get_settings()
    crops = get_crop_dict()
    scenarios = get_scenario_dict()

    return ConfigResponse(
        region_name=settings.region_name,
        default_land_ha=settings.default_land_ha,
        default_water_budget_m3=settings.default_water_budget_m3,
        available_crops=list(crops.keys()),
        rainfall_scenarios=list(scenarios.keys()),
        crop_details=crops,
    )


@router.get("/baseline")
async def get_baseline() -> dict[str, Any]:
    """Return baseline plan for the default region."""
    settings = get_settings()
    crops = get_crop_dict()

    baseline = compute_baseline(
        land_ha=settings.default_land_ha,
        water_budget_m3=settings.default_water_budget_m3,
        rainfall_scenario="Normal",
        selected_crops=list(crops.keys()),
    )

    predictions = predict_all_crops(1.0, "Normal")

    return {
        "plan": baseline,
        "predictions": predictions,
    }


@router.post("/predict")
async def predict(request: PredictRequest) -> dict[str, Any]:
    """Get ML predictions for crop yields and water demand."""
    try:
        predictions = predict_all_crops(
            water_fraction=request.water_fraction,
            rainfall_scenario=request.rainfall_scenario.value,
            crops=request.crops,
        )
        return {"predictions": predictions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize(scenario: ScenarioInput) -> dict[str, Any]:
    """Run the crop allocation optimizer."""
    settings = get_settings()
    crops_data = get_crop_dict()

    # Cache check
    key = _cache_key("optimize", **scenario.model_dump())
    if key in _cache:
        return _cache[key]

    # Compute water fraction
    water_fraction = 1.0 + scenario.water_change_pct / 100.0
    actual_water = scenario.water_budget_m3 * water_fraction

    # Compute baseline for targets and deltas
    baseline = compute_baseline(
        land_ha=scenario.land_ha,
        water_budget_m3=scenario.water_budget_m3,
        rainfall_scenario=scenario.rainfall_scenario.value,
        selected_crops=scenario.selected_crops,
    )
    baseline_alloc = {a["crop"]: a["area_ha"] for a in baseline["allocations"]}

    # Compute targets
    food_target = baseline["total_production_tonnes"] * (1.0 + scenario.food_target_change_pct / 100.0)
    income_target = baseline["total_income_inr"] * (1.0 + scenario.income_target_change_pct / 100.0)

    try:
        result = solve(
            land_ha=scenario.land_ha,
            water_budget_m3=actual_water,
            food_target_tonnes=food_target,
            income_target_inr=income_target,
            rainfall_scenario=scenario.rainfall_scenario.value,
            water_fraction=water_fraction,
            selected_crops=scenario.selected_crops,
            mode=scenario.optimization_mode.value,
            weights=scenario.weights,
            allow_slack=True,
            baseline_allocations=baseline_alloc,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

    response = {"plan": result, "baseline": baseline}
    _cache[key] = response
    return response


@router.post("/stress-test")
async def stress_test(scenario: ScenarioInput) -> dict[str, Any]:
    """Run stress test with extreme parameters."""
    try:
        result = run_stress_test(
            land_ha=scenario.land_ha,
            water_budget_m3=scenario.water_budget_m3,
            rainfall_scenario=scenario.rainfall_scenario.value,
            selected_crops=scenario.selected_crops,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress test failed: {str(e)}")


@router.post("/explain")
async def explain(request: ExplainRequest) -> dict[str, Any]:
    """Get AI explanation of a plan."""
    try:
        result = await explain_plan(
            plan=request.plan,
            audience=request.audience.value,
            language=request.language.value,
            baseline=request.baseline,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.post("/simulate/sweep")
async def simulate_sweep(request: SweepRequest) -> dict[str, Any]:
    """Run water sweep simulation."""
    key = _cache_key("sweep", **request.model_dump())
    if key in _cache:
        return _cache[key]

    try:
        result = run_sweep(
            land_ha=request.land_ha,
            water_budget_m3=request.water_budget_m3,
            rainfall_scenario=request.rainfall_scenario.value,
            selected_crops=request.selected_crops,
            steps=request.steps,
        )
        _cache[key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sweep simulation failed: {str(e)}")
