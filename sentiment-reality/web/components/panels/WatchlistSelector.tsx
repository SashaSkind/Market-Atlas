'use client'

import { Chip, Skeleton, Stack } from '@mui/material'

interface WatchlistSelectorProps {
  tickers: string[]
  selectedTicker: string | null
  onTickerChange: (ticker: string) => void
  isLoading?: boolean
}

export default function WatchlistSelector({
  tickers,
  selectedTicker,
  onTickerChange,
  isLoading,
}: WatchlistSelectorProps) {
  return (
    <Stack direction="row" spacing={1} flexWrap="wrap" alignItems="center">
      {isLoading ? (
        Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="rounded" width={64} height={32} />
        ))
      ) : (
        tickers.map((ticker) => (
          <Chip
            key={ticker}
            label={ticker}
            clickable
            onClick={() => onTickerChange(ticker)}
            variant={ticker === selectedTicker ? 'filled' : 'outlined'}
            color={ticker === selectedTicker ? 'primary' : 'default'}
          />
        ))
      )}
    </Stack>
  )
}
