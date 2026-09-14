import { useEffect, useRef } from 'react'
import ReactECharts from 'echarts-for-react'
import { buildChartOption, type ChartStyle, type VizConfig } from '../lib/chartOptions'

type Props = {
  config: VizConfig
  columns: string[]
  rows: Array<Record<string, unknown>>
  height?: number
  theme?: Partial<ChartStyle> | null
}

export function ResultChart({ config, columns, rows, height = 360, theme }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const chartRef = useRef<ReactECharts | null>(null)
  const option = buildChartOption(config, columns, rows, theme)
  const bg = (theme?.background || config.style?.background || '#FFFFFF') as string

  useEffect(() => {
    const node = hostRef.current
    if (!node || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(() => {
      chartRef.current?.getEchartsInstance()?.resize()
    })
    ro.observe(node)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    chartRef.current?.getEchartsInstance()?.resize()
  }, [height, columns, rows, config])

  return (
    <div className="result-chart" ref={hostRef} style={{ background: bg }}>
      <ReactECharts
        ref={chartRef}
        option={option}
        style={{ height, width: '100%' }}
        notMerge
        lazyUpdate
      />
    </div>
  )
}
