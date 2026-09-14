import { useEffect, useMemo, useRef, useState } from 'react'
import { ReactGridLayout, type LayoutItem } from 'react-grid-layout/legacy'
import { VisualizationCard } from './VisualizationCard'
import type { QueryResult, StudioLayoutItem, StudioVisualization } from '../types'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

type Props = {
  visualizations: StudioVisualization[]
  layout: StudioLayoutItem[]
  editable?: boolean
  onLayoutChange?: (layout: StudioLayoutItem[]) => void
  onRemoveChart?: (vizId: string) => void
  fetchResult?: (viz: StudioVisualization) => Promise<QueryResult>
  sampleDataById?: Record<string, Pick<QueryResult, 'columns' | 'data'>>
  theme?: Partial<import('../lib/chartOptions').ChartStyle> | null
}

function toRgl(layout: StudioLayoutItem[]): LayoutItem[] {
  return layout.map((item) => ({
    i: item.i,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
    minW: item.minW ?? 3,
    minH: item.minH ?? 4,
  }))
}

function fromRgl(layout: readonly LayoutItem[]): StudioLayoutItem[] {
  return layout.map((item) => ({
    i: item.i,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
    minW: item.minW ?? 3,
    minH: item.minH ?? 4,
  }))
}

export function DashboardGrid({
  visualizations,
  layout,
  editable = true,
  onLayoutChange,
  onRemoveChart,
  fetchResult,
  sampleDataById,
  theme,
}: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const [containerWidth, setContainerWidth] = useState(960)
  const byId = useMemo(
    () => Object.fromEntries(visualizations.map((v) => [v.id, v])),
    [visualizations],
  )
  const rglLayout = useMemo(() => toRgl(layout), [layout])

  useEffect(() => {
    const node = hostRef.current
    if (!node || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width
      if (w && w > 0) setContainerWidth(w)
    })
    ro.observe(node)
    setContainerWidth(node.getBoundingClientRect().width || 960)
    return () => ro.disconnect()
  }, [])

  return (
    <div className="dashboard-grid-layout" ref={hostRef}>
      <ReactGridLayout
        className="layout"
        layout={rglLayout}
        cols={12}
        rowHeight={36}
        width={containerWidth}
        isDraggable={editable}
        isResizable={editable}
        draggableHandle=".drag-handle"
        compactType="vertical"
        onDragStop={(next) => onLayoutChange?.(fromRgl(next))}
        onResizeStop={(next) => onLayoutChange?.(fromRgl(next))}
      >
        {layout.map((item) => {
          const viz = byId[item.i]
          if (!viz) return <div key={item.i} />
          const chartHeight = Math.max(160, item.h * 36 - 72)
          return (
            <div key={item.i} className="grid-item-shell">
              <VisualizationCard
                viz={viz}
                height={chartHeight}
                compact
                fetchResult={fetchResult}
                staticResult={sampleDataById?.[viz.id]}
                theme={theme}
                onRemove={onRemoveChart ? () => onRemoveChart(viz.id) : undefined}
              />
            </div>
          )
        })}
      </ReactGridLayout>
    </div>
  )
}
