"""AI explanation service using Claude (with fallback).

The LLM explains the solver's JSON in plain language.
It NEVER computes or invents numbers — only interprets what the solver produced.
"""

from __future__ import annotations

import os
from typing import Any

from app.llm.templates import generate_template_explanation
from app.llm.validate import validate_explanation


async def explain_plan(
    plan: dict[str, Any],
    audience: str = "farmer",
    language: str = "en",
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an AI explanation of the optimizer's plan.

    Tries Claude first, validates the output, falls back to template.

    Args:
        plan: Optimizer result dict.
        audience: "farmer" or "planner".
        language: "en" or "hi".
        baseline: Optional baseline plan for comparison.

    Returns:
        Dict with text, audience, language, source, verified, verification_errors.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Try LLM if key is available
    if api_key:
        try:
            llm_text = await _call_claude(plan, audience, language, baseline, api_key, model)
            is_valid, errors = validate_explanation(llm_text, plan)

            if is_valid:
                return {
                    "text": llm_text,
                    "audience": audience,
                    "language": language,
                    "source": "llm",
                    "verified": True,
                    "verification_errors": [],
                }
            else:
                # LLM output failed validation — fall back to template
                template_text = generate_template_explanation(plan, audience, language, baseline)
                return {
                    "text": template_text,
                    "audience": audience,
                    "language": language,
                    "source": "template",
                    "verified": True,
                    "verification_errors": errors,
                }
        except Exception:
            pass  # Fall through to template

    # Fallback: deterministic template
    template_text = generate_template_explanation(plan, audience, language, baseline)
    return {
        "text": template_text,
        "audience": audience,
        "language": language,
        "source": "template",
        "verified": True,
        "verification_errors": [],
    }


async def _call_claude(
    plan: dict[str, Any],
    audience: str,
    language: str,
    baseline: dict[str, Any] | None,
    api_key: str,
    model: str,
) -> str:
    """Call Claude API for explanation."""
    import anthropic
    import json

    lang_instruction = "Respond in Hindi." if language == "hi" else "Respond in English."
    audience_instruction = (
        "Write for a farmer with limited technical knowledge. Use simple language."
        if audience == "farmer" else
        "Write for a district planner. Include technical details like shadow prices."
    )

    plan_json = json.dumps(plan, indent=2, default=str)
    baseline_json = json.dumps(baseline, indent=2, default=str) if baseline else "No baseline provided."

    prompt = f"""You are an agricultural advisor explaining an optimization result.

RULES (CRITICAL):
1. You MUST NOT compute, change, or invent any numbers.
2. Every number you mention MUST come directly from the plan JSON below.
3. Keep the explanation under 180 words.
4. Structure: headline, what changes, what it costs/gains, biggest risk, next steps.
5. {audience_instruction}
6. {lang_instruction}

OPTIMIZER PLAN JSON:
{plan_json}

BASELINE (for comparison):
{baseline_json}

Generate a clear, actionable explanation."""

    client = anthropic.AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
