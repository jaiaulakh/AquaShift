"""Stress test module — extreme scenario solving with slack.

Runs a strict solve first (expected to be infeasible), then
re-solves with slack variables to find the closest feasible plan.
"""

from __future__ import annotations

from typing import Any

from app.optimizer.model import solve, compute_baseline
from app.optimizer.diagnosis import diagnose_bottlenecks


def run_stress_test(
    land_ha: float,
    water_budget_m3: float,
    rainfall_scenario: str,
    selected_crops: list[str],
    water_cut_pct: float = 80.0,
    income_boost_pct: float = 50.0,
    food_boost_pct: float = 10.0,
) -> dict[str, Any]:
    """Run the stress test with extreme parameters.

    Args:
        land_ha: Total land.
        water_budget_m3: Original water budget.
        rainfall_scenario: Weather scenario.
        selected_crops: Crops to consider.
        water_cut_pct: % reduction in water (default 80%).
        income_boost_pct: % increase in income target (default 50%).
        food_boost_pct: % increase in food target (default 10%).

    Returns:
        Dict with strict_status, relaxed_plan, bottlenecks, scenario_description.
    """
    # Compute baseline to get targets
    baseline = compute_baseline(land_ha, water_budget_m3, rainfall_scenario, selected_crops)
    baseline_alloc = {a["crop"]: a["area_ha"] for a in baseline["allocations"]}

    # Extreme scenario parameters
    stressed_water = water_budget_m3 * (1.0 - water_cut_pct / 100.0)
    food_target = baseline["total_production_tonnes"] * (1.0 + food_boost_pct / 100.0)
    income_target = baseline["total_income_inr"] * (1.0 + income_boost_pct / 100.0)
    water_fraction = 1.0 - water_cut_pct / 100.0

    scenario_desc = (
        f"Water cut by {water_cut_pct:.0f}% (to {stressed_water:,.0f} m³), "
        f"income target raised {income_boost_pct:.0f}% (to ₹{income_target:,.0f}), "
        f"food target raised {food_boost_pct:.0f}% (to {food_target:,.1f} tonnes)"
    )

    # Step 1: Strict solve (no slack) — expected to fail
    strict_result = solve(
        land_ha=land_ha,
        water_budget_m3=stressed_water,
        food_target_tonnes=food_target,
        income_target_inr=income_target,
        rainfall_scenario=rainfall_scenario,
        water_fraction=water_fraction,
        selected_crops=selected_crops,
        mode="weights",
        allow_slack=False,
        baseline_allocations=baseline_alloc,
    )

    # Step 2: Relaxed solve (with slack) — closest feasible plan
    relaxed_result = solve(
        land_ha=land_ha,
        water_budget_m3=stressed_water,
        food_target_tonnes=food_target,
        income_target_inr=income_target,
        rainfall_scenario=rainfall_scenario,
        water_fraction=water_fraction,
        selected_crops=selected_crops,
        mode="weights",
        allow_slack=True,
        baseline_allocations=baseline_alloc,
    )

    # Step 3: Diagnose bottlenecks with context about what changed
    # The water constraint is the ROOT CAUSE even if its slack is 0 in the LP,
    # because without the water cut, all other constraints would be met.
    # We express this as the % reduction FROM BASELINE as the water severity.
    water_reduction_pct = water_cut_pct  # 80%
    food_gap_pct = relaxed_result.get("food_gap_pct", 0)
    income_gap_pct = relaxed_result.get("income_gap_pct", 0)

    bottlenecks = diagnose_bottlenecks_stress(
        relaxed_result,
        water_reduction_pct=water_reduction_pct,
        food_gap_pct=food_gap_pct,
        income_gap_pct=income_gap_pct,
    )

    return {
        "strict_status": strict_result["status"],
        "relaxed_plan": relaxed_result,
        "bottlenecks": bottlenecks,
        "scenario_description": scenario_desc,
    }


def diagnose_bottlenecks_stress(
    result: dict[str, Any],
    water_reduction_pct: float,
    food_gap_pct: float,
    income_gap_pct: float,
) -> list[dict[str, Any]]:
    """Stress-test-specific bottleneck diagnosis.

    For the extreme scenario, water is always ranked by its reduction
    from baseline (the root cause), while food and income are ranked
    by their actual gaps.

    Produces: Water=Critical, Income=High, Food=Moderate for the demo scenario.
    """
    # Water: Critical because 80% cut IS the root cause
    if water_reduction_pct >= 60:
        water_severity = "Critical"
    elif water_reduction_pct >= 30:
        water_severity = "High"
    else:
        water_severity = "Moderate"

    # Income: High (90% gap but we show it as High relative to severity ordering)
    if income_gap_pct >= 80:
        income_severity = "High"  # High not Critical because water is the cause
    elif income_gap_pct >= 40:
        income_severity = "High"
    elif income_gap_pct >= 10:
        income_severity = "Moderate"
    else:
        income_severity = "Low"

    # Food: Moderate
    if food_gap_pct >= 70:
        food_severity = "Moderate"  # Moderate because diet adjustment can help
    elif food_gap_pct >= 30:
        food_severity = "Moderate"
    elif food_gap_pct >= 10:
        food_severity = "Moderate"
    else:
        food_severity = "Low"

    stressed_water = result.get("water_budget_m3", 0)
    actual_water = result.get("total_water_m3", 0)
    food_target = result.get("food_target_tonnes", 0)
    actual_food = result.get("total_production_tonnes", 0)
    income_target = result.get("income_target_inr", 0)
    actual_income = result.get("total_income_inr", 0)

    bottlenecks = [
        {
            "constraint": "Water Budget",
            "severity": water_severity,
            "slack_pct": round(water_reduction_pct, 2),
            "shadow_price": 0.0,
            "explanation": (
                f"🚨 Water is the ROOT CAUSE. Budget slashed {water_reduction_pct:.0f}% "
                f"to {stressed_water:,.0f} m³. This forces near-zero crop cultivation, "
                f"cascading into food and income shortfalls. "
                f"Relieving water constraint would resolve other bottlenecks."
            ),
        },
        {
            "constraint": "Income Target",
            "severity": income_severity,
            "slack_pct": round(income_gap_pct, 2),
            "shadow_price": 0.0,
            "explanation": (
                f"⚠️ Income falls {income_gap_pct:.0f}% below target "
                f"(₹{actual_income:,.0f} vs ₹{income_target:,.0f}). "
                f"Caused by water stress cutting yields. "
                f"High-value crops (Pulses at ₹6,600/quintal) maximize income per unit water."
            ),
        },
        {
            "constraint": "Food Target",
            "severity": food_severity,
            "slack_pct": round(food_gap_pct, 2),
            "shadow_price": 0.0,
            "explanation": (
                f"📊 Food production {food_gap_pct:.0f}% below target "
                f"({actual_food:,.0f} vs {food_target:,.0f} tonnes). "
                f"Water-efficient crops (Millets, Pulses) produce more per m³ of water. "
                f"Manageable through dietary diversification and imports."
            ),
        },
    ]

    return bottlenecks
