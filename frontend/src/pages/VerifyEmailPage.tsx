import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { accessErrorMessage, useAuth } from '../auth/AuthContext'

export function VerifyEmailPage() {
  const { verifyEmail } = useAuth()
  const [params] = useSearchParams()
  const [status, setStatus] = useState<'working' | 'ok' | 'error'>('working')
  const [message, setMessage] = useState('Verifying your email…')

  useEffect(() => {
    const token = params.get('token')
    if (!token) {
      setStatus('error')
      setMessage('Missing verification token.')
      return
    }
    void verifyEmail(token)
      .then((user) => {
        setStatus('ok')
        setMessage(
          user.can_run_queries
            ? 'Email verified. You can open Query Studio.'
            : 'Email verified. You are on the early-access waitlist.',
        )
      })
      .catch((err) => {
        setStatus('error')
        setMessage(accessErrorMessage(err))
      })
  }, [params, verifyEmail])

  return (
    <main className="shell page auth-page">
      <h1>Email verification</h1>
      <p className={status === 'error' ? 'error' : 'lede'}>{message}</p>
      {status === 'ok' && (
        <div className="cta-row">
          <Link className="btn btn-primary" to="/query">
            Open Query Studio
          </Link>
          <Link className="btn btn-ghost" to="/early-access">
            Waitlist status
          </Link>
        </div>
      )}
    </main>
  )
}
