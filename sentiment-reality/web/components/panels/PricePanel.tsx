'use client'

import { Box, Button, Card, CardContent, Skeleton, Stack, Typography } from '@mui/material'

interface PricePanelProps {
  score?: number | null
  interpretation?: string | null
  period?: number
  onPeriodChange?: (period: number) => void
  isLoading?: boolean
}

export default function PricePanel({
  score,
  interpretation,
  period = 90,
  onPeriodChange,
  isLoading,
}: PricePanelProps) {
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
        <Stack spacing={1}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={2}>
            <Typography variant="h6">Alignment Score</Typography>
            <Stack direction="row" spacing={1}>
              {[7, 14, 30].map((value) => (
                <Button
                  key={value}
                  size="small"
                  variant={period === value ? 'contained' : 'outlined'}
                  onClick={() => onPeriodChange?.(value)}
                >
                  {value}d
                </Button>
              ))}
            </Stack>
          </Stack>
          {isLoading ? (
            <Stack spacing={1}>
              <Skeleton variant="text" width={90} height={36} />
              <Skeleton variant="text" width={180} />
              <Skeleton variant="rounded" height={42} />
            </Stack>
          ) : (
            <>
              <Typography variant="h4">
                {score !== undefined && score !== null ? score.toFixed(2) : '—'}
              </Typography>
              <Typography color="text.secondary">
                {interpretation ?? 'Waiting for signal'}
              </Typography>
              <Box
                sx={{
                  mt: 2,
                  height: 42,
                  borderRadius: 2,
                  bgcolor: 'action.hover',
                }}
              />
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
