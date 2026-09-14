import { Link } from 'react-router-dom'
import type { LabDetail } from '../types'

type Props = {
  lab: LabDetail
  compact?: boolean
}

export function LabCard({ lab, compact = false }: Props) {
  const skills = lab.skills?.length ? lab.skills.join(' · ') : null
  const minutes = lab.estimated_minutes ? `~${lab.estimated_minutes} min` : null
  const cta =
    lab.status === 'coming_soon' ? (
      <span className="btn btn-ghost lab-row-cta" style={{ opacity: 0.6, pointerEvents: 'none' }}>
        Coming soon
      </span>
    ) : (
      <Link className="btn btn-primary lab-row-cta" to={`/labs/${lab.slug}`}>
        Start lab →
      </Link>
    )

  return (
    <article className={`lab-item panel lab-row ${compact ? 'lab-card-compact' : ''}`}>
      <div className="lab-row-body">
        <p className="lab-number">Lab {String(lab.number).padStart(2, '0')}</p>
        <h3>{lab.title}</h3>
        <p>{lab.task}</p>
        {skills && !compact && <p className="lab-skills">You&apos;ll learn: {skills}</p>}
        <div className="meta">
          <span className="chip">{lab.level}</span>
          <span className="chip">{lab.dataset_slug}</span>
          {minutes && <span className="chip">{minutes}</span>}
          {lab.status === 'coming_soon' && <span className="chip">Coming soon</span>}
        </div>
      </div>
      {cta}
    </article>
  )
}
