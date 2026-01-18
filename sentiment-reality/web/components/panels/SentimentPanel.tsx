'use client'

import { Card, CardContent, Chip, Skeleton, Stack, Typography } from '@mui/material'

interface SentimentPanelProps {
  ticker?: string
  sentimentScore?: number | null
  tags: string[]
  isLoading?: boolean
}

export default function SentimentPanel({
  ticker,
  sentimentScore,
  tags,
  isLoading,
}: SentimentPanelProps) {
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
          <Typography variant="h6">Top Divergence</Typography>
          {isLoading ? (
            <Stack spacing={1}>
              <Skeleton variant="text" width={80} height={32} />
              <Skeleton variant="text" width={220} />
              <Stack direction="row" spacing={1}>
                <Skeleton variant="rounded" width={64} height={24} />
                <Skeleton variant="rounded" width={64} height={24} />
                <Skeleton variant="rounded" width={64} height={24} />
              </Stack>
            </Stack>
          ) : (
            <>
              <Typography variant="h4">{ticker ?? '—'}</Typography>
              <Typography color="text.secondary">
                Sentiment {sentimentScore !== undefined && sentimentScore !== null
                  ? sentimentScore.toFixed(2)
                  : '—'}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Stack>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
