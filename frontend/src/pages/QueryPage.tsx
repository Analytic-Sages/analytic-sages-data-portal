import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { QueryStudio } from '../components/QueryStudio'
import { parseQuerySearch } from '../lib/queryLinks'
import type { VizConfig } from '../lib/chartOptions'

const DEFAULT_SQL = `SELECT
  mint,
  SUM(transfer_count) AS transfers,
  SUM(total_volume) AS volume
FROM solana_curated.token_activity
WHERE block_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND CURRENT_DATE()
GROUP BY mint
ORDER BY volume DESC
LIMIT 10`

export function QueryPage() {
  const [searchParams] = useSearchParams()
  const params = parseQuerySearch(searchParams.toString())
  const [initialSql, setInitialSql] = useState(DEFAULT_SQL)
  const [contextLabel, setContextLabel] = useState<string | undefined>()
  const [initialViz, setInitialViz] = useState<Partial<VizConfig> | undefined>()
  const [savedVizTitle, setSavedVizTitle] = useState<string | undefined>()
  const [autoRun, setAutoRun] = useState(false)
  const [openVisualizeTab, setOpenVisualizeTab] = useState(false)
  const [loading, setLoading] = useState(Boolean(params.dataset || params.lab || params.viz))

  useEffect(() => {
    let cancelled = false

    async function loadContext() {
      setLoading(true)
      setInitialViz(undefined)
      setSavedVizTitle(undefined)
      setAutoRun(false)
      setOpenVisualizeTab(false)
      try {
        if (params.viz) {
          const res = await api.getVisualization(params.viz)
          const viz = res.visualization
          if (!cancelled) {
            setInitialSql(viz.sql)
            setContextLabel(`Saved visualization · ${viz.title}`)
            setSavedVizTitle(viz.title)
            setInitialViz({
              chartType: viz.chart_type as VizConfig['chartType'],
              xAxis: viz.x_axis ?? '',
              yAxis: viz.y_axis ?? '',
              style: viz.style,
            })
            setAutoRun(true)
            setOpenVisualizeTab(true)
          }
          return
        }

        if (params.lab) {
          const lab = await api.lab(params.lab)
          if (!cancelled) {
            setInitialSql(lab.starter_sql)
            setContextLabel(`Lab ${String(lab.number).padStart(2, '0')} · ${lab.title}`)
          }
          return
        }

        if (params.dataset) {
          const dataset = await api.dataset(params.dataset)
          const sql =
            params.sql ||
            dataset.sql_examples[0]?.sql ||
            `SELECT * FROM ${dataset.curated_table} LIMIT 10`
          if (!cancelled) {
            setInitialSql(sql)
            setContextLabel(`Dataset · ${dataset.name}`)
          }
          return
        }

        if (params.sql) {
          if (!cancelled) {
            setInitialSql(params.sql)
            setContextLabel(undefined)
          }
          return
        }

        if (!cancelled) {
          setInitialSql(DEFAULT_SQL)
          setContextLabel(undefined)
        }
      } catch {
        if (!cancelled) {
          setInitialSql(params.sql || DEFAULT_SQL)
          setContextLabel(undefined)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadContext()
    return () => {
      cancelled = true
    }
  }, [searchParams.toString()])

  return (
    <main className="shell">
      <div className="page-head">
        <h1>Query Studio</h1>
        <p>Write SQL against curated blockchain data.</p>
        <div className="cta-row page-actions">
          <Link className="btn btn-ghost" to="/dashboards">
            Dashboards
          </Link>
        </div>
      </div>

      {loading ? (
        <p className="status-banner">Loading query context…</p>
      ) : (
        <QueryStudio
          initialSql={initialSql}
          contextLabel={contextLabel}
          initialViz={initialViz}
          autoRun={autoRun}
          openVisualizeTab={openVisualizeTab}
          savedVizTitle={savedVizTitle}
        />
      )}
    </main>
  )
}
