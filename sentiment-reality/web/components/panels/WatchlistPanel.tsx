'use client'

import { Box, Card, CardContent, Skeleton, Stack, Typography } from '@mui/material'

interface WatchlistPanelProps {
  statusText: string
  selectedTicker?: string
  selectedPrice?: number | null
  selectedSentiment?: number | null
  priceReturn?: number | null
  selectedVolume?: number | null
  isLoading?: boolean
}

export default function WatchlistPanel({
  statusText,
  selectedTicker,
  selectedPrice,
  selectedSentiment,
  priceReturn,
  selectedVolume,
  isLoading,
}: WatchlistPanelProps) {
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
          <Typography variant="h6">
            {selectedTicker ? `${selectedTicker} Details` : 'Stock Details'}
          </Typography>
          {isLoading ? (
            <Stack spacing={1}>
              <Skeleton variant="text" width={200} />
              <Skeleton variant="text" width={150} />
              <Skeleton variant="text" width={120} />
            </Stack>
          ) : (
            <Stack spacing={1}>
              {statusText.toLowerCase() !== 'ready' && (
                <Typography variant="body1" color="text.secondary">
                  {statusText}
                </Typography>
              )}
              <Typography variant="h5" color="text.secondary">
                Price:{' '}
                {selectedPrice != null ? `$${selectedPrice.toFixed(2)}` : '—'}
                {selectedPrice != null && priceReturn != null && (
                  <Box
                    component="span"
                    sx={{ color: priceReturn >= 0 ? '#4ade80' : '#f87171', fontWeight: 500, ml: 1 }}
                  >
                    {(() => {
                      const absChange = selectedPrice * (priceReturn / 100) / (1 + priceReturn / 100)
                      return (
                        <>
                          {priceReturn >= 0 ? '+' : ''}${absChange.toFixed(2)} ({Math.abs(priceReturn).toFixed(2)}%)
                          <Box
                            component="span"
                            sx={{
                              display: 'inline-block',
                              ml: 0.5,
                              transform: priceReturn >= 0 ? 'rotate(-45deg)' : 'rotate(45deg)',
                            }}
                          >
                            →
                          </Box>
                        </>
                      )
                    })()}
                  </Box>
                )}
              </Typography>
              <Typography variant="h5" color="text.secondary">
                Sentiment score:{' '}
                {selectedSentiment !== undefined && selectedSentiment !== null
                  ? selectedSentiment.toFixed(2)
                  : '—'}
              </Typography>
              <Typography variant="h5" color="text.secondary">
                Trade volume:{' '}
                {selectedVolume != null
                  ? selectedVolume.toLocaleString('en-US')
                  : '—'}
              </Typography>
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
