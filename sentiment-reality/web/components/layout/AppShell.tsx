'use client'

import { Box, Button, Container, Link, Stack, Toolbar, Typography } from '@mui/material'

interface AppShellProps {
  ticker: string
  tickers: string[]
  period: number
  onTickerChange: (ticker: string) => void
  onPeriodChange: (period: number) => void
  onRefresh: () => void
  onAddStock: () => void
  lastUpdated?: string | null
  children: React.ReactNode
}

export default function AppShell({
  ticker: _ticker,
  tickers: _tickers,
  period: _period,
  onTickerChange: _onTickerChange,
  onPeriodChange: _onPeriodChange,
  onRefresh: _onRefresh,
  onAddStock: _onAddStock,
  lastUpdated,
  children,
}: AppShellProps) {
  return (
    <Box>
      <Box sx={{ color: 'text.primary', pt: { xs: 2, md: 3 } }}>
        <Container
          maxWidth={false}
          sx={{ px: { xs: 2, sm: 3 }, maxWidth: { md: 960 }, mx: 'auto' }}
        >
          <Toolbar disableGutters sx={{ flexWrap: 'wrap', gap: 2 }}>
            <Stack direction="row" spacing={2} alignItems="center" sx={{ flexGrow: 1 }}>
              <Box
                sx={{
                  width: 36,
                  height: 36,
                  display: 'grid',
                  placeItems: 'center',
                }}
              >
                <svg
                  width="36"
                  height="36"
                  viewBox="0 0 512 512"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <rect width="512" height="512" rx="90" fill="url(#paint0_linear)" />
                  <path
                    d="M108 356 L196 248 L296 300 L404 148"
                    stroke="white"
                    strokeWidth="28"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <circle cx="196" cy="248" r="18" fill="#3b82f6" stroke="white" strokeWidth="14" />
                  <circle cx="296" cy="300" r="18" fill="#3b82f6" stroke="white" strokeWidth="14" />
                  <defs>
                    <linearGradient
                      id="paint0_linear"
                      x1="0"
                      y1="0"
                      x2="512"
                      y2="512"
                      gradientUnits="userSpaceOnUse"
                    >
                      <stop stopColor="#4fa9ff" />
                      <stop offset="1" stopColor="#1f4ddc" />
                    </linearGradient>
                  </defs>
                </svg>
              </Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  letterSpacing: 0.6,
                  textTransform: 'uppercase',
                }}
              >
                Atlas: Market Sentiment Tool
              </Typography>
            </Stack>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              sx={{
                display: { xs: 'none', md: 'flex' },
                '& a': {
                  color: 'text.secondary',
                  fontSize: 14,
                  '&:hover': { color: 'text.primary' },
                },
              }}
            >
              <Link href="#overview" underline="none">
                Overview
              </Link>
              <Link href="#signals" underline="none">
                Signals
              </Link>
              <Link href="#watchlist" underline="none">
                Watchlist
              </Link>
            </Stack>
            <Button
              variant="outlined"
              color="inherit"
              sx={{
                display: { xs: 'none', md: 'inline-flex' },
                borderColor: 'rgba(255, 255, 255, 0.2)',
              }}
            >
              Run Daily Scan
            </Button>
          </Toolbar>
          {lastUpdated && (
            <Box sx={{ pb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Last updated {lastUpdated}
              </Typography>
            </Box>
          )}
        </Container>
      </Box>
      <Container
        maxWidth={false}
        sx={{
          py: { xs: 3, sm: 4 },
          px: { xs: 2, sm: 3 },
          maxWidth: { md: 960 },
          mx: 'auto',
        }}
      >
        {children}
      </Container>
    </Box>
  )
}
