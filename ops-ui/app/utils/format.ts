/** Display helpers for ops UI. */

export function formatPaise(paise: number, currency = 'INR'): string {
  const rupees = paise / 100
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(rupees)
  } catch {
    return `₹${rupees.toFixed(2)}`
  }
}

export function paiseFromRupeesInput(value: string | number): number {
  const n = typeof value === 'number' ? value : Number.parseFloat(String(value).replace(/,/g, ''))
  if (Number.isNaN(n) || n < 0) return 0
  return Math.round(n * 100)
}

export function rupeesFromPaise(paise: number): string {
  return (paise / 100).toFixed(2)
}

/** Serviceable weekdays only (0=Mon … 5=Sat). Sunday is never serviceable. */
export const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as const

/**
 * Selectable service days for society create/edit (Mon–Sat only).
 * Sunday is not offered as a service day.
 */
export const SERVICE_WEEKDAY_OPTIONS = [
  { label: 'Mon', value: 0 },
  { label: 'Tue', value: 1 },
  { label: 'Wed', value: 2 },
  { label: 'Thu', value: 3 },
  { label: 'Fri', value: 4 },
  { label: 'Sat', value: 5 },
] as const

export function formatWeekdays(days: number[]): string {
  return days
    .filter((d) => d >= 0 && d <= 5)
    .slice()
    .sort((a, b) => a - b)
    .map((d) => WEEKDAY_LABELS[d] ?? String(d))
    .join(', ')
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Intl.DateTimeFormat('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

export function shortId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id
}
