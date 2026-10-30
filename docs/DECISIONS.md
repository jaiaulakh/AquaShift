# Design Decisions — AquaShift

One-line log of every design choice made during development.

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | LP solver type | Continuous (GLOP) not MIP | Faster, simpler, sufficient for hectare-level FPO planning |
| 2 | Slack normalisation | Divide by target value | Makes weights comparable across constraints of different scales |
| 3 | Bottleneck thresholds | Causal weight approach | Water gets 2x causal weight; Income/Food classified by gap % |
| 4 | Stress test parameters | Water −80%, Income +50%, Food +10% | Tuned to produce Water=Critical, Income=High, Food=Moderate |
| 5 | ML model | RandomForest (50 trees) | Handles non-linearity; gives P10/P90 from ensemble spread |
| 6 | Training seed | 42 | Standard ML seed; SHA256-verified reproducibility |
| 7 | Fallback template | f-string based, no dependencies | Zero-dependency; always works; validated against plan JSON |
| 8 | LLM validation tolerance | 5% relative, same order-of-magnitude | Prevents rounding errors from failing but catches fabricated numbers |
| 9 | Shadow prices | OR-Tools dual_value() | Built-in GLOP output; no extra solve needed |
| 10 | Demo timing | 3s per step in browser Demo Mode | Fits 2-min with narration pauses |
| 11 | numpy version | ≥2.0.0 (not pinned) | numpy 1.26.x crashes on Python 3.13 (access violation) |
| 12 | Frontend state | useState only, no Redux | App is simple enough; avoids bundle bloat |
| 13 | Recharts | Not Plotly | Smaller bundle; native React; sufficient for bar + line charts |
| 14 | Tailwind v4 | @tailwindcss/vite plugin | Newer DX; no config file needed |
| 15 | Region default | Punjab-Haryana paddy-wheat belt | Most extreme water-crop conflict in India; narrative clarity |
| 16 | Crops default | 5 (Paddy, Wheat, Maize, Pulses, Millets) | Covers major crop types; extensible via crops.csv |
| 17 | No database | CSV + joblib files | Zero operational complexity; works offline; demo reproducibility |
| 18 | CORS | Allow all origins | Hackathon setting; no auth; not production |
| 19 | Lexicographic mode | Extreme weight differences (1000x, 10x, 1x) | True lexicographic needs sequential solves; approximation is sufficient for demo |
| 20 | AI insight max words | 180 | Forces conciseness; readable on mobile |
