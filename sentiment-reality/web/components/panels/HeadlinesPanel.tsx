'use client'

import {
  Box,
  Card,
  CardContent,
  Chip,
  Skeleton,
  Stack,
  Typography,
  Paper,
} from '@mui/material'
import type { NewsItem } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface HeadlinesPanelProps {
  headlines: NewsItem[]
  isLoading?: boolean
  onSelectHeadline: (headline: NewsItem) => void
}

export default function HeadlinesPanel({ headlines, isLoading, onSelectHeadline }: HeadlinesPanelProps) {
  return (
    <Card
      sx={{
        height: '100%',
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
          <Typography variant="h6">Recent Articles</Typography>
          {isLoading ? (
            <Stack spacing={2}>
              {Array.from({ length: 2 }).map((_, index) => (
                <Paper key={index} variant="outlined" sx={{ p: 2 }}>
                  <Skeleton variant="text" width={80} />
                  <Skeleton variant="text" width="80%" />
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    <Skeleton variant="rounded" width={72} height={24} />
                    <Skeleton variant="rounded" width={48} height={24} />
                    <Skeleton variant="rounded" width={64} height={24} />
                  </Stack>
                </Paper>
              ))}
            </Stack>
          ) : headlines.length === 0 ? (
            <Typography color="text.secondary">No data yet. Click Refresh.</Typography>
          ) : (
            <Stack spacing={2}>
              {headlines.map((item) => (
                <Paper
                  key={item.id ?? item.title}
                  variant="outlined"
                  onClick={() => onSelectHeadline(item)}
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    bgcolor: 'rgba(20, 27, 26, 0.8)',
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {formatDate(item.published_at)}
                  </Typography>
                  <Typography variant="subtitle1" sx={{ mt: 0.5 }}>
                    {item.url ? (
                      <Box
                        component="a"
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{
                          color: 'inherit',
                          textDecoration: 'none',
                          '&:hover': { textDecoration: 'underline' },
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {item.title}
                      </Box>
                    ) : (
                      item.title
                    )}
                  </Typography>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
                    <Chip
                      size="small"
                      label={item.sentiment_label ?? 'Scoring...'}
                      color={item.sentiment_label ? 'default' : 'warning'}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {item.confidence ? `${Math.round(item.confidence * 100)}%` : '—'}
                    </Typography>
                    {item.source && (
                      <Typography variant="caption" color="text.secondary">
                        {item.source}
                      </Typography>
                    )}
                  </Stack>
                </Paper>
              ))}
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
