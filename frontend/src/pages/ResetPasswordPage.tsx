import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { accessErrorMessage } from '../auth/AuthContext'

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const [password, setPassword] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const token = params.get('token') || ''

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.resetPassword(token, password)
      setDone(true)
    } catch (err) {
      setError(accessErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="shell page auth-page">
      <h1>Reset password</h1>
      {done ? (
        <>
          <p className="lede">Password updated. You can sign in now.</p>
          <Link className="btn btn-primary" to="/login">
            Sign in
          </Link>
        </>
      ) : (
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            New password
            <input
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={busy || !token}>
            Update password
          </button>
        </form>
      )}
    </main>
  )
}
