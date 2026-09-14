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
          {needsVerify
            ? 'Verify your email'
            : pending
              ? 'You are on the waitlist'
              : 'Early access required'}
        </h2>
        <p>
          {needsVerify
            ? 'Check your inbox for a verification link. Query Studio unlocks after email verification and approval.'
            : pending
              ? 'Thanks for joining. We are approving early-access accounts in waves. You can browse the catalog and labs while you wait.'
              : 'Query Studio is limited to approved early-access users. Request access to run SQL against curated blockchain datasets.'}
        </p>
        <div className="cta-row">
          {!user && (
            <>
              <Link className="btn btn-primary" to="/signup" onClick={onClose}>
                Request early access
              </Link>
              <Link className="btn btn-ghost" to="/login" onClick={onClose}>
                Sign in
              </Link>
            </>
          )}
          {user && pending && (
            <Link className="btn btn-primary" to="/early-access" onClick={onClose}>
              View waitlist status
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
