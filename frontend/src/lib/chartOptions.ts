import type { EChartsOption } from 'echarts'

export type ChartType = 'line' | 'bar' | 'area' | 'pie' | 'scatter' | 'kpi'

export const CHART_TYPES: ChartType[] = ['line', 'bar', 'area', 'pie', 'scatter', 'kpi']

export type ChartStyle = {
  primary: string
  secondary: string
  background: string
  text: string
  muted: string
  palette: string[]
}

export const DEFAULT_CHART_STYLE: ChartStyle = {
  primary: '#F97316',
  secondary: '#0B1F3A',
  background: '#FFFFFF',
  text: '#0B1F3A',
  muted: '#64748B',
  palette: ['#F97316', '#0B1F3A', '#38BDF8', '#A78BFA', '#34D399', '#FBBF24'],
}

export const STYLE_PRESETS: Array<{ id: string; label: string; style: ChartStyle }> = [
  { id: 'as-brand', label: 'AS brand', style: { ...DEFAULT_CHART_STYLE, palette: [...DEFAULT_CHART_STYLE.palette] } },
  {
    id: 'ocean',
    label: 'Ocean',
    style: {
      primary: '#0284C7',
      secondary: '#0F172A',
      background: '#F8FAFC',
      text: '#0F172A',
      muted: '#64748B',
      palette: ['#0284C7', '#0EA5E9', '#0369A1', '#38BDF8', '#14B8A6', '#0F172A'],
    },
  },
  {
    id: 'forest',
    label: 'Forest',
    style: {
      primary: '#059669',
      secondary: '#14532D',
      background: '#F7FEE7',
      text: '#14532D',
      muted: '#4B5563',
      palette: ['#059669', '#10B981', '#65A30D', '#84CC16', '#166534', '#14532D'],
    },
  },
  {
    id: 'sunset',
    label: 'Sunset',
    style: {
      primary: '#E11D48',
      secondary: '#7C2D12',
      background: '#FFF7ED',
      text: '#7C2D12',
      muted: '#9A3412',
      palette: ['#E11D48', '#F97316', '#F59E0B', '#FB7185', '#C2410C', '#7C2D12'],
    },
  },
  {
    id: 'mono',
    label: 'Mono',
    style: {
      primary: '#111827',
      secondary: '#374151',
      background: '#FFFFFF',
      text: '#111827',
      muted: '#6B7280',
      palette: ['#111827', '#374151', '#4B5563', '#6B7280', '#9CA3AF', '#D1D5DB'],
    },
  },
]

export type VizConfig = {
  chartType: ChartType
  xAxis: string
  yAxis: string
  style?: Partial<ChartStyle>
  /** Human-readable label for KPI cards (avoids raw field names). */
  kpiLabel?: string
}

function isNumeric(value: unknown): boolean {
  if (typeof value === 'number' && Number.isFinite(value)) return true
  if (typeof value === 'string' && value.trim() !== '' && !Number.isNaN(Number(value))) return true
  return false
}

function asNumber(value: unknown): number {
  return typeof value === 'number' ? value : Number(value)
}

export function mergeChartStyle(
  ...layers: Array<Partial<ChartStyle> | ChartStyle | null | undefined>
): ChartStyle {
  const out: ChartStyle = {
    ...DEFAULT_CHART_STYLE,
    palette: [...DEFAULT_CHART_STYLE.palette],
  }
  for (const layer of layers) {
    if (!layer) continue
    if (layer.primary) out.primary = layer.primary
    if (layer.secondary) out.secondary = layer.secondary
    if (layer.background) out.background = layer.background
    if (layer.text) out.text = layer.text
    if (layer.muted) out.muted = layer.muted
    if (layer.palette?.length) out.palette = [...layer.palette]
  }
  return out
}

export function guessAxes(columns: string[], rows: Array<Record<string, unknown>>): VizConfig {
  const sample = rows[0] ?? {}
  const numeric = columns.filter((c) => isNumeric(sample[c]))
  const categorical = columns.filter((c) => !numeric.includes(c))
  return {
    chartType: 'bar',
    xAxis: categorical[0] ?? columns[0] ?? '',
    yAxis: numeric[0] ?? columns[1] ?? columns[0] ?? '',
    style: { ...DEFAULT_CHART_STYLE, palette: [...DEFAULT_CHART_STYLE.palette] },
  }
}

export function buildChartOption(
  config: VizConfig,
  columns: string[],
  rows: Array<Record<string, unknown>>,
  theme?: Partial<ChartStyle> | null,
): EChartsOption {
  const { chartType, xAxis, yAxis } = config
  const style = mergeChartStyle(theme, config.style)
  const { primary, secondary, background, text, muted, palette } = style

  if (!rows.length || !columns.length) {
    return {
      backgroundColor: background,
      title: { text: 'No data', left: 'center', top: 'middle', textStyle: { color: muted } },
    }
  }

  if (chartType === 'kpi') {
    const total = rows.reduce((sum, row) => sum + (isNumeric(row[yAxis]) ? asNumber(row[yAxis]) : 0), 0)
    const label = config.kpiLabel || yAxis || 'value'
    const display =
      Math.abs(total) >= 1_000_000
        ? `${(total / 1_000_000).toFixed(2)}M`
        : Math.abs(total) >= 1_000
          ? `${(total / 1_000).toFixed(1)}K`
          : String(Number.isInteger(total) ? total : total.toFixed(2))
    return {
      backgroundColor: background,
      title: {
        text: display,
        subtext: label,
        left: 'center',
        top: 'center',
        textStyle: { fontSize: 48, fontWeight: 700, color: primary },
        subtextStyle: { fontSize: 16, color: muted },
      },
    }
  }

  if (chartType === 'pie') {
    const data = rows.map((row) => ({
      name: String(row[xAxis] ?? ''),
      value: isNumeric(row[yAxis]) ? asNumber(row[yAxis]) : 0,
    }))
    return {
      backgroundColor: background,
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'pie',
          radius: ['35%', '65%'],
          data,
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' } },
        },
      ],
      color: palette.length ? palette : [primary, secondary],
    }
  }

  const categories = rows.map((row) => String(row[xAxis] ?? ''))
  const values = rows.map((row) => (isNumeric(row[yAxis]) ? asNumber(row[yAxis]) : 0))

  if (chartType === 'scatter') {
    return {
      backgroundColor: background,
      tooltip: { trigger: 'item' },
      grid: { left: 48, right: 24, top: 32, bottom: 48 },
      xAxis: { type: 'category', data: categories, axisLabel: { color: muted } },
      yAxis: { type: 'value', axisLabel: { color: muted } },
      series: [
        {
          type: 'scatter',
          data: values.map((v, i) => [categories[i], v]),
          symbolSize: 12,
          itemStyle: { color: primary },
        },
      ],
    }
  }

  const seriesType = chartType === 'area' ? 'line' : chartType
  return {
    backgroundColor: background,
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 32, bottom: 48 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: muted, hideOverlap: true },
    },
    yAxis: { type: 'value', axisLabel: { color: muted } },
    textStyle: { color: text },
    series: [
      {
        type: seriesType as 'line' | 'bar',
        data: values,
        smooth: chartType === 'line' || chartType === 'area',
        areaStyle: chartType === 'area' ? { opacity: 0.18, color: primary } : undefined,
        itemStyle: { color: primary },
        lineStyle: { color: primary, width: 2 },
      },
    ],
  }
}
