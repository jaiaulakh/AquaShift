import React from 'react'
import type { OptimizationResult } from '../types'
import type { Strings } from '../i18n'
import { CROP_COLORS, formatINR, formatWater, formatTonnes } from '../utils'

interface AllocationViewProps {
  baseline: OptimizationResult | null
  optimized: OptimizationResult | null
  strings: Strings
}

function statusText(gap: number) {
  if (gap === 0) return 'On target'
  if (gap < 20) return `Short by ${gap.toFixed(0)}%`
  return 'Critical'
}

function KpiColumn({
  label,
  value,
  target,
  gap,
  color,
}: {
  label: string
  value: string
  target: number
  gap: number
  color: string
}) {
  const fill = Math.max(0, Math.min(100, 100 - gap))
  return (
    <div className="kpi-column">
      <div className="kpi-label">{label}</div>
      <div className="serif-number">{value}</div>
      <div className="kpi-bar" aria-hidden="true">
        <div className="kpi-bar-fill" style={{ width: `${fill}%`, backgroundColor: color }} />
      </div>
      <div className="kpi-note">
        {gap === 0 ? 'On target' : `${statusText(gap)} · target ${target.toLocaleString()}`}
      </div>
    </div>
  )
}

function StackedAllocationBar({ plan, label }: { plan: OptimizationResult; label: string }) {
  return (
    <div className="allocation-row">
      <div className="allocation-row-label">
        <span>{label}</span>
        <span className="mono-number">{plan.allocations.reduce((sum, item) => sum + item.area_ha, 0).toFixed(0)} ha</span>
      </div>
      <div className="stacked-bar" aria-label={`${label} crop allocation`}>
        {plan.allocations.map((allocation) => (
          <div
            key={allocation.crop}
            className={`stacked-segment ${allocation.crop.toLowerCase()}`}
            style={{ width: `${allocation.area_pct}%`, backgroundColor: CROP_COLORS[allocation.crop] ?? '#6e8b4d' }}
            title={`${allocation.crop}: ${allocation.area_ha.toFixed(0)} ha`}
          >
            {allocation.area_pct >= 10 ? allocation.crop : ''}
          </div>
        ))}
      </div>
    </div>
  )
}

export function AllocationView({ baseline, optimized, strings }: AllocationViewProps) {
  if (!optimized) return null

  return (
    <div className="space-y-6">
      <section className="kpi-panel" aria-label="Plan indicators">
        <KpiColumn
          label={strings.kpiWater}
          value={formatWater(optimized.total_water_m3)}
          target={optimized.water_budget_m3}
          gap={optimized.water_gap_pct}
          color="#1f6f96"
        />
        <KpiColumn
          label={strings.kpiFood}
          value={formatTonnes(optimized.total_production_tonnes)}
          target={optimized.food_target_tonnes}
          gap={optimized.food_gap_pct}
          color="#b8891f"
        />
        <KpiColumn
          label={strings.kpiIncome}
          value={formatINR(optimized.total_income_inr)}
          target={optimized.income_target_inr}
          gap={optimized.income_gap_pct}
          color="#2f7a55"
        />
      </section>

      <section className="data-section">
        <div className="eyebrow">{strings.comparison}</div>
        <h2>Crop allocation</h2>
        {baseline && <StackedAllocationBar plan={baseline} label={strings.baseline} />}
        <StackedAllocationBar plan={optimized} label={strings.optimized} />
        <div className="crop-legend">
          {optimized.allocations.map((allocation) => (
            <span key={allocation.crop}><span className="crop-swatch" style={{ backgroundColor: CROP_COLORS[allocation.crop] }} />{allocation.crop}</span>
          ))}
        </div>
      </section>

      <section className="data-section">
        <div className="eyebrow">Allocation changes</div>
        <table>
          <thead>
            <tr>
              <th>Crop</th>
              <th>Baseline ha</th>
              <th>Optimized ha</th>
              <th>Change</th>
              <th>Yield t/ha</th>
              <th>Income</th>
            </tr>
          </thead>
          <tbody>
            {optimized.allocations.map((allocation) => {
              const baselineArea = allocation.area_ha - allocation.delta_area_ha
              return (
                <tr key={allocation.crop}>
                  <td><span className="crop-swatch" style={{ backgroundColor: CROP_COLORS[allocation.crop] }} />{allocation.crop}</td>
                  <td>{baselineArea.toFixed(0)}</td>
                  <td>{allocation.area_ha.toFixed(0)}</td>
                  <td className={allocation.delta_area_ha < 0 ? 'down-value' : allocation.delta_area_ha > 0 ? 'up-value' : ''}>
                    {allocation.delta_area_ha > 0 ? '+' : ''}{allocation.delta_area_ha.toFixed(0)} ha
                  </td>
                  <td>{allocation.yield_t_ha.toFixed(2)}</td>
                  <td>{formatINR(allocation.income_inr)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <div className="result-meta">
          Status: {optimized.status.replace('_', ' ')} · Mode: {optimized.mode} · Solve time: {optimized.solve_time_ms.toFixed(1)} ms
        </div>
      </section>

      {optimized.constraints.length > 0 && (
        <section className="data-section">
          <div className="eyebrow">{strings.bindingConstraints}</div>
          <h3>Constraints at the margin</h3>
          <table>
            <thead>
              <tr><th>Constraint</th><th>Actual</th><th>Target</th><th>{strings.shadowPrice}</th></tr>
            </thead>
            <tbody>
              {optimized.constraints.filter((constraint) => constraint.binding).map((constraint) => (
                <tr key={constraint.name}>
                  <td>{constraint.name}</td>
                  <td>{constraint.actual.toLocaleString()}</td>
                  <td>{constraint.target.toLocaleString()}</td>
                  <td>{Math.abs(constraint.shadow_price).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}
