import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { api } from '../api'
import { useState } from 'react'

export function EarlyAccessPage() {
  const { user, state, logout } = useAuth()
  const [msg, setMsg] = useState<string | null>(null)

  async function resend() {
    setMsg(null)
    try {
      await api.resendVerification()
      setMsg('Verification email sent. Check your inbox (and server logs in local dev).')
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Could not resend email.')
    }
  }

  if (state === 'anonymous') {
    return (
      <main className="shell page auth-page">
        <h1>Private access</h1>
        <p className="lede">
          Query Studio requires an account. Browse the catalog and labs anytime, then sign in to run
          SQL.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" to="/signup">
            Create account
          </Link>
          <Link className="btn btn-ghost" to="/login">
            Sign in
          </Link>
        </div>
      </main>
    )
  }

  if (state === 'approved') {
    return (
      <main className="shell page auth-page">
        <h1>You have access</h1>
        <p className="lede">Your account can run queries in Query Studio.</p>
        <Link className="btn btn-primary" to="/query">
          Open Query Studio
        </Link>
      </main>
    )
  }

  return (
    <main className="shell page auth-page">
      <h1>Account pending</h1>
      <p className="lede">
        Signed in as <strong>{user?.email}</strong>. Access is limited until an admin approves your
        account (waitlist mode).
      </p>
      {!user?.email_verified && (
        <div className="callout">
          <p>Verify your email to finish setting up your account.</p>
          <button type="button" className="btn btn-ghost" onClick={() => void resend()}>
            Resend verification email
          </button>
        </div>
      )}
      {msg && <p className="muted-text">{msg}</p>}
      <div className="cta-row">
        <Link className="btn btn-ghost" to="/catalog">
          Browse catalog
        </Link>
        <button type="button" className="btn btn-ghost" onClick={() => void logout()}>
          Sign out
        </button>
      </div>
    </main>
  )
}
