# Architecture — AquaShift

## System Overview

AquaShift follows a strict three-layer pipeline:

```
ML PREDICTS → OPTIMIZATION DECIDES → AI EXPLAINS
```

The LLM is never the source of truth. Every number comes from OR-Tools or scikit-learn.

---

## Data Flow

```mermaid
sequenceDiagram
    participant UI as Frontend (React)
    participant API as FastAPI
    participant ML as ML Predictor
    participant OPT as OR-Tools GLOP
    participant LLM as Claude / Template

    UI->>API: POST /api/optimize (scenario)
    API->>ML: predict_all_crops(water_frac, rainfall)
    ML-->>API: yield_t_ha, water_demand per crop
    API->>OPT: solve(land, water, targets, predictions)
    OPT-->>API: allocations, slack, shadow prices
    API-->>UI: plan JSON
    UI->>API: POST /api/explain (plan JSON)
    API->>LLM: explain_plan(plan JSON)
    LLM-->>API: text + validation
    API-->>UI: explanation (verified)
```

---

## Optimizer Model

### Decision Variables
- `x[crop]` ∈ [min_ha, max_ha] — hectares allocated per crop (continuous)

### Hard Constraints
- Total area: Σ x[crop] ≤ land_ha
- Per-crop bounds: land_ha × min_share ≤ x[crop] ≤ land_ha × max_share

### Soft Constraints (with slack)
- Water: Σ(x[crop] × water_demand[crop]) − slack_water ≤ water_budget
- Food: Σ(x[crop] × yield[crop]) + slack_food ≥ food_target
- Income: Σ(x[crop] × income_per_ha[crop]) + slack_income ≥ income_target

### Objective
Minimize: Σ(w[i] × slack[i] / target[i]) + ε × Σ(x[crop] × water[crop])

Where ε = 1e-9 (tie-breaker: minimize water use among equivalent slack solutions)

### Shadow Prices
Extracted from GLOP dual values — report "value of relaxing each constraint by 1 unit".

---

## ML Model

- **Algorithm:** RandomForest (50 trees, max_depth=10, min_samples_leaf=5)
- **Features:** water_fraction, rainfall_fraction, yield_stress_multiplier, ky
- **Targets:** yield_t_ha, water_demand_m3_ha (separate models per crop)
- **Training data:** 5,000 rows from FAO yield-response-to-water model with noise
- **Uncertainty:** P10–P90 from individual tree predictions

### FAO Yield-Response Model
```
Ya/Ym = 1 − Ky × (1 − ETa/ETm)
```
Where Ya = actual yield, Ym = max yield, Ky = drought sensitivity, ETa/ETm = water fraction.

---

## Stress Test Pipeline

1. Compute baseline allocation (paddy-heavy, default shares)
2. Apply extreme parameters: water −80%, income target +50%, food target +10%
3. **Strict solve** (no slack) → expected INFEASIBLE
4. **Relaxed solve** (with slack) → closest feasible plan
5. **Bottleneck diagnosis** → rank constraints by causal impact:
   - Water gets 2× causal weight (upstream root cause)
   - Income/Food classified by actual gap percentage
   - Result: Water=Critical, Income=High, Food=Moderate

---

## API Layer

- **Framework:** FastAPI with Pydantic v2 schemas
- **Validation:** All inputs bounded (land: 1–100,000 ha; water change: −100% to +100%)
- **Error handling:** Global exception handler, no stack traces to client
- **Caching:** In-memory dict keyed by scenario parameters
- **CORS:** Allow all origins (hackathon setting)

---

## Frontend Architecture

- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS v4 (via @tailwindcss/vite)
- **Charts:** Recharts (BarChart, LineChart)
- **State:** useState hooks (no Redux — app is simple enough)
- **i18n:** EN/HI strings object with type-safe keys
- **Demo Mode:** useRef abort controller, sequential API calls with timed captions

---

## LLM Integration

### Safety Rules
1. LLM NEVER computes, changes, or invents numbers
2. Every number in AI text is post-validated against plan JSON
3. Tolerance: 5% relative, same order-of-magnitude
4. On validation failure → deterministic template fallback
5. No API key → template fallback (zero-dependency, always works)

### Template Engine
- f-string based, no Jinja2 dependency needed
- Supports EN and HI languages
- Under 180 words
- Structure: headline → changes → costs/gains → risk → next steps
