import type { DashboardData, TaskResponse, ApiResponse } from './types'

// API base URL - configured via environment variable
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic fetch wrapper with error handling
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options)

    if (!response.ok) {
      return {
        data: null as T,
        success: false,
        error: `HTTP ${response.status}: ${response.statusText}`,
      }
    }

    const data = await response.json()
    return { data, success: true }
  } catch (error) {
    return {
      data: null as T,
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Dashboard API
export const api = {
  // Health check
  health: () => fetchApi<{ ok: boolean }>('/health'),

  // Get dashboard data for a ticker
  getDashboard: (ticker: string, period: number = 90) =>
    fetchApi<DashboardData>(`/dashboard?ticker=${ticker}&period=${period}`),

  // Add a stock to track (creates BACKFILL_STOCK task)
  addStock: (ticker: string) =>
    fetchApi<TaskResponse>('/stocks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker }),
    }),

  // Refresh a stock (creates REFRESH_STOCK task)
  refreshStock: (ticker: string) =>
    fetchApi<TaskResponse>('/stocks/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker }),
    }),
}

export default api
