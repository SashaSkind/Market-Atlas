import type { Metadata } from 'next'
// TODO: Uncomment when ready to add styling
// import '@/styles/globals.css'

export const metadata: Metadata = {
  title: 'Sentiment Reality | Market Sentiment Analysis',
  description: 'Analyze when market sentiment diverges from actual performance',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {/* TODO: Add header with navigation */}
        {/* TODO: Add footer */}
        <main>{children}</main>
      </body>
    </html>
  )
}
