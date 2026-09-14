import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { buildQueryLink } from '../lib/queryLinks'
import type { LabDetail } from '../types'

export function LabDetailPage() {
  const { slug } = useParams()
  const [lab, setLab] = useState<LabDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [allLabs, setAllLabs] = useState<LabDetail[]>([])

  useEffect(() => {
    if (!slug) return
    api
      .lab(slug)
      .then(setLab)
      .catch((err: Error) => setError(err.message))
    api.labs().then((r) => setAllLabs(r.labs)).catch(() => setAllLabs([]))
  }, [slug])

  if (error) {
    return (
      <main className="shell page-head">
        <p className="error">{error}</p>
        <Link to="/labs">Back to labs</Link>
      </main>
    )
  }

  if (!lab) {
    return (
      <main className="shell page-head">
        <p className="status-banner">Loading lab…</p>
      </main>
    )
  }

  const nextLab = allLabs.find(
    (item) => item.number === lab.number + 1 && item.status !== 'coming_soon',
  )
  const isBeginner = lab.level.toLowerCase() === 'beginner'

  if (lab.status === 'coming_soon') {
    return (
      <main className="shell">
        <div className="page-head">
          <p className="breadcrumb">
            <Link to="/labs">Labs</Link> / Lab {String(lab.number).padStart(2, '0')}
          </p>
          <h1>
            Lab {String(lab.number).padStart(2, '0')} · {lab.title}
          </h1>
          <p>{lab.objective}</p>
          <span className="chip">Coming soon</span>
        </div>
        <section className="panel empty-state">
          <h2>This lab is coming soon</h2>
          <p>Finish the beginner labs first, then return for intermediate and advanced challenges.</p>
          <Link className="btn btn-primary" to="/labs">
            Back to labs
          </Link>
        </section>
      </main>
    )
  }

  return (
    <main className="shell">
      <div className="page-head">
        <p className="breadcrumb">
          <Link to="/labs">Labs</Link> / Lab {String(lab.number).padStart(2, '0')}
        </p>
        <h1>
          Lab {String(lab.number).padStart(2, '0')} · {lab.title}
        </h1>
        <div className="meta">
          <span className="chip available">{lab.level}</span>
          <Link className="chip" to={`/datasets/${lab.dataset_slug}`}>
            Dataset: {lab.dataset_slug}
          </Link>
          {lab.estimated_minutes && <span className="chip">~{lab.estimated_minutes} min</span>}
          <span className="chip code-inline">{lab.curated_table}</span>
        </div>
      </div>

      <section className="panel">
        <h2>Goal</h2>
        <p>{lab.objective}</p>
      </section>

      <section className="panel">
        <h2>Dataset</h2>
        <p>
          You will query <code>{lab.curated_table}</code>.{' '}
          <Link to={`/datasets/${lab.dataset_slug}`}>View dataset schema →</Link>
        </p>
      </section>

      <section className="panel">
        <h2>What you&apos;ll learn</h2>
        {lab.skills && lab.skills.length > 0 && (
          <div className="meta" style={{ marginBottom: '0.75rem' }}>
            {lab.skills.map((skill) => (
              <span key={skill} className="chip available">
                {skill}
              </span>
            ))}
          </div>
        )}
        <ul className="learn-list">
          {lab.what_you_learn.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Question</h2>
        <p>{lab.task}</p>
      </section>

      {isBeginner && lab.starter_sql && (
        <section className="panel">
          <h2>Starter SQL</h2>
          <p className="status-banner">
            Beginner labs include starter SQL. Edit it in Query Studio, run it, then visualize your results.
          </p>
          <pre className="sql-block-pre">{lab.starter_sql}</pre>
          <div className="cta-row page-actions">
            <Link className="btn btn-primary" to={buildQueryLink({ lab: lab.slug })}>
              Open in Query Studio →
            </Link>
          </div>
        </section>
      )}

      {!isBeginner && (
        <section className="panel">
          <h2>Your workspace</h2>
          <p className="status-banner">
            Intermediate and advanced labs give you less scaffolding. Open Query Studio and solve the
            question with the curated dataset.
          </p>
          <Link className="btn btn-primary" to={buildQueryLink({ lab: lab.slug, dataset: lab.dataset_slug })}>
            Open in Query Studio →
          </Link>
        </section>
      )}

      <section className="panel">
        <h2>Check your work</h2>
        <p>{lab.check_hint}</p>
      </section>

      <section className="panel">
        <h2>Continue</h2>
        <div className="cta-row">
          {nextLab ? (
            <Link className="btn btn-primary" to={`/labs/${nextLab.slug}`}>
              Next: Lab {String(nextLab.number).padStart(2, '0')} →
            </Link>
          ) : (
            <Link className="btn btn-primary" to="/query">
              Continue in Query Studio →
            </Link>
          )}
          <Link className="btn btn-ghost" to="/labs">
            All labs
          </Link>
        </div>
      </section>
    </main>
  )
}
