/**
 * Format a date string for display.
 * Returns short format like "Jan 15" by default, or with year if specified.
 */
export function formatDate(value?: string | null, includeYear = false): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }
  if (includeYear) options.year = 'numeric'
  return new Intl.DateTimeFormat('en-US', options).format(date)
}
