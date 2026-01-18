'use client'

import { Box, Stack, Typography } from '@mui/material'
import type { MisalignmentRow } from '@/lib/types'

interface MisalignmentMiniGraphProps {
  rows: MisalignmentRow[]
  selectedDate?: string | null
}

function buildPath(values: Array<number | null>, maxAbs: number): string {
  if (values.length === 0) return ''
  const safeMax = maxAbs || 1
  return values
    .map((value, index) => {
      const x = values.length === 1 ? 50 : (index / (values.length - 1)) * 100
      const normalized = value === null ? 0 : value / safeMax
      const y = 50 - normalized * 40
      return `${index === 0 ? 'M' : 'L'}${x},${y}`
    })
    .join(' ')
}

export default function MisalignmentMiniGraph({ rows, selectedDate }: MisalignmentMiniGraphProps) {
  if (!rows.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        No data for graph.
      </Typography>
    )
  }

  const sorted = [...rows].sort((a, b) => a.date.localeCompare(b.date))
  const sentimentValues = sorted.map((row) => row.sentiment_avg ?? 0)
  const returnValues = sorted.map((row) => row.return_1d ?? 0)
  const maxAbs = Math.max(
    1,
    ...sentimentValues.map((v) => Math.abs(v)),
    ...returnValues.map((v) => Math.abs(v)),
  )
  const sentimentPath = buildPath(sentimentValues, maxAbs)
  const returnPath = buildPath(returnValues, maxAbs)
  const selectedIndex = selectedDate
    ? sorted.findIndex((row) => row.date === selectedDate)
    : -1
  const selectedX = selectedIndex >= 0 && sorted.length > 1
    ? (selectedIndex / (sorted.length - 1)) * 100
    : null

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
        Sentiment vs Return (basic)
      </Typography>
      <Box
        sx={{
          borderRadius: 2,
          border: '1px solid',
          borderColor: 'divider',
          p: 2,
        }}
      >
        <Box component="svg" viewBox="0 0 100 100" sx={{ width: '100%', height: 140 }}>
          <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" opacity={0.2} />
          {selectedX !== null && (
            <line
              x1={selectedX}
              y1="5"
              x2={selectedX}
              y2="95"
              stroke="currentColor"
              opacity={0.35}
            />
          )}
          <path d={sentimentPath} fill="none" stroke="#26a69a" strokeWidth="2" />
          <path d={returnPath} fill="none" stroke="#ff7043" strokeWidth="2" />
        </Box>
        <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 10, height: 10, bgcolor: '#26a69a', borderRadius: 999 }} />
            <Typography variant="caption" color="text.secondary">
              Sentiment
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 10, height: 10, bgcolor: '#ff7043', borderRadius: 999 }} />
            <Typography variant="caption" color="text.secondary">
              Return
            </Typography>
          </Stack>
        </Stack>
      </Box>
    </Stack>
  )
}
