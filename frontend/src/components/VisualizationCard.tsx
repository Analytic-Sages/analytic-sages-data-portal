import { useEffect, useState } from 'react'
import { api } from '../api'
import { ResultChart } from './ResultChart'
import type { ChartStyle, ChartType } from '../lib/chartOptions'
import type { QueryResult, StudioVisualization } from '../types'

type Props = {
  viz: StudioVisualization
  height?: number
  compact?: boolean
  theme?: Partial<ChartStyle> | null
  fetchResult?: (viz: StudioVisualization) => Promise<QueryResult>
  staticResult?: Pick<QueryResult, 'columns' | 'data'>
  onRemove?: (viz: StudioVisualization) => void
}

/** Chart card that re-runs saved SQL and renders ECharts. */
export function VisualizationCard({
  viz,
  height = 280,
  compact = false,
  theme,
  fetchResult,
  staticResult,
  onRemove,
}: Props) {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(!staticResult)
  const [rows, setRows] = useState<Array<Record<string, unknown>>>(staticResult?.data ?? [])
  const [columns, setColumns] = useState<string[]>(staticResult?.columns ?? [])

  useEffect(() => {
    if (staticResult) {
      setColumns(staticResult.columns)
      setRows(staticResult.data)
      setError(null)
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    const runner =
      fetchResult ?? ((item: StudioVisualization) => api.runQuery(item.sql))
    runner(viz)
      .then((res) => {
        if (cancelled) return
        setColumns(res.columns)
        setRows(res.data)
        setError(null)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [viz, fetchResult, staticResult])

  return (
    <article className={`viz-card ${compact ? 'viz-card-compact' : ''}`}>
      <div className="viz-card-head drag-handle">
        <h3>{viz.title}</h3>
        <div className="viz-card-actions">
          <span className="chip">{viz.chart_type}</span>
          {onRemove && (
            <button
              type="button"
              className="viz-remove-btn"
              title="Remove from dashboard"
              onMouseDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation()
                onRemove(viz)
              }}
            >
              Remove
            </button>
          )}
        </div>
      </div>
      {loading && <p className="status-banner">Refreshing chart…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <ResultChart
          config={{
            chartType: viz.chart_type as ChartType,
            xAxis: viz.x_axis || columns[0] || '',
            yAxis: viz.y_axis || columns[1] || columns[0] || '',
            style: viz.style,
            kpiLabel: viz.chart_type === 'kpi' ? viz.title : undefined,
          }}
          columns={columns}
          rows={rows}
          height={height}
          theme={theme}
        />
      )}
      {!compact && (
        <details className="viz-sql">
          <summary>SQL</summary>
          <pre>{viz.sql}</pre>
        </details>
      )}
    </article>
  )
}
