'use client'

import { Box, Card, CardContent, Paper, Skeleton, Stack, Typography } from '@mui/material'
import type { MisalignmentDay } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface MisalignmentDaysPanelProps {
  misalignmentList: MisalignmentDay[]
  onSelectDate: (date: string) => void
  isLoading?: boolean
}

export default function MisalignmentDaysPanel({
  misalignmentList,
  onSelectDate,
  isLoading,
}: MisalignmentDaysPanelProps) {
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
          <Typography variant="h6">Where the Narrative Failed</Typography>

          {isLoading ? (
            <Stack spacing={1}>
              {Array.from({ length: 3 }).map((_, index) => (
                <Paper key={index} variant="outlined" sx={{ p: 1.5 }}>
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="text" width="40%" />
                </Paper>
              ))}
            </Stack>
          ) : misalignmentList.length === 0 ? (
            <Typography color="text.secondary">
              No misalignment days in period
            </Typography>
          ) : (
            <Stack spacing={1}>
              {misalignmentList.map((day) => (
                <Paper
                  key={day.date}
                  variant="outlined"
                  onClick={() => onSelectDate(day.date)}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    bgcolor: 'rgba(248, 113, 113, 0.1)',
                    borderColor: 'rgba(248, 113, 113, 0.3)',
                    '&:hover': {
                      bgcolor: 'rgba(248, 113, 113, 0.2)',
                    },
                  }}
                >
                  <Stack
                    direction="row"
                    alignItems="center"
                    justifyContent="space-between"
                    spacing={2}
                  >
                    <Box>
                      <Typography variant="subtitle2">
                        {formatDate(day.date)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {day.tag}
                      </Typography>
                    </Box>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        color: day.return_1d && day.return_1d < 0 ? '#f87171' : '#4ade80',
                        fontWeight: 600,
                      }}
                    >
                      {day.return_1d !== null && day.return_1d !== undefined
                        ? `${day.return_1d >= 0 ? '+' : ''}${day.return_1d.toFixed(2)}%`
                        : '—'}
                    </Typography>
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
