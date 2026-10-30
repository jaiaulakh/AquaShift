import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { OptimizationResult } from '../types'
import type { Strings } from '../i18n'
import { CROP_COLORS, CROP_ICONS, formatINR, formatWater, formatTonnes, getKPIStatus } from '../utils'

interface AllocationViewProps {
  baseline: OptimizationResult | null
  optimized: OptimizationResult | null
  strings: Strings
}

function KPICard({
  label,
  value,
  target,
  actual,
  gapPct,
  icon,
}: {
  label: string
  value: string
  target?: string
  actual?: string
  gapPct: number
  icon: string
}) {
  const status = getKPIStatus(gapPct)
  const classes = {
    green: 'bg-green-50 border-green-200',
    amber: 'bg-amber-50 border-amber-200',
    red: 'bg-red-50 border-red-200',
  }
  const textClasses = {
    green: 'text-green-800',
    amber: 'text-amber-800',
    red: 'text-red-800',
  }

  return (
    <div className={`rounded-xl border-2 p-4 ${classes[status]}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="kpi-mark">{icon}</span>
        <span className={`text-sm font-semibold ${textClasses[status]}`}>{label}</span>
      </div>
      <div className={`text-2xl font-bold ${textClasses[status]}`}>{value}</div>
      {target && (
        <div className="text-xs text-stone-500 mt-1">
          Target: {target} · Actual: {actual}
          {gapPct > 0 && (
            <span className="text-red-600 font-medium"> · {gapPct.toFixed(0)}% gap</span>
          )}
        </div>
      )}
    </div>
  )
}

function AllocationBar({
  plan,
  label,
}: {
  plan: OptimizationResult
  label: string
}) {
  const data = plan.allocations.map((a) => ({
    name: `${CROP_ICONS[a.crop] ?? ''} ${a.crop}`.trim(),
    crop: a.crop,
    area: a.area_ha,
    pct: a.area_pct,
  }))

  return (
    <div>
      <h3 className="text-sm font-semibold text-stone-600 mb-2">{label}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" barSize={22} margin={{ left: 10, right: 30 }}>
          <XAxis type="number" unit=" ha" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={80} />
          <Tooltip
            formatter={(v, _name, props) => [
              `${Number(v).toFixed(0)} ha (${((props.payload as { pct?: number })?.pct ?? 0).toFixed(0)}%)`,
              (props.payload as { crop?: string })?.crop ?? String(_name),
            ]}
          />
          <Bar dataKey="area" radius={[0, 4, 4, 0]}>
            {data.map((entry) => (
              <Cell key={entry.crop} fill={CROP_COLORS[entry.crop] ?? '#94a3b8'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AllocationView({ baseline, optimized, strings }: AllocationViewProps) {
  if (!optimized) return null

  const waterGap = optimized.water_gap_pct
  const foodGap = optimized.food_gap_pct
  const incomeGap = optimized.income_gap_pct

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPICard
          label={strings.kpiWater}
          value={formatWater(optimized.total_water_m3)}
          target={formatWater(optimized.water_budget_m3)}
          actual={formatWater(optimized.total_water_m3)}
          gapPct={waterGap}
          icon="W"
        />
        <KPICard
          label={strings.kpiFood}
          value={formatTonnes(optimized.total_production_tonnes)}
          target={formatTonnes(optimized.food_target_tonnes)}
          actual={formatTonnes(optimized.total_production_tonnes)}
          gapPct={foodGap}
          icon="F"
        />
        <KPICard
          label={strings.kpiIncome}
          value={formatINR(optimized.total_income_inr)}
          target={formatINR(optimized.income_target_inr)}
          actual={formatINR(optimized.total_income_inr)}
          gapPct={incomeGap}
          icon="I"
        />
      </div>

      {/* Before / After bars */}
      <div className="card">
        <h2 className="text-lg font-bold text-stone-800 mb-4">{strings.comparison}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {baseline && <AllocationBar plan={baseline} label={strings.baseline} />}
          <AllocationBar plan={optimized} label={strings.optimized} />
        </div>
      </div>

      {/* Delta table */}
      <div className="card overflow-x-auto">
        <h3 className="text-sm font-semibold text-stone-600 mb-3">Allocation Changes</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-stone-200">
              <th className="text-left py-2 text-stone-600">Crop</th>
              <th className="text-right py-2 text-stone-600">Area (ha)</th>
              <th className="text-right py-2 text-stone-600">Share</th>
              <th className="text-right py-2 text-stone-600">Δ vs Baseline</th>
              <th className="text-right py-2 text-stone-600">Yield (t/ha)</th>
              <th className="text-right py-2 text-stone-600">Income</th>
            </tr>
          </thead>
          <tbody>
            {optimized.allocations.map((a) => (
              <tr key={a.crop} className="border-b border-stone-100 hover:bg-stone-50">
                <td className="py-2 font-medium">
                  {CROP_ICONS[a.crop]} {a.crop}
                </td>
                <td className="text-right py-2">{a.area_ha.toFixed(0)}</td>
                <td className="text-right py-2">{a.area_pct.toFixed(0)}%</td>
                <td className={`text-right py-2 font-medium ${a.delta_area_ha < -1 ? 'text-red-600' : a.delta_area_ha > 1 ? 'text-green-600' : 'text-stone-500'}`}>
                  {a.delta_area_ha > 0 ? '+' : ''}{a.delta_area_ha.toFixed(0)} ha
                </td>
                <td className="text-right py-2">{a.yield_t_ha.toFixed(2)}</td>
                <td className="text-right py-2">{formatINR(a.income_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Solve info */}
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-stone-400">
          <span>Status: <span className="font-medium text-stone-600">{optimized.status.replace('_', ' ')}</span></span>
          <span>Mode: <span className="font-medium text-stone-600">{optimized.mode}</span></span>
          <span>Solve time: <span className="font-medium text-stone-600">{optimized.solve_time_ms.toFixed(1)} ms</span></span>
        </div>
      </div>

      {/* Shadow prices */}
      {optimized.constraints.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-stone-600 mb-3">{strings.bindingConstraints}</h3>
          <div className="space-y-2">
            {optimized.constraints
              .filter((c) => c.binding)
              .map((c) => (
                <div key={c.name} className="flex items-center justify-between text-sm bg-stone-50 rounded-lg px-3 py-2">
                  <span className="font-medium">{c.name}</span>
                  <div className="text-right text-xs text-stone-500 space-x-3">
                    <span>{c.actual.toLocaleString()} / {c.target.toLocaleString()}</span>
                    {c.shadow_price !== 0 && (
                      <span className="text-blue-600">
                        {strings.shadowPrice}: {Math.abs(c.shadow_price).toFixed(4)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
