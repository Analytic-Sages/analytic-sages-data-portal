import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { AnalyticsPreview } from '../components/AnalyticsPreview'
import { DatasetCard } from '../components/DatasetCard'
import { FeaturedShowcase } from '../components/FeaturedShowcase'
import { LabCard } from '../components/LabCard'
import type { CatalogResponse, LabDetail } from '../types'

export function HomePage() {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null)
  const [labs, setLabs] = useState<LabDetail[]>([])

  useEffect(() => {
    api.catalog().then(setCatalog).catch(() => setCatalog(null))
    api
      .labs()
      .then((r) => setLabs(r.labs.filter((l) => l.status !== 'coming_soon').slice(0, 4)))
      .catch(() => setLabs([]))
  }, [])

  return (
    <main>
      <section className="hero hero-product">
        <div className="shell hero-grid">
          <div className="hero-copy">
            <h1>Learn Blockchain Through Data.</h1>
            <p className="hero-lead">
              Explore real blockchain datasets, write SQL, analyze results, and build dashboards.
            </p>
            <div className="cta-row hero-cta">
              <Link className="btn btn-primary btn-lg" to="/catalog">
                Explore datasets
              </Link>
              <Link className="btn btn-ghost btn-lg" to="/labs">
                Start a lab
              </Link>
            </div>
          </div>
          <AnalyticsPreview />
        </div>
      </section>

      <FeaturedShowcase />

      <section className="section">
        <div className="shell">
          <h2>From data to insight</h2>
          <div className="learning-path-light">
            <span>Explore data</span>
            <span className="learning-path-arrow" aria-hidden="true">
              →
            </span>
            <span>Learn SQL</span>
            <span className="learning-path-arrow" aria-hidden="true">
              →
            </span>
            <span>Analyze</span>
            <span className="learning-path-arrow" aria-hidden="true">
              →
            </span>
            <span>Build</span>
          </div>
        </div>
      </section>

      {catalog && catalog.datasets.length > 0 && (
        <section className="section section-surface">
          <div className="shell">
            <div className="section-head-row">
              <div className="prose-narrow">
                <h2>Learn with real blockchain data</h2>
                <p className="section-lead">Explore the datasets behind the analytics you&apos;ll build.</p>
              </div>
              <Link to="/catalog" className="section-link">
                View all datasets →
              </Link>
            </div>
            <div className="dataset-grid compact">
              {catalog.datasets.slice(0, 4).map((dataset) => (
                <DatasetCard key={dataset.id} dataset={dataset} />
              ))}
            </div>
          </div>
        </section>
      )}

      {labs.length > 0 && (
        <section className="section">
          <div className="shell">
            <div className="section-head-row">
              <div className="prose-narrow">
                <h2>Learning Labs</h2>
                <p className="section-lead">Practice blockchain analytics by answering real data questions.</p>
              </div>
              <Link to="/labs" className="section-link">
                View all labs →
              </Link>
            </div>
            <div className="lab-list lab-preview-grid">
              {labs.map((lab) => (
                <LabCard key={lab.id} lab={lab} compact />
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="section section-surface">
        <div className="shell build-cta-block prose-narrow">
          <h2>Build your own</h2>
          <p className="section-lead">
            Open Query Studio to write SQL, visualize results, and save charts to a dashboard.
            Sign in to run queries against curated blockchain data.
          </p>
          <div className="cta-row">
            <Link className="btn btn-primary btn-lg" to="/query">
              Open Query Studio
            </Link>
            <Link className="btn btn-ghost btn-lg" to="/signup">
              Create account
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
