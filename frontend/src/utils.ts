export const CROP_COLORS: Record<string, string> = {
  Paddy: '#2A7F78',
  Wheat: '#C0912C',
  Maize: '#D9A93A',
  Pulses: '#8A5A3B',
  Millets: '#6E8B4D',
}

export const SEVERITY_COLORS: Record<string, string> = {
  Critical: 'critical',
  High: 'high',
  Moderate: 'moderate',
  Low: 'ok',
}

export const SEVERITY_ICONS: Record<string, string> = {
  Critical: 'Critical',
  High: 'High',
  Moderate: 'Moderate',
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
