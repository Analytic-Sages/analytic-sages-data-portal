import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { BrandLockup } from '../components/BrandLockup'
import { DashboardGrid } from '../components/DashboardGrid'
import type { StudioDashboardDetail } from '../types'

export function PublicSharePage() {
  const { token } = useParams()
  const [payload, setPayload] = useState<StudioDashboardDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    api
      .publicDashboard(token)
      .then(setPayload)
      .catch((err: Error) => setError(err.message))
  }, [token])

  const fetchResult = useCallback(
    async (viz: { id: string }) => {
      if (!token) throw new Error('Share not loaded')
      return api.publicRunViz(token, viz.id)
    },
    [token],
  )

  if (error) {
    return (
      <main className="shell page-head">
        <BrandLockup size="sm" />
        <p className="error">{error}</p>
        <p className="status-banner">This share link may be disabled or invalid.</p>
        <Link to="/">Go to Analytic Sages</Link>
      </main>
    )
  }

  if (!payload) {
    return (
      <main className="shell page-head">
        <p className="status-banner">Loading shared dashboard…</p>
      </main>
    )
  }

  const { dashboard, visualizations } = payload

  return (
    <main className="shell">
      <div className="page-head">
        <BrandLockup size="sm" />
        <p className="status-banner">Public shared dashboard · read only</p>
        <h1>{dashboard.title}</h1>
        {dashboard.description ? (
          <p>{dashboard.description}</p>
        ) : (
          <p className="muted-text">Shared from Analytic Sages Data Portal.</p>
        )}
        <div className="meta">
          <span className="chip available">{visualizations.length} charts</span>
          <Link className="chip" to="/query">
            Build your own in Query studio
          </Link>
        </div>
      </div>

      {visualizations.length === 0 ? (
        <p className="status-banner">This board has no charts yet.</p>
      ) : (
        <DashboardGrid
          visualizations={visualizations}
          layout={
            dashboard.layout?.length
              ? dashboard.layout
              : visualizations.map((v, idx) => ({
                  i: v.id,
                  x: (idx % 2) * 6,
                  y: Math.floor(idx / 2) * 8,
                  w: 6,
                  h: 8,
                }))
          }
          editable={false}
          fetchResult={fetchResult}
          theme={dashboard.theme}
        />
      )}
    </main>
  )
}
