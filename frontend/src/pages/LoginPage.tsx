import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { accessErrorMessage, useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { login, state } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (state === 'approved') {
    const next = params.get('next') || '/query'
    return <Navigate to={next} replace />
  }
  if (state === 'pending') {
    return <Navigate to="/early-access" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const user = await login(email, password)
      const next = params.get('next')
      if (user.is_admin && next) {
        navigate(next)
      } else if (user.can_run_queries) {
        navigate(next || '/query')
      } else {
        navigate('/early-access')
      }
    } catch (err) {
      setError(accessErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="shell page auth-page">
      <h1>Sign in</h1>
      <p className="lede">Access Query Studio with your account.</p>
      <form className="auth-form" onSubmit={onSubmit}>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="muted-text">
        No account yet? <Link to="/signup">Create account</Link>
        {' · '}
        <Link to="/forgot-password">Forgot password</Link>
      </p>
    </main>
  )
}
