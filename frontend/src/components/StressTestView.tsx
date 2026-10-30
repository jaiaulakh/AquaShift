import React from 'react'
import type { StressTestResult } from '../types'
import type { Strings } from '../i18n'
import { SEVERITY_COLORS, SEVERITY_ICONS, formatINR, formatWater, formatTonnes } from '../utils'

interface StressTestViewProps {
  result: StressTestResult | null
  loading: boolean
  strings: Strings
}

export function StressTestView({ result, loading, strings }: StressTestViewProps) {
  if (loading) {
    return (
      <div className="card">
        <h2 className="text-lg font-bold text-stone-800 mb-4">{strings.stressTitle}</h2>
        <div className="flex items-center justify-center py-12">
          <div className="loading-indicator" />
          <span className="ml-3 text-stone-500">{strings.loading}</span>
        </div>
      </div>
    )
  }

  if (!result) return null

  const { strict_status, relaxed_plan, bottlenecks, scenario_description } = result

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-stone-800">{strings.stressTitle}</h2>

      {/* Scenario description */}
      <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 text-sm text-orange-800">
        <strong>Extreme Scenario:</strong> {scenario_description}
      </div>

      {/* Side-by-side: Standard vs AquaShift */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Standard solver card */}
        <div className="rounded-xl border-2 border-red-300 bg-red-50 p-5">
          <h3 className="font-bold text-red-800 text-base mb-3 flex items-center gap-2">
            <span className="status-mark status-mark-danger">!</span>
            {strings.standardSolver}
          </h3>
          <div className="text-3xl font-black text-red-600 mb-2">INFEASIBLE</div>
          <p className="text-sm text-red-700">
            A standard LP solver returns no solution — all constraints cannot be satisfied
            simultaneously under these extreme conditions.
          </p>
          <div className="mt-4 text-xs text-red-500 bg-red-100 rounded p-2 font-mono">
            Status: {strict_status.toUpperCase()}
          </div>
        </div>

        {/* AquaShift card */}
        <div className="rounded-xl border-2 border-green-300 bg-green-50 p-5">
          <h3 className="font-bold text-green-800 text-base mb-3 flex items-center gap-2">
            <span className="status-mark status-mark-success">OK</span>
            {strings.aquaShiftSays}
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-stone-600">Water used:</span>
              <span className="font-semibold">{formatWater(relaxed_plan.total_water_m3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-stone-600">Production:</span>
              <span className="font-semibold">{formatTonnes(relaxed_plan.total_production_tonnes)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-stone-600">Income:</span>
              <span className="font-semibold">{formatINR(relaxed_plan.total_income_inr)}</span>
            </div>
          </div>
          <div className="mt-4 space-y-1">
            {relaxed_plan.allocations.map((a) => (
              <div key={a.crop} className="flex justify-between text-xs text-stone-600 bg-white rounded px-2 py-1">
                <span>{a.crop}</span>
                <span className="font-medium">{a.area_ha.toFixed(0)} ha ({a.area_pct.toFixed(0)}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottleneck Diagnosis */}
      <div className="card">
        <h3 className="font-bold text-stone-800 mb-4">{strings.bottlenecks}</h3>
        <div className="space-y-3">
          {bottlenecks.map((b) => (
            <div
              key={b.constraint}
              className={`rounded-xl border p-4 ${SEVERITY_COLORS[b.severity]}`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 font-semibold">
                  <span>{SEVERITY_ICONS[b.severity]}</span>
                  <span>{b.constraint}</span>
                </div>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[b.severity]}`}>
                  {b.severity}
                </span>
              </div>
              <div className="text-sm mt-1">{b.explanation}</div>
              <div className="flex gap-4 mt-2 text-xs opacity-75">
                <span>Gap: {b.slack_pct.toFixed(0)}%</span>
                {b.shadow_price !== 0 && (
                  <span>Shadow price: {Math.abs(b.shadow_price).toFixed(4)}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
