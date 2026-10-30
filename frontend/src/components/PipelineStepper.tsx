import React from 'react'
import type { Strings } from '../i18n'

interface PipelineStepperProps {
  currentStep: number
  strings: Strings
}

export function PipelineStepper({ currentStep, strings }: PipelineStepperProps) {
  return (
    <div className="pipeline-panel">
      <div className="pipeline-title">{strings.pipeline}</div>
      <div className="pipeline-track" aria-label={strings.pipeline}>
        {strings.steps.map((step, i) => (
          <div
            key={step}
            className={`pipeline-step ${i < currentStep ? 'done' : ''} ${i === currentStep ? 'active' : ''}`}
            aria-current={i === currentStep ? 'step' : undefined}
          >
            <div className="pipeline-step-number">{String(i + 1).padStart(2, '0')}</div>
            <div className="pipeline-step-label">{step}</div>
          </div>
        ))}
      </div>
      <div className="pipeline-mobile-status">{currentStep + 1} of {strings.steps.length}: {strings.steps[currentStep]}</div>
    </div>
  )
}
