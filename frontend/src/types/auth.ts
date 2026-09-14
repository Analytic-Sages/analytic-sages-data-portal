export type AccessStatus = 'WAITLIST_PENDING' | 'APPROVED' | 'SUSPENDED'

export type AuthUser = {
  id: string
  email: string
  first_name: string
  last_name: string
  email_verified: boolean
  access_status: AccessStatus
  is_tester: boolean
  can_run_queries: boolean
  created_at?: string | null
}

export type AuthState = 'loading' | 'anonymous' | 'pending' | 'approved' | 'suspended'

export function authStateFromUser(user: AuthUser | null): AuthState {
  if (!user) return 'anonymous'
  if (user.access_status === 'SUSPENDED') return 'suspended'
  if (user.can_run_queries) return 'approved'
  return 'pending'
}
