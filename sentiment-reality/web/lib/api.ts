import type { DashboardData, ApiResponse } from './types'

// API base URL - configured via environment variable
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic fetch wrapper with error handling
async function fetchApi<T>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`)

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

// Dashboard API endpoints
export const api = {
  // Get dashboard data for a ticker
  getDashboard: (ticker: string, period = '7d') =>
    fetchApi<DashboardData>(`/dashboard/${ticker}?period=${period}`),

  // Health check
  health: () => fetchApi<{ status: string }>('/health'),
}

export default api
