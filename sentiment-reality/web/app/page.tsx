'use client'

import { useEffect, useMemo, useState } from 'react'
import { Alert, Box, Button, Grid, Stack, Typography } from '@mui/material'
import AppShell from '@/components/layout/AppShell'
import PricePanel from '@/components/panels/PricePanel'
import SentimentPanel from '@/components/panels/SentimentPanel'
import AlignmentPanel from '@/components/panels/AlignmentPanel'
import HeadlinesPanel from '@/components/panels/HeadlinesPanel'
import AddStockModal from '@/components/modals/AddStockModal'
import HeadlineDetailsModal from '@/components/modals/HeadlineDetailsModal'
import { getDashboard, refreshStock } from '@/lib/api'
import type { DashboardData, NewsItem } from '@/lib/types'

const DEFAULT_TICKERS = ['AAPL', 'AMZN', 'MSFT', 'NVDA', 'TSLA']
const SAMPLE_HEADLINES: NewsItem[] = [
  {
    id: '1',
    title: 'Tesla sentiment cools as deliveries miss expectations',
    source: 'MarketWire',
    published_at: new Date().toISOString(),
    sentiment_label: 'NEGATIVE',
    confidence: 0.72,
    snippet: 'Analysts highlighted softening demand signals across key regions.',
  },
  {
    id: '2',
    title: 'AI capex narrative boosts Nvidia chatter',
    source: 'Tech Pulse',
    published_at: new Date().toISOString(),
    sentiment_label: 'POSITIVE',
    confidence: 0.81,
    snippet: 'Optimism around data center spend returned to headlines.',
  },
  {
    id: '3',
    title: 'Energy narrative flips bullish on supply headlines',
    source: 'Commodities Desk',
    published_at: new Date().toISOString(),
    sentiment_label: 'POSITIVE',
    confidence: 0.66,
  },
]

export default function Home() {
  const [selectedTicker, setSelectedTicker] = useState('TSLA')
  const [trackedTicker, setTrackedTicker] = useState('TSLA')
  const [period, setPeriod] = useState(90)
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAddStockOpen, setIsAddStockOpen] = useState(false)
  const [selectedHeadline, setSelectedHeadline] = useState<NewsItem | null>(null)

  const tickers = useMemo(() => {
    const set = new Set(DEFAULT_TICKERS)
    if (selectedTicker) set.add(selectedTicker)
    return Array.from(set).sort((a, b) => a.localeCompare(b))
  }, [selectedTicker])

  const lastUpdated = useMemo(() => {
    const value = data?.daily_data.at(-1)?.date
    if (!value) return null
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return value
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(parsed)
  }, [data])

  useEffect(() => {
    let isMounted = true
    const fetchDashboard = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await getDashboard(selectedTicker, period)
        if (isMounted) setData(response)
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load dashboard.')
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    fetchDashboard()
    return () => {
      isMounted = false
    }
  }, [selectedTicker, period])

  const handleRefresh = async () => {
    setIsLoading(true)
    setError(null)
    try {
      await refreshStock(selectedTicker)
      const response = await getDashboard(selectedTicker, period)
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh ticker.')
    } finally {
      setIsLoading(false)
    }
  }

  const sentimentScore = data?.sentiment_summary.current_score ?? null
  const priceReturn = data?.price_summary.period_return ?? null
  const alignmentScore = data?.alignment.score ?? null

  return (
    <>
      <AppShell
        ticker={selectedTicker}
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
          {!data && !isLoading && !error && (
            <Alert severity="info">No data yet. Click Refresh.</Alert>
          )}

          <Box id="overview">
            <Stack spacing={2}>
              <Typography variant="overline" color="text.secondary">
                Narrative vs. Performance
              </Typography>
              <Typography variant="h3">
                Find the moments when sentiment goes confidently wrong.
              </Typography>
              <Typography color="text.secondary">
                Track the gap between public narratives and actual price action. Surface
                misalignment, quantify conviction, and explain the why.
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
                  ticker={selectedTicker}
                  sentimentScore={sentimentScore}
                  priceReturn={priceReturn}
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
                    error ? 'API unavailable.' : data ? 'Ready' : 'Loading data...'
                  }
                  selectedTicker={trackedTicker}
                  selectedPrice={null}
                  selectedSentiment={sentimentScore}
                  onSelectTicker={setTrackedTicker}
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
                  headlines={SAMPLE_HEADLINES.map((headline) => ({
                    ...headline,
                    title: `[${trackedTicker}] ${headline.title}`,
                  }))}
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
