'use client'

import { Box, Button, Card, CardContent, Skeleton, Stack, Typography } from '@mui/material'

interface NarrativeReliabilityPanelProps {
  score?: number | null
  interpretation?: string | null
  misalignmentDays?: number | null
  period: number
  onPeriodChange: (period: number) => void
  isLoading?: boolean
}

function getScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return '#9ca3af' // gray
  if (score > 0.3) return '#4ade80' // green
  if (score < -0.3) return '#f87171' // red
  return '#facc15' // yellow
}

export default function NarrativeReliabilityPanel({
  score,
  interpretation,
  misalignmentDays,
  period,
  onPeriodChange,
  isLoading,
}: NarrativeReliabilityPanelProps) {
  const scoreColor = getScoreColor(score)

  return (
    <Card
      sx={{
        width: '100%',
        minHeight: 220,
        borderRadius: 3,
        boxShadow: '0 12px 30px rgba(0, 0, 0, 0.45)',
        bgcolor: 'background.paper',
        border: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={2}>
            <Typography variant="h6">Narrative Reliability</Typography>
            <Stack direction="row" spacing={1}>
              {[7, 14, 30].map((value) => (
                <Button
                  key={value}
                  size="small"
                  variant={period === value ? 'contained' : 'outlined'}
                  onClick={() => onPeriodChange(value)}
                >
                  {value}d
                </Button>
              ))}
            </Stack>
          </Stack>

          {isLoading ? (
            <Stack spacing={1}>
              <Skeleton variant="text" width={120} height={64} />
              <Skeleton variant="text" width={100} />
              <Skeleton variant="text" width={180} />
            </Stack>
          ) : (
            <>
              <Typography
                variant="h2"
                sx={{
                  fontWeight: 700,
                  color: scoreColor,
                  lineHeight: 1,
                }}
              >
                {score !== undefined && score !== null ? score.toFixed(2) : '—'}
              </Typography>
              <Typography variant="h6" color="text.secondary">
                {interpretation ?? 'Waiting for signal'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {misalignmentDays !== undefined && misalignmentDays !== null
                  ? `${misalignmentDays} misalignment day${misalignmentDays === 1 ? '' : 's'} in period`
                  : 'No misalignment data'}
              </Typography>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
