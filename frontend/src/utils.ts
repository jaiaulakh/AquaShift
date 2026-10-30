// Crop labels and colors used by charts and allocation tables.
export const CROP_COLORS: Record<string, string> = {
  Paddy: '#16a34a',    // green
  Wheat: '#d97706',   // amber
  Maize: '#eab308',   // yellow
  Pulses: '#7c3aed',  // purple
  Millets: '#c2410c', // orange-red
}

export const CROP_ICONS: Record<string, string> = {
  Paddy: 'PD',
  Wheat: 'WH',
  Maize: 'MZ',
  Pulses: 'PL',
  Millets: 'ML',
}

export const SEVERITY_COLORS: Record<string, string> = {
  Critical: 'text-red-700 bg-red-100 border-red-300',
  High: 'text-orange-700 bg-orange-100 border-orange-300',
  Moderate: 'text-yellow-700 bg-yellow-100 border-yellow-300',
  Low: 'text-green-700 bg-green-100 border-green-300',
}

export const SEVERITY_ICONS: Record<string, string> = {
  Critical: '!',
  High: '!',
  Moderate: 'i',
  Low: 'OK',
}

export function formatINR(value: number): string {
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(1)}Cr`
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(1)}L`
  if (value >= 1e3) return `₹${(value / 1e3).toFixed(0)}K`
  return `₹${value.toFixed(0)}`
}

export function formatWater(value: number): string {
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M m³`
  if (value >= 1e3) return `${(value / 1e3).toFixed(0)}K m³`
  return `${value.toFixed(0)} m³`
}

export function formatTonnes(value: number): string {
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K t`
  return `${value.toFixed(0)} t`
}

export function getKPIStatus(gapPct: number): 'green' | 'amber' | 'red' {
  if (gapPct === 0) return 'green'
  if (gapPct < 20) return 'amber'
  return 'red'
}
