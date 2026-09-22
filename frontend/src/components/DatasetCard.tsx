import { Link } from 'react-router-dom'
import type { DatasetSummary } from '../types'

type Props = {
  dataset: DatasetSummary
}

export function DatasetCard({ dataset }: Props) {
  return (
    <article className="dataset-card">
      <div className="meta">
        <span className={`chip ${dataset.status}`}>{dataset.status.replace('_', ' ')}</span>
        <span className="chip">{dataset.grain}</span>
        <span className="chip">{dataset.column_count} columns</span>
      </div>
      <h3>{dataset.name}</h3>
      <p>{dataset.description}</p>
      <Link className="btn btn-ghost dataset-cta" to={`/datasets/${dataset.slug}`}>
        View dataset →
      </Link>
    </article>
  )
}
