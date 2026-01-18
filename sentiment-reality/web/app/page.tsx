'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Box, Button, Grid, Stack, Typography } from '@mui/material'
import AppShell from '@/components/layout/AppShell'
import PricePanel from '@/components/panels/PricePanel'
import SentimentPanel from '@/components/panels/SentimentPanel'
import AlignmentPanel from '@/components/panels/AlignmentPanel'
import HeadlinesPanel from '@/components/panels/HeadlinesPanel'
import AddStockModal from '@/components/modals/AddStockModal'
import HeadlineDetailsModal from '@/components/modals/HeadlineDetailsModal'
import { getDashboard, getStocks, refreshStock } from '@/lib/api'
import type { DashboardData, NewsItem, Stock } from '@/lib/types'

export default function Home() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)
  const [period, setPeriod] = useState(30)
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAddStockOpen, setIsAddStockOpen] = useState(false)
  const [selectedHeadline, setSelectedHeadline] = useState<NewsItem | null>(null)

  // Get active tickers from stocks
  const tickers = useMemo(() => {
    return stocks.filter((s) => s.is_active).map((s) => s.ticker).sort()
  }, [stocks])

  const lastUpdated = useMemo(() => {
    const value = data?.daily_data.at(-1)?.date
    if (!value) return null
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return value
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(parsed)
  }, [data])

  // Fetch stocks on mount
  useEffect(() => {
    let isMounted = true
    const fetchStockList = async () => {
      try {
        const stockList = await getStocks()
        if (isMounted && stockList.length > 0) {
          setStocks(stockList)
          const activeTickers = stockList.filter((s) => s.is_active).map((s) => s.ticker)
          if (activeTickers.length > 0 && !selectedTicker) {
            setSelectedTicker(activeTickers[0])
          }
        }
      } catch (err) {
        console.error('Failed to fetch stocks:', err)
      }
    }
    fetchStockList()
    return () => { isMounted = false }
  }, [])

  // Fetch dashboard when ticker or period changes
  const fetchDashboard = useCallback(async () => {
    if (!selectedTicker) return
    setIsLoading(true)
    setError(null)
    try {
      const response = await getDashboard(selectedTicker, period)
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedTicker, period])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  const handleRefresh = async () => {
    if (!selectedTicker) return
    setIsRefreshing(true)
    setError(null)
    try {
      await refreshStock(selectedTicker)
      // Re-fetch after 10 seconds to allow backend to process
      setTimeout(() => {
        fetchDashboard()
        setIsRefreshing(false)
      }, 10000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh ticker.')
      setIsRefreshing(false)
    }
  }

  const sentimentScore = data?.sentiment_summary.current_score ?? null
  const priceReturn = data?.price_summary.period_return ?? null
  const alignmentScore = data?.alignment.score ?? null
  const coverage = data?.coverage
  const hasCoverageGap = coverage && coverage.sentiment_period_used < coverage.sentiment_period_requested

  return (
    <>
      <AppShell
        ticker={selectedTicker ?? ''}
        tickers={tickers}
        period={period}
        onTickerChange={setSelectedTicker}
        onPeriodChange={setPeriod}
        onRefresh={handleRefresh}
        onAddStock={() => setIsAddStockOpen(true)}
        lastUpdated={lastUpdated}
      >
        <Stack spacing={{ xs: 4, md: 5 }}>
          {error && <Alert severity="error">{error}</Alert>}
          {isRefreshing && (
            <Alert severity="info">Refreshing data... This may take a few seconds.</Alert>
          )}
          {!data && !isLoading && !error && !isRefreshing && (
            <Alert severity="info">No data yet. Click Refresh.</Alert>
          )}
          {hasCoverageGap && (
            <Alert severity="warning">
              We measure narrative alignment only where we have narrative data.
              <Typography variant="caption" display="block">
                Sentiment coverage: {coverage.sentiment_days_available} / {coverage.sentiment_period_requested} days
              </Typography>
            </Alert>
          )}

          <Box id="overview">
            <Stack spacing={1.5}>
              <Typography variant="overline" color="text.secondary">
                Narrative vs. Performance
              </Typography>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700, lineHeight: 1.1 }}
              >
                Find false conviction.
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.8 }}>
                Where headlines are confident and price action disagrees.
              </Typography>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                alignItems={{ xs: 'stretch', sm: 'center' }}
              >
                <Button
                  variant="contained"
                  color="primary"
                  fullWidth
                  sx={{ maxWidth: { sm: 240 }, borderRadius: 999 }}
                >
                  View Misalignment Map
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  fullWidth
                  sx={{ maxWidth: { sm: 240 }, borderRadius: 999 }}
                >
                  Export Weekly Brief
                </Button>
              </Stack>
            </Stack>
          </Box>

          <Box id="signals">
            <Grid container spacing={3} alignItems="stretch">
              <Grid size={{ xs: 12, md: 4 }}>
                <SentimentPanel
                  ticker={selectedTicker ?? ''}
                  sentimentScore={sentimentScore}
                  tags={[
                    data?.alignment.interpretation ?? 'Unlabeled',
                    data?.sentiment_summary.dominant_label ?? 'NEUTRAL',
                    data?.sentiment_summary.trend ?? 'stable',
                  ]}
                  isLoading={isLoading}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <AlignmentPanel
                  tickers={tickers}
                  statusText={
                    isRefreshing ? 'Refreshing...' : error ? 'API unavailable.' : data ? 'Ready' : 'Loading data...'
                  }
                  selectedTicker={selectedTicker ?? ''}
                  selectedPrice={data?.price_summary.current_price ?? null}
                  selectedSentiment={sentimentScore}
                  priceReturn={priceReturn}
                  onSelectTicker={(t) => t && setSelectedTicker(t)}
                  isLoading={isLoading}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <PricePanel
                  score={alignmentScore}
                  interpretation={data?.alignment.interpretation ?? null}
                  period={period}
                  onPeriodChange={setPeriod}
                  isLoading={isLoading}
                />
              </Grid>
            </Grid>
          </Box>

          {/* Watchlist removed for now */}

          <Box id="timeline">
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Stack spacing={1}>
                  <Typography variant="h6">Today&apos;s Narrative Shifts</Typography>
                  <Typography color="text.secondary">
                    Generated by clustering topics across news and social feeds.
                  </Typography>
                </Stack>
              </Grid>
              <Grid size={{ xs: 12, md: 8 }}>
                <HeadlinesPanel
                  headlines={data?.headlines ?? []}
                  isLoading={isLoading}
                  onSelectHeadline={setSelectedHeadline}
                />
              </Grid>
            </Grid>
          </Box>
        </Stack>
      </AppShell>

      <AddStockModal
        open={isAddStockOpen}
        onClose={() => setIsAddStockOpen(false)}
        onAdded={setSelectedTicker}
      />
      <HeadlineDetailsModal
        headline={selectedHeadline}
        onClose={() => setSelectedHeadline(null)}
      />
    </>
  )
}
