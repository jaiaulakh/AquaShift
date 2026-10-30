"""Deterministic template fallback for AI explanations.

Used when no LLM key is available, or when LLM output fails validation.
Templates produce consistent, accurate summaries from optimizer JSON.
"""

from __future__ import annotations

from typing import Any


def generate_template_explanation(
    plan: dict[str, Any],
    audience: str = "farmer",
    language: str = "en",
    baseline: dict[str, Any] | None = None,
) -> str:
    """Generate a deterministic explanation from optimizer output.

    Args:
        plan: Optimizer result dict.
        audience: "farmer" or "planner".
        language: "en" or "hi".

    Returns:
        Plain-language explanation under 180 words.
    """
    if language == "hi":
        return _hindi_template(plan, audience, baseline)
    return _english_template(plan, audience, baseline)


def _english_template(
    plan: dict[str, Any],
    audience: str,
    baseline: dict[str, Any] | None,
) -> str:
    """English template."""
    status = plan.get("status", "unknown")
    allocs = plan.get("allocations", [])
    total_water = plan.get("total_water_m3", 0)
    water_budget = plan.get("water_budget_m3", 0)
    total_income = plan.get("total_income_inr", 0)
    total_prod = plan.get("total_production_tonnes", 0)
    water_gap = plan.get("water_gap_pct", 0)
    food_gap = plan.get("food_gap_pct", 0)
    income_gap = plan.get("income_gap_pct", 0)

    # Top crops by area
    sorted_allocs = sorted(allocs, key=lambda a: a["area_ha"], reverse=True)
    top3 = sorted_allocs[:3]

    # Changes vs baseline
    changes = []
    for a in allocs:
        delta = a.get("delta_area_ha", 0)
        if abs(delta) > 1:
            direction = "increased" if delta > 0 else "reduced"
            changes.append(f"{a['crop']} {direction} by {abs(delta):.0f} ha")

    if audience == "farmer":
        headline = "🌾 Your Optimized Crop Plan"
        if status == "feasible_with_slack":
            headline = "⚠️ Best Possible Plan Under Tight Constraints"
    else:
        headline = f"Optimization Result: {status.replace('_', ' ').title()}"

    lines = [f"**{headline}**\n"]

    # What the plan looks like
    crop_summary = ", ".join(f"{a['crop']} ({a['area_pct']:.0f}%)" for a in top3)
    lines.append(f"The plan allocates land across {crop_summary}.")

    # Changes
    if changes:
        lines.append(f"Key changes: {'; '.join(changes[:3])}.")

    # KPIs
    lines.append(
        f"Water usage: {total_water:,.0f} m³ of {water_budget:,.0f} m³ budget "
        f"({water_gap:.0f}% gap)." if water_gap > 0 else
        f"Water usage: {total_water:,.0f} m³ — within the {water_budget:,.0f} m³ budget."
    )
    lines.append(f"Total production: {total_prod:,.0f} tonnes. Net income: ₹{total_income:,.0f}.")

    # Gaps
    if food_gap > 0:
        lines.append(f"⚠️ Food production is {food_gap:.0f}% below the target.")
    if income_gap > 0:
        lines.append(f"⚠️ Income is {income_gap:.0f}% below the target.")

    # Risk
    if status == "feasible_with_slack":
        lines.append(
            "**Biggest risk:** Not all targets can be met simultaneously. "
            "Consider reducing water-intensive crops or relaxing income targets."
        )

    # Next steps
    if audience == "farmer":
        lines.append("**Next steps:** Discuss this plan with your FPO and local agronomist.")
    else:
        lines.append("**Next steps:** Review constraint shadow prices to identify high-impact interventions.")

    return "\n".join(lines)


def _hindi_template(
    plan: dict[str, Any],
    audience: str,
    baseline: dict[str, Any] | None,
) -> str:
    """Hindi template."""
    allocs = plan.get("allocations", [])
    total_water = plan.get("total_water_m3", 0)
    water_budget = plan.get("water_budget_m3", 0)
    total_income = plan.get("total_income_inr", 0)
    total_prod = plan.get("total_production_tonnes", 0)
    status = plan.get("status", "")

    sorted_allocs = sorted(allocs, key=lambda a: a["area_ha"], reverse=True)
    top3 = sorted_allocs[:3]
    crop_summary = ", ".join(f"{a['crop']} ({a['area_pct']:.0f}%)" for a in top3)

    lines = [
        "**🌾 आपकी अनुकूलित फसल योजना**\n",
        f"यह योजना भूमि को इस प्रकार बाँटती है: {crop_summary}।",
        f"पानी का उपयोग: {total_water:,.0f} m³ (बजट: {water_budget:,.0f} m³)।",
        f"कुल उत्पादन: {total_prod:,.0f} टन। शुद्ध आय: ₹{total_income:,.0f}।",
    ]

    if status == "feasible_with_slack":
        lines.append("⚠️ सभी लक्ष्य एक साथ पूरे नहीं हो सकते। पानी की बचत वाली फसलों पर विचार करें।")

    lines.append("**अगला कदम:** अपने FPO और कृषि विशेषज्ञ से चर्चा करें।")
    return "\n".join(lines)
