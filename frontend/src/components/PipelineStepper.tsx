import React from 'react'
import type { Strings } from '../i18n'

interface PipelineStepperProps {
  currentStep: number
  strings: Strings
}

export function PipelineStepper({ currentStep, strings }: PipelineStepperProps) {
  return (
    <div className="w-full py-4 px-2">
      <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wider mb-4 text-center">
        {strings.pipeline}
      </h2>
      <div className="flex items-center justify-between relative">
        {/* Progress line */}
        <div className="absolute top-6 left-0 right-0 h-0.5 bg-stone-200 z-0" />
        <div
          className="absolute top-6 left-0 h-0.5 bg-green-600 z-0 transition-all duration-700"
          style={{ width: `${(currentStep / (strings.steps.length - 1)) * 100}%` }}
        />

        {strings.steps.map((step, i) => {
          const isActive = i === currentStep
          const isDone = i < currentStep

          return (
            <div key={i} className="flex flex-col items-center z-10 flex-1">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center text-lg border-2 transition-all duration-500 ${
                  isDone
                    ? 'bg-green-600 border-green-600 text-white shadow-md'
                    : isActive
                    ? 'bg-white border-green-600 text-green-600 shadow-lg scale-110'
                    : 'bg-white border-stone-300 text-stone-400'
                }`}
              >
                {isDone ? '✓' : String(i + 1).padStart(2, '0')}
              </div>
              <span
                className={`mt-2 text-xs text-center font-medium leading-tight max-w-16 ${
                  isActive ? 'text-green-700' : isDone ? 'text-green-600' : 'text-stone-400'
                }`}
              >
                {step}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
