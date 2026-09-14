import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { useAuth } from '../auth/AuthContext'
import type { AdminAnalyticsSummary, AdminInvite, AuthUser } from '../types/auth'

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
  const { user, loading: authLoading, logout } = useAuth()
  const [summary, setSummary] = useState<AdminAnalyticsSummary | null>(null)
  const [users, setUsers] = useState<AuthUser[]>([])
  const [invites, setInvites] = useState<AdminInvite[]>([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteNote, setInviteNote] = useState('')
  const [lastInviteUrl, setLastInviteUrl] = useState<string | null>(null)
  const [inviteMessage, setInviteMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const isAdmin = Boolean(user?.is_admin)

  const load = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const [analytics, userRes, inviteRes] = await Promise.all([
        api.adminAnalytics(30),
        api.adminUsers({
          access_status: statusFilter || undefined,
          q: search.trim() || undefined,
        }),
        api.adminInvites(),
      ])
      setSummary(analytics)
      setUsers(userRes.users)
      setInvites(inviteRes.invites)
    } catch (err) {
      setSummary(null)
      setUsers([])
      setInvites([])
      setError(err instanceof ApiError ? err.message : 'Could not load admin data')
    } finally {
      setBusy(false)
    }
  }, [search, statusFilter])

  useEffect(() => {
    if (isAdmin) void load()
  }, [isAdmin, load])

  async function approve(id: string) {
    await api.adminApproveUser(id)
    await load()
  }

  async function suspend(id: string) {
    await api.adminSuspendUser(id)
    await load()
  }

  async function onInvite(e: FormEvent) {
    e.preventDefault()
    if (!inviteEmail.trim()) return
    setBusy(true)
    setInviteMessage(null)
    setLastInviteUrl(null)
    setError(null)
    try {
      const res = await api.adminCreateInvite({
        email: inviteEmail.trim(),
        note: inviteNote.trim() || undefined,
      })
      setInviteEmail('')
      setInviteNote('')
      setLastInviteUrl(res.invite_url)
      setInviteMessage(
        res.existing_user_approved
          ? `Approved existing account for ${res.invite.email}.`
          : `Invite created for ${res.invite.email}. Share the link below (also logged by the API emailer).`,
      )
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create invite')
    } finally {
      setBusy(false)
    }
  }

  async function revokeInvite(id: string) {
    await api.adminRevokeInvite(id)
    await load()
  }

  async function resendInvite(id: string) {
    setBusy(true)
    setError(null)
    try {
      const res = await api.adminResendInvite(id)
      setLastInviteUrl(res.invite_url)
      setInviteMessage(
        res.existing_user_approved
          ? 'User already had an account — access granted.'
          : 'Fresh invite sent. Copy the link below if email delivery is log-only.',
      )
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not resend invite')
    } finally {
      setBusy(false)
    }
  }

  const signupSlice = useMemo(() => summary?.users.signups_by_day.slice(-14) ?? [], [summary])
  const querySlice = useMemo(() => summary?.queries.by_day.slice(-14) ?? [], [summary])

  if (authLoading) {
    return (
      <main className="shell page auth-page">
        <h1>Admin dashboard</h1>
        <p className="lede">Checking your session…</p>
      </main>
    )
  }

  if (!user) {
    return <Navigate to="/login?next=/admin" replace />
  }

  if (!isAdmin) {
    return (
      <main className="shell page auth-page">
        <h1>Admin dashboard</h1>
        <p className="lede">
          Signed in as <strong>{user.email}</strong>, but this account is not an admin.
        </p>
        <p className="muted-text">
          Ask an operator to add your email to <code>ADMIN_EMAILS</code> on the API, then sign in again.
        </p>
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
        <p>
          Signed in as {user.email}. User growth, query usage, and access management for the Data
          Portal.
        </p>
        <div className="cta-row page-actions">
          <button type="button" className="btn btn-ghost" onClick={() => void load()} disabled={busy}>
            Refresh
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              void logout()
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="panel">
        <div className="panel-head-row">
          <h2>Invite testers</h2>
        </div>
        <p className="muted-text">
          Add an email to grant Query Studio access. If they already signed up, they are approved
          immediately. Otherwise they get a signup invite link.
        </p>
        <form className="admin-invite-form" onSubmit={(e) => void onInvite(e)}>
          <label>
            Email
            <input
              type="email"
              className="text-input"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="tester@example.com"
              required
            />
          </label>
          <label>
            Note (optional)
            <input
              className="text-input"
              value={inviteNote}
              onChange={(e) => setInviteNote(e.target.value)}
              placeholder="Cohort, reason…"
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Sending…' : 'Send invite'}
          </button>
        </form>
        {inviteMessage && <p className="success-text">{inviteMessage}</p>}
        {lastInviteUrl && (
          <p className="admin-invite-url">
            <span className="muted-text">Invite link:</span>{' '}
            <a href={lastInviteUrl}>{lastInviteUrl}</a>
          </p>
        )}
        <div className="data-table-wrap" style={{ marginTop: '1rem' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Status</th>
                <th>Note</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invites.map((inv) => (
                <tr key={inv.id}>
                  <td>{inv.email}</td>
                  <td>
                    <span className="chip">{inv.status}</span>
                  </td>
                  <td>{inv.note || '—'}</td>
                  <td>{inv.expires_at ? new Date(inv.expires_at).toLocaleDateString() : '—'}</td>
                  <td>
                    <div className="cta-row">
                      {inv.status === 'PENDING' && (
                        <>
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => void resendInvite(inv.id)}
                          >
                            Resend
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-danger-text"
                            onClick={() => void revokeInvite(inv.id)}
                          >
                            Revoke
                          </button>
                        </>
                      )}
                      {inv.status !== 'PENDING' && <span className="muted-text">—</span>}
                    </div>
                  </td>
                </tr>
              ))}
              {invites.length === 0 && (
                <tr>
                  <td colSpan={5}>No invites yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

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
            <button type="button" className="btn btn-ghost" onClick={() => void load()}>
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
                        <button
                          type="button"
                          className="btn btn-ghost btn-danger-text"
                          onClick={() => void suspend(u.id)}
                        >
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
