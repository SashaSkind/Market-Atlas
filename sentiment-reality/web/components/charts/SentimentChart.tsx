'use client'

// SentimentChart component
//
// TODO: Implement a bar chart showing daily sentiment scores
//
// Props:
//   data: DailySentiment[] from @/lib/types
//
// Implementation:
//   - Use Recharts library
//   - Components needed: BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
//   - X-axis: date field
//   - Y-axis: avg_score, domain [-1, 1]
//   - Bars: colored based on value
//     - Positive (> 0.1): green (#22c55e)
//     - Negative (< -0.1): red (#ef4444)
//     - Neutral: gray (#6b7280)
//   - Add ReferenceLine at y=0
//   - Height: 300px via ResponsiveContainer
//
// Example usage:
//   <SentimentChart data={dailyData.map(d => d.sentiment)} />

import type { DailySentiment } from '@/lib/types'

interface SentimentChartProps {
  data: DailySentiment[]
}

export function SentimentChart({ data }: SentimentChartProps) {
  // TODO: Replace with Recharts implementation
  return (
    <div>
      <p>SentimentChart placeholder - {data.length} data points</p>
    </div>
  )
}
