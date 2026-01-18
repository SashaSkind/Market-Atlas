'use client'

import { useMemo } from 'react'
import {
  AppBar,
  Box,
  Button,
  Dialog,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import type { DailyDataPoint } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface MisalignmentMapModalProps {
  open: boolean
  onClose: () => void
  ticker: string | null
  period: number
  data: DailyDataPoint[]
}

const PRICE_SENSITIVITY = 0.02

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function mapRange(value: number, inMin: number, inMax: number, outMin: number, outMax: number) {
  if (inMax === inMin) return outMin
  return ((value - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin
}

export default function MisalignmentMapModal({
  open,
  onClose,
  ticker,
  period,
  data,
}: MisalignmentMapModalProps) {
  const chartData = useMemo(() => {
    if (!data.length) {
      return {
        dates: [],
        sentimentSeries: [],
        priceSeries: [],
        alignmentSeries: [],
        volumes: [],
        volumeRange: { min: 0, max: 1 },
        volumeNorm: [],
      }
    }

    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date))
    const dates = sorted.map((point) => point.date)
    const sentimentSeries = sorted.map((point) => point.sentiment?.avg_score ?? 0)

    const priceReturns: number[] = []
    let prevClose: number | null = null
    sorted.forEach((point) => {
      const close = point.price?.close ?? null
      if (close === null || prevClose === null) {
        priceReturns.push(0)
      } else {
        priceReturns.push((close - prevClose) / prevClose)
      }
      prevClose = close
    })

    const priceSeries = priceReturns.map((value) =>
      clamp(value / PRICE_SENSITIVITY, -2, 2),
    )

    const alignmentSeries = sentimentSeries.map((sentiment, idx) => {
      const priceMove = priceReturns[idx]
      if (priceMove === 0) return 0
      const direction = priceMove > 0 ? 1 : -1
      return clamp(sentiment * direction, -1, 1)
    })

    const volumes = sorted.map((point) => point.price?.volume ?? 0)
    const volumeMin = Math.min(...volumes.filter((v) => v > 0), 0)
    const volumeMax = Math.max(...volumes, 1)
    const volumeNorm = volumes.map((value) =>
      clamp(mapRange(value, volumeMin, volumeMax, 0, 1), 0, 1),
    )


    return {
      dates,
      sentimentSeries,
      priceSeries,
      alignmentSeries,
      volumes,
      volumeRange: { min: volumeMin, max: volumeMax },
      volumeNorm,
    }
  }, [data])

  return (
    <Dialog open={open} onClose={onClose} fullScreen>
      <AppBar position="relative" color="transparent" elevation={0}>
        <Toolbar sx={{ justifyContent: 'space-between', gap: 2 }}>
          <Box>
            <Typography variant="h6">Misalignment Map</Typography>
            <Typography variant="body2" color="text.secondary">
              Sentiment vs price trends and alignment strength
            </Typography>
          </Box>
          <Button onClick={onClose}>Close</Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ px: { xs: 3, md: 6 }, pb: 6 }}>
        <Stack spacing={2}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {ticker ?? '—'} · Last {period} days
          </Typography>

          {!data.length && (
            <Typography color="text.secondary">
              No data available for this period.
            </Typography>
          )}

          {data.length > 0 && (
            <Stack spacing={3}>
              <Box
                sx={{
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  p: { xs: 2, md: 3 },
                }}
              >
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Sentiment vs Price (normalized)
                </Typography>
                <Box component="svg" viewBox="0 0 640 360" sx={{ width: '100%', height: 400 }}>
                  <rect x="48" y="20" width="560" height="280" fill="rgba(255,255,255,0.02)" />
                  <line x1="48" y1="160" x2="608" y2="160" stroke="currentColor" opacity={0.2} />
                  <line x1="48" y1="20" x2="48" y2="300" stroke="currentColor" opacity={0.25} />
                  <line x1="48" y1="300" x2="608" y2="300" stroke="currentColor" opacity={0.25} />
                  {[2, 1, 0, -1, -2].map((tick) => {
                    const y = mapRange(tick, 2, -2, 20, 300)
                    return (
                      <g key={`y-${tick}`}>
                        <line x1="48" y1={y} x2="608" y2={y} stroke="currentColor" opacity={0.06} />
                        <text x="12" y={y + 5} fill="currentColor" opacity={0.8} fontSize="14">
                          {tick}
                        </text>
                      </g>
                    )
                  })}
                  <path
                    d={chartData.sentimentSeries
                      .map((value, idx) => {
                        const x = mapRange(idx, 0, chartData.sentimentSeries.length - 1 || 1, 48, 608)
                        const y = mapRange(value, 2, -2, 20, 300)
                        return `${idx === 0 ? 'M' : 'L'}${x},${y}`
                      })
                      .join(' ')}
                    fill="none"
                    stroke="#26a69a"
                    strokeWidth="3"
                  />
                  <path
                    d={chartData.priceSeries
                      .map((value, idx) => {
                        const x = mapRange(idx, 0, chartData.priceSeries.length - 1 || 1, 48, 608)
                        const y = mapRange(value, 2, -2, 20, 300)
                        return `${idx === 0 ? 'M' : 'L'}${x},${y}`
                      })
                      .join(' ')}
                    fill="none"
                    stroke="#ff7043"
                    strokeWidth="3"
                  />
                  <text x="48" y="340" fill="currentColor" opacity={0.8} fontSize="14">
                    {chartData.dates[0] ? formatDate(chartData.dates[0], true) : ''}
                  </text>
                  <text x="608" y="340" fill="currentColor" opacity={0.8} fontSize="14" textAnchor="end">
                    {chartData.dates.at(-1) ? formatDate(chartData.dates.at(-1) ?? '', true) : ''}
                  </text>
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
                    Price (2% = 1.0)
                  </Typography>
                </Stack>
              </Stack>
            </Box>

              <Box
                sx={{
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  p: { xs: 2, md: 3 },
                }}
              >
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Is the market acting in agreement with the narrative?
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Alignment and trade volume over time
                </Typography>
                <Box component="svg" viewBox="0 0 640 380" sx={{ width: '100%', height: 400 }}>
                  <rect x="56" y="20" width="552" height="320" fill="rgba(255,255,255,0.02)" />
                  <line x1="56" y1="180" x2="608" y2="180" stroke="currentColor" opacity={0.18} />
                  <line x1="56" y1="20" x2="56" y2="340" stroke="currentColor" opacity={0.22} />
                  <line x1="56" y1="340" x2="608" y2="340" stroke="currentColor" opacity={0.22} />
                  <line x1="56" y1="200" x2="608" y2="200" stroke="currentColor" opacity={0.12} />
                  {[1, 0.5, 0, -0.5, -1].map((tick) => {
                    const y = mapRange(tick, 1, -1, 20, 180)
                    return (
                      <g key={`align-${tick}`}>
                        <line x1="56" y1={y} x2="608" y2={y} stroke="currentColor" opacity={0.06} />
                        <text x="18" y={y + 5} fill="currentColor" opacity={0.85} fontSize="14">
                          {tick}
                        </text>
                      </g>
                    )
                  })}
                  {[0, 0.5, 1].map((tick) => {
                    const y = mapRange(tick, 1, 0, 220, 340)
                    return (
                      <g key={`vol-${tick}`}>
                        <text x="612" y={y + 5} fill="currentColor" opacity={0.8} fontSize="14">
                          {tick}
                        </text>
                      </g>
                    )
                  })}
                  <path
                    d={chartData.alignmentSeries
                      .map((value, idx) => {
                        const x = mapRange(idx, 0, chartData.alignmentSeries.length - 1 || 1, 56, 608)
                        const y = mapRange(value, 1, -1, 20, 180)
                        return `${idx === 0 ? 'M' : 'L'}${x},${y}`
                      })
                      .join(' ')}
                    fill="none"
                    stroke="#26a69a"
                    strokeWidth="3"
                  />
                  <path
                    d={chartData.volumeNorm
                      .map((value, idx) => {
                        const x = mapRange(idx, 0, chartData.volumeNorm.length - 1 || 1, 56, 608)
                        const y = mapRange(value, 1, 0, 220, 340)
                        return `${idx === 0 ? 'M' : 'L'}${x},${y}`
                      })
                      .join(' ')}
                    fill="none"
                    stroke="#ffb74d"
                    strokeWidth="3"
                  />
                  <text x="56" y="350" fill="currentColor" opacity={0.8} fontSize="14">
                    {chartData.dates[0] ? formatDate(chartData.dates[0], true) : ''}
                  </text>
                  <text x="608" y="350" fill="currentColor" opacity={0.8} fontSize="14" textAnchor="end">
                    {chartData.dates.at(-1) ? formatDate(chartData.dates.at(-1) ?? '', true) : ''}
                  </text>
                </Box>
                <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Box sx={{ width: 10, height: 10, bgcolor: '#26a69a', borderRadius: 999 }} />
                    <Typography variant="caption" color="text.secondary">
                      Alignment (−1 to +1)
                    </Typography>
                  </Stack>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Box sx={{ width: 10, height: 10, bgcolor: '#ffb74d', borderRadius: 999 }} />
                    <Typography variant="caption" color="text.secondary">
                      Trade volume (normalized)
                    </Typography>
                  </Stack>
                </Stack>
              </Box>
            </Stack>
          )}
        </Stack>
      </Box>
    </Dialog>
  )
}
