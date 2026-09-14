import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { CatalogResponse, DatasetSummary } from '../types'

const CATEGORIES = ['All', 'Tokens', 'Wallets', 'Transactions', 'Transfers'] as const

function categoryFor(dataset: DatasetSummary): string {
  const key = `${dataset.category} ${dataset.slug} ${dataset.name}`.toLowerCase()
  if (key.includes('token')) return 'Tokens'
  if (key.includes('wallet')) return 'Wallets'
  if (key.includes('transaction')) return 'Transactions'
  if (key.includes('transfer')) return 'Transfers'
  return 'All'
}

export function CatalogPage() {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>('All')

  useEffect(() => {
    api
      .catalog()
      .then(setCatalog)
      .catch((err: Error) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    if (!catalog) return []
    const q = search.trim().toLowerCase()
    return catalog.datasets.filter((d) => {
      const matchesSearch =
        !q ||
        d.name.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        d.curated_table.toLowerCase().includes(q)
      const matchesCategory = category === 'All' || categoryFor(d) === category
      return matchesSearch && matchesCategory
    })
  }, [catalog, search, category])

  return (
    <main className="shell">
      <div className="page-head">
        <h1>Dataset catalog</h1>
        <p>Browse Analytic Sages curated blockchain datasets.</p>
      </div>

      {error && <p className="error">{error}</p>}
      {!catalog && !error && <p className="status-banner">Loading datasets…</p>}

      {catalog && (
        <>
          <div className="catalog-toolbar">
            <input
              className="text-input catalog-search"
              placeholder="Search datasets…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="filter-chips">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`chip ${category === cat ? 'available' : ''}`}
                  onClick={() => setCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="catalog-list">
            {filtered.map((dataset) => (
              <article key={dataset.id} className="catalog-row">
                <div>
                  <h3>{dataset.name}</h3>
                  <p>{dataset.description}</p>
                  <p className="dataset-table muted-text" style={{ marginTop: '0.45rem' }}>
                    {dataset.curated_table}
                  </p>
                </div>
                <div className="catalog-row-meta">
                  <span className={`chip ${dataset.status}`}>{dataset.status.replace('_', ' ')}</span>
                  <span className="chip">{dataset.grain}</span>
                  <span className="chip">{dataset.column_count} columns</span>
                </div>
                <Link className="btn btn-primary" to={`/datasets/${dataset.slug}`}>
                  View dataset →
                </Link>
              </article>
            ))}
          </div>

          {filtered.length === 0 && (
            <p className="status-banner">No datasets match your search.</p>
          )}
        </>
      )}
    </main>
  )
}
