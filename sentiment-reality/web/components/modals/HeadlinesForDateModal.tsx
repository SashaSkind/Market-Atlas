'use client'

import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import type { NewsItem } from '@/lib/types'
import { getHeadlinesByDate } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface HeadlinesForDateModalProps {
  ticker: string | null
  date: string | null  // YYYY-MM-DD
  onClose: () => void
}

export default function HeadlinesForDateModal({
  ticker,
  date,
  onClose,
}: HeadlinesForDateModalProps) {
  const [headlines, setHeadlines] = useState<NewsItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!ticker || !date) {
      setHeadlines([])
      return
    }

    const fetchHeadlines = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getHeadlinesByDate(ticker, date)
        setHeadlines(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch headlines')
      } finally {
        setIsLoading(false)
      }
    }

    fetchHeadlines()
  }, [ticker, date])

  const isOpen = Boolean(ticker && date)

  return (
    <Dialog open={isOpen} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>
        Headlines for {date ? formatDate(date) : ''}
      </DialogTitle>
      <DialogContent>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : headlines.length === 0 ? (
          <Typography color="text.secondary">
            No headlines found for this date.
          </Typography>
        ) : (
          <Stack spacing={2} sx={{ mt: 1 }}>
            {headlines.map((headline, index) => (
              <Paper
                key={headline.id ?? index}
                variant="outlined"
                sx={{ p: 2, bgcolor: 'rgba(20, 27, 26, 0.8)' }}
              >
                <Typography variant="subtitle1">
                  {headline.url ? (
                    <Box
                      component="a"
                      href={headline.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{
                        color: 'inherit',
                        textDecoration: 'none',
                        '&:hover': { textDecoration: 'underline' },
                      }}
                    >
                      {headline.title}
                    </Box>
                  ) : (
                    headline.title
                  )}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
                  <Chip
                    size="small"
                    label={headline.sentiment_label ?? 'NEUTRAL'}
                    color={
                      headline.sentiment_label === 'POSITIVE'
                        ? 'success'
                        : headline.sentiment_label === 'NEGATIVE'
                          ? 'error'
                          : 'default'
                    }
                  />
                  {headline.confidence && (
                    <Typography variant="caption" color="text.secondary">
                      {Math.round(headline.confidence * 100)}%
                    </Typography>
                  )}
                  {headline.source && (
                    <Typography variant="caption" color="text.secondary">
                      {headline.source}
                    </Typography>
                  )}
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
