import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { AddVisualizationPanel } from '../components/AddVisualizationPanel'
import { ChartStylePicker } from '../components/ChartStylePicker'
import { DashboardGrid } from '../components/DashboardGrid'
import { DEFAULT_CHART_STYLE, type ChartStyle } from '../lib/chartOptions'
import type { StudioDashboardDetail, StudioLayoutItem } from '../types'

export function DashboardDetailPage() {
  const { slug } = useParams()
  const [payload, setPayload] = useState<StudioDashboardDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [shareMsg, setShareMsg] = useState<string | null>(null)
  const [savingLayout, setSavingLayout] = useState(false)
  const [themeDraft, setThemeDraft] = useState<ChartStyle>({
    ...DEFAULT_CHART_STYLE,
    palette: [...DEFAULT_CHART_STYLE.palette],
  })
  const [themeMsg, setThemeMsg] = useState<string | null>(null)
  const [titleDraft, setTitleDraft] = useState('')
  const [noteDraft, setNoteDraft] = useState('')
  const [detailsMsg, setDetailsMsg] = useState<string | null>(null)
  const [savingDetails, setSavingDetails] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [showTheme, setShowTheme] = useState(false)

  function refresh() {
    if (!slug) return
    api
      .studioDashboard(slug)
      .then((res) => {
        setPayload(res)
        setTitleDraft(res.dashboard.title)
        setNoteDraft(res.dashboard.description || '')
        if (res.dashboard.theme) {
          setThemeDraft({
            ...DEFAULT_CHART_STYLE,
            ...res.dashboard.theme,
            palette: res.dashboard.theme.palette?.length
              ? [...res.dashboard.theme.palette]
              : [...DEFAULT_CHART_STYLE.palette],
          })
        }
      })
      .catch((err: Error) => setError(err.message))
  }

  useEffect(() => {
    refresh()
  }, [slug])

  const onLayoutChange = useCallback(
    async (layout: StudioLayoutItem[]) => {
      if (!slug) return
      setSavingLayout(true)
      try {
        const res = await api.updateStudioDashboard(slug, { layout })
        setPayload((prev) => (prev ? { ...prev, dashboard: res.dashboard } : prev))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not save layout')
      } finally {
        setSavingLayout(false)
      }
    },
    [slug],
  )

  if (error && !payload) {
    return (
      <main className="shell page-head">
        <p className="error">{error}</p>
        <Link to="/dashboards">Back to dashboards</Link>
      </main>
    )
  }

  if (!payload) {
    return (
      <main className="shell page-head">
        <p className="status-banner">Loading dashboard…</p>
      </main>
    )
  }

  const { dashboard, visualizations } = payload
  const shareUrl =
    dashboard.share_enabled && dashboard.share_token
      ? `${window.location.origin}/share/${dashboard.share_token}`
      : null

  async function removeBoard() {
    if (!slug) return
    if (!window.confirm(`Delete dashboard “${dashboard.title}”?`)) return
    try {
      await api.deleteStudioDashboard(slug)
      window.location.href = '/dashboards'
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  async function toggleShare(enabled: boolean) {
    if (!slug) return
    try {
      const res = await api.setDashboardShare(slug, enabled)
      setPayload((prev) => (prev ? { ...prev, dashboard: res.dashboard } : prev))
      if (enabled && res.dashboard.share_token) {
        const url = `${window.location.origin}/share/${res.dashboard.share_token}`
        await navigator.clipboard.writeText(url)
        setShareMsg(`Public link copied: ${url}`)
      } else {
        setShareMsg('Sharing disabled.')
      }
    } catch (err) {
      setShareMsg(err instanceof Error ? err.message : 'Share update failed')
    }
  }

  async function copyShare() {
    if (!shareUrl) return
    await navigator.clipboard.writeText(shareUrl)
    setShareMsg('Public link copied.')
  }

  async function saveTheme() {
    if (!slug) return
    try {
      const res = await api.updateStudioDashboard(slug, { theme: themeDraft })
      setPayload((prev) => (prev ? { ...prev, dashboard: res.dashboard } : prev))
      setThemeMsg('Board theme saved.')
    } catch (err) {
      setThemeMsg(err instanceof Error ? err.message : 'Could not save theme')
    }
  }

  async function removeChart(vizId: string) {
    if (!slug) return
    const viz = visualizations.find((v) => v.id === vizId)
    if (!viz) return
    if (!window.confirm(`Remove “${viz.title}” from this dashboard?`)) return
    try {
      const newIds = dashboard.visualization_ids.filter((id) => id !== vizId)
      const newLayout = dashboard.layout.filter((item) => item.i !== vizId)
      const res = await api.updateStudioDashboard(slug, {
        visualization_ids: newIds,
        layout: newLayout,
      })
      setPayload((prev) => {
        if (!prev) return prev
        return {
          dashboard: res.dashboard,
          visualizations: prev.visualizations.filter((v) => v.id !== vizId),
        }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove chart')
    }
  }

  async function saveDetails() {
    if (!slug) return
    if (!titleDraft.trim()) {
      setDetailsMsg('Title is required.')
      return
    }
    setSavingDetails(true)
    setDetailsMsg(null)
    try {
      const res = await api.updateStudioDashboard(slug, {
        title: titleDraft.trim(),
        description: noteDraft.trim(),
      })
      setPayload((prev) => (prev ? { ...prev, dashboard: res.dashboard } : prev))
      setTitleDraft(res.dashboard.title)
      setNoteDraft(res.dashboard.description || '')
      setDetailsMsg('Saved.')
      setShowEdit(false)
    } catch (err) {
      setDetailsMsg(err instanceof Error ? err.message : 'Could not save')
    } finally {
      setSavingDetails(false)
    }
  }

  return (
    <main className="shell">
      <div className="page-head">
        <p className="breadcrumb">
          <Link to="/dashboards">← Dashboards</Link>
        </p>
        <h1>{dashboard.title}</h1>
        {dashboard.description && <p>{dashboard.description}</p>}
        <div className="meta page-actions-row">
          <span className="chip">{visualizations.length} charts</span>
          {savingLayout && <span className="chip">Saving layout…</span>}
          <button type="button" className="btn btn-ghost" onClick={() => setShowEdit((v) => !v)}>
            Edit
          </button>
          {!dashboard.share_enabled ? (
            <button type="button" className="btn btn-ghost" onClick={() => toggleShare(true)}>
              Share
            </button>
          ) : (
            <>
              <button type="button" className="btn btn-ghost" onClick={copyShare}>
                Copy link
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => toggleShare(false)}>
                Disable share
              </button>
            </>
          )}
          <button type="button" className="btn btn-ghost btn-danger-text" onClick={removeBoard}>
            Delete
          </button>
        </div>
        {shareMsg && <p className="status-banner">{shareMsg}</p>}
      </div>

      {error && <p className="error">{error}</p>}

      {showEdit && (
        <section className="panel">
          <h2>Edit dashboard</h2>
          <div className="form-stack">
            <label className="field-label">
              Title
              <input className="text-input" value={titleDraft} onChange={(e) => setTitleDraft(e.target.value)} />
            </label>
            <label className="field-label">
              Note <span className="field-hint">(optional)</span>
              <textarea
                className="note-input"
                value={noteDraft}
                onChange={(e) => setNoteDraft(e.target.value)}
                rows={3}
              />
            </label>
            <div className="cta-row">
              <button type="button" className="btn btn-primary" onClick={saveDetails} disabled={savingDetails}>
                {savingDetails ? 'Saving…' : 'Save'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowTheme((v) => !v)}>
                {showTheme ? 'Hide theme' : 'Board theme'}
              </button>
            </div>
            {detailsMsg && <p className="status-banner">{detailsMsg}</p>}
          </div>
          {showTheme && (
            <div style={{ marginTop: '1rem' }}>
              <ChartStylePicker style={themeDraft} onChange={setThemeDraft} label="Theme presets" />
              <div className="cta-row" style={{ marginTop: '0.85rem' }}>
                <button type="button" className="btn btn-primary" onClick={saveTheme}>
                  Save theme
                </button>
              </div>
              {themeMsg && <p className="status-banner">{themeMsg}</p>}
            </div>
          )}
        </section>
      )}

      <AddVisualizationPanel
        dashboardSlug={slug!}
        existingIds={dashboard.visualization_ids}
        onAdded={refresh}
      />

      {visualizations.length === 0 ? (
        <section className="panel empty-state">
          <h2>No charts yet</h2>
          <p>Add a saved visualization or create one in Query Studio.</p>
          <Link className="btn btn-primary" to="/query">
            Open Query Studio
          </Link>
        </section>
      ) : (
        <>
          <p className="muted-text layout-hint">Drag chart headers to move. Resize from corner handles.</p>
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
            editable
            onLayoutChange={onLayoutChange}
            onRemoveChart={removeChart}
            theme={dashboard.theme || themeDraft}
          />
        </>
      )}
    </main>
  )
}
