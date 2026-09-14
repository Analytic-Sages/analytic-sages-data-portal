import { Link } from 'react-router-dom'
import {
  SHOWCASE_DASHBOARD,
  SHOWCASE_SAMPLE_DATA,
  SHOWCASE_VISUALIZATIONS,
} from '../data/showcaseSnapshot'
import { DashboardGrid } from './DashboardGrid'

export function FeaturedShowcase() {
  return (
    <section className="section section-surface showcase-section">
      <div className="shell">
        <div className="section-head-row">
          <div className="prose-narrow">
            <h2>See what you&apos;ll build</h2>
            <p className="section-lead">
              Work with real Solana data and turn onchain activity into useful analytics.
            </p>
            <p className="showcase-sample-note">
              Built from curated Solana data in the Analytic Sages Data Portal. Everything you see
              here can be recreated from the datasets and tools in this portal.
            </p>
          </div>
          <Link className="btn btn-primary" to="/query">
            Open Query Studio
          </Link>
        </div>
        <p className="showcase-board-title">{SHOWCASE_DASHBOARD.title}</p>
        <DashboardGrid
          visualizations={SHOWCASE_VISUALIZATIONS}
          layout={SHOWCASE_DASHBOARD.layout}
          editable={false}
          sampleDataById={SHOWCASE_SAMPLE_DATA}
          theme={SHOWCASE_DASHBOARD.theme}
        />
        <div className="cta-row" style={{ marginTop: '1.25rem' }}>
          <Link className="btn btn-ghost" to="/labs">
            Start a lab
          </Link>
        </div>
      </div>
    </section>
  )
}
