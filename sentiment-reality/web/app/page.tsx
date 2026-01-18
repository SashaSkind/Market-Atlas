'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Box, Button, Stack, Typography } from '@mui/material'
import AppShell from '@/components/layout/AppShell'
import WatchlistSelector from '@/components/panels/WatchlistSelector'
import NarrativeReliabilityPanel from '@/components/panels/NarrativeReliabilityPanel'
import MisalignmentDaysPanel from '@/components/panels/MisalignmentDaysPanel'
import WatchlistPanel from '@/components/panels/WatchlistPanel'
import HeadlinesPanel from '@/components/panels/HeadlinesPanel'
import AddStockModal from '@/components/modals/AddStockModal'
import HeadlineDetailsModal from '@/components/modals/HeadlineDetailsModal'
import HeadlinesForDateModal from '@/components/modals/HeadlinesForDateModal'
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
  const [selectedMisalignmentDate, setSelectedMisalignmentDate] = useState<string | null>(null)

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
                <Button
                  variant="outlined"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  sx={{ borderRadius: 999 }}
                >
                  {isRefreshing ? 'Refreshing...' : 'Refresh'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setIsAddStockOpen(true)}
                  sx={{ borderRadius: 999 }}
                >
                  Add Stock
                </Button>
              </Stack>
            </Stack>
          </Box>

          {/* Stock Selector */}
          <WatchlistSelector
            tickers={tickers}
            selectedTicker={selectedTicker}
            onTickerChange={setSelectedTicker}
            isLoading={isLoading}
          />

          {/* Primary Signal Box - Narrative Reliability */}
          <NarrativeReliabilityPanel
            score={data?.alignment.score}
            interpretation={data?.alignment.interpretation}
            misalignmentDays={data?.alignment.misalignment_days}
            period={period}
            onPeriodChange={setPeriod}
            isLoading={isLoading}
          />

          {/* Box 2: Where the Narrative Failed */}
          <MisalignmentDaysPanel
            misalignmentList={data?.alignment.misalignment_list ?? []}
            onSelectDate={setSelectedMisalignmentDate}
            isLoading={isLoading}
          />

          {/* Watchlist Panel */}
          <WatchlistPanel
            statusText={isRefreshing ? 'Refreshing...' : error ? 'API unavailable.' : data ? 'Ready' : 'Loading data...'}
            selectedTicker={selectedTicker ?? ''}
            selectedPrice={data?.price_summary.current_price ?? null}
            selectedSentiment={data?.sentiment_summary.current_score ?? null}
            priceReturn={data?.price_summary.period_return ?? null}
            isLoading={isLoading}
          />

          {/* Box 3: Recent Articles */}
          <HeadlinesPanel
            headlines={data?.headlines ?? []}
            isLoading={isLoading}
            onSelectHeadline={setSelectedHeadline}
          />
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
      <HeadlinesForDateModal
        ticker={selectedTicker}
        date={selectedMisalignmentDate}
        onClose={() => setSelectedMisalignmentDate(null)}
      />
    </>
  )
}
