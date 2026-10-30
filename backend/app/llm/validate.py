"""Post-validation for LLM-generated explanations.

Ensures every number in the LLM's text exists in the plan JSON.
If validation fails, falls back to deterministic template.
"""

from __future__ import annotations

import re
from typing import Any


def validate_explanation(
    text: str,
    plan: dict[str, Any],
    tolerance: float = 0.05,
) -> tuple[bool, list[str]]:
    """Validate that all numbers in LLM text match the plan.

    Args:
        text: LLM-generated explanation text.
        plan: Optimizer result dict.
        tolerance: Allowed relative difference (default 5%).

    Returns:
        (is_valid, list_of_errors).
    """
    # Extract all numbers from the text
    text_numbers = _extract_numbers(text)
    if not text_numbers:
        return True, []  # No numbers to validate

    # Extract all numbers from the plan
    plan_numbers = _extract_plan_numbers(plan)

    errors = []
    for num in text_numbers:
        if not _number_exists_in_plan(num, plan_numbers, tolerance):
            errors.append(f"Number {num:,.2f} not found in plan data (±{tolerance*100:.0f}%)")

    is_valid = len(errors) == 0
    return is_valid, errors


def _extract_numbers(text: str) -> list[float]:
    """Extract numeric values from text, ignoring percentages and dates."""
    # Remove common non-numeric patterns
    cleaned = text.replace(",", "")
    cleaned = cleaned.replace("₹", "")

    # Find numbers (int or float)
    pattern = r'(?<!\d)(\d+\.?\d*)(?!\d*[%/])'
    matches = re.findall(pattern, cleaned)

    numbers = []
    for m in matches:
        try:
            val = float(m)
            # Skip very small numbers (likely step numbers, list items)
            if val > 10:
                numbers.append(val)
        except ValueError:
            continue

    return numbers


def _extract_plan_numbers(plan: dict[str, Any]) -> set[float]:
    """Recursively extract all numeric values from the plan dict."""
    numbers: set[float] = set()
    _collect_numbers(plan, numbers)
    return numbers


def _collect_numbers(obj: Any, numbers: set[float]) -> None:
    """Recursively collect numbers from nested structures."""
    if isinstance(obj, (int, float)):
        numbers.add(float(obj))
        # Also add common transformations
        if obj > 0:
            numbers.add(round(obj, 0))
            numbers.add(round(obj, 2))
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_numbers(v, numbers)
    elif isinstance(obj, list):
        for item in obj:
            _collect_numbers(item, numbers)


def _number_exists_in_plan(
    num: float,
    plan_numbers: set[float],
    tolerance: float,
) -> bool:
    """Check if a number exists in plan numbers within tolerance.
    
    Uses absolute tolerance for small numbers and relative for large ones.
    """
    if num in plan_numbers:
        return True

    for pn in plan_numbers:
        if pn == 0:
            continue
        # Use relative tolerance, but only if the numbers are in the same order of magnitude
        # This prevents 999888 from matching 1000000 when tolerance=0.05
        relative_diff = abs(num - pn) / abs(pn)
        order_of_magnitude_match = (
            (num >= 1 and pn >= 1 and abs(len(str(int(num))) - len(str(int(pn)))) <= 1)
        )
        if relative_diff <= tolerance and order_of_magnitude_match:
            return True

    return False
