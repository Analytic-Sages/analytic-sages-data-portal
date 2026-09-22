import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api'
import { accessErrorMessage, useAuth } from '../auth/AuthContext'
import { ChartStylePicker } from './ChartStylePicker'
import { EarlyAccessModal } from './EarlyAccessModal'
import { ResultChart } from './ResultChart'
import { SchemaExplorer } from './SchemaExplorer'
import {
  CHART_TYPES,
  DEFAULT_CHART_STYLE,
  guessAxes,
  type ChartStyle,
  type ChartType,
  type VizConfig,
} from '../lib/chartOptions'
import type { QueryPolicy, QueryResult, StudioDashboard } from '../types'

type SaveDestination = 'library' | 'dashboard'

type Props = {
  initialSql: string
  contextLabel?: string
  initialViz?: Partial<VizConfig>
  autoRun?: boolean
  openVisualizeTab?: boolean
  savedVizTitle?: string
}

type ResultTab = 'table' | 'visualize'

export function QueryStudio({
  initialSql,
  contextLabel,
  initialViz,
  autoRun = false,
  openVisualizeTab = false,
  savedVizTitle,
}: Props) {
  const { state: authState } = useAuth()
  const [sql, setSql] = useState(initialSql)
  const [policy, setPolicy] = useState<QueryPolicy | null>(null)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [accessCode, setAccessCode] = useState<string | null>(null)
  const [showAccessModal, setShowAccessModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<ResultTab>('table')
  const [viz, setViz] = useState<VizConfig>({
    chartType: 'bar',
    xAxis: '',
    yAxis: '',
    style: { ...DEFAULT_CHART_STYLE, palette: [...DEFAULT_CHART_STYLE.palette] },
  })
  const [saveTitle, setSaveTitle] = useState('')
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<{ title: string; boardSlug?: string; boardTitle?: string } | null>(
    null,
  )
  const [saveDestination, setSaveDestination] = useState<SaveDestination>('library')
  const [dashboards, setDashboards] = useState<StudioDashboard[]>([])
  const [selectedDashboard, setSelectedDashboard] = useState('')
  const [newDashboardTitle, setNewDashboardTitle] = useState('')
  const [newDashboardNote, setNewDashboardNote] = useState('')
  const [showSavePanel, setShowSavePanel] = useState(false)
  const [saving, setSaving] = useState(false)
  const sqlEditorRef = useRef<HTMLTextAreaElement | null>(null)
  const autoRanKey = useRef<string | null>(null)
  const pendingVisualize = useRef(openVisualizeTab)

  useEffect(() => {
    pendingVisualize.current = openVisualizeTab
  }, [openVisualizeTab])

  useEffect(() => {
    setSql(initialSql)
    setResult(null)
    setError(null)
    setTab('table')
    setSaveMsg(null)
    setSaveSuccess(null)
    setShowSavePanel(false)
    setSaveTitle(savedVizTitle ?? '')
    autoRanKey.current = null
    if (initialViz) {
      setViz({
        chartType: (initialViz.chartType as ChartType) || 'bar',
        xAxis: initialViz.xAxis || '',
        yAxis: initialViz.yAxis || '',
        style: initialViz.style
          ? { ...DEFAULT_CHART_STYLE, ...initialViz.style, palette: [...(initialViz.style.palette ?? DEFAULT_CHART_STYLE.palette)] }
          : { ...DEFAULT_CHART_STYLE, palette: [...DEFAULT_CHART_STYLE.palette] },
      })
    }
  }, [initialSql, initialViz, savedVizTitle])

  useEffect(() => {
    api.queryPolicy().then(setPolicy).catch(() => setPolicy(null))
    api
      .studioDashboards()
      .then((res) => setDashboards(res.dashboards))
      .catch(() => setDashboards([]))
  }, [])

  useEffect(() => {
    if (!result?.columns.length) return
    if (initialViz?.xAxis && initialViz?.yAxis) {
      setViz((prev) => ({
        ...prev,
        chartType: (initialViz.chartType as ChartType) || prev.chartType,
        xAxis: initialViz.xAxis || prev.xAxis,
        yAxis: initialViz.yAxis || prev.yAxis,
      }))
    } else {
      setViz(guessAxes(result.columns, result.data))
    }
    const hasChartData = Boolean(result.data.length > 0)
    if (pendingVisualize.current && hasChartData) {
      setTab('visualize')
      pendingVisualize.current = false
    } else {
      setTab('table')
    }
    if (!savedVizTitle) setSaveTitle('')
    setSaveMsg(null)
    setSaveSuccess(null)
    setShowSavePanel(false)
  }, [result, initialViz, savedVizTitle])

  const canChart = Boolean(result && result.columns.length > 0 && result.data.length > 0)
  const chartStyle = (viz.style as ChartStyle) || DEFAULT_CHART_STYLE
  const previewConfig = useMemo(() => viz, [viz])
  const canRunQueries = authState === 'approved'

  async function run() {
    if (!canRunQueries) {
      setAccessCode(authState === 'pending' ? 'WAITLIST_PENDING' : 'EARLY_ACCESS_REQUIRED')
      setShowAccessModal(true)
      return
    }
    setLoading(true)
    setError(null)
    setAccessCode(null)
    setResult(null)
    setSaveMsg(null)
    setSaveSuccess(null)
    setShowSavePanel(false)
    try {
      const res = await api.runQuery(sql)
      setResult(res)
    } catch (err) {
      if (err instanceof ApiError && err.code) {
        setAccessCode(err.code)
        if (
          err.code === 'EARLY_ACCESS_REQUIRED' ||
          err.code === 'WAITLIST_PENDING' ||
          err.code === 'EMAIL_VERIFICATION_REQUIRED' ||
          err.code === 'ACCESS_SUSPENDED'
        ) {
          setShowAccessModal(true)
        }
      }
      setError(accessErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!autoRun || !initialSql.trim() || !canRunQueries) return
    const key = `${initialSql}::${savedVizTitle ?? ''}`
    if (autoRanKey.current === key) return
    autoRanKey.current = key
    run()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per loaded context
  }, [autoRun, initialSql, savedVizTitle, canRunQueries])

  async function saveVisualization() {
    if (!result) return
    const name = saveTitle.trim() || `${viz.chartType} · ${viz.yAxis} by ${viz.xAxis}`
    if (saveDestination === 'dashboard' && !selectedDashboard && !newDashboardTitle.trim()) {
      setSaveMsg('Choose an existing dashboard or enter a name for a new one.')
      return
    }
    setSaving(true)
    setSaveMsg(null)
    setSaveSuccess(null)
    try {
      const created = await api.createVisualization({
        title: name,
        sql,
        chart_type: viz.chartType,
        x_axis: viz.xAxis || null,
        y_axis: viz.yAxis || null,
        description: contextLabel ? `Saved from ${contextLabel}` : '',
        style: chartStyle,
      })
      let boardSlug: string | undefined
      let boardTitle: string | undefined

      if (saveDestination === 'dashboard') {
        if (!selectedDashboard && newDashboardTitle.trim()) {
          const board = await api.createStudioDashboard({
            title: newDashboardTitle.trim(),
            description: newDashboardNote.trim(),
            visualization_ids: [created.visualization.id],
          })
          boardSlug = board.dashboard.slug
          boardTitle = board.dashboard.title
          setDashboards((prev) => [board.dashboard, ...prev])
          setNewDashboardTitle('')
          setNewDashboardNote('')
        } else if (selectedDashboard) {
          await api.addVizToDashboard(selectedDashboard, created.visualization.id)
          const match = dashboards.find((d) => d.slug === selectedDashboard)
          boardSlug = selectedDashboard
          boardTitle = match?.title
        }
      }

      const boards = await api.studioDashboards()
      setDashboards(boards.dashboards)
      setSaveSuccess({ title: created.visualization.title, boardSlug, boardTitle })
      setShowSavePanel(false)
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  function insertSql(value: string) {
    const editor = sqlEditorRef.current
    if (!editor) {
      setSql((current) => `${current}${current ? ' ' : ''}${value}`)
      return
    }
    const start = editor.selectionStart
    const end = editor.selectionEnd
    const before = sql.slice(0, start)
    const after = sql.slice(end)
    const prefix = before && !/\s$/.test(before) ? ' ' : ''
    const suffix = after && !/^\s/.test(after) ? ' ' : ''
    const nextSql = `${before}${prefix}${value}${suffix}${after}`
    setSql(nextSql)
    requestAnimationFrame(() => {
      const cursor = start + prefix.length + value.length + suffix.length
      editor.focus()
      editor.setSelectionRange(cursor, cursor)
    })
  }

  return (
    <div className="query-studio">
      <EarlyAccessModal
        open={showAccessModal}
        onClose={() => setShowAccessModal(false)}
        code={accessCode}
      />
      {contextLabel && (
        <p className="context-banner">
          <span className="chip available">{contextLabel}</span>
        </p>
      )}

      <div className="query-studio-workspace">
        <div className="query-studio-main">
          <label className="sql-label" htmlFor="learning-sql">
            SQL
          </label>
          <textarea
            id="learning-sql"
            className="sql-editor"
            ref={sqlEditorRef}
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            rows={16}
            spellCheck={false}
          />

          <div className="cta-row query-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={run}
              disabled={loading || policy?.enabled === false}
            >
              {loading ? 'Running…' : 'Run query'}
            </button>
            <Link className="btn btn-ghost" to="/visualizations">
              My visualizations
            </Link>
          </div>
        </div>

        <aside className="query-studio-aside" aria-label="Query information">
          <div>
            <h3>Query info</h3>
            <p>
              Run SELECT queries against curated Solana datasets. Cost and time limits protect the
              learning sandbox.
            </p>
          </div>
          {policy && (
            <div className="meta query-policy-chips">
              <span className="chip">max {policy.max_days} days</span>
              <span className="chip">
                {policy.data_window_start} → {policy.data_window_end}
              </span>
              <span className="chip">≤ {policy.max_bytes_billed_mb} MB</span>
              <span className="chip">≤ {policy.max_rows} rows</span>
              <span className="chip">{policy.enabled ? 'Sandbox on' : 'Sandbox off'}</span>
            </div>
          )}
          {!canRunQueries && authState !== 'loading' && (
            <div className="callout access-banner">
              <p>
                {authState === 'pending'
                  ? 'Your account is pending access. Draft SQL anytime; Run unlocks after approval.'
                  : 'Sign in to run queries against curated blockchain data.'}
              </p>
              <div className="cta-row">
                {authState === 'anonymous' ? (
                  <>
                    <Link className="btn btn-primary" to="/signup">
                      Create account
                    </Link>
                    <Link className="btn btn-ghost" to="/login">
                      Sign in
                    </Link>
                  </>
                ) : (
                  <Link className="btn btn-primary" to="/early-access">
                    Account status
                  </Link>
                )}
              </div>
            </div>
          )}
          <SchemaExplorer onInsert={insertSql} />
        </aside>
      </div>

      {error && (
        <div className="error-panel">
          <p className="error">Something went wrong with your query.</p>
          <p className="error-detail">{error}</p>
        </div>
      )}

      {result && (
        <section className="results-panel">
          <div className="results-meta">
            <h2>Query results</h2>
            <p className="results-summary">
              {result.row_count} row{result.row_count === 1 ? '' : 's'}
              {result.bytes_processed ? ` · scanned ${Math.round(result.bytes_processed / 1024)} KB` : ''}
            </p>
            <div className="tab-row">
              <button
                type="button"
                className={`tab-btn ${tab === 'table' ? 'active' : ''}`}
                onClick={() => setTab('table')}
              >
                Table
              </button>
              <button
                type="button"
                className={`tab-btn ${tab === 'visualize' ? 'active' : ''}`}
                onClick={() => setTab('visualize')}
                disabled={!canChart}
              >
                Visualize
              </button>
            </div>
          </div>

          {tab === 'table' && (
            <>
              {result.row_count === 0 ? (
                <div className="empty-state compact">
                  <p>No results found.</p>
                  <p className="muted-text">Try changing your filters or date range.</p>
                </div>
              ) : result.columns.length === 0 ? (
                <p className="error">No columns parsed from the result.</p>
              ) : (
                <div className="data-table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {result.columns.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.data.map((row, idx) => (
                        <tr key={idx}>
                          {result.columns.map((col) => (
                            <td key={col}>{String(row[col] ?? '')}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {tab === 'visualize' && !canChart && (
            <div className="empty-state compact">
              <p>We couldn&apos;t find a useful chart from these results.</p>
              <p className="muted-text">Choose a different field or return to the table.</p>
            </div>
          )}

          {tab === 'visualize' && canChart && (
            <div className="visualize-panel">
              <h3>Visualization</h3>
              <div className="viz-controls">
                <label>
                  Chart type
                  <select
                    value={viz.chartType}
                    onChange={(e) =>
                      setViz((v) => ({ ...v, chartType: e.target.value as ChartType }))
                    }
                  >
                    {CHART_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </label>
                {viz.chartType !== 'kpi' && (
                  <label>
                    X axis
                    <select
                      value={viz.xAxis}
                      onChange={(e) => setViz((v) => ({ ...v, xAxis: e.target.value }))}
                    >
                      {result.columns.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <label>
                  Y axis
                  <select
                    value={viz.yAxis}
                    onChange={(e) => setViz((v) => ({ ...v, yAxis: e.target.value }))}
                  >
                    {result.columns.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <ChartStylePicker
                style={chartStyle}
                onChange={(style) => setViz((v) => ({ ...v, style }))}
              />

              <div className="chart-preview-wrap">
                <ResultChart config={previewConfig} columns={result.columns} rows={result.data} />
              </div>

              {!showSavePanel && !saveSuccess && (
                <div className="cta-row" style={{ marginTop: '1rem' }}>
                  <button type="button" className="btn btn-primary" onClick={() => setShowSavePanel(true)}>
                    Save visualization
                  </button>
                </div>
              )}

              {showSavePanel && !saveSuccess && (
                <div className="save-viz panel-lite save-flow">
                  <h3>Save visualization</h3>
                  <label className="field-label">
                    Name
                    <input
                      className="text-input"
                      placeholder="Daily transfer volume"
                      value={saveTitle}
                      onChange={(e) => setSaveTitle(e.target.value)}
                    />
                  </label>

                  <fieldset className="save-destination">
                    <legend className="field-label">Destination</legend>
                    <label className="radio-label">
                      <input
                        type="radio"
                        name="save-dest"
                        checked={saveDestination === 'library'}
                        onChange={() => setSaveDestination('library')}
                      />
                      Save to my visualizations
                    </label>
                    <label className="radio-label">
                      <input
                        type="radio"
                        name="save-dest"
                        checked={saveDestination === 'dashboard'}
                        onChange={() => setSaveDestination('dashboard')}
                      />
                      Save and add to dashboard
                    </label>
                  </fieldset>

                  {saveDestination === 'dashboard' && (
                    <div className="form-stack">
                      {dashboards.length > 0 && (
                        <label className="field-label">
                          Existing dashboard
                          <select
                            value={selectedDashboard}
                            onChange={(e) => setSelectedDashboard(e.target.value)}
                          >
                      <option value="">Create new</option>
                            {dashboards.map((d) => (
                              <option key={d.id} value={d.slug}>
                                {d.title}
                              </option>
                            ))}
                          </select>
                        </label>
                      )}
                      {!selectedDashboard && (
                        <>
                          <label className="field-label">
                            New dashboard title
                            <input
                              className="text-input"
                              value={newDashboardTitle}
                              onChange={(e) => setNewDashboardTitle(e.target.value)}
                              placeholder="My Solana dashboard"
                            />
                          </label>
                          <label className="field-label">
                            Note <span className="field-hint">(optional)</span>
                            <textarea
                              className="note-input"
                              value={newDashboardNote}
                              onChange={(e) => setNewDashboardNote(e.target.value)}
                              placeholder="What this board is for…"
                              rows={2}
                            />
                          </label>
                        </>
                      )}
                    </div>
                  )}

                  <div className="cta-row" style={{ marginTop: '0.85rem' }}>
                    <button type="button" className="btn btn-primary" onClick={saveVisualization} disabled={saving}>
                      {saving ? 'Saving…' : 'Save'}
                    </button>
                    <button type="button" className="btn btn-ghost" onClick={() => setShowSavePanel(false)}>
                      Cancel
                    </button>
                  </div>
                  {saveMsg && <p className="error">{saveMsg}</p>}
                </div>
              )}

              {saveSuccess && (
                <div className="save-success panel-lite">
                  <p>
                    <strong>Visualization saved.</strong> “{saveSuccess.title}”
                  </p>
                  {saveSuccess.boardSlug ? (
                    <p>
                      Added to <strong>{saveSuccess.boardTitle ?? saveSuccess.boardSlug}</strong>.
                    </p>
                  ) : null}
                  <div className="cta-row">
                    {saveSuccess.boardSlug ? (
                      <Link className="btn btn-primary" to={`/dashboards/${saveSuccess.boardSlug}`}>
                        View dashboard
                      </Link>
                    ) : (
                      <Link className="btn btn-primary" to="/visualizations">
                        My visualizations
                      </Link>
                    )}
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => {
                        setSaveSuccess(null)
                        setShowSavePanel(false)
                      }}
                    >
                      Continue editing
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
