'use client'

// AlignmentChart component
//
// TODO: Implement a combined chart showing sentiment vs price alignment
//
// Props:
//   data: WindowMetric[] from @/lib/types
//
// Implementation:
//   - Use Recharts library
//   - Components needed: ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine
//   - Two Y-axes:
//     - Left (yAxisId="left"): sentiment_score, domain [-1, 1]
//     - Right (yAxisId="right"): price_return percentage
//   - Sentiment as bars (blue, opacity 0.6)
//   - Price return as line (orange/amber #f59e0b, strokeWidth 2)
//   - Add ReferenceLine at y=0 on left axis
//   - Height: 400px via ResponsiveContainer
//
// This is the key visualization showing when sentiment and price diverge
//
// Example usage:
//   <AlignmentChart data={dailyData.map(d => d.alignment)} />

import type { WindowMetric } from '@/lib/types'

interface AlignmentChartProps {
  data: WindowMetric[]
}

export function AlignmentChart({ data }: AlignmentChartProps) {
  // TODO: Replace with Recharts implementation
  return (
    <div>
      <p>AlignmentChart placeholder - {data.length} data points</p>
    </div>
  )
}
