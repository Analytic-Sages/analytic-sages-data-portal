import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { buildQueryLink } from '../lib/queryLinks'
import type { DatasetDetail } from '../types'

export function DatasetDetailPage() {
  const { slug } = useParams()
  const [dataset, setDataset] = useState<DatasetDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    api
      .dataset(slug)
      .then(setDataset)
      .catch((err: Error) => setError(err.message))
  }, [slug])

  if (error) {
    return (
      <main className="shell page-head">
        <p className="error">{error}</p>
        <Link to="/catalog">Back to catalog</Link>
      </main>
    )
  }

  if (!dataset) {
    return (
      <main className="shell page-head">
        <p className="status-banner">Loading dataset…</p>
      </main>
    )
  }

  const starterSql =
    dataset.sql_examples[0]?.sql ?? `SELECT * FROM ${dataset.curated_table} LIMIT 10`

  return (
    <main className="shell">
      <div className="page-head">
        <p className="breadcrumb">
          <Link to="/catalog">Catalog</Link> / {dataset.name}
        </p>
        <h1>{dataset.name}</h1>
        <p>{dataset.description}</p>
        <div className="meta">
          <span className={`chip ${dataset.status}`}>{dataset.status.replace('_', ' ')}</span>
          <span className="chip">{dataset.grain}</span>
          <span className="chip code-inline">{dataset.curated_table}</span>
          {dataset.freshness && <span className="chip">{dataset.freshness}</span>}
        </div>
        <div className="cta-row page-actions">
          <Link className="btn btn-primary" to={buildQueryLink({ dataset: dataset.slug, sql: starterSql })}>
            Try this dataset →
          </Link>
        </div>
      </div>

      {dataset.what_you_learn && (
        <section className="panel">
          <h2>Overview</h2>
          <p>{dataset.what_you_learn}</p>
        </section>
      )}

      <section className="panel">
        <h2>Example question</h2>
        <p>{dataset.example_question}</p>
      </section>

      <section className="panel">
        <h2>Schema</h2>
        <table className="schema-table">
          <thead>
            <tr>
              <th>Column</th>
              <th>Type</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {dataset.columns.map((col) => (
              <tr key={col.name}>
                <td>
                  <code>{col.name}</code>
                </td>
                <td>{col.type}</td>
                <td>{col.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {dataset.coverage && (
        <section className="panel">
          <h2>Coverage</h2>
          <p>{dataset.coverage}</p>
        </section>
      )}

      {dataset.sql_examples.length > 0 && (
        <section className="panel">
          <h2>Example SQL</h2>
          {dataset.sql_examples.map((example) => (
            <article key={example.title} className="sql-block">
              <h3>{example.title}</h3>
              <pre>{example.sql}</pre>
              <Link
                className="btn btn-primary"
                style={{ marginTop: '0.75rem' }}
                to={buildQueryLink({ dataset: dataset.slug, sql: example.sql })}
              >
                Run in Query Studio →
              </Link>
            </article>
          ))}
        </section>
      )}

      {dataset.labs.length > 0 && (
        <section className="panel">
          <h2>Related labs</h2>
          <div className="lab-list">
            {dataset.labs.map((lab) => (
              <article key={lab.id} className="lab-item">
                <h3>
                  {lab.title} <span className="chip">{lab.level}</span>
                </h3>
                <p>{lab.prompt}</p>
                {lab.slug && (
                  <Link className="btn btn-ghost" to={`/labs/${lab.slug}`}>
                    Start lab →
                  </Link>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {dataset.related_datasets && dataset.related_datasets.length > 0 && (
        <section className="panel">
          <h2>Related datasets</h2>
          <div className="meta">
            {dataset.related_datasets.map((related) => (
              <Link key={related} className="chip" to={`/datasets/${related}`}>
                {related}
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
