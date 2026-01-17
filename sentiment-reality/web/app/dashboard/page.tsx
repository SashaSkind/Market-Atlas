'use client'

// Dashboard page for sentiment analysis
//
// TODO: This page should contain:
//
// 1. Ticker selector (dropdown or search)
//    - Default to SPY or user's last selection
//    - Options: SPY, AAPL, TSLA, etc.
//
// 2. Summary cards (3 cards in a row):
//    - Sentiment card: current_score, dominant_label, trend indicator
//    - Price card: current_price, period_return percentage
//    - Alignment card: alignment score, interpretation text
//
// 3. Charts section:
//    - PriceChart: Line chart showing close prices over time
//    - SentimentChart: Bar chart showing daily sentiment scores
//    - AlignmentChart: Combined view of sentiment vs price returns
//
// 4. State management:
//    - Use useState for ticker, data, loading, error
//    - Use useEffect to fetch data when ticker changes
//    - Call api.getDashboard(ticker) from @/lib/api
//
// 5. Loading and error states:
//    - Show "Loading..." while fetching
//    - Show error message if fetch fails

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <p>TODO: Implement dashboard with charts</p>
    </div>
  )
}
