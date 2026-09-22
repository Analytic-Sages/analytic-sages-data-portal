import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { DatasetDetail } from '../types'

type Props = {
  onInsert: (value: string) => void
}

export function SchemaExplorer({ onInsert }: Props) {
  const [datasets, setDatasets] = useState<DatasetDetail[]>([])
  const [search, setSearch] = useState('')
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({})
  const [openTables, setOpenTables] = useState<Record<string, boolean>>({})
  const [collapsed, setCollapsed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function loadSchemas() {
      try {
        const catalog = await api.catalog()
        const details = await Promise.all(catalog.datasets.map((dataset) => api.dataset(dataset.slug)))
        if (!cancelled) {
          setDatasets(details)
          setOpenCategories(Object.fromEntries([...new Set(details.map((dataset) => dataset.category))].map((category) => [category, true])))
        }
      } catch {
        if (!cancelled) setError(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadSchemas()
    return () => {
      cancelled = true
    }
  }, [])

  const filteredDatasets = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return datasets
    return datasets.filter((dataset) =>
      [dataset.name, dataset.slug, dataset.curated_table, dataset.category, ...dataset.columns.map((column) => `${column.name} ${column.type} ${column.description}`)]
        .join(' ')
        .toLowerCase()
        .includes(term),
    )
  }, [datasets, search])

  const grouped = useMemo(() => {
    return filteredDatasets.reduce<Record<string, DatasetDetail[]>>((groups, dataset) => {
      const category = dataset.category || 'Other'
      groups[category] = [...(groups[category] ?? []), dataset]
      return groups
    }, {})
  }, [filteredDatasets])

  function toggleCategory(category: string) {
    setOpenCategories((current) => ({ ...current, [category]: !current[category] }))
  }

  function toggleTable(slug: string) {
    setOpenTables((current) => ({ ...current, [slug]: !current[slug] }))
  }

  if (loading) {
    return <aside className="schema-explorer"><p className="muted-text">Loading schema…</p></aside>
  }

  if (error) {
    return <aside className="schema-explorer"><p className="muted-text">Schema unavailable.</p></aside>
  }

  return (
    <aside className="schema-explorer" aria-label="Schema explorer">
      <div className="schema-explorer-head">
        <div>
          <h3>Schema explorer</h3>
          {!collapsed && <p>Browse tables and insert fields into your query.</p>}
        </div>
        <div className="schema-explorer-actions">
          {!collapsed && <span className="schema-count">{filteredDatasets.length}</span>}
          <button
            type="button"
            className="schema-collapse"
            aria-expanded={!collapsed}
            aria-label={collapsed ? 'Expand schema explorer' : 'Collapse schema explorer'}
            onClick={() => setCollapsed((current) => !current)}
          >
            {collapsed ? '▸' : '▾'}
          </button>
        </div>
      </div>
      {!collapsed && (
        <>
          <label className="sr-only" htmlFor="schema-search">Search schema</label>
          <input
            id="schema-search"
            className="text-input schema-search"
            type="search"
            placeholder="Search tables or columns"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          {Object.keys(grouped).length === 0 ? (
            <p className="muted-text schema-empty">No matching tables or columns.</p>
          ) : (
            <div className="schema-tree">
              {Object.entries(grouped).map(([category, categoryDatasets]) => (
                <section className="schema-category" key={category}>
                  <button type="button" className="schema-disclosure" onClick={() => toggleCategory(category)}>
                    <span aria-hidden="true">{openCategories[category] ? '▾' : '▸'}</span>
                    <strong>{category}</strong>
                    <span className="schema-count">{categoryDatasets.length}</span>
                  </button>
                  {openCategories[category] && categoryDatasets.map((dataset) => (
                    <div className="schema-table" key={dataset.slug}>
                      <button type="button" className="schema-disclosure schema-table-toggle" onClick={() => toggleTable(dataset.slug)}>
                        <span aria-hidden="true">{openTables[dataset.slug] ? '▾' : '▸'}</span>
                        <span className="schema-table-name">{dataset.slug}</span>
                        <span className="schema-count">{dataset.columns.length}</span>
                      </button>
                      {openTables[dataset.slug] && (
                        <div className="schema-table-body">
                          <button type="button" className="schema-insert schema-table-insert" onClick={() => onInsert(dataset.curated_table)}>
                            <code>{dataset.curated_table}</code>
                            <span>Insert table</span>
                          </button>
                          {dataset.columns.map((column) => (
                            <button
                              type="button"
                              className="schema-column"
                              key={column.name}
                              title={column.description}
                              onClick={() => onInsert(column.name)}
                            >
                              <span>
                                <code>{column.name}</code>
                                <small>{column.description}</small>
                              </span>
                              <span className="schema-type">{column.type}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </section>
              ))}
            </div>
          )}
        </>
      )}
    </aside>
  )
}
