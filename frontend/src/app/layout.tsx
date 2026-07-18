import './globals.css'
import type { Metadata } from 'next'
import { Outfit, JetBrains_Mono } from 'next/font/google'

const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: "DataTalk — AI Data Assistant",
  description: "Talk to your databases and documents using natural language. Powered by agentic AI with real-time reasoning transparency.",
  icons: { icon: "/favicon.ico" },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${outfit.variable} ${jetbrainsMono.variable} font-sans`}>{children}</body>
    </html>
  )
}
