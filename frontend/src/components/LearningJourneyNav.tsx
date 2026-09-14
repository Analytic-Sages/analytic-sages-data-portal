import { Link } from 'react-router-dom'
import type { LearningJourney } from '../types'

type Props = {
  journey?: LearningJourney | null
  activeId?: string
  compact?: boolean
}

const FALLBACK: LearningJourney = {
  note: 'Catalog → Labs → Query → Dashboards. Charts render in-browser with ECharts.',
  steps: [
    { id: 'catalog', title: 'Understand', path: '/catalog', summary: 'Browse curated datasets' },
    { id: 'labs', title: 'Learn', path: '/labs', summary: 'Guided SQL labs' },
    { id: 'query', title: 'Query', path: '/query', summary: 'Write SQL and visualize' },
    { id: 'dashboards', title: 'Build', path: '/dashboards', summary: 'Save charts into boards' },
  ],
}

export function LearningJourneyNav({ journey, activeId, compact = false }: Props) {
  const data = journey ?? FALLBACK

  return (
    <section className={`journey ${compact ? 'journey-compact' : ''}`}>
      {!compact && <h2>Learning path</h2>}
      <ol className="journey-steps">
        {data.steps.map((step, idx) => {
          const active = activeId === step.id
          return (
            <li key={step.id} className={active ? 'active' : undefined}>
              <Link to={step.path}>
                <span className="journey-index">{idx + 1}</span>
                <span className="journey-copy">
                  <strong>{step.title}</strong>
                  <span>{step.summary}</span>
                </span>
              </Link>
            </li>
          )
        })}
      </ol>
      {!compact && <p className="status-banner">{data.note}</p>}
    </section>
  )
}
