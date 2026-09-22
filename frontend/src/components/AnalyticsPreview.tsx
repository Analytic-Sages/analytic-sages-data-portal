import ReactECharts from 'echarts-for-react'
import { DEFAULT_CHART_STYLE } from '../lib/chartOptions'

const VOLUME_SERIES = [
  1.1, 1.2, 1.05, 1.35, 1.5, 1.42, 1.6, 1.55, 1.7, 1.65, 1.8, 1.75, 1.9, 1.85, 2.0, 1.95,
]

const TOKEN_BARS = [
  { symbol: 'SOL', pct: 92 },
  { symbol: 'USDC', pct: 74 },
  { symbol: 'JUP', pct: 48 },
  { symbol: 'BONK', pct: 36 },
]

export function AnalyticsPreview() {
  const lineOption = {
    grid: { left: 12, right: 12, top: 16, bottom: 12 },
    xAxis: {
      type: 'category',
      show: true,
      boundaryGap: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      data: VOLUME_SERIES.map((_, i) => i),
    },
    yAxis: {
      type: 'value',
      show: true,
      splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } },
      axisLabel: { show: false },
    },
    series: [
      {
        type: 'line',
        data: VOLUME_SERIES,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2.5, color: DEFAULT_CHART_STYLE.primary },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(249, 115, 22, 0.28)' },
              { offset: 1, color: 'rgba(249, 115, 22, 0.02)' },
            ],
          },
        },
      },
    ],
  }

  return (
    <aside className="analytics-preview" aria-label="Sample Solana analytics preview">
      <div className="analytics-preview-head">
        <h2>Solana Network Activity</h2>
        <span className="chip available">Sample</span>
      </div>
      <div className="analytics-metrics">
        <div className="analytics-metric">
          <span className="analytics-metric-label">Transactions</span>
          <strong>12.4M</strong>
        </div>
        <div className="analytics-metric">
          <span className="analytics-metric-label">Active wallets</span>
          <strong>842K</strong>
        </div>
        <div className="analytics-metric">
          <span className="analytics-metric-label">Volume</span>
          <strong>$1.82B</strong>
        </div>
      </div>
      <div className="analytics-mini-chart">
        <ReactECharts
          option={lineOption}
          style={{ height: 200, width: '100%' }}
          opts={{ renderer: 'canvas' }}
        />
      </div>
      <div className="analytics-token-block">
        <h3>Token activity</h3>
        <ul className="analytics-token-list">
          {TOKEN_BARS.map((token) => (
            <li key={token.symbol}>
              <span className="analytics-token-symbol">{token.symbol}</span>
              <span className="analytics-token-bar" aria-hidden="true">
                <span style={{ width: `${token.pct}%` }} />
              </span>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}
