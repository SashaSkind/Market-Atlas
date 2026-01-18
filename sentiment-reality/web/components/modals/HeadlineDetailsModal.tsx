'use client'

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from '@mui/material'
import type { NewsItem } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface HeadlineDetailsModalProps {
  headline: NewsItem | null
  onClose: () => void
}

export default function HeadlineDetailsModal({ headline, onClose }: HeadlineDetailsModalProps) {
  return (
    <Dialog open={Boolean(headline)} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Headline Details</DialogTitle>
      <DialogContent>
        {headline ? (
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography variant="h6">{headline.title}</Typography>
            <Typography color="text.secondary">
              {headline.source ?? 'Unknown source'} · {formatDate(headline.published_at, true)}
            </Typography>
            <Divider />
            <Typography>
              Sentiment: {headline.sentiment_label ?? 'NEUTRAL'} · Confidence{' '}
              {headline.confidence ? `${Math.round(headline.confidence * 100)}%` : '—'}
            </Typography>
            {headline.snippet && (
              <Typography color="text.secondary">{headline.snippet}</Typography>
            )}
          </Stack>
        ) : (
          <Typography color="text.secondary">No headline selected.</Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
