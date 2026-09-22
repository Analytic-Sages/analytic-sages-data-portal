import { DEFAULT_CHART_STYLE, STYLE_PRESETS, type ChartStyle } from '../lib/chartOptions'

type Props = {
  style: ChartStyle
  onChange: (style: ChartStyle) => void
  label?: string
}

export function ChartStylePicker({ style, onChange, label = 'Colors' }: Props) {
  function setField<K extends keyof ChartStyle>(key: K, value: ChartStyle[K]) {
    onChange({ ...style, [key]: value })
  }

  return (
    <div className="style-picker">
      <div className="style-picker-head">
        <strong>{label}</strong>
        <div className="meta">
          {STYLE_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className="chip"
              onClick={() => onChange({ ...preset.style, palette: [...preset.style.palette] })}
            >
              {preset.label}
            </button>
          ))}
          <button
            type="button"
            className="chip"
            onClick={() =>
              onChange({ ...DEFAULT_CHART_STYLE, palette: [...DEFAULT_CHART_STYLE.palette] })
            }
          >
            Reset
          </button>
        </div>
      </div>
      <div className="style-swatches">
        {(
          [
            ['primary', 'Primary'],
            ['secondary', 'Secondary'],
            ['background', 'Background'],
            ['text', 'Text'],
            ['muted', 'Muted'],
          ] as const
        ).map(([key, title]) => (
          <label key={key} className="swatch">
            <span>{title}</span>
            <input
              type="color"
              value={style[key]}
              onChange={(e) => setField(key, e.target.value.toUpperCase())}
            />
            <input
              className="text-input swatch-hex"
              value={style[key]}
              onChange={(e) => setField(key, e.target.value)}
            />
          </label>
        ))}
      </div>
      <div className="palette-row">
        <span className="status-banner">Palette (pie / multi-series)</span>
        <div className="meta">
          {style.palette.map((color, idx) => (
            <label key={`${color}-${idx}`} className="swatch-mini">
              <input
                type="color"
                value={color}
                onChange={(e) => {
                  const next = [...style.palette]
                  next[idx] = e.target.value.toUpperCase()
                  setField('palette', next)
                }}
              />
            </label>
          ))}
          {style.palette.length < 8 && (
            <button
              type="button"
              className="chip"
              onClick={() => setField('palette', [...style.palette, style.primary])}
            >
              + color
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
