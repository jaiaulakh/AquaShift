# Judging Notes — AquaShift

## 5 Likely Judge Questions + Strong Answers

---

### Q1: "Why not just ask ChatGPT?"

**Answer:**

ChatGPT hallucinates numbers. It cannot solve an LP. It has no constraint system.

AquaShift enforces a strict separation:
- **ML predicts** → scikit-learn RandomForest, trained on FAO yield-response data
- **Optimization decides** → OR-Tools GLOP, a production-grade linear programming solver
- **AI explains** → Claude (or a deterministic template) interprets the solver's JSON

The LLM is the last step, not the source of truth. We post-validate every number in the AI's text against the solver output. If a number doesn't match within ±5%, we fall back to a template. 

ChatGPT can't guarantee feasibility, can't compute shadow prices, can't handle hard constraints. We can — in under 50ms.

---

### Q2: "Where does your data come from?"

**Answer:**

We're transparent: all data is **synthetic demo data calibrated to public agri-statistics**.

Our numbers are calibrated to:
- **ICAR** district crop yield averages
- **CACP** cost-of-cultivation reports
- **GoI MSP 2023–24** prices
- **FAO Irrigation & Drainage Paper 33** (yield-response-to-water, Ky coefficients)
- **USDA FoodData Central** (calorie values)

The `data/ASSUMPTIONS.md` file lists every assumed number and its source.

For production, our `data/loaders/` directory has documented stubs for each real data source — CGWB groundwater data, IMD weather, Agmarknet prices — with expected schemas. Swapping in real data requires changing one file, not rebuilding the system.

---

### Q3: "How do you protect farmer income?"

**Answer:**

Income is a **soft constraint** in the optimizer with a non-negative slack variable. This means:

1. The solver *always* tries to meet the income target first.
2. If it can't (e.g., extreme water stress), it finds the closest feasible plan and reports *exactly* how far short it is — in rupees and percentage.
3. Shadow prices tell us: "1 extra m³ of water is worth ₹X in income" — actionable for policy.

We also provide a **lexicographic optimization mode** that prioritises water → food → income sequentially, so farmers can see what income sacrifice is needed to meet water limits first.

The stress test bottleneck diagnosis explicitly surfaces whether income is a root-cause problem (rare) or a downstream consequence of water shortage (common) — so interventions can be targeted correctly.

---

### Q4: "What if the ML model is wrong?"

**Answer:**

Three defences:

1. **Uncertainty ranges** — Every prediction comes with P10–P90 intervals from the RandomForest ensemble. The UI displays these as confidence bands.

2. **The optimizer is model-agnostic** — The solver takes yield predictions as inputs. If the predictions change (better model, real data), the solver still works correctly.

3. **Honest labelling** — The UI footer and README explicitly state: *"Synthetic demo data — not a substitute for agronomic advice."* The model is a scenario planner, not a prescription system.

In production, we'd replace the RandomForest with a calibrated ensemble trained on actual district-level ICAR yield data, with cross-validation and out-of-sample testing documented in `docs/architecture.md`.

---

### Q5: "How would this scale to real districts?"

**Answer:**

**Technically:** The LP is O(n·m) where n=crops, m=constraints. Adding 50 crops and 100 constraints would still solve in milliseconds on GLOP. The ML models are per-crop, so adding a new crop means training one more RandomForest on district data.

**Data-wise:** We have documented stubs (`data/loaders/`) for every real source — CGWB groundwater, IMD weather, ICAR yields, Agmarknet prices. Real data plugs in at those connectors without changing the optimizer or UI.

**Operationally:** A district FPO pilot would run on a simple server or even a laptop. No internet required for the core pipeline. The LLM is optional.

**What we'd add next:** Multi-season rotation constraints, soil health variables, satellite-derived ET from ISRO Bhuvan data, and price volatility scenarios using APEDA market data.

The architecture is designed for this: no database, no auth, no microservices — just a well-typed FastAPI + OR-Tools core that scales by adding more crop and constraint rows to the CSVs.

---

## Key Metrics for the Pitch

| Metric | Value |
|--------|-------|
| ML model R² (yield) | 0.97–0.99 |
| Optimizer solve time | < 50 ms |
| Test coverage | 27 tests, all passing |
| Lines of Python | ~1,200 |
| Lines of TypeScript | ~900 |
| Works offline | ✓ (no LLM key, no internet) |
| Demo reproducibility | Seeded (SHA256 verified) |
