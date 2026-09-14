import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { StudioDashboard } from '../types'

function formatUpdated(iso: string) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return 'Updated today'
    if (diffDays === 1) return 'Updated yesterday'
    return `Updated ${d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`
  } catch {
    return ''
  }
}

export function DashboardsPage() {
  const [boards, setBoards] = useState<StudioDashboard[]>([])
  const [error, setError] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [boardNote, setBoardNote] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  function refresh() {
    api
      .studioDashboards()
      .then((res) => setBoards(res.dashboards))
      .catch((err: Error) => setError(err.message))
  }

  useEffect(() => {
    refresh()
  }, [])

  async function createBoard() {
    if (!title.trim()) return
    try {
      await api.createStudioDashboard({
        title: title.trim(),
        description: boardNote.trim(),
      })
      setTitle('')
      setBoardNote('')
      setShowCreate(false)
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create dashboard')
    }
  }

  return (
    <main className="shell">
      <div className="page-head">
        <h1>Dashboards</h1>
        <p>Build and organize your blockchain analysis.</p>
        <div className="cta-row page-actions">
          <button type="button" className="btn btn-primary" onClick={() => setShowCreate((v) => !v)}>
            + New dashboard
          </button>
          <Link className="btn btn-ghost" to="/visualizations">
            My visualizations
          </Link>
          <Link className="btn btn-ghost" to="/query">
            Query Studio
          </Link>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {showCreate && (
        <section className="panel">
          <h2>New dashboard</h2>
          <div className="form-stack">
            <label className="field-label">
              Title
              <input
                className="text-input"
                placeholder="My Solana dashboard"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label className="field-label">
              Note <span className="field-hint">(optional)</span>
              <textarea
                className="note-input"
                placeholder="What this board tracks…"
                value={boardNote}
                onChange={(e) => setBoardNote(e.target.value)}
                rows={3}
              />
            </label>
            <div className="cta-row">
              <button type="button" className="btn btn-primary" onClick={createBoard}>
                Create dashboard
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
            </div>
          </div>
        </section>
      )}

      {boards.length === 0 && !error && !showCreate && (
        <section className="panel empty-state">
          <h2>No dashboards yet</h2>
          <p>Save visualizations to a dashboard to start building your analytics workspace.</p>
          <button type="button" className="btn btn-primary" onClick={() => setShowCreate(true)}>
            Create dashboard
          </button>
        </section>
      )}

      <div className="dashboard-grid">
        {boards.map((board) => (
          <article key={board.id} className="dashboard-card">
            <div className="meta">
              <span className="chip">{board.visualization_ids.length} visualization{board.visualization_ids.length === 1 ? '' : 's'}</span>
              {board.share_enabled && <span className="chip available">Public</span>}
              {board.updated_at && <span className="chip">{formatUpdated(board.updated_at)}</span>}
            </div>
            <h3>{board.title}</h3>
            {board.description ? (
              <p>{board.description}</p>
            ) : (
              <p className="muted-text">No note yet.</p>
            )}
            <Link className="btn btn-primary" to={`/dashboards/${board.slug}`}>
              Open dashboard →
            </Link>
          </article>
        ))}
      </div>
    </main>
  )
}
