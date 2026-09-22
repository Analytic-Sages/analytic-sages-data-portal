import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { buildQueryLink } from '../lib/queryLinks'
import type { StudioVisualization } from '../types'

type Props = {
  dashboardSlug: string
  existingIds: string[]
  onAdded: () => void
}

export function AddVisualizationPanel({ dashboardSlug, existingIds, onAdded }: Props) {
  const [open, setOpen] = useState(false)
  const [visualizations, setVisualizations] = useState<StudioVisualization[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api
      .listVisualizations()
      .then((res) => setVisualizations(res.visualizations))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [open])

  const available = visualizations.filter((v) => !existingIds.includes(v.id))

  async function attach(vizId: string) {
    setMsg(null)
    try {
      await api.addVizToDashboard(dashboardSlug, vizId)
      setMsg('Visualization added.')
      onAdded()
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Could not add visualization')
    }
  }

  return (
    <section className="panel">
      <div className="panel-head-row">
        <h2>Add visualization</h2>
        <button type="button" className="btn btn-ghost" onClick={() => setOpen((v) => !v)}>
          {open ? 'Close' : '+ Add visualization'}
        </button>
      </div>

      {open && (
        <>
          {loading && <p className="status-banner">Loading saved visualizations…</p>}
          {error && <p className="error">{error}</p>}
          {msg && <p className="status-banner">{msg}</p>}

          {!loading && available.length === 0 && (
            <div className="empty-state compact">
              <p>No saved visualizations available to add.</p>
              <div className="cta-row">
                <Link className="btn btn-primary" to="/query">
                  Create from Query Studio
                </Link>
                <Link className="btn btn-ghost" to="/visualizations">
                  My visualizations
                </Link>
              </div>
            </div>
          )}

          {available.length > 0 && (
            <ul className="add-viz-list">
              {available.map((viz) => (
                <li key={viz.id} className="add-viz-item">
                  <div>
                    <strong>{viz.title}</strong>
                    <span className="chip">{viz.chart_type}</span>
                  </div>
                  <div className="cta-row">
                    <button type="button" className="btn btn-primary" onClick={() => attach(viz.id)}>
                      Add to board
                    </button>
                    <Link className="btn btn-ghost" to={buildQueryLink({ viz: viz.id })}>
                      Open in Query
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="cta-row" style={{ marginTop: '1rem' }}>
            <Link className="btn btn-ghost" to="/query">
              Create new from Query Studio
            </Link>
          </div>
        </>
      )}
    </section>
  )
}
