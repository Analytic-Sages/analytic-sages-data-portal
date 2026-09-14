export type DatasetSummary = {
  id: string
  name: string
  slug: string
  description: string
  grain: string
  category: string
  status: string
  curated_table: string
  open_in_bigquery_url?: string
  freshness?: string
  example_question: string
  column_count: number
}

export type Column = {
  name: string
  type: string
  description: string
}

export type SqlExample = {
  title: string
  sql: string
}

export type Lab = {
  id: string
  title: string
  level: string
  prompt: string
  slug?: string
}

export type Project = {
  id: string
  title: string
  level: string
  prompt: string
}

export type DatasetDetail = DatasetSummary & {
  columns: Column[]
  sql_examples: SqlExample[]
  labs: Lab[]
  projects: Project[]
  internal_table_key: string | null
  what_you_learn?: string
  coverage?: string
  related_datasets?: string[]
}

export type CatalogResponse = {
  product: string
  promise: string
  description: string
  bigquery_console_url?: string
  datasets: DatasetSummary[]
}

export type LabDetail = {
  id: string
  slug: string
  number: number
  title: string
  level: string
  dataset_slug: string
  objective: string
  task: string
  starter_sql: string
  check_hint: string
  what_you_learn: string[]
  skills?: string[]
  estimated_minutes?: number
  status?: 'available' | 'coming_soon' | string
  curated_table: string
  open_in_bigquery_url?: string
  bigquery_console_url?: string
}

export type QueryPolicy = {
  enabled: boolean
  max_bytes_billed: number
  max_bytes_billed_mb: number
  timeout_seconds: number
  max_rows: number
  max_days: number
  data_window_start: string
  data_window_end: string
  allowed_dataset: string
  allowed_tables: string[]
  allowed_refs: string[]
  note: string
}

export type QueryResult = {
  columns: string[]
  data: Array<Record<string, unknown>>
  row_count: number
  bytes_processed: number
  bytes_billed: number
  job_id: string
  cache_hit: boolean
  policy: QueryPolicy
  mode: string
  note?: string
}

export type JourneyStep = {
  id: string
  title: string
  path: string
  summary: string
}

export type LearningJourney = {
  steps: JourneyStep[]
  note: string
}

export type PortalDashboard = {
  id: string
  slug: string
  title: string
  description: string
  category: string
  embed_url: string | null
  looker_report_url?: string | null
  thumbnail_url?: string | null
  is_published: boolean
  sort_order: number
  dataset_slugs: string[]
  charts_preview: string[]
  learning_note: string
  status: 'live' | 'coming_soon' | string
}

export type DashboardsResponse = {
  product: string
  note: string
  journey: LearningJourney
  counts: { total: number; live: number; coming_soon: number }
  dashboards: PortalDashboard[]
}

export type DashboardDetailResponse = {
  dashboard: PortalDashboard
  related: PortalDashboard[]
  journey: LearningJourney
}

export type StudioVisualization = {
  id: string
  title: string
  sql: string
  chart_type: string
  x_axis: string | null
  y_axis: string | null
  description: string
  owner_user_id?: string
  style?: {
    primary: string
    secondary: string
    background: string
    text: string
    muted: string
    palette: string[]
  }
  created_at: string
  updated_at: string
}

export type StudioLayoutItem = {
  i: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
}

export type StudioDashboard = {
  id: string
  slug: string
  title: string
  description: string
  visualization_ids: string[]
  layout: StudioLayoutItem[]
  theme?: {
    primary: string
    secondary: string
    background: string
    text: string
    muted: string
    palette: string[]
  }
  is_published: boolean
  share_enabled: boolean
  share_token?: string | null
  share_path?: string | null
  owner_user_id?: string
  created_at: string
  updated_at: string
}

export type StudioDashboardsResponse = {
  note: string
  dashboards: StudioDashboard[]
}

export type StudioDashboardDetail = {
  dashboard: StudioDashboard
  visualizations: StudioVisualization[]
}
