import type {
  CatalogResponse,
  DashboardDetailResponse,
  DashboardsResponse,
  DatasetDetail,
  LabDetail,
  LearningJourney,
  QueryPolicy,
  QueryResult,
  StudioDashboard,
  StudioDashboardDetail,
  StudioDashboardsResponse,
  StudioVisualization,
} from './types'
import type { AuthUser } from './types/auth'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  status: number
  code: string | null

  constructor(message: string, status: number, code: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

function parseErrorDetail(raw: string): { message: string; code: string | null } {
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown }
    const detail = parsed.detail
    if (typeof detail === 'string') return { message: detail, code: null }
    if (detail && typeof detail === 'object' && 'message' in detail) {
      const d = detail as { message?: string; code?: string }
      return { message: d.message || raw, code: d.code ?? null }
    }
  } catch {
    /* keep */
  }
  return { message: raw || 'Request failed', code: null }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const text = await res.text()
    const { message, code } = parseErrorDetail(text)
    throw new ApiError(message || `Request failed: ${res.status}`, res.status, code)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

async function get<T>(path: string): Promise<T> {
  return request<T>(path)
}

async function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export const api = {
  catalog: () => get<CatalogResponse>('/datasets'),
  dataset: (slug: string) => get<DatasetDetail>(`/datasets/${slug}`),
  labs: () => get<{ labs: LabDetail[] }>('/labs'),
  lab: (slug: string) => get<LabDetail>(`/labs/${slug}`),
  health: () => get<{ status: string; mode: string; trino: string }>('/health'),
  queryPolicy: () => get<QueryPolicy>('/query/policy'),
  learningJourney: () => get<LearningJourney>('/learning-journey'),
  dashboards: (dataset?: string) =>
    get<DashboardsResponse>(dataset ? `/dashboards?dataset=${encodeURIComponent(dataset)}` : '/dashboards'),
  dashboard: (slug: string) => get<DashboardDetailResponse>(`/dashboards/${slug}`),
  runQuery: (sql: string) => send<QueryResult>('/query/run', 'POST', { sql }),
  me: () => get<{ user: AuthUser | null }>('/auth/me'),
  signup: (body: {
    email: string
    password: string
    first_name?: string
    last_name?: string
    phone_country_code: string
    phone_number: string
    country_of_residence: string
  }) => send<{ user: AuthUser }>('/auth/signup', 'POST', body),
  login: (body: { email: string; password: string }) =>
    send<{ user: AuthUser }>('/auth/login', 'POST', body),
  logout: () => send<{ status: string }>('/auth/logout', 'POST'),
  verifyEmail: (token: string) => send<{ user: AuthUser }>('/auth/verify-email', 'POST', { token }),
  forgotPassword: (email: string) =>
    send<{ status: string }>('/auth/forgot-password', 'POST', { email }),
  resetPassword: (token: string, password: string) =>
    send<{ status: string }>('/auth/reset-password', 'POST', { token, password }),
  resendVerification: () => send<{ status: string }>('/auth/resend-verification', 'POST'),
  adminAnalytics: (adminKey: string, days = 30) =>
    request<import('./types/auth').AdminAnalyticsSummary>(`/admin/analytics/summary?days=${days}`, {
      headers: { 'X-Admin-Key': adminKey },
    }),
  adminUsers: (adminKey: string, params?: { access_status?: string; q?: string }) => {
    const qs = new URLSearchParams()
    if (params?.access_status) qs.set('access_status', params.access_status)
    if (params?.q) qs.set('q', params.q)
    const suffix = qs.toString() ? `?${qs}` : ''
    return request<{ users: AuthUser[] }>(`/admin/users${suffix}`, {
      headers: { 'X-Admin-Key': adminKey },
    })
  },
  adminApproveUser: (adminKey: string, userId: string) =>
    request<{ user: AuthUser }>(`/admin/users/${userId}/approve`, {
      method: 'POST',
      headers: { 'X-Admin-Key': adminKey },
    }),
  adminSuspendUser: (adminKey: string, userId: string) =>
    request<{ user: AuthUser }>(`/admin/users/${userId}/suspend`, {
      method: 'POST',
      headers: { 'X-Admin-Key': adminKey },
    }),
  adminQueryPolicy: (adminKey: string) =>
    request<QueryPolicy>('/admin/query-policy', {
      headers: { 'X-Admin-Key': adminKey },
    }),
  studioDashboards: () => get<StudioDashboardsResponse>('/studio/dashboards'),
  studioDashboard: (slug: string) => get<StudioDashboardDetail>(`/studio/dashboards/${slug}`),
  createStudioDashboard: (body: {
    title: string
    description?: string
    slug?: string
    visualization_ids?: string[]
  }) => send<{ dashboard: StudioDashboard }>('/studio/dashboards', 'POST', body),
  updateStudioDashboard: (
    slug: string,
    body: {
      title?: string
      description?: string
      visualization_ids?: string[]
      layout?: Array<{ i: string; x: number; y: number; w: number; h: number; minW?: number; minH?: number }>
      theme?: {
        primary?: string
        secondary?: string
        background?: string
        text?: string
        muted?: string
        palette?: string[]
      }
    },
  ) => send<{ dashboard: StudioDashboard }>(`/studio/dashboards/${slug}`, 'PUT', body),
  setDashboardShare: (slug: string, enabled: boolean) =>
    send<{ dashboard: StudioDashboard }>(`/studio/dashboards/${slug}/share`, 'POST', { enabled }),
  addVizToDashboard: (slug: string, visualization_id: string) =>
    send<{ dashboard: StudioDashboard }>(`/studio/dashboards/${slug}/visualizations`, 'POST', {
      visualization_id,
    }),
  deleteStudioDashboard: (slug: string) => send<{ status: string }>(`/studio/dashboards/${slug}`, 'DELETE'),
  publicDashboard: (token: string) => get<StudioDashboardDetail>(`/public/dashboards/${token}`),
  publicRunViz: (token: string, visualization_id: string) =>
    send<QueryResult>(`/public/dashboards/${token}/run`, 'POST', { visualization_id }),
  featuredDashboard: () => get<StudioDashboardDetail>('/public/featured-dashboard'),
  featuredRunViz: (visualization_id: string) =>
    send<QueryResult>('/public/featured-dashboard/run', 'POST', { visualization_id }),
  listVisualizations: () =>
    get<{ visualizations: StudioVisualization[]; chart_types: string[] }>('/studio/visualizations'),
  getVisualization: (id: string) =>
    get<{ visualization: StudioVisualization }>(`/studio/visualizations/${id}`),
  createVisualization: (body: {
    title: string
    sql: string
    chart_type: string
    x_axis?: string | null
    y_axis?: string | null
    description?: string
    style?: {
      primary?: string
      secondary?: string
      background?: string
      text?: string
      muted?: string
      palette?: string[]
    }
  }) => send<{ visualization: StudioVisualization }>('/studio/visualizations', 'POST', body),
  deleteVisualization: (id: string) => send<{ status: string }>(`/studio/visualizations/${id}`, 'DELETE'),
  tokensTop: (limit = 10) =>
    get<{ data: Array<{ mint: string; total_volume: number; transfer_count: number }>; mode: string }>(
      `/tokens/top?limit=${limit}`,
    ),
  tokensDaily: (limit = 10) =>
    get<{ data: Array<Record<string, unknown>>; mode: string }>(`/tokens/daily?limit=${limit}`),
  transfersRecent: (limit = 10) =>
    get<{ data: Array<Record<string, unknown>>; mode: string }>(`/transfers/recent?limit=${limit}`),
}
