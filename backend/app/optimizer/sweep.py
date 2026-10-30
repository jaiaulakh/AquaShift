"""Water sweep simulation — vary water from 0% to -80% and observe impacts."""

from __future__ import annotations

from typing import Any

from app.optimizer.model import solve, compute_baseline


def run_sweep(
    land_ha: float,
    water_budget_m3: float,
    rainfall_scenario: str,
    selected_crops: list[str],
    steps: int = 17,
) -> dict[str, Any]:
    """Simulate water cuts from 0% to -80% in steps.

    Args:
        land_ha: Total land.
        water_budget_m3: Original water budget.
        rainfall_scenario: Weather scenario.
        selected_crops: Crops to consider.
        steps: Number of steps.

    Returns:
        Dict with points (list of sweep results) and tipping_point_pct.
    """
    baseline = compute_baseline(land_ha, water_budget_m3, rainfall_scenario, selected_crops)
    baseline_alloc = {a["crop"]: a["area_ha"] for a in baseline["allocations"]}
    baseline_income = baseline["total_income_inr"]
    baseline_production = baseline["total_production_tonnes"]

    points = []
    tipping_point = None
    prev_paddy_pct = None

    for i in range(steps):
        cut_pct = -80.0 * i / (steps - 1)  # 0% to -80%
        water_frac = 1.0 + cut_pct / 100.0
        stressed_water = water_budget_m3 * water_frac

        # Use baseline values as targets
        result = solve(
            land_ha=land_ha,
            water_budget_m3=stressed_water,
            food_target_tonnes=baseline_production,
            income_target_inr=baseline_income,
            rainfall_scenario=rainfall_scenario,
            water_fraction=water_frac,
            selected_crops=selected_crops,
            mode="weights",
            allow_slack=True,
            baseline_allocations=baseline_alloc,
        )

        # Find paddy allocation
        paddy_alloc = next(
            (a for a in result["allocations"] if a["crop"] == "Paddy"),
            None
        )
        paddy_ha = paddy_alloc["area_ha"] if paddy_alloc else 0
        paddy_pct = paddy_alloc["area_pct"] if paddy_alloc else 0

        point = {
            "water_change_pct": round(cut_pct, 1),
            "total_income_inr": result["total_income_inr"],
            "total_production_tonnes": result["total_production_tonnes"],
            "paddy_area_ha": round(paddy_ha, 2),
            "paddy_area_pct": round(paddy_pct, 2),
            "status": result["status"],
        }
        points.append(point)

        # Detect tipping point: where paddy drops significantly or income falls > 10%
        if prev_paddy_pct is not None and tipping_point is None:
            if paddy_pct < prev_paddy_pct * 0.9 or result["income_gap_pct"] > 10:
                tipping_point = cut_pct
        prev_paddy_pct = paddy_pct

    return {
        "points": points,
        "tipping_point_pct": round(tipping_point, 1) if tipping_point is not None else None,
    }
