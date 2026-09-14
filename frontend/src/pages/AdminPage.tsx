import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api'
import type { AdminAnalyticsSummary, AuthUser } from '../types/auth'

const ADMIN_KEY_STORAGE = 'as_admin_api_key'

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(2)} MB`
}

function MiniBars({
  points,
  valueKey,
}: {
  points: Array<Record<string, string | number>>
  valueKey: string
}) {
  const max = Math.max(1, ...points.map((p) => Number(p[valueKey] || 0)))
  return (
    <div className="admin-bars" role="img" aria-label="Trend chart">
      {points.map((p) => {
        const v = Number(p[valueKey] || 0)
        const h = Math.max(2, Math.round((v / max) * 100))
        return (
          <div key={String(p.day)} className="admin-bar-col" title={`${p.day}: ${v}`}>
            <div className="admin-bar" style={{ height: `${h}%` }} />
          </div>
        )
      })}
    </div>
  )
}

export function AdminPage() {
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem(ADMIN_KEY_STORAGE) || '')
  const [keyInput, setKeyInput] = useState('')
  const [unlocked, setUnlocked] = useState(Boolean(sessionStorage.getItem(ADMIN_KEY_STORAGE)))
  const [summary, setSummary] = useState<AdminAnalyticsSummary | null>(null)
  const [users, setUsers] = useState<AuthUser[]>([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(
    async (key: string) => {
      setBusy(true)
      setError(null)
      try {
        const [analytics, userRes] = await Promise.all([
          api.adminAnalytics(key, 30),
          api.adminUsers(key, {
            access_status: statusFilter || undefined,
            q: search.trim() || undefined,
          }),
        ])
        setSummary(analytics)
        setUsers(userRes.users)
        setUnlocked(true)
        sessionStorage.setItem(ADMIN_KEY_STORAGE, key)
        setAdminKey(key)
      } catch (err) {
        setUnlocked(false)
        sessionStorage.removeItem(ADMIN_KEY_STORAGE)
        setSummary(null)
        setUsers([])
        setError(err instanceof ApiError ? err.message : 'Could not load admin data')
      } finally {
        setBusy(false)
      }
    },
    [search, statusFilter],
  )

  useEffect(() => {
    if (adminKey && unlocked) void load(adminKey)
  }, [adminKey, unlocked, load])

  async function onUnlock(e: FormEvent) {
    e.preventDefault()
    await load(keyInput.trim())
  }

  async function approve(id: string) {
    if (!adminKey) return
    await api.adminApproveUser(adminKey, id)
    await load(adminKey)
  }

  async function suspend(id: string) {
    if (!adminKey) return
    await api.adminSuspendUser(adminKey, id)
    await load(adminKey)
  }

  const signupSlice = useMemo(() => summary?.users.signups_by_day.slice(-14) ?? [], [summary])
  const querySlice = useMemo(() => summary?.queries.by_day.slice(-14) ?? [], [summary])

  if (!unlocked) {
    return (
      <main className="shell page auth-page">
        <h1>Admin dashboard</h1>
        <p className="lede">Enter the server ADMIN_API_KEY to view portal analytics and manage users.</p>
        <form className="auth-form" onSubmit={onUnlock}>
          <label>
            Admin API key
            <input
              type="password"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              autoComplete="off"
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Checking…' : 'Unlock admin'}
          </button>
        </form>
        <p className="muted-text">
          <Link to="/">Back to portal</Link>
        </p>
      </main>
    )
  }

  return (
    <main className="shell page admin-page">
      <div className="page-head">
        <p className="breadcrumb">
          <Link to="/">Home</Link> / Admin
        </p>
        <h1>Admin dashboard</h1>
        <p>User growth, query usage, and access management for the Data Portal.</p>
        <div className="cta-row page-actions">
          <button type="button" className="btn btn-ghost" onClick={() => void load(adminKey)} disabled={busy}>
            Refresh
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              sessionStorage.removeItem(ADMIN_KEY_STORAGE)
              setUnlocked(false)
              setAdminKey('')
              setSummary(null)
            }}
          >
            Lock admin
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {summary && (
        <>
          <section className="admin-kpi-grid">
            <article className="admin-kpi">
              <span className="admin-kpi-label">Users</span>
              <strong>{summary.users.total}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Approved</span>
              <strong>{summary.users.approved}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Pending</span>
              <strong>{summary.users.waitlist_pending}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Queries (30d)</span>
              <strong>{summary.queries.total}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Active queriers</span>
              <strong>{summary.queries.active_users}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Bytes billed (30d)</span>
              <strong>{formatBytes(summary.queries.bytes_billed_total)}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Data mode</span>
              <strong>{summary.mode}</strong>
            </article>
            <article className="admin-kpi">
              <span className="admin-kpi-label">Failed queries</span>
              <strong>{summary.queries.failed}</strong>
            </article>
          </section>

          <section className="admin-charts">
            <article className="admin-chart-card">
              <h2>Signups (14 days)</h2>
              <MiniBars points={signupSlice} valueKey="count" />
            </article>
            <article className="admin-chart-card">
              <h2>Queries (14 days)</h2>
              <MiniBars points={querySlice} valueKey="count" />
            </article>
          </section>

          <section className="panel">
            <h2>Users by country</h2>
            <div className="admin-country-list">
              {summary.users.by_country.length === 0 && <p className="muted-text">No country data yet.</p>}
              {summary.users.by_country.map((row) => (
                <div key={row.country} className="admin-country-row">
                  <span>{row.country}</span>
                  <strong>{row.count}</strong>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      <section className="panel">
        <div className="panel-head-row">
          <h2>Users</h2>
          <div className="admin-filters">
            <input
              className="text-input"
              placeholder="Search email, name, phone…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All statuses</option>
              <option value="APPROVED">Approved</option>
              <option value="WAITLIST_PENDING">Pending</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
            <button type="button" className="btn btn-ghost" onClick={() => void load(adminKey)}>
              Apply
            </button>
          </div>
        </div>
        <div className="data-table-wrap">
          <table className="data-table admin-users-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Phone</th>
                <th>Country</th>
                <th>Status</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className="admin-user-cell">
                      <strong>
                        {u.first_name} {u.last_name}
                      </strong>
                      <span>{u.email}</span>
                    </div>
                  </td>
                  <td>
                    {u.phone_country_code} {u.phone_number}
                  </td>
                  <td>{u.country_of_residence || '—'}</td>
                  <td>
                    <span className="chip">{u.access_status}</span>
                  </td>
                  <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                  <td>
                    <div className="cta-row">
                      {u.access_status !== 'APPROVED' && (
                        <button type="button" className="btn btn-primary" onClick={() => void approve(u.id)}>
                          Approve
                        </button>
                      )}
                      {u.access_status !== 'SUSPENDED' && (
                        <button type="button" className="btn btn-ghost btn-danger-text" onClick={() => void suspend(u.id)}>
                          Suspend
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6}>No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {summary && summary.queries.recent.length > 0 && (
        <section className="panel">
          <h2>Recent queries</h2>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Result</th>
                  <th>Mode</th>
                  <th>Bytes</th>
                  <th>SQL</th>
                </tr>
              </thead>
              <tbody>
                {summary.queries.recent.map((ev) => (
                  <tr key={ev.id}>
                    <td>{ev.created_at ? new Date(ev.created_at).toLocaleString() : '—'}</td>
                    <td>{ev.success ? 'OK' : ev.error_code || 'Failed'}</td>
                    <td>{ev.mode}</td>
                    <td>{formatBytes(ev.bytes_billed)}</td>
                    <td className="admin-sql-cell">{ev.sql_preview}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  )
}
