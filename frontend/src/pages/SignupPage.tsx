import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { accessErrorMessage, useAuth } from '../auth/AuthContext'
import { COUNTRIES } from '../data/countries'
import { PasswordField } from '../components/PasswordField'
import { api } from '../api'

export function SignupPage() {
  const { signup, state } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const inviteToken = params.get('invite')?.trim() || ''
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [residence, setResidence] = useState('NG')
  const [dialCode, setDialCode] = useState('+234')
  const [phone, setPhone] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [inviteOnlyMode, setInviteOnlyMode] = useState(true)
  const [inviteHint, setInviteHint] = useState('An active invite link is required to create an account.')

  const residenceCountry = useMemo(
    () => COUNTRIES.find((c) => c.code === residence) ?? COUNTRIES[0],
    [residence],
  )

  useEffect(() => {
    let cancelled = false
    void api.authConfig().then((config) => {
      if (!cancelled) {
        setInviteOnlyMode(config.invite_only_mode)
        if (!inviteToken && !config.invite_only_mode) {
          setInviteHint('Create an account to access Query Studio.')
        }
      }
    }).catch(() => {})
    return () => {
      cancelled = true
    }
  }, [inviteToken])

  useEffect(() => {
    if (!inviteToken) return
    let cancelled = false
    void (async () => {
      try {
        const invite = await api.peekInvite(inviteToken)
        if (!cancelled) {
          setEmail(invite.email)
          setInviteHint(`Invite verified for ${invite.email}.`)
        }
      } catch {
        if (!cancelled) setInviteHint('This invite link is invalid or expired. Request a new invite link.')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [inviteToken])

  if (state === 'approved') {
    return <Navigate to="/query" replace />
  }

  function onResidenceChange(code: string) {
    setResidence(code)
    const match = COUNTRIES.find((c) => c.code === code)
    if (match && match.dial !== '+') setDialCode(match.dial)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const user = await signup({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        phone_country_code: dialCode,
        phone_number: phone,
        country_of_residence: residenceCountry.code === 'XX' ? 'XX' : residence,
        invite_token: inviteToken || undefined,
      })
      navigate(user.can_run_queries ? '/query' : '/early-access')
    } catch (err) {
      setError(accessErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="shell page auth-page">
      <h1>Create account</h1>
      <p className="lede">{inviteHint}</p>
      <form className="auth-form" onSubmit={onSubmit}>
        <div className="auth-name-row">
          <label>
            First name
            <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </label>
          <label>
            Last name
            <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </label>
        </div>
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
          Country of residence
          <select value={residence} onChange={(e) => onResidenceChange(e.target.value)} required>
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Phone number
          <div className="phone-row">
            <select
              aria-label="Country calling code"
              value={dialCode}
              onChange={(e) => setDialCode(e.target.value)}
              required
            >
              {[...new Map(COUNTRIES.map((c) => [c.dial, c])).values()]
                .filter((c) => c.dial !== '+')
                .map((c) => (
                  <option key={`${c.code}-${c.dial}`} value={c.dial}>
                    {c.dial} ({c.code})
                  </option>
                ))}
            </select>
            <input
              type="tel"
              inputMode="numeric"
              autoComplete="tel-national"
              placeholder="Phone number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              minLength={4}
              required
            />
          </div>
        </label>
        <PasswordField
          label="Password"
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
          minLength={8}
          required
        />
        {error && <p className="error">{error}</p>}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={busy || (inviteOnlyMode && !inviteToken)}
        >
          {busy ? 'Creating account…' : inviteOnlyMode ? 'Accept invite' : 'Create account'}
        </button>
      </form>
      <p className="muted-text">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </main>
  )
}
