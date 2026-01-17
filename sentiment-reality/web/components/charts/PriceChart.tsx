'use client'

// PriceChart component
//
// TODO: Implement a line chart showing stock prices over time
//
// Props:
//   data: PricePoint[] from @/lib/types
//
// Implementation:
//   - Use Recharts library (already in package.json)
//   - Components needed: LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
//   - X-axis: date field
//   - Y-axis: close price (auto-scaled)
//   - Line: blue color (#3b82f6), no dots, strokeWidth 2
//   - Height: 300px via ResponsiveContainer
//
// Example usage:
//   <PriceChart data={dailyData.map(d => d.price)} />

import type { PricePoint } from '@/lib/types'

interface PriceChartProps {
  data: PricePoint[]
}

export function PriceChart({ data }: PriceChartProps) {
  // TODO: Replace with Recharts implementation
  return (
    <div>
      <p>PriceChart placeholder - {data.length} data points</p>
    </div>
  )
}
