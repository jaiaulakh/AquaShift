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

  return (
    <div className="card space-y-4">
      <h2 className="text-lg font-bold text-stone-800 flex items-center gap-2">
        {strings.aiInsight}
      </h2>

      <div className="flex gap-2">
        <button
          onClick={() => setAudience('farmer')}
          className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors cursor-pointer ${
            audience === 'farmer'
              ? 'bg-green-700 text-white border-green-700'
              : 'bg-white text-stone-600 border-stone-300'
          }`}
        >
          {strings.audienceFarmer}
        </button>
        <button
          onClick={() => setAudience('planner')}
          className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors cursor-pointer ${
            audience === 'planner'
              ? 'bg-blue-700 text-white border-blue-700'
              : 'bg-white text-stone-600 border-stone-300'
          }`}
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
          Get AI Explanation
        </button>
      )}

      {loading && (
        <div className="flex items-center gap-3 py-6 justify-center">
          <div className="loading-indicator" />
          <span className="text-stone-500">Generating insight...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          {/* Source badge */}
          <div className="flex flex-wrap gap-2 items-center">
            {result.source === 'llm' ? (
              <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-800 rounded-full border border-purple-200">
                AI Generated
              </span>
            ) : (
              <span className="text-xs px-2 py-0.5 bg-stone-100 text-stone-600 rounded-full border border-stone-200">
                {strings.template}
              </span>
            )}
            {result.verified && (
              <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded-full border border-green-200">
                {strings.verified}
              </span>
            )}
          </div>

          {/* Explanation text */}
          <div className="prose prose-sm max-w-none text-stone-700 bg-stone-50 rounded-xl p-4 text-sm leading-relaxed whitespace-pre-wrap">
            {result.text}
          </div>

          {/* Regenerate */}
          <button
            onClick={handleExplain}
            className="btn-ghost text-sm"
          >
            ↺ Regenerate
          </button>
        </div>
      )}
    </div>
  )
}
