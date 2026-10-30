import React from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ReferenceLine, Legend,
} from 'recharts'
import type { SweepResult } from '../types'
import type { Strings } from '../i18n'

interface WaterSweepChartProps {
  data: SweepResult | null
  loading: boolean
  strings: Strings
}

export function WaterSweepChart({ data, loading, strings }: WaterSweepChartProps) {
  if (loading) {
    return (
      <div className="card flex items-center justify-center py-12">
        <div className="loading-indicator" />
        <span className="ml-3 text-stone-500">Simulating water scenarios...</span>
      </div>
    )
  }

  if (!data) return null

  const chartData = data.points.map((p) => ({
    cut: p.water_change_pct,
    income: Math.round(p.total_income_inr / 1e5),  // in Lakhs
    production: Math.round(p.total_production_tonnes),
    paddyPct: p.paddy_area_pct,
  }))

  const tipping = data.tipping_point_pct

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-stone-800">{strings.waterSweep}</h2>
        {tipping !== null && (
          <div className="text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-1 text-red-700">
            {strings.tippingPoint}: {tipping}%
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis
            dataKey="cut"
            label={{ value: 'Water Change (%)', position: 'insideBottom', offset: -5 }}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `${v}%`}
          />
          <YAxis yAxisId="income" label={{ value: 'Income (₹L)', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 11 }} />
          <YAxis yAxisId="paddy" orientation="right" label={{ value: 'Paddy (%)', angle: 90, position: 'insideRight' }} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(value, name) => {
              const v = Number(value)
              if (name === 'Income (₹L)') return [`₹${v}L`, String(name)]
              if (name === 'Paddy (%)') return [`${v.toFixed(0)}%`, String(name)]
              return [v, String(name)]
            }}
            labelFormatter={(l) => `Water: ${l}%`}
          />
          <Legend />
          {tipping !== null && (
            <ReferenceLine
              x={tipping}
              yAxisId="income"
              stroke="#ef4444"
              strokeDasharray="5 5"
              label={{ value: 'Tipping Point', fill: '#ef4444', fontSize: 11 }}
            />
          )}
          <Line
            yAxisId="income"
            type="monotone"
            dataKey="income"
            name="Income (₹L)"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="paddy"
            type="monotone"
            dataKey="paddyPct"
            name="Paddy (%)"
            stroke="#16a34a"
            strokeWidth={2}
            dot={false}
            strokeDasharray="4 2"
          />
        </LineChart>
      </ResponsiveContainer>

      <p className="text-xs text-stone-500 text-center">
        Each point is a full optimizer run. {data.points.length} scenarios simulated.
      </p>
    </div>
  )
}
