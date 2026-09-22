import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { LabCard } from '../components/LabCard'
import type { LabDetail } from '../types'

const LEVELS = ['Beginner', 'Intermediate', 'Advanced'] as const

export function LabsPage() {
  const [labs, setLabs] = useState<LabDetail[]>([])
  const [error, setError] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<string>('All')

  useEffect(() => {
    api
      .labs()
      .then((data) => setLabs(data.labs))
      .catch((err: Error) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    if (levelFilter === 'All') return labs
    return labs.filter((l) => l.level.toLowerCase() === levelFilter.toLowerCase())
  }, [labs, levelFilter])

  const byLevel = useMemo(() => {
    const groups: Record<string, LabDetail[]> = {}
    for (const level of LEVELS) {
      groups[level] = filtered.filter((l) => l.level.toLowerCase() === level.toLowerCase())
    }
    return groups
  }, [filtered])

  return (
    <main className="shell">
      <div className="page-head">
        <h1>Learning Labs</h1>
        <p>Learn to answer real blockchain questions with SQL.</p>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="filter-chips" style={{ marginBottom: '1.25rem' }}>
        <button
          type="button"
          className={`chip ${levelFilter === 'All' ? 'available' : ''}`}
          onClick={() => setLevelFilter('All')}
        >
          All
        </button>
        {LEVELS.map((level) => (
          <button
            key={level}
            type="button"
            className={`chip ${levelFilter === level ? 'available' : ''}`}
            onClick={() => setLevelFilter(level)}
          >
            {level}
          </button>
        ))}
      </div>

      {LEVELS.map((level) => {
        const group = byLevel[level]
        if (group.length === 0) return null
        return (
          <section key={level} className="lab-level-section">
            <h2>{level}</h2>
            <div className="lab-list lab-curriculum-grid">
              {group.map((lab) => (
                <LabCard key={lab.id} lab={lab} />
              ))}
            </div>
          </section>
        )
      })}

      {labs.length === 0 && !error && (
        <p className="status-banner">Loading labs…</p>
      )}
    </main>
  )
}
