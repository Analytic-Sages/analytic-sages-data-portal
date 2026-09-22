import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

type ExploreMode = 'tokens-top' | 'tokens-daily' | 'transfers'

export function ExplorePage() {
  const [mode, setMode] = useState<ExploreMode>('tokens-top')
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([])
  const [meta, setMeta] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      if (mode === 'tokens-top') {
        const res = await api.tokensTop(10)
        setRows(res.data)
        setMeta(`${res.data.length} rows`)
      } else if (mode === 'tokens-daily') {
        const res = await api.tokensDaily(10)
        setRows(res.data)
        setMeta(`${res.data.length} rows`)
      } else {
        const res = await api.transfersRecent(10)
        setRows(res.data)
        setMeta(`${res.data.length} rows`)
      }
    } catch (err) {
      setRows([])
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  const columns = rows[0] ? Object.keys(rows[0]) : []

  return (
    <main className="shell">
      <div className="page-head">
        <h1>Explore</h1>
        <p>Discover sample analytics from curated Solana data.</p>
      </div>

      <div className="explore-controls">
        <select value={mode} onChange={(e) => setMode(e.target.value as ExploreMode)}>
          <option value="tokens-top">Top tokens by volume</option>
          <option value="tokens-daily">Token daily activity</option>
          <option value="transfers">Recent transfers</option>
        </select>
        <button type="button" className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? 'Loading…' : 'View sample'}
        </button>
      </div>

      {meta && <p className="status-banner">{meta}</p>}
      {error && <p className="error">{error}</p>}

      {rows.length > 0 && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={idx}>
                  {columns.map((col) => (
                    <td key={col}>{String(row[col] ?? '')}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <section className="panel" style={{ marginTop: '1.5rem' }}>
        <h2>Want to go deeper?</h2>
        <div className="cta-row">
          <Link className="btn btn-primary" to="/query">
            Open Query Studio
          </Link>
          <Link className="btn btn-ghost" to="/catalog">
            Browse datasets
          </Link>
        </div>
      </section>
    </main>
  )
}
