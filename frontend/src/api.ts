// API client for AquaShift backend

import type {
  ScenarioInput,
  OptimizationResult,
  StressTestResult,
  ExplainResult,
  SweepResult,
  AppConfig,
  PredictionResult,
} from './types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export const api = {
  health: () => fetchJSON<{ status: string }>(`${API_BASE}/api/health`),

  config: () => fetchJSON<AppConfig>(`${API_BASE}/api/config`),

  baseline: () =>
    fetchJSON<{ plan: OptimizationResult; predictions: PredictionResult[] }>(
      `${API_BASE}/api/baseline`
    ),

  predict: (water_fraction: number, rainfall_scenario: string, crops?: string[]) =>
    fetchJSON<{ predictions: PredictionResult[] }>(`${API_BASE}/api/predict`, {
      method: 'POST',
      body: JSON.stringify({ water_fraction, rainfall_scenario, crops }),
    }),

  optimize: (scenario: ScenarioInput) =>
    fetchJSON<{ plan: OptimizationResult; baseline: OptimizationResult }>(
      `${API_BASE}/api/optimize`,
      { method: 'POST', body: JSON.stringify(scenario) }
    ),

  stressTest: (scenario: Partial<ScenarioInput>) =>
    fetchJSON<StressTestResult>(`${API_BASE}/api/stress-test`, {
      method: 'POST',
      body: JSON.stringify(scenario),
    }),

  explain: (
    plan: OptimizationResult,
    audience: string,
    language: string,
    baseline?: OptimizationResult
  ) =>
    fetchJSON<ExplainResult>(`${API_BASE}/api/explain`, {
      method: 'POST',
      body: JSON.stringify({ plan, audience, language, baseline }),
    }),

  sweep: (
    land_ha: number,
    water_budget_m3: number,
    rainfall_scenario: string,
    selected_crops: string[]
  ) =>
    fetchJSON<SweepResult>(`${API_BASE}/api/simulate/sweep`, {
      method: 'POST',
      body: JSON.stringify({ land_ha, water_budget_m3, rainfall_scenario, selected_crops }),
    }),
}
