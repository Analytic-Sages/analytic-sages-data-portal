export type AccessStatus = 'WAITLIST_PENDING' | 'APPROVED' | 'SUSPENDED'

export type AuthUser = {
  id: string
  email: string
  first_name: string
  last_name: string
  phone_country_code?: string
  phone_number?: string
  country_of_residence?: string
  email_verified: boolean
  access_status: AccessStatus
  is_tester: boolean
  is_admin?: boolean
  can_run_queries: boolean
  created_at?: string | null
  approved_at?: string | null
}

export type AuthState = 'loading' | 'anonymous' | 'pending' | 'approved' | 'suspended'

export type AdminInvite = {
  id: string
  email: string
  status: 'PENDING' | 'ACCEPTED' | 'REVOKED'
  note: string
  invited_by: string
  created_at?: string | null
  expires_at?: string | null
  accepted_at?: string | null
  accepted_user_id?: string | null
  invite_url?: string
}

export type AdminAnalyticsSummary = {
  generated_at: string
  window_days: number
  mode: string
  private_access_mode: boolean
  users: {
    total: number
    approved: number
    waitlist_pending: number
    suspended: number
    verified: number
    by_country: Array<{ country: string; count: number }>
    signups_by_day: Array<{ day: string; count: number }>
  }
  queries: {
    total: number
    success: number
    failed: number
    active_users: number
    bytes_billed_total: number
    by_day: Array<{ day: string; count: number; bytes_billed: number }>
    recent: Array<{
      id: string
      user_id: string | null
      success: boolean
      mode: string
      bytes_billed: number
      row_count: number
      error_code: string
      sql_preview: string
      created_at: string | null
    }>
  }
  policy: Record<string, unknown>
}

export function authStateFromUser(user: AuthUser | null): AuthState {
  if (!user) return 'anonymous'
  if (user.access_status === 'SUSPENDED') return 'suspended'
  if (user.can_run_queries) return 'approved'
  return 'pending'
}
