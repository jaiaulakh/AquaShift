import React from 'react'
import type { ScenarioInput, AppConfig } from '../types'
import type { Strings } from '../i18n'

interface ScenarioBuilderProps {
  scenario: ScenarioInput
  onChange: (s: ScenarioInput) => void
  config: AppConfig | null
  strings: Strings
  isDemo: boolean
  demoHighlight: number
}

const RAINFALL_LABELS: Record<string, string> = {
  Normal: 'Normal',
  Deficit: 'Deficit',
  'Severe Deficit': 'Severe Deficit',
  Surplus: 'Surplus',
}

export function ScenarioBuilder({
  scenario,
  onChange,
  config,
  strings,
  isDemo,
  demoHighlight,
}: ScenarioBuilderProps) {
  const crops = config?.available_crops ?? ['Paddy', 'Wheat', 'Maize', 'Pulses', 'Millets']
  const scenarios = config?.rainfall_scenarios ?? ['Normal', 'Deficit', 'Severe Deficit', 'Surplus']

  const update = (field: keyof ScenarioInput, value: unknown) => {
    onChange({ ...scenario, [field]: value })
  }

  const toggleCrop = (crop: string) => {
    const selected = scenario.selected_crops.includes(crop)
      ? scenario.selected_crops.filter((c) => c !== crop)
      : [...scenario.selected_crops, crop]
    if (selected.length > 0) update('selected_crops', selected)
  }

  const signed = (value: number) => `${value > 0 ? '+' : ''}${value}%`

  return (
    <div className="card scenario-form space-y-5">
      <div className="section-heading">
        <span className="section-kicker">01</span>
        <h2>{strings.scenarioBuilder}</h2>
      </div>

      {/* Land */}
      <div>
        <label className="label">{strings.land}</label>
        <input
          type="number"
          className={`input-field ${isDemo && demoHighlight === 0 ? 'demo-highlight' : ''}`}
          value={scenario.land_ha}
          min={1}
          max={100000}
          onChange={(e) => update('land_ha', parseFloat(e.target.value) || 1000)}
        />
      </div>

      {/* Water Budget */}
      <div>
        <label className="label">{strings.water}</label>
        <input
          type="number"
          className="input-field"
          value={scenario.water_budget_m3}
          min={0}
          step={100000}
          onChange={(e) => update('water_budget_m3', parseFloat(e.target.value) || 8000000)}
        />
      </div>

      {/* Water Change Slider */}
      <div>
        <label className="label">
          {strings.waterChange}:{' '}
          <span className="metric-value">
            {signed(scenario.water_change_pct)}
          </span>
        </label>
        <input
          type="range"
          className={`w-full accent-green-600 ${isDemo && demoHighlight === 1 ? 'demo-highlight rounded' : ''}`}
          min={-80}
          max={50}
          step={5}
          value={scenario.water_change_pct}
          onChange={(e) => update('water_change_pct', parseInt(e.target.value))}
        />
        <div className="flex justify-between text-xs text-stone-400 mt-1">
          <span>-80%</span>
          <span>0</span>
          <span>+50%</span>
        </div>
      </div>

      {/* Food Target */}
      <div>
        <label className="label">
          {strings.foodTarget}:{' '}
          <span className="font-bold text-amber-700">
            {signed(scenario.food_target_change_pct)}
          </span>
        </label>
        <input
          type="range"
          className="w-full accent-amber-600"
          min={-50}
          max={100}
          step={5}
          value={scenario.food_target_change_pct}
          onChange={(e) => update('food_target_change_pct', parseInt(e.target.value))}
        />
      </div>

      {/* Income Target */}
      <div>
        <label className="label">
          {strings.incomeTarget}:{' '}
          <span className="font-bold text-blue-700">
            {signed(scenario.income_target_change_pct)}
          </span>
        </label>
        <input
          type="range"
          className="w-full accent-blue-600"
          min={-50}
          max={100}
          step={5}
          value={scenario.income_target_change_pct}
          onChange={(e) => update('income_target_change_pct', parseInt(e.target.value))}
        />
      </div>

      {/* Rainfall Scenario */}
      <div>
        <label className="label">{strings.rainfallScenario}</label>
        <div className="rainfall-control">
          {scenarios.map((s) => (
            <button
              key={s}
              onClick={() => update('rainfall_scenario', s)}
              className={`rainfall-option ${
                scenario.rainfall_scenario === s
                  ? 'selected'
                  : ''
              }`}
            >
              {RAINFALL_LABELS[s] ?? s}
            </button>
          ))}
        </div>
      </div>

      {/* Crop Selection */}
      <div>
        <label className="label">{strings.crops}</label>
        <div className="crop-checklist">
          {crops.map((crop) => (
            <button
              key={crop}
              onClick={() => toggleCrop(crop)}
              className={`crop-option ${scenario.selected_crops.includes(crop) ? 'selected' : ''}`}
            >
              <span className={`crop-swatch crop-${crop.toLowerCase()}`} aria-hidden="true" />
              <span>{crop}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
