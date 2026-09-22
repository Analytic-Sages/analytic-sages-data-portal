import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

type Props = {
  open: boolean
  onClose: () => void
  code?: string | null
}

export function EarlyAccessModal({ open, onClose, code }: Props) {
  const { user, state } = useAuth()
  if (!open) return null

  const pending = state === 'pending' || code === 'WAITLIST_PENDING'
  const needsVerify = code === 'EMAIL_VERIFICATION_REQUIRED' || (user && !user.email_verified)

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal-panel early-access-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="early-access-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="early-access-title">
          {needsVerify ? 'Verify your email' : pending ? 'Account pending' : 'Sign in required'}
        </h2>
        <p>
          {needsVerify
            ? 'Check your inbox for a verification link before using Query Studio.'
            : pending
              ? 'Your account is pending access. You can browse the catalog and labs while you wait.'
              : 'Create an account or sign in to run SQL against curated blockchain datasets.'}
        </p>
        <div className="cta-row">
          {!user && (
            <>
              <Link className="btn btn-primary" to="/signup" onClick={onClose}>
                Create account
              </Link>
              <Link className="btn btn-ghost" to="/login" onClick={onClose}>
                Sign in
              </Link>
            </>
          )}
          {user && pending && (
            <Link className="btn btn-primary" to="/early-access" onClick={onClose}>
              Account status
            </Link>
          )}
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
