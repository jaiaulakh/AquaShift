# Demo Script — AquaShift 2-Minute Walkthrough

**Event:** Zinnovatio 4.0 · AgriTech Track  
**Team:** NullPointers  
**Duration:** ~2 minutes

---

## Setup (before presenting)

1. Run `python scripts/dev.py` — both servers should be green.
2. Open http://localhost:5173 in Chrome, full-screen.
3. Confirm the baseline allocation is visible (paddy-heavy bars showing).

---

## Script

### [0:00–0:15] Hook

> "India loses 40% of its agricultural water to paddy cultivation alone.  
> When water runs short — and it will — farmers face an impossible choice: grow less, earn less, or go thirsty.  
> AquaShift is the missing decision layer."

*Click the header logo to draw attention.*

---

### [0:15–0:40] Baseline Plan

> "Here's the current situation in a typical Punjab FPO — 1,000 hectares, paddy-heavy, 8 million cubic metres of water.  
> The pipeline shows where we are: Step 1, Scenario."

*Point to the stacked bar on the left — Paddy at 45%.*

> "This is the status quo. AquaShift knows what it costs in water, food and income."

---

### [0:40–1:05] Optimize with Water Stress

> "Now let's say the monsoon is 20% weaker this year — Deficit scenario."

*Drag the water slider to −20%. Click **Optimize Plan**.*

> "Our ML model — trained on FAO yield-response equations — predicts reduced yields.  
> OR-Tools finds the best crop mix in under 50 milliseconds.  
> Notice: Paddy drops, Pulses and Millets rise. KPI cards show green, amber, red — instantly readable."

*Point to KPI cards and the delta column.*

---

### [1:05–1:30] Stress Test — Our Differentiator

> "Now the extreme case. Water cut 80%. Income target up 50%. Food target up 10%."

*Click **Run Stress Test**.*

> "A standard LP solver just says INFEASIBLE — and stops.  
> AquaShift finds the *closest feasible plan* using slack variables — and diagnoses WHY it's hard."

*Point to the two cards: red INFEASIBLE vs green AquaShift plan.*

> "Water: Critical — it's the root cause.  
> Income: High — because low water means low yields.  
> Food: Moderate — manageable through crop diversification.  
> This is actionable intelligence, not just an error message."

---

### [1:30–1:50] AI Insight

> "Finally, the AI explanation — in the farmer's language."

*Click **Get AI Explanation** → select Farmer mode.*

> "Claude summarises the plan: what changed, what it costs, biggest risk, next steps.  
> Every number in that text is verified against the solver output.  
> And if there's no internet, no API key — a deterministic template kicks in instantly.  
> The LLM never computes. It only explains."

---

### [1:50–2:00] Close

> "AquaShift works offline. It's reproducible. No database, no auth, no satellite imagery.  
> Just solid ML, proven optimization, and honest AI.  
> Plan crops. Balance water. Protect livelihoods."

---

## Fallback (if demo breaks)

Run the CLI backup:
```bash
python scripts/run_demo.py
```
This runs the full pipeline — baseline, optimize, stress test, AI insight — entirely in the terminal, no browser needed.
