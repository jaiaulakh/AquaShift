# Data Assumptions — AquaShift

> ⚠️ All values are **synthetic demo data calibrated to public agricultural statistics**.
> They are indicative only and must not be used for real planning decisions.

## Crop Parameters (`crops.csv`)

| Parameter | Source / Basis | Notes |
|-----------|---------------|-------|
| Baseline yield (t/ha) | ICAR state-average figures, Punjab/Haryana belt | Rounded to nearest 0.5 |
| Water requirement (m³/ha) | FAO Crop Water Information, adapted for NW India | Seasonal total, not irrigation-only |
| Cost of cultivation (₹/ha) | CACP cost reports (indicative averages) | Includes inputs, labour, overheads |
| Price (₹/quintal) | GoI MSP 2023-24 (Paddy, Wheat, Maize, Pulses, Millets) | |
| Calories/kg | USDA FoodData Central (approximate) | |
| Drought sensitivity Ky | FAO Irrigation & Drainage Paper 33 | Key parameter for yield-response |
| Min/max land shares | Agronomic rotation constraints + policy range | Configurable |
| Baseline shares | Typical Punjab allocation (paddy-heavy) | Sum = 1.0 |

## Weather Scenarios (`weather_scenarios.csv`)

| Scenario | Rainfall fraction | Yield stress | Basis |
|----------|-------------------|-------------|-------|
| Normal | 1.00 | 1.00 | Long-period average |
| Deficit | 0.75 | 0.85 | ~1-in-4-year event |
| Severe Deficit | 0.50 | 0.65 | ~1-in-10-year drought |
| Surplus | 1.20 | 0.95 | Excess rainfall, minor damage |

## Default Region

- **Punjab-Haryana paddy-wheat belt**
- Default land: 1,000 ha (small FPO / demonstration scale)
- Default water budget: 8,000,000 m³ (≈ 8,000 m³/ha)
- This is configurable via `backend/app/core/config.py`.

## Synthetic Training Data

- Generated via `scripts/generate_data.py` with fixed seed (42).
- Uses FAO yield-response-to-water: `Ya/Ym = 1 − Ky × (1 − ETa/ETm)`.
- Gaussian noise (σ = 5% of mean) added to simulate field variability.
- 1,000 samples per crop × 5 crops = 5,000 rows.

## Key Limitations

1. Real yields depend on soil type, variety, sowing date, pest pressure, etc.
2. Water requirements vary with micro-climate and irrigation efficiency.
3. Prices fluctuate; MSP is a floor, not the market price.
4. Calorie values ignore protein quality and micronutrient content.
5. Single-season model; does not capture multi-season rotation benefits.
