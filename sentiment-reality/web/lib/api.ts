import type { DashboardData, Stock, TaskResponse, NewsItem } from './types'

async function fetchJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  return (await response.json()) as T
}

export async function getStocks(): Promise<Stock[]> {
  return fetchJson<Stock[]>('/api/stocks')
}

export async function getDashboard(ticker: string, period: number): Promise<DashboardData> {
  return fetchJson<DashboardData>(`/api/dashboard?ticker=${ticker}&period=${period}`)
}

export async function refreshStock(ticker: string): Promise<TaskResponse> {
  return fetchJson<TaskResponse>('/api/stocks/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker }),
  })
}

export async function addStock(ticker: string): Promise<TaskResponse> {
  return fetchJson<TaskResponse>('/api/stocks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker }),
  })
}

export async function getHeadlinesByDate(ticker: string, date: string): Promise<NewsItem[]> {
  return fetchJson<NewsItem[]>(`/api/headlines/by-date?ticker=${ticker}&date=${date}`)
}
