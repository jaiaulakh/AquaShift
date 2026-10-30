"""CLI demo script — backup for the 2-minute live demo.

Runs the full AquaShift pipeline from the command line:
  Baseline → Optimize → Stress Test → AI Insight

Works fully offline with no LLM key.
Usage: python scripts/run_demo.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

# Ensure data and models exist
from generate_data import main as gen_data
from train_model import train as train_models

from app.optimizer.model import compute_baseline, solve
from app.optimizer.stress import run_stress_test
from app.optimizer.sweep import run_sweep
from app.ml.predictor import predict_all_crops
from app.llm.templates import generate_template_explanation

LAND = 1000.0
WATER = 8_000_000.0
CROPS = ["Paddy", "Wheat", "Maize", "Pulses", "Millets"]


def sep(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def main() -> None:
    """Run the full demo pipeline."""
    print("\n" + "🌊 "*10)
    print("  AquaShift — Water-Constrained Crop Planning Simulator")
    print("  NullPointers · Zinnovatio 4.0 · AgriTech Track")
    print("🌊 "*10)

    # ── Step 0: Ensure data/models ──────────────────────────────
    sep("SETUP: Generating data and training models")
    data_path = ROOT / "data" / "training_data.csv"
    model_path = ROOT / "models" / "crop_models.joblib"

    if not data_path.exists():
        print("  Generating training data...")
        gen_data()
    else:
        print(f"  ✓ Training data exists: {data_path.name}")

    if not model_path.exists():
        print("  Training ML models...")
        train_models()
    else:
        print(f"  ✓ Models exist: {model_path.name}")

    input("\n  [Press Enter to start the demo]")

    # ── Step 1: Baseline ─────────────────────────────────────────
    sep("STEP 1: BASELINE PLAN (Punjab-Haryana paddy-wheat belt)")
    baseline = compute_baseline(LAND, WATER, "Normal", CROPS)
    print(f"  Region: Punjab-Haryana Belt")
    print(f"  Land: {LAND:,.0f} ha | Water: {WATER/1e6:.1f}M m³")
    print()
    for a in baseline["allocations"]:
        bar = "█" * int(a["area_pct"] / 3)
        print(f"  {a['crop']:8s} {bar:20s} {a['area_pct']:4.0f}%  ({a['area_ha']:5.0f} ha)")

    print(f"\n  Total Production: {baseline['total_production_tonnes']:,.0f} t")
    print(f"  Total Income:     ₹{baseline['total_income_inr']/1e5:.1f}L")
    print(f"  Total Water:      {baseline['total_water_m3']/1e6:.2f}M m³")

    # ── Step 2: ML Predictions ───────────────────────────────────
    sep("STEP 2: ML PREDICTIONS — Water stress scenario")
    print("  Scenario: Water −20%, Deficit rainfall")
    print("  Model: RandomForest (yield R² ≈ 0.97, water R² ≈ 0.99)")
    print()

    preds = predict_all_crops(0.8, "Deficit")
    print(f"  {'Crop':8s} {'Yield (t/ha)':>14s} {'Range':>18s} {'Water (m³/ha)':>14s}")
    print("  " + "-"*60)
    for p in preds:
        print(f"  {p['crop']:8s} {p['yield_t_ha']:>14.3f} "
              f"[{p['yield_lower']:.2f}–{p['yield_upper']:.2f}] "
              f"{p['water_demand_m3_ha']:>14.0f}")

    # ── Step 3: Optimize ─────────────────────────────────────────
    sep("STEP 3: OPTIMIZER — OR-Tools GLOP LP")
    print("  Water budget: −20%  |  Mode: Weighted slack minimization")
    print("  Solving...", end=" ", flush=True)

    baseline_alloc = {a["crop"]: a["area_ha"] for a in baseline["allocations"]}
    t0 = time.perf_counter()
    result = solve(
        land_ha=LAND,
        water_budget_m3=WATER * 0.8,
        food_target_tonnes=baseline["total_production_tonnes"],
        income_target_inr=baseline["total_income_inr"],
        rainfall_scenario="Deficit",
        water_fraction=0.8,
        selected_crops=CROPS,
        mode="weights",
        baseline_allocations=baseline_alloc,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"Done in {elapsed:.1f} ms")

    print(f"\n  Status: {result['status'].upper()}")
    print()
    for a in result["allocations"]:
        delta = a["delta_area_ha"]
        sign = "▲" if delta > 0 else "▼" if delta < 0 else "─"
        bar = "█" * int(a["area_pct"] / 3)
        print(f"  {a['crop']:8s} {bar:20s} {a['area_pct']:4.0f}%  "
              f"{sign}{abs(delta):4.0f} ha  ₹{a['income_inr']/1e5:.1f}L")

    print(f"\n  Water used:  {result['total_water_m3']/1e6:.2f}M m³ "
          f"(budget: {WATER*0.8/1e6:.2f}M m³)")
    print(f"  Production:  {result['total_production_tonnes']:,.0f} t "
          f"(target: {baseline['total_production_tonnes']:,.0f} t)")
    print(f"  Income:      ₹{result['total_income_inr']/1e5:.1f}L "
          f"(target: ₹{baseline['total_income_inr']/1e5:.1f}L)")

    if result["food_gap_pct"] > 0:
        print(f"\n  ⚠️  Food gap: {result['food_gap_pct']:.1f}%")
    if result["income_gap_pct"] > 0:
        print(f"  ⚠️  Income gap: {result['income_gap_pct']:.1f}%")

    # ── Step 4: Stress Test ──────────────────────────────────────
    sep("STEP 4: STRESS TEST — Extreme scenario")
    print("  Water: −80%  |  Income target: +50%  |  Food target: +10%")
    print("  Running strict solve...", end=" ", flush=True)

    stress = run_stress_test(LAND, WATER, "Normal", CROPS)
    print("Done")

    print(f"\n  Standard solver:  {stress['strict_status'].upper()}")
    print(f"  AquaShift:        Closest feasible plan found\n")
    print("  BOTTLENECK DIAGNOSIS:")
    icons = {"Critical": "🚨", "High": "⚠️ ", "Moderate": "📊", "Low": "✅"}
    for b in stress["bottlenecks"]:
        icon = icons.get(b["severity"], "  ")
        print(f"  {icon} {b['constraint']:16s} [{b['severity']:8s}]  gap={b['slack_pct']:.0f}%")
        print(f"      {b['explanation'][:80]}...")

    # ── Step 5: AI Insight ───────────────────────────────────────
    sep("STEP 5: AI INSIGHT — Template fallback (offline mode)")
    print("  No LLM key required. Deterministic template from solver JSON.\n")

    insight = generate_template_explanation(result, "farmer", "en", baseline)
    for line in insight.split("\n"):
        print(f"  {line}")

    # ── Done ─────────────────────────────────────────────────────
    sep("DEMO COMPLETE")
    print("  AquaShift: Plan crops. Balance water. Protect livelihoods.")
    print()
    print("  Key differentiators:")
    print("  ✓ ML predicts (RandomForest, FAO yield-response model)")
    print("  ✓ Optimization decides (OR-Tools GLOP LP, never INFEASIBLE)")
    print("  ✓ AI explains (Claude + deterministic fallback)")
    print("  ✓ Works fully offline · Reproducible · No database")
    print("  ✓ Stress test surfaces bottleneck diagnosis")
    print()


if __name__ == "__main__":
    main()
