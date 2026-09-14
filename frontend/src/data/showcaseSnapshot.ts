import type { StudioDashboard, StudioLayoutItem, StudioVisualization } from '../types'

/** Fixed sample rows for the homepage demo. No live query refresh. */
export type ShowcaseSample = {
  columns: string[]
  data: Array<Record<string, unknown>>
}

const HOURS = Array.from({ length: 24 }, (_, i) => {
  const day = 12
  const hour = i
  return `2026-09-${String(day).padStart(2, '0')}T${String(hour).padStart(2, '0')}:00:00+00:00`
})

function wave(base: number, amp: number, i: number, period = 3, bump = 0) {
  return Math.round((base + amp * Math.sin(i / period) + (i % 4) * bump) * 100) / 100
}

const VIZ_IDS = {
  peak: 'a1000001-0000-4000-8000-000000000001',
  volume: 'a1000002-0000-4000-8000-000000000002',
  count: 'a1000003-0000-4000-8000-000000000003',
  tokens: 'a1000004-0000-4000-8000-000000000004',
  tx: 'a1000005-0000-4000-8000-000000000005',
} as const

export const SHOWCASE_SAMPLE_DATA: Record<string, ShowcaseSample> = {
  [VIZ_IDS.peak]: {
    columns: ['peak_hour_volume'],
    data: [{ peak_hour_volume: 248_500 }],
  },
  [VIZ_IDS.volume]: {
    columns: ['hour', 'transfer_volume'],
    data: HOURS.map((hour, i) => ({
      hour,
      transfer_volume: wave(120_000, 35_000, i, 3, 5_000),
    })),
  },
  [VIZ_IDS.count]: {
    columns: ['hour', 'transfer_count'],
    data: HOURS.map((hour, i) => ({
      hour,
      transfer_count: Math.round(wave(900, 180, i, 2.5, 40)),
    })),
  },
  [VIZ_IDS.tokens]: {
    columns: ['mint', 'total_volume'],
    data: [
      { mint: 'USDC', total_volume: 2_450_000 },
      { mint: 'SOL', total_volume: 1_820_000 },
      { mint: 'BONK', total_volume: 640_000 },
      { mint: 'JUP', total_volume: 275_000 },
      { mint: 'RAY', total_volume: 210_000 },
    ],
  },
  [VIZ_IDS.tx]: {
    columns: ['hour', 'tx_count'],
    data: HOURS.map((hour, i) => ({
      hour,
      tx_count: Math.round(wave(4_200, 900, i, 3.5, 120)),
    })),
  },
}

export const SHOWCASE_DASHBOARD: StudioDashboard = {
  id: 'showcase-dashboard-0001',
  slug: 'solana-hourly-showcase',
  title: 'Solana Hourly Activity',
  description:
    'Sample dashboard built from curated Solana data. In Query Studio you write SQL, visualize results, and save charts to boards like this one.',
  visualization_ids: Object.values(VIZ_IDS),
  layout: [
    { i: VIZ_IDS.peak, x: 0, y: 0, w: 3, h: 6, minW: 3, minH: 5 },
    { i: VIZ_IDS.volume, x: 3, y: 0, w: 9, h: 11, minW: 4, minH: 6 },
    { i: VIZ_IDS.count, x: 0, y: 11, w: 6, h: 10, minW: 4, minH: 6 },
    { i: VIZ_IDS.tx, x: 6, y: 11, w: 6, h: 10, minW: 4, minH: 6 },
    { i: VIZ_IDS.tokens, x: 0, y: 21, w: 12, h: 12, minW: 6, minH: 6 },
  ] as StudioLayoutItem[],
  theme: {
    primary: '#F97316',
    secondary: '#0B1F3A',
    background: '#FFFFFF',
    text: '#0B1F3A',
    muted: '#64748B',
    palette: ['#F97316', '#0B1F3A', '#38BDF8', '#A78BFA', '#34D399', '#FBBF24'],
  },
  is_published: true,
  share_enabled: true,
  share_token: 'as-hourly-showcase',
  share_path: '/share/as-hourly-showcase',
  created_at: '2026-09-12T00:00:00+00:00',
  updated_at: '2026-09-12T00:00:00+00:00',
}

export const SHOWCASE_VISUALIZATIONS: StudioVisualization[] = [
  {
    id: VIZ_IDS.peak,
    title: 'Peak transfer volume',
    sql: '-- sample KPI from hourly transfer volume',
    chart_type: 'kpi',
    x_axis: null,
    y_axis: 'peak_hour_volume',
    description: 'Homepage sample',
    created_at: '',
    updated_at: '',
  },
  {
    id: VIZ_IDS.volume,
    title: 'Transfer volume by hour',
    sql: '-- sample line chart',
    chart_type: 'line',
    x_axis: 'hour',
    y_axis: 'transfer_volume',
    description: 'Homepage sample',
    created_at: '',
    updated_at: '',
  },
  {
    id: VIZ_IDS.count,
    title: 'Transfer count by hour',
    sql: '-- sample area chart',
    chart_type: 'area',
    x_axis: 'hour',
    y_axis: 'transfer_count',
    description: 'Homepage sample',
    created_at: '',
    updated_at: '',
  },
  {
    id: VIZ_IDS.tokens,
    title: 'Top tokens by volume',
    sql: '-- sample bar chart',
    chart_type: 'bar',
    x_axis: 'mint',
    y_axis: 'total_volume',
    description: 'Homepage sample',
    created_at: '',
    updated_at: '',
  },
  {
    id: VIZ_IDS.tx,
    title: 'Transactions by hour',
    sql: '-- sample line chart',
    chart_type: 'line',
    x_axis: 'hour',
    y_axis: 'tx_count',
    description: 'Homepage sample',
    created_at: '',
    updated_at: '',
  },
]
