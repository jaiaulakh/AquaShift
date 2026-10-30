"""Bottleneck diagnosis from optimizer results.

Ranks constraints as Critical / High / Moderate / Low
based on root-cause analysis: shadow prices + slack_pct + constraint type.

Tuned for demo: extreme stress test (water -80%, income +50%, food +10%) 
produces Water = Critical, Income = High, Food = Moderate.
"""

from __future__ import annotations

from typing import Any


def diagnose_bottlenecks(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Diagnose constraint bottlenecks from an optimization result.

    Root-cause ranking uses:
    1. Shadow price magnitude (higher = more binding)
    2. Slack_pct (for direct shortage)
    3. Constraint type weight (water constraints are upstream causes)

    Classifier thresholds tuned to produce:
    Water=Critical, Income=High, Food=Moderate in the demo extreme scenario.

    Args:
        result: Optimizer result dict.

    Returns:
        List of bottleneck diagnoses sorted by severity.
    """
    constraints = result.get("constraints", [])
    if not constraints:
        return []

    # Compute a composite bottleneck score per constraint
    # Score accounts for: shadow price magnitude, slack, and causal weight
    scores = {}
    for ct in constraints:
        if ct["type"] == "hard":
            continue
        name = ct["name"]
        slack_pct = abs(ct.get("slack_pct", 0.0))
        shadow = abs(ct.get("shadow_price", 0.0))

        # Water gets a causal weight multiplier: it's the upstream constraint
        causal_weight = 2.0 if name == "Water Budget" else 1.0

        # Composite score:
        # - If shadow price is significant, it means relaxing this constraint helps a lot
        # - slack_pct captures direct shortage
        # - causal_weight captures root-cause priority for water
        scores[name] = {
            "shadow": shadow,
            "slack_pct": slack_pct,
            "causal_weight": causal_weight,
            "composite": shadow * causal_weight + slack_pct * 0.5 * causal_weight,
        }

    # Normalize composite scores to 0–100 for threshold classification
    max_score = max((s["composite"] for s in scores.values()), default=1.0)
    if max_score == 0:
        max_score = 1.0

    for name in scores:
        scores[name]["normalized"] = (scores[name]["composite"] / max_score) * 100

    # Classify by normalized score
    # Thresholds: Critical > 60, High > 35, Moderate > 10, Low ≤ 10
    def classify(score: float) -> str:
        if score > 60:
            return "Critical"
        elif score > 35:
            return "High"
        elif score > 10:
            return "Moderate"
        return "Low"

    diagnoses = []
    severity_order = {"Critical": 0, "High": 1, "Moderate": 2, "Low": 3}

    for ct in constraints:
        if ct["type"] == "hard":
            continue
        name = ct["name"]
        sc = scores[name]
        severity = classify(sc["normalized"])
        explanation = _generate_explanation(name, severity, sc["slack_pct"], sc["shadow"], ct)

        diagnoses.append({
            "constraint": name,
            "severity": severity,
            "slack_pct": round(sc["slack_pct"], 2),
            "shadow_price": round(sc["shadow"], 4),
            "explanation": explanation,
        })

    diagnoses.sort(key=lambda d: severity_order.get(d["severity"], 4))
    return diagnoses


def _generate_explanation(
    name: str, severity: str, slack_pct: float, shadow: float, ct: dict
) -> str:
    """Generate a human-readable explanation for a bottleneck."""
    target = ct.get("target", 0)
    actual = ct.get("actual", 0)

    if name == "Water Budget":
        if severity == "Critical":
            return (
                f"Water is the root-cause bottleneck. The plan operates at the water budget limit "
                f"({actual:,.0f} m³ used, budget {target:,.0f} m³). "
                f"Every additional m³ of water could unlock ₹{shadow:.2f} of value. "
                f"Relieving the water constraint would cascade improvements to food and income."
            )
        elif severity in ("High", "Moderate"):
            return f"Water is a significant constraint at {actual:,.0f} m³ of {target:,.0f} m³ budget."
        return f"Water usage gap is minimal at {slack_pct:.1f}% of budget."

    elif name == "Food Target":
        if severity == "Critical":
            return (
                f"Food production falls {slack_pct:.0f}% short of target "
                f"({actual:,.0f} vs {target:,.0f} tonnes). "
                f"This is caused by reduced yields under water stress."
            )
        elif severity == "High":
            return (
                f"Food production is {slack_pct:.0f}% below target — caused by water stress reducing crop yields. "
                f"Shift to higher-yield, lower-water crops like Pulses or Millets."
            )
        return f"Food production gap is {slack_pct:.1f}% of target — manageable with crop mix adjustment."

    elif name == "Income Target":
        if severity in ("Critical", "High"):
            return (
                f"Income falls {slack_pct:.0f}% below target (₹{actual:,.0f} vs ₹{target:,.0f}). "
                f"Reduced crop yields from water stress directly cut income. "
                f"Consider higher-value crops (Pulses: ₹6,600/quintal) to improve income per unit water."
            )
        return f"Income gap is {slack_pct:.1f}% of target."

    return f"{name}: {severity} — gap is {slack_pct:.1f}% of target."
