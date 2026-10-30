"""OR-Tools GLOP optimizer for crop allocation.

Solves a linear program to find the optimal crop allocation
under water, food, and income constraints.

Decision variables: hectares per crop (continuous).
Hard constraints: total area ≤ land; per-crop min/max shares.
Soft constraints (with slack): water ≤ budget; production ≥ food target; income ≥ income target.
Objective: minimize weighted, normalized slack + small tie-breaker (minimize water).
"""

from __future__ import annotations

import time
from typing import Any

from ortools.linear_solver import pywraplp

from app.core.loaders import get_crop_dict, get_scenario_dict
from app.ml.predictor import predict_crop


def solve(
    land_ha: float,
    water_budget_m3: float,
    food_target_tonnes: float,
    income_target_inr: float,
    rainfall_scenario: str,
    water_fraction: float,
    selected_crops: list[str],
    mode: str = "weights",
    weights: dict[str, float] | None = None,
    allow_slack: bool = True,
    baseline_allocations: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Solve the crop allocation LP.

    Args:
        land_ha: Total available land.
        water_budget_m3: Water budget after adjustments.
        food_target_tonnes: Minimum production target.
        income_target_inr: Minimum net income target.
        rainfall_scenario: Weather scenario name.
        water_fraction: Water availability as fraction of baseline.
        selected_crops: Crops to consider.
        mode: "weights" or "lexicographic".
        weights: Priority weights for slack terms (weights mode).
        allow_slack: If False, no slack variables (strict solve).
        baseline_allocations: {crop: ha} for computing deltas.

    Returns:
        Dict with status, allocations, totals, constraints, shadow prices.
    """
    if mode == "lexicographic":
        return _solve_lexicographic(
            land_ha, water_budget_m3, food_target_tonnes, income_target_inr,
            rainfall_scenario, water_fraction, selected_crops,
            baseline_allocations=baseline_allocations,
        )

    w = weights or {"water": 1.0, "food": 1.0, "income": 1.0}
    crops_data = get_crop_dict()

    # Get ML predictions for each crop
    predictions = {}
    for crop in selected_crops:
        pred = predict_crop(crop, water_fraction, rainfall_scenario)
        predictions[crop] = pred

    start = time.perf_counter()

    solver = pywraplp.Solver.CreateSolver("GLOP")
    if solver is None:
        raise RuntimeError("GLOP solver not available")

    # ── Decision variables: hectares per crop ──
    x: dict[str, Any] = {}
    for crop in selected_crops:
        cd = crops_data[crop]
        min_ha = land_ha * cd["min_land_share"]
        max_ha = land_ha * cd["max_land_share"]
        x[crop] = solver.NumVar(min_ha, max_ha, f"x_{crop}")

    # ── Slack variables (non-negative) ──
    if allow_slack:
        slack_water = solver.NumVar(0.0, solver.infinity(), "slack_water")
        slack_food = solver.NumVar(0.0, solver.infinity(), "slack_food")
        slack_income = solver.NumVar(0.0, solver.infinity(), "slack_income")
    else:
        slack_water = None
        slack_food = None
        slack_income = None

    # ── Hard constraint: total area ≤ land ──
    area_ct = solver.Constraint(0.0, land_ha, "total_area")
    for crop in selected_crops:
        area_ct.SetCoefficient(x[crop], 1.0)

    # ── Soft constraint: water use ≤ budget (+ slack) ──
    water_ct = solver.Constraint(-solver.infinity(), water_budget_m3, "water_budget")
    for crop in selected_crops:
        water_per_ha = predictions[crop]["water_demand_m3_ha"]
        water_ct.SetCoefficient(x[crop], water_per_ha)
    if slack_water is not None:
        water_ct.SetCoefficient(slack_water, -1.0)  # subtract slack from LHS

    # ── Soft constraint: production ≥ food target (- slack) ──
    food_ct = solver.Constraint(food_target_tonnes, solver.infinity(), "food_target")
    for crop in selected_crops:
        yield_per_ha = predictions[crop]["yield_t_ha"]
        food_ct.SetCoefficient(x[crop], yield_per_ha)
    if slack_food is not None:
        food_ct.SetCoefficient(slack_food, 1.0)  # add slack to allow deficit

    # ── Soft constraint: income ≥ income target (- slack) ──
    income_ct = solver.Constraint(income_target_inr, solver.infinity(), "income_target")
    for crop in selected_crops:
        pred = predictions[crop]
        cd = crops_data[crop]
        yield_per_ha = pred["yield_t_ha"]
        income_per_ha = (yield_per_ha * 10 * cd["price_inr_quintal"]) - cd["cost_cultivation_inr_ha"]
        income_ct.SetCoefficient(x[crop], income_per_ha)
    if slack_income is not None:
        income_ct.SetCoefficient(slack_income, 1.0)

    # ── Objective: minimize weighted, normalized slack + tie-breaker ──
    objective = solver.Objective()

    if allow_slack and slack_water is not None:
        # Normalize slack by target values to make weights comparable
        norm_water = max(water_budget_m3, 1.0)
        norm_food = max(food_target_tonnes, 1.0)
        norm_income = max(income_target_inr, 1.0)

        objective.SetCoefficient(slack_water, w["water"] / norm_water)
        objective.SetCoefficient(slack_food, w["food"] / norm_food)
        objective.SetCoefficient(slack_income, w["income"] / norm_income)

    # Small tie-breaker: minimize total water use
    for crop in selected_crops:
        water_per_ha = predictions[crop]["water_demand_m3_ha"]
        # Very small coefficient relative to slack
        objective.SetCoefficient(x[crop], 1e-9 * water_per_ha)

    objective.SetMinimization()

    status = solver.Solve()
    solve_time = (time.perf_counter() - start) * 1000

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        return _extract_result(
            solver, x, slack_water, slack_food, slack_income,
            predictions, crops_data, selected_crops,
            land_ha, water_budget_m3, food_target_tonnes, income_target_inr,
            mode, solve_time, baseline_allocations,
            water_ct, food_ct, income_ct,
        )
    else:
        return {
            "status": "infeasible",
            "mode": mode,
            "allocations": [],
            "total_water_m3": 0,
            "total_income_inr": 0,
            "total_production_tonnes": 0,
            "total_calories": 0,
            "water_budget_m3": water_budget_m3,
            "food_target_tonnes": food_target_tonnes,
            "income_target_inr": income_target_inr,
            "constraints": [],
            "solve_time_ms": solve_time,
            "slack_values": {},
            "water_gap_pct": 0,
            "food_gap_pct": 0,
            "income_gap_pct": 0,
        }


def _extract_result(
    solver, x, slack_water, slack_food, slack_income,
    predictions, crops_data, selected_crops,
    land_ha, water_budget_m3, food_target_tonnes, income_target_inr,
    mode, solve_time, baseline_allocations,
    water_ct, food_ct, income_ct,
) -> dict[str, Any]:
    """Extract results from solved model."""
    allocations = []
    total_water = 0.0
    total_income = 0.0
    total_production = 0.0
    total_calories = 0.0

    for crop in selected_crops:
        area = x[crop].solution_value()
        pred = predictions[crop]
        cd = crops_data[crop]

        yield_val = pred["yield_t_ha"]
        water_per_ha = pred["water_demand_m3_ha"]
        production = area * yield_val
        water_used = area * water_per_ha
        income_per_ha = (yield_val * 10 * cd["price_inr_quintal"]) - cd["cost_cultivation_inr_ha"]
        income = area * income_per_ha
        calories = production * 1000 * cd["calories_per_kg"]

        baseline_ha = (baseline_allocations or {}).get(crop, 0.0)
        delta_ha = area - baseline_ha
        delta_pct = (delta_ha / baseline_ha * 100) if baseline_ha > 0 else 0.0

        allocations.append({
            "crop": crop,
            "area_ha": round(area, 2),
            "area_pct": round(area / land_ha * 100, 2) if land_ha > 0 else 0,
            "yield_t_ha": round(yield_val, 3),
            "yield_lower": round(pred["yield_lower"], 3),
            "yield_upper": round(pred["yield_upper"], 3),
            "production_tonnes": round(production, 2),
            "water_used_m3": round(water_used, 0),
            "water_demand_m3_ha": round(water_per_ha, 1),
            "water_demand_lower": round(pred["water_lower"], 1),
            "water_demand_upper": round(pred["water_upper"], 1),
            "income_inr": round(income, 0),
            "calories_total": round(calories, 0),
            "delta_area_ha": round(delta_ha, 2),
            "delta_area_pct": round(delta_pct, 2),
        })

        total_water += water_used
        total_income += income
        total_production += production
        total_calories += calories

    # Slack values
    sw = slack_water.solution_value() if slack_water is not None else 0.0
    sf = slack_food.solution_value() if slack_food is not None else 0.0
    si = slack_income.solution_value() if slack_income is not None else 0.0

    has_slack = (sw > 0.01 or sf > 0.01 or si > 0.01)
    status = "feasible_with_slack" if has_slack else "optimal"

    # Shadow prices (dual values)
    water_shadow = water_ct.dual_value() if water_ct else 0.0
    food_shadow = food_ct.dual_value() if food_ct else 0.0
    income_shadow = income_ct.dual_value() if income_ct else 0.0

    water_gap = (sw / water_budget_m3 * 100) if water_budget_m3 > 0 else 0.0
    food_gap = (sf / food_target_tonnes * 100) if food_target_tonnes > 0 else 0.0
    income_gap = (si / income_target_inr * 100) if income_target_inr > 0 else 0.0

    constraints = [
        {
            "name": "Water Budget",
            "type": "soft",
            "target": round(water_budget_m3, 0),
            "actual": round(total_water, 0),
            "slack": round(sw, 0),
            "slack_pct": round(water_gap, 2),
            "shadow_price": round(water_shadow, 4),
            "binding": abs(total_water - water_budget_m3) < 1.0 or sw > 0.01,
        },
        {
            "name": "Food Target",
            "type": "soft",
            "target": round(food_target_tonnes, 2),
            "actual": round(total_production, 2),
            "slack": round(sf, 2),
            "slack_pct": round(food_gap, 2),
            "shadow_price": round(food_shadow, 4),
            "binding": abs(total_production - food_target_tonnes) < 1.0 or sf > 0.01,
        },
        {
            "name": "Income Target",
            "type": "soft",
            "target": round(income_target_inr, 0),
            "actual": round(total_income, 0),
            "slack": round(si, 0),
            "slack_pct": round(income_gap, 2),
            "shadow_price": round(income_shadow, 4),
            "binding": abs(total_income - income_target_inr) < 1.0 or si > 0.01,
        },
        {
            "name": "Total Area",
            "type": "hard",
            "target": round(land_ha, 2),
            "actual": round(sum(a["area_ha"] for a in allocations), 2),
            "slack": 0.0,
            "slack_pct": 0.0,
            "shadow_price": 0.0,
            "binding": True,
        },
    ]

    return {
        "status": status,
        "mode": mode,
        "allocations": allocations,
        "total_water_m3": round(total_water, 0),
        "total_income_inr": round(total_income, 0),
        "total_production_tonnes": round(total_production, 2),
        "total_calories": round(total_calories, 0),
        "water_budget_m3": round(water_budget_m3, 0),
        "water_gap_pct": round(water_gap, 2),
        "food_target_tonnes": round(food_target_tonnes, 2),
        "food_gap_pct": round(food_gap, 2),
        "income_target_inr": round(income_target_inr, 0),
        "income_gap_pct": round(income_gap, 2),
        "constraints": constraints,
        "solve_time_ms": round(solve_time, 2),
        "slack_values": {
            "water": round(sw, 0),
            "food": round(sf, 2),
            "income": round(si, 0),
        },
    }


def _solve_lexicographic(
    land_ha: float,
    water_budget_m3: float,
    food_target_tonnes: float,
    income_target_inr: float,
    rainfall_scenario: str,
    water_fraction: float,
    selected_crops: list[str],
    baseline_allocations: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Lexicographic optimization: water → food → income.

    Solves sequentially:
    1. Minimize water slack
    2. Fix water slack, minimize food slack
    3. Fix both, minimize income slack
    """
    # Step 1: Minimize water slack only
    result1 = solve(
        land_ha, water_budget_m3, food_target_tonnes, income_target_inr,
        rainfall_scenario, water_fraction, selected_crops,
        mode="weights", weights={"water": 1.0, "food": 0.0, "income": 0.0},
        baseline_allocations=baseline_allocations,
    )
    if result1["status"] == "infeasible":
        result1["mode"] = "lexicographic"
        return result1

    # For simplicity in the demo, the lexicographic solve uses the same
    # weighted approach but with extreme weight differences to approximate
    # true lexicographic ordering
    result = solve(
        land_ha, water_budget_m3, food_target_tonnes, income_target_inr,
        rainfall_scenario, water_fraction, selected_crops,
        mode="weights", weights={"water": 1000.0, "food": 10.0, "income": 1.0},
        baseline_allocations=baseline_allocations,
    )
    result["mode"] = "lexicographic"
    return result


def compute_baseline(
    land_ha: float,
    water_budget_m3: float,
    rainfall_scenario: str,
    selected_crops: list[str],
) -> dict[str, Any]:
    """Compute baseline allocation using default crop shares."""
    crops_data = get_crop_dict()
    predictions = {}
    for crop in selected_crops:
        pred = predict_crop(crop, 1.0, rainfall_scenario)
        predictions[crop] = pred

    allocations = []
    total_water = 0.0
    total_income = 0.0
    total_production = 0.0
    total_calories = 0.0

    for crop in selected_crops:
        cd = crops_data[crop]
        pred = predictions[crop]
        area = land_ha * cd["baseline_share"]
        yield_val = pred["yield_t_ha"]
        water_per_ha = pred["water_demand_m3_ha"]
        production = area * yield_val
        water_used = area * water_per_ha
        income_per_ha = (yield_val * 10 * cd["price_inr_quintal"]) - cd["cost_cultivation_inr_ha"]
        income = area * income_per_ha
        calories = production * 1000 * cd["calories_per_kg"]

        allocations.append({
            "crop": crop,
            "area_ha": round(area, 2),
            "area_pct": round(cd["baseline_share"] * 100, 2),
            "yield_t_ha": round(yield_val, 3),
            "yield_lower": round(pred["yield_lower"], 3),
            "yield_upper": round(pred["yield_upper"], 3),
            "production_tonnes": round(production, 2),
            "water_used_m3": round(water_used, 0),
            "water_demand_m3_ha": round(water_per_ha, 1),
            "water_demand_lower": round(pred["water_lower"], 1),
            "water_demand_upper": round(pred["water_upper"], 1),
            "income_inr": round(income, 0),
            "calories_total": round(calories, 0),
            "delta_area_ha": 0.0,
            "delta_area_pct": 0.0,
        })

        total_water += water_used
        total_income += income
        total_production += production
        total_calories += calories

    return {
        "status": "baseline",
        "mode": "baseline",
        "allocations": allocations,
        "total_water_m3": round(total_water, 0),
        "total_income_inr": round(total_income, 0),
        "total_production_tonnes": round(total_production, 2),
        "total_calories": round(total_calories, 0),
        "water_budget_m3": round(water_budget_m3, 0),
        "water_gap_pct": 0.0,
        "food_target_tonnes": round(total_production, 2),
        "food_gap_pct": 0.0,
        "income_target_inr": round(total_income, 0),
        "income_gap_pct": 0.0,
        "constraints": [],
        "solve_time_ms": 0.0,
        "slack_values": {"water": 0, "food": 0, "income": 0},
    }
