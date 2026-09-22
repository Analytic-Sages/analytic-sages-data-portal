export type QueryLinkParams = {
  sql?: string
  dataset?: string
  lab?: string
  viz?: string
}

export function buildQueryLink(params: QueryLinkParams): string {
  const sp = new URLSearchParams()
  if (params.dataset) sp.set('dataset', params.dataset)
  if (params.lab) sp.set('lab', params.lab)
  if (params.viz) sp.set('viz', params.viz)
  if (params.sql) sp.set('sql', params.sql)
  const qs = sp.toString()
  return qs ? `/query?${qs}` : '/query'
}

export function parseQuerySearch(search: string): QueryLinkParams {
  const sp = new URLSearchParams(search)
  return {
    dataset: sp.get('dataset') ?? undefined,
    lab: sp.get('lab') ?? undefined,
    viz: sp.get('viz') ?? undefined,
    sql: sp.get('sql') ?? undefined,
  }
}
