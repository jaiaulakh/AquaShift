"""Tests for LLM explain module — especially template fallback and validation."""

import sys
import asyncio
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))


def test_template_fallback_no_key(monkeypatch):
    """Explanation works with no API key (template fallback)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from app.llm.explain import explain_plan

    plan = {
        "status": "optimal",
        "allocations": [
            {"crop": "Paddy", "area_ha": 300, "area_pct": 30, "yield_t_ha": 4.0,
             "production_tonnes": 1200, "water_used_m3": 4200000, "income_inr": 630000,
             "delta_area_ha": -150, "delta_area_pct": -33.3},
            {"crop": "Wheat", "area_ha": 350, "area_pct": 35, "yield_t_ha": 3.5,
             "production_tonnes": 1225, "water_used_m3": 1575000, "income_inr": 445000,
             "delta_area_ha": 50, "delta_area_pct": 16.7},
        ],
        "total_water_m3": 5775000,
        "total_income_inr": 1075000,
        "total_production_tonnes": 2425,
        "total_calories": 0,
        "water_budget_m3": 6400000,
        "water_gap_pct": 0,
        "food_target_tonnes": 2500,
        "food_gap_pct": 3.0,
        "income_target_inr": 1100000,
        "income_gap_pct": 2.3,
    }

    result = asyncio.run(explain_plan(plan, audience="farmer", language="en"))

    assert result["source"] == "template"
    assert len(result["text"]) > 50
    assert result["verified"] is True


def test_template_hindi():
    """Hindi template produces Hindi text."""
    from app.llm.templates import generate_template_explanation

    plan = {
        "status": "optimal",
        "allocations": [
            {"crop": "Paddy", "area_ha": 300, "area_pct": 30},
        ],
        "total_water_m3": 5000000,
        "water_budget_m3": 6400000,
        "total_income_inr": 1000000,
        "total_production_tonnes": 2000,
    }

    text = generate_template_explanation(plan, "farmer", "hi")
    assert "योजना" in text  # "plan" in Hindi


def test_validation_rejects_fabricated_number():
    """Validator should reject a number not in the plan."""
    from app.llm.validate import validate_explanation

    plan = {
        "total_water_m3": 5000000,
        "total_income_inr": 1000000,
        "allocations": [{"area_ha": 300}],
    }

    # Text with a clearly fabricated number (123456 - not in plan at all)
    text = "The plan uses 123456 tonnes of water and 300 ha of land."
    is_valid, errors = validate_explanation(text, plan)
    assert not is_valid, "Should reject fabricated number"
    assert len(errors) > 0


def test_validation_accepts_plan_numbers():
    """Validator should accept numbers that exist in the plan."""
    from app.llm.validate import validate_explanation

    plan = {
        "total_water_m3": 5000000,
        "total_income_inr": 1000000,
        "allocations": [{"area_ha": 300}],
    }

    text = "The plan uses 5000000 m³ of water across 300 hectares."
    is_valid, errors = validate_explanation(text, plan)
    assert is_valid, f"Should accept plan numbers, errors: {errors}"
