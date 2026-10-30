// API types for AquaShift

export interface CropAllocation {
  crop: string
  area_ha: number
  area_pct: number
  yield_t_ha: number
  yield_lower: number
  yield_upper: number
  production_tonnes: number
  water_used_m3: number
  water_demand_m3_ha: number
  water_demand_lower: number
  water_demand_upper: number
  income_inr: number
  calories_total: number
  delta_area_ha: number
  delta_area_pct: number
}

export interface ConstraintInfo {
  name: string
  type: string
  target: number
  actual: number
  slack: number
  slack_pct: number
  shadow_price: number
  binding: boolean
}

export interface OptimizationResult {
  status: string
  mode: string
  allocations: CropAllocation[]
  total_water_m3: number
  total_income_inr: number
  total_production_tonnes: number
  total_calories: number
  water_budget_m3: number
  water_gap_pct: number
  food_target_tonnes: number
  food_gap_pct: number
  income_target_inr: number
  income_gap_pct: number
  constraints: ConstraintInfo[]
  solve_time_ms: number
  slack_values: { water: number; food: number; income: number }
}

export interface BottleneckDiagnosis {
  constraint: string
  severity: 'Critical' | 'High' | 'Moderate' | 'Low'
  slack_pct: number
  shadow_price: number
  explanation: string
}

export interface StressTestResult {
  strict_status: string
  relaxed_plan: OptimizationResult
  bottlenecks: BottleneckDiagnosis[]
  scenario_description: string
}

export interface PredictionResult {
  crop: string
  water_fraction: number
  rainfall_scenario: string
  yield_t_ha: number
  yield_lower: number
  yield_upper: number
  water_demand_m3_ha: number
  water_lower: number
  water_upper: number
}

export interface ExplainResult {
  text: string
  audience: string
  language: string
  source: string
  verified: boolean
  verification_errors: string[]
}

export interface SweepPoint {
  water_change_pct: number
  total_income_inr: number
  total_production_tonnes: number
  paddy_area_ha: number
  paddy_area_pct: number
  status: string
}

export interface SweepResult {
  points: SweepPoint[]
  tipping_point_pct: number | null
}

export interface ScenarioInput {
  land_ha: number
  water_budget_m3: number
  water_change_pct: number
  food_target_change_pct: number
  income_target_change_pct: number
  rainfall_scenario: string
  selected_crops: string[]
  optimization_mode: string
  weights: { water: number; food: number; income: number }
}

export interface CropConfig {
  baseline_yield_t_ha: number
  water_need_m3_ha: number
  cost_cultivation_inr_ha: number
  price_inr_quintal: number
  calories_per_kg: number
  drought_sensitivity_ky: number
  min_land_share: number
  max_land_share: number
  baseline_share: number
}

export interface AppConfig {
  region_name: string
  default_land_ha: number
  default_water_budget_m3: number
  available_crops: string[]
  rainfall_scenarios: string[]
  crop_details: Record<string, CropConfig>
}
