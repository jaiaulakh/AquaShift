import React from 'react'
import type { StressTestResult } from '../types'
import type { Strings } from '../i18n'
import { SEVERITY_COLORS, SEVERITY_ICONS, formatINR, formatWater, formatTonnes } from '../utils'

interface StressTestViewProps {
  result: StressTestResult | null
  loading: boolean
  strings: Strings
}

const severityWidth: Record<string, string> = {
  Critical: '100%',
  High: '75%',
  Moderate: '50%',
  Low: '25%',
}

function cleanExplanation(text: string) {
  return text
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '')
    .replace(/[\uFE0F\u200D]/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

export function StressTestView({ result, loading, strings }: StressTestViewProps) {
  if (loading) {
    return (
      <section className="data-section">
        <div className="eyebrow">{strings.stressTitle}</div>
        <div className="loading-indicator" aria-label={strings.loading} />
      </section>
    )
  }

  if (!result) return null

  const { strict_status, relaxed_plan, bottlenecks, scenario_description } = result

  return (
    <div className="space-y-6">
      <section className="data-section">
        <div className="eyebrow">{strings.stressTitle}</div>
        <p className="scenario-note">{scenario_description}</p>
        <div className="comparison-panel">
          <div className="comparison-column comparison-muted">
            <h3>{strings.standardSolver}</h3>
            <div className="comparison-result">Infeasible</div>
            <p>No plan returned. The constraints cannot be satisfied together under this scenario.</p>
            <div className="result-meta">Status: {strict_status.toUpperCase()}</div>
          </div>
          <div className="comparison-column comparison-accent">
            <h3>AquaShift</h3>
            <div className="comparison-result">Closest feasible plan</div>
            <div className="metric-list">
              <div><span>Water used</span><strong>{formatWater(relaxed_plan.total_water_m3)}</strong></div>
              <div><span>Production</span><strong>{formatTonnes(relaxed_plan.total_production_tonnes)}</strong></div>
              <div><span>Income</span><strong>{formatINR(relaxed_plan.total_income_inr)}</strong></div>
            </div>
            <div className="allocation-list">
              {relaxed_plan.allocations.map((allocation) => (
                <div className="allocation-list-row" key={allocation.crop}>
                  <span>{allocation.crop}</span>
                  <span>{allocation.area_ha.toFixed(0)} ha ({allocation.area_pct.toFixed(0)}%)</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="data-section">
        <div className="eyebrow">{strings.bottlenecks}</div>
        <table className="bottleneck-table">
          <thead>
            <tr><th>Rank</th><th>Constraint</th><th>Severity</th><th>Explanation</th><th>Gap</th></tr>
          </thead>
          <tbody>
            {bottlenecks.map((bottleneck, index) => (
              <tr key={bottleneck.constraint}>
                <td>{index + 1}</td>
                <td>{bottleneck.constraint}</td>
                <td>
                  <span className={`severity-square ${SEVERITY_COLORS[bottleneck.severity]}`} />
                  {SEVERITY_ICONS[bottleneck.severity]}
                </td>
                <td>{cleanExplanation(bottleneck.explanation)}</td>
                <td>
                  <span className="severity-bar"><span className={`severity-bar-fill ${SEVERITY_COLORS[bottleneck.severity]}`} style={{ width: severityWidth[bottleneck.severity] }} /></span>
                  {bottleneck.slack_pct.toFixed(0)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="data-section">
        <div className="eyebrow">{strings.relaxation}</div>
        <ol className="relaxation-list">
          {bottlenecks.slice(0, 3).map((bottleneck) => (
            <li key={bottleneck.constraint}>Review the {bottleneck.constraint.toLowerCase()} target by up to {bottleneck.slack_pct.toFixed(0)}% before the next planning cycle.</li>
          ))}
        </ol>
      </section>
    </div>
  )
}
