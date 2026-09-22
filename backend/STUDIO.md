# Query Studio + native dashboards (Dune-like, $0 charts)

Learners:

1. `/query` — write SQL, run, Table | Visualize (ECharts)
2. Save visualization (+ optional add to dashboard)
3. `/dashboards` — boards that re-run saved SQL and render charts in-browser

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/studio/visualizations` | List / save chart configs |
| DELETE | `/studio/visualizations/{id}` | Remove viz |
| GET/POST | `/studio/dashboards` | List / create boards |
| GET/PUT/DELETE | `/studio/dashboards/{slug}` | Board CRUD |
| POST | `/studio/dashboards/{slug}/visualizations` | Attach a viz |

Persistence: `STUDIO_STORE_PATH` (default `backend/var/studio_store.json`).

Queries still use `POST /query/run` with learning limits. Visualization itself has no vendor fee.

## Colors

Visualizations accept optional `style` (`primary`, `secondary`, `background`, `text`, `muted`, `palette`).
Dashboards accept optional `theme` with the same shape. Merge order in the UI:

`defaults → board theme → chart style`

Presets in Query studio: AS brand, Ocean, Forest, Sunset, Mono.

## Layout

Dashboards store a 12-column grid layout (`x`, `y`, `w`, `h` per visualization).
`PUT /studio/dashboards/{slug}` with `{ "layout": [...] }` persists drag/resize.

## Public share

```bash
# Enable share (returns share_token + share_path)
curl -X POST http://localhost:8000/studio/dashboards/my-board/share \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Public read (no API key)
curl http://localhost:8000/public/dashboards/TOKEN

# Public chart refresh
curl -X POST http://localhost:8000/public/dashboards/TOKEN/run \
  -H "Content-Type: application/json" \
  -d '{"visualization_id":"VIZ_ID"}'
```

Frontend route: `/share/{token}` (read-only grid).
