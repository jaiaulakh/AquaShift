import React, { useState, useEffect, useCallback, useRef } from 'react'
import type { ScenarioInput, OptimizationResult, StressTestResult, ExplainResult, SweepResult, AppConfig } from './types'
import { api } from './api'
import { strings as allStrings } from './i18n'
import type { Language } from './i18n'
import { PipelineStepper } from './components/PipelineStepper'
import { ScenarioBuilder } from './components/ScenarioBuilder'
import { AllocationView } from './components/AllocationView'
import { StressTestView } from './components/StressTestView'
import { AIInsightCard } from './components/AIInsightCard'
import { WaterSweepChart } from './components/WaterSweepChart'
import './index.css'

const DEFAULT_SCENARIO: ScenarioInput = {
  land_ha: 1000,
  water_budget_m3: 8000000,
  water_change_pct: 0,
  food_target_change_pct: 0,
  income_target_change_pct: 0,
  rainfall_scenario: 'Normal',
  selected_crops: ['Paddy', 'Wheat', 'Maize', 'Pulses', 'Millets'],
  optimization_mode: 'weights',
  weights: { water: 1, food: 1, income: 1 },
}

export default function App() {
  const [lang, setLang] = useState<Language>('en')
  const s = allStrings[lang]

  const [config, setConfig] = useState<AppConfig | null>(null)
  const [scenario, setScenario] = useState<ScenarioInput>(DEFAULT_SCENARIO)
  const [pipelineStep, setPipelineStep] = useState(0)
  const [baseline, setBaseline] = useState<OptimizationResult | null>(null)
  const [optimized, setOptimized] = useState<OptimizationResult | null>(null)
  const [stressResult, setStressResult] = useState<StressTestResult | null>(null)
  const [sweepData, setSweepData] = useState<SweepResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [stressLoading, setStressLoading] = useState(false)
  const [sweepLoading, setSweepLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [demoRunning, setDemoRunning] = useState(false)
  const [demoCaption, setDemoCaption] = useState('')
  const [demoHighlight, setDemoHighlight] = useState(-1)
  const [waterFirst, setWaterFirst] = useState(false)

  const demoAbortRef = useRef(false)

  // Load config on mount
  useEffect(() => {
    api.config().then(setConfig).catch(console.error)
    api.baseline().then((r) => {
      setBaseline(r.plan)
      setPipelineStep(0)
    }).catch(console.error)
  }, [])

  const handleWeightChange = (key: 'water' | 'food' | 'income', value: number) => {
    setScenario((sc) => ({ ...sc, weights: { ...sc.weights, [key]: value } }))
  }

  const handleOptimize = useCallback(async (sc?: ScenarioInput) => {
    const toRun = sc ?? scenario
    setLoading(true)
    setError(null)
    setPipelineStep(1)

    try {
      await new Promise((r) => setTimeout(r, 300))
      setPipelineStep(2)
      const result = await api.optimize(toRun)
      setOptimized(result.plan)
      if (!baseline) setBaseline(result.baseline)
      setPipelineStep(5)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : s.error)
    } finally {
      setLoading(false)
    }
  }, [scenario, baseline, s])

  const handleStressTest = useCallback(async () => {
    setStressLoading(true)
    setError(null)
    setPipelineStep(3)
    try {
      const result = await api.stressTest({
        land_ha: scenario.land_ha,
        water_budget_m3: scenario.water_budget_m3,
        rainfall_scenario: scenario.rainfall_scenario,
        selected_crops: scenario.selected_crops,
      })
      setStressResult(result)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : s.error)
    } finally {
      setStressLoading(false)
    }
  }, [scenario, s])

  const handleSweep = useCallback(async () => {
    setSweepLoading(true)
    try {
      const result = await api.sweep(
        scenario.land_ha,
        scenario.water_budget_m3,
        scenario.rainfall_scenario,
        scenario.selected_crops
      )
      setSweepData(result)
    } catch (e) {
      console.error(e)
    } finally {
      setSweepLoading(false)
    }
  }, [scenario])

  const handleExplain = useCallback(
    async (audience: string, language: string): Promise<ExplainResult | null> => {
      if (!optimized) return null
      setPipelineStep(4)
      try {
        const result = await api.explain(optimized, audience, language, baseline ?? undefined)
        return result
      } catch {
        return null
      }
    },
    [optimized, baseline]
  )

  const runDemo = useCallback(async () => {
    demoAbortRef.current = false
    setDemoRunning(true)
    setError(null)
    setOptimized(null)
    setStressResult(null)
    setSweepData(null)
    setPipelineStep(0)

    const demoScenario: ScenarioInput = {
      ...DEFAULT_SCENARIO,
      water_change_pct: -20,
      rainfall_scenario: 'Deficit',
    }

    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))
    const check = () => demoAbortRef.current

    try {
      setDemoCaption('Step 1: Loading baseline scenario (paddy-heavy, Punjab-Haryana belt)...')
      setDemoHighlight(0)
      setScenario(demoScenario)
      await sleep(3000); if (check()) return

      setDemoCaption('Step 2: ML model predicting yields under water stress...')
      setPipelineStep(1)
      setDemoHighlight(1)
      await sleep(2500); if (check()) return

      setDemoCaption('Step 3: OR-Tools optimizer finding best crop mix with water −20%...')
      setPipelineStep(2)
      setDemoHighlight(-1)
      const optResult = await api.optimize(demoScenario)
      setOptimized(optResult.plan)
      setBaseline(optResult.baseline)
      await sleep(2000); if (check()) return

      setDemoCaption('Step 4: Running extreme stress test (water −80%, income +50%)...')
      setPipelineStep(3)
      const stressRes = await api.stressTest({
        land_ha: demoScenario.land_ha,
        water_budget_m3: demoScenario.water_budget_m3,
        rainfall_scenario: demoScenario.rainfall_scenario,
        selected_crops: demoScenario.selected_crops,
      })
      setStressResult(stressRes)
      await sleep(2000); if (check()) return

      setDemoCaption('Step 5: Generating AI explanation (offline-capable template)...')
      setPipelineStep(4)
      await sleep(2000); if (check()) return

      setDemoCaption('Demo complete. AquaShift: ML predicts, optimization decides, AI explains.')
      setPipelineStep(5)
      setDemoHighlight(-1)

    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Demo failed')
    } finally {
      setDemoRunning(false)
    }
  }, [])

  const stopDemo = () => {
    demoAbortRef.current = true
    setDemoRunning(false)
    setDemoCaption('')
    setDemoHighlight(-1)
  }

  const resetScenario = () => {
    setScenario(DEFAULT_SCENARIO)
    setOptimized(null)
    setStressResult(null)
    setSweepData(null)
    setError(null)
    setPipelineStep(0)
  }

  useEffect(() => {
    setScenario((sc) => ({
      ...sc,
      weights: waterFirst ? { water: 10, food: 1, income: 1 } : { water: 1, food: 1, income: 1 },
    }))
  }, [waterFirst])

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      {/* Header */}
      <header>
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="wordmark">{s.appName}</span>
            </div>
            <p className="text-green-300 text-xs">{s.tagline}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="language-toggle" aria-label="Language">
              <button onClick={() => setLang('en')} className={lang === 'en' ? 'active' : ''}>EN</button>
              <button onClick={() => setLang('hi')} className={lang === 'hi' ? 'active' : ''}>HI</button>
            </div>
            {!demoRunning ? (
              <button onClick={runDemo} className="btn-secondary text-sm">
                Run demo
              </button>
            ) : (
              <button onClick={stopDemo} className="btn-secondary text-sm">Exit demo</button>
            )}
            <span className="text-xs">{s.synthBadge}</span>
          </div>
        </div>
      </header>

      {/* Demo Caption */}
      {demoCaption && (
        <div className="demo-caption">
          <span>{demoCaption}</span>
          <span>Step {Math.min(pipelineStep + 1, s.steps.length)} of {s.steps.length}</span>
          <button onClick={() => setPipelineStep(Math.max(0, pipelineStep - 1))}>Previous</button>
          <button onClick={() => setPipelineStep(Math.min(s.steps.length - 1, pipelineStep + 1))}>Next</button>
          <button onClick={stopDemo}>Exit</button>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="error-message">
          {error}
          <button className="ml-2 underline" onClick={() => setError(null)}>Retry</button>
        </div>
      )}

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 space-y-6">
        {/* Pipeline Stepper */}
        <div className="card pipeline-panel">
          <PipelineStepper currentStep={pipelineStep} strings={s} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Controls */}
          <div className="lg:col-span-1 space-y-4">
            <ScenarioBuilder
              scenario={scenario}
              onChange={setScenario}
              config={config}
              strings={s}
              isDemo={demoRunning}
              demoHighlight={demoHighlight}
            />

            {/* Priority Weights */}
            <div className="card space-y-3 priority-panel">
              <h3 className="text-sm font-semibold text-stone-700">{s.weights}</h3>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs text-stone-600">{s.waterFirst}</span>
                <button
                  onClick={() => setWaterFirst(!waterFirst)}
                  className={`text-toggle-button ${waterFirst ? 'active' : ''}`}
                  aria-pressed={waterFirst}
                >
                  {waterFirst ? 'On' : 'Off'}
                </button>
              </div>
              {(['water', 'food', 'income'] as const).map((key) => (
                <div key={key}>
                  <div className="flex justify-between text-xs text-stone-600 mb-1">
                    <span className="capitalize">{key}</span>
                    <span className="font-medium">{scenario.weights[key]}x</span>
                  </div>
                  <input
                    type="range" min={0} max={10} step={1}
                    value={scenario.weights[key]}
                    onChange={(e) => handleWeightChange(key, parseInt(e.target.value))}
                    className="w-full accent-green-600"
                  />
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <button
                onClick={() => handleOptimize()}
                disabled={loading || demoRunning}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? s.loading : s.optimize}
              </button>
              <button
                onClick={handleStressTest}
                disabled={stressLoading || demoRunning}
                className="btn-ghost w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {stressLoading ? s.loading : s.stressTest}
              </button>
              <button
                onClick={handleSweep}
                disabled={sweepLoading || demoRunning}
                className="btn-ghost w-full"
              >
                {sweepLoading ? s.loading : s.runSweep}
              </button>
              <button onClick={resetScenario} className="btn-ghost w-full">Reset</button>
            </div>
          </div>

          {/* Right: Results */}
          <div className="lg:col-span-2 space-y-6">
            {optimized ? (
              <AllocationView
                baseline={baseline}
                optimized={optimized}
                strings={s}
              />
            ) : (
              <div className="empty-state">
                <div className="eyebrow">Plan output</div>
                <h2>No plan yet</h2>
                <p>Set the scenario and press Optimize, or load the demo scenario.</p>
                <button onClick={runDemo} className="btn-primary">Load demo scenario</button>
              </div>
            )}
            {(stressResult || stressLoading) && (
              <StressTestView result={stressResult} loading={stressLoading} strings={s} />
            )}
            {(sweepData || sweepLoading) && (
              <WaterSweepChart data={sweepData} loading={sweepLoading} strings={s} />
            )}
            {optimized && (
              <AIInsightCard
                plan={optimized}
                baseline={baseline}
                strings={s}
                language={lang}
                onExplain={handleExplain}
              />
            )}
          </div>
        </div>
      </main>

      <footer className="bg-stone-800 text-stone-400 text-xs text-center py-3 px-4">
        {s.footer}
      </footer>
    </div>
  )
}
