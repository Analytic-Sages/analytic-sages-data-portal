import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, ApiError } from '../api'
import {
  authStateFromUser,
  type AuthState,
  type AuthUser,
} from '../types/auth'

type AuthContextValue = {
  user: AuthUser | null
  state: AuthState
  loading: boolean
  refresh: () => Promise<void>
  login: (email: string, password: string) => Promise<AuthUser>
  signup: (input: {
    email: string
    password: string
    first_name?: string
    last_name?: string
  }) => Promise<AuthUser>
  logout: () => Promise<void>
  verifyEmail: (token: string) => Promise<AuthUser>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const res = await api.me()
      setUser(res.user)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login({ email, password })
    setUser(res.user)
    return res.user
  }, [])

  const signup = useCallback(
    async (input: { email: string; password: string; first_name?: string; last_name?: string }) => {
      const res = await api.signup(input)
      setUser(res.user)
      return res.user
    },
    [],
  )

  const logout = useCallback(async () => {
    await api.logout()
    setUser(null)
  }, [])

  const verifyEmail = useCallback(async (token: string) => {
    const res = await api.verifyEmail(token)
    setUser(res.user)
    return res.user
  }, [])

  const state = loading ? 'loading' : authStateFromUser(user)

  const value = useMemo(
    () => ({
      user,
      state,
      loading,
      refresh,
      login,
      signup,
      logout,
      verifyEmail,
    }),
    [user, state, loading, refresh, login, signup, logout, verifyEmail],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function accessErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === 'WAITLIST_PENDING') {
      return 'Your account is on the early-access waitlist. Query Studio unlocks after approval.'
    }
    if (err.code === 'EARLY_ACCESS_REQUIRED') {
      return 'Query Studio access requires early access approval.'
    }
    if (err.code === 'EMAIL_VERIFICATION_REQUIRED') {
      return 'Verify your email before using Query Studio.'
    }
    if (err.code === 'ACCESS_SUSPENDED') {
      return 'Your Query Studio access has been suspended.'
    }
    return err.message
  }
  return err instanceof Error ? err.message : 'Something went wrong.'
}
