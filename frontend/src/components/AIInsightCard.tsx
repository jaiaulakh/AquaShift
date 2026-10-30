import React, { useState } from 'react'
import type { OptimizationResult, ExplainResult } from '../types'
import type { Strings, Language } from '../i18n'

interface AIInsightCardProps {
  plan: OptimizationResult | null
  baseline: OptimizationResult | null
  strings: Strings
  language: Language
  onExplain: (audience: string, lang: string) => Promise<ExplainResult | null>
}

function cleanSummary(text: string) {
  return text
    .replace(/\*\*/g, '')
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '')
    .replace(/[\uFE0F\u200D]/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

export function AIInsightCard({
  plan,
  strings,
  language,
  onExplain,
}: AIInsightCardProps) {
  const [result, setResult] = useState<ExplainResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [audience, setAudience] = useState<'farmer' | 'planner'>('farmer')
  const [error, setError] = useState<string | null>(null)

  const handleExplain = async () => {
    if (!plan) return
    setLoading(true)
    setError(null)
    try {
      const r = await onExplain(audience, language)
      setResult(r)
    } catch {
      setError(strings.error)
    } finally {
      setLoading(false)
    }
  }

  const handleReadAloud = () => {
    if (!result || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(cleanSummary(result.text)))
  }

  return (
    <section className="plain-summary">
      <h2>Plain-language summary</h2>
      <div className="plain-summary-meta">Written by a language model from solver output. Figures are checked against the solver.</div>

      <div className="text-toggle">
        <button
          onClick={() => setAudience('farmer')}
          className={audience === 'farmer' ? 'active' : ''}
        >
          {strings.audienceFarmer}
        </button>
        <button
          onClick={() => setAudience('planner')}
          className={audience === 'planner' ? 'active' : ''}
        >
          {strings.audiencePlanner}
        </button>
      </div>

      {!result && !loading && (
        <button
          onClick={handleExplain}
          disabled={!plan}
          className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Generate summary
        </button>
      )}

      {loading && (
        <div className="flex items-center gap-3 py-6 justify-center">
          <div className="loading-indicator" />
          <span className="text-stone-500">Preparing summary</span>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          {result.verified && <div className="plain-summary-meta">All figures match solver output</div>}
          <div className="summary-text">
            {cleanSummary(result.text)}
          </div>

          <div className="plain-summary-actions">
            <button onClick={handleReadAloud} className="btn-ghost text-sm">{strings.readAloud}</button>
            <button onClick={handleExplain} className="btn-ghost text-sm">Regenerate</button>
          </div>
        </div>
      )}
    </section>
  )
}
