import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { accessErrorMessage } from '../auth/AuthContext'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.forgotPassword(email)
      setDone(true)
    } catch (err) {
      setError(accessErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="shell page auth-page">
      <h1>Forgot password</h1>
      {done ? (
        <p className="lede">If that email exists, a reset link was sent.</p>
      ) : (
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={busy}>
            Send reset link
          </button>
        </form>
      )}
      <p className="muted-text">
        <Link to="/login">Back to sign in</Link>
      </p>
    </main>
  )
}
