import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { buildQueryLink } from '../lib/queryLinks'
import type { StudioDashboard, StudioVisualization } from '../types'

function formatDate(iso: string) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

export function VisualizationsPage() {
  const [visualizations, setVisualizations] = useState<StudioVisualization[]>([])
  const [dashboards, setDashboards] = useState<StudioDashboard[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [addTarget, setAddTarget] = useState<Record<string, string>>({})
  const [actionMsg, setActionMsg] = useState<string | null>(null)

  const boardsByViz = useMemo(() => {
    const map: Record<string, StudioDashboard[]> = {}
    for (const board of dashboards) {
      for (const id of board.visualization_ids) {
        map[id] = [...(map[id] ?? []), board]
      }
    }
    return map
  }, [dashboards])

  function refresh() {
    setLoading(true)
    Promise.all([api.listVisualizations(), api.studioDashboards()])
      .then(([vizRes, boardRes]) => {
        setVisualizations(vizRes.visualizations)
        setDashboards(boardRes.dashboards)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
  }, [])

  async function addToBoard(vizId: string) {
    const slug = addTarget[vizId]
    if (!slug) return
    try {
      await api.addVizToDashboard(slug, vizId)
      const boards = await api.studioDashboards()
      setDashboards(boards.dashboards)
      setActionMsg('Visualization added to dashboard.')
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : 'Could not add to dashboard')
    }
  }

  async function removeViz(viz: StudioVisualization) {
    if (!window.confirm(`Delete visualization “${viz.title}”?`)) return
    try {
      await api.deleteVisualization(viz.id)
      refresh()
      setActionMsg('Visualization deleted.')
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  return (
    <main className="shell">
      <div className="page-head">
        <p className="breadcrumb">
          <Link to="/query">Query</Link> / My visualizations
        </p>
        <h1>My visualizations</h1>
        <p>Saved charts from Query Studio. Open one to edit, or add it to a dashboard.</p>
        <div className="cta-row page-actions">
          <Link className="btn btn-primary" to="/query">
            + New visualization
          </Link>
          <Link className="btn btn-ghost" to="/dashboards">
            Dashboards
          </Link>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {actionMsg && <p className="status-banner">{actionMsg}</p>}

      {loading && <p className="status-banner">Loading visualizations…</p>}

      {!loading && visualizations.length === 0 && !error && (
        <section className="panel empty-state">
          <h2>No saved visualizations yet</h2>
          <p>Run a query and turn your results into a chart.</p>
          <Link className="btn btn-primary" to="/query">
            Open Query Studio
          </Link>
        </section>
      )}

      {!loading && visualizations.length > 0 && (
        <div className="viz-library-list">
          {visualizations.map((viz) => {
            const onBoards = boardsByViz[viz.id] ?? []
            return (
              <article key={viz.id} className="viz-library-item panel">
                <div className="viz-library-main">
                  <h3>{viz.title}</h3>
                  <div className="meta">
                    <span className="chip">{viz.chart_type}</span>
                    {viz.x_axis && viz.y_axis && (
                      <span className="chip">
                        {viz.y_axis} by {viz.x_axis}
                      </span>
                    )}
                    {viz.created_at && <span className="chip">Saved {formatDate(viz.created_at)}</span>}
                  </div>
                  {onBoards.length > 0 ? (
                    <p className="viz-library-boards">
                      On:{' '}
                      {onBoards.map((b, i) => (
                        <span key={b.id}>
                          {i > 0 && ', '}
                          <Link to={`/dashboards/${b.slug}`}>{b.title}</Link>
                        </span>
                      ))}
                    </p>
                  ) : (
                    <p className="muted-text">Not on any dashboard yet.</p>
                  )}
                </div>
                <div className="viz-library-actions">
                  <Link className="btn btn-primary" to={buildQueryLink({ viz: viz.id })}>
                    Open
                  </Link>
                  {dashboards.length > 0 && (
                    <div className="viz-add-row">
                      <select
                        value={addTarget[viz.id] ?? ''}
                        onChange={(e) => setAddTarget((prev) => ({ ...prev, [viz.id]: e.target.value }))}
                      >
                        <option value="">Add to dashboard…</option>
                        {dashboards.map((d) => (
                          <option key={d.id} value={d.slug}>
                            {d.title}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        disabled={!addTarget[viz.id]}
                        onClick={() => addToBoard(viz.id)}
                      >
                        Add
                      </button>
                    </div>
                  )}
                  <button type="button" className="btn btn-ghost btn-danger-text" onClick={() => removeViz(viz)}>
                    Delete
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </main>
  )
}
