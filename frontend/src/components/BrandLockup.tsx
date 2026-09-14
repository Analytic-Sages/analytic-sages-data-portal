type BrandLockupProps = {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** When false, show the mark only. Default shows the full logo lockup. */
  showWordmark?: boolean
  className?: string
}

const heights = {
  sm: 32,
  md: 40,
  lg: 64,
  xl: 96,
} as const

export function BrandLockup({
  size = 'md',
  showWordmark = true,
  className = '',
}: BrandLockupProps) {
  const h = heights[size]

  if (!showWordmark) {
    return (
      <span className={`brand-lockup brand-lockup--${size} ${className}`.trim()}>
        <img
          src="/brand/as-mark.png"
          alt="Analytic Sages"
          height={h}
          width={Math.round(h * 1.19)}
          className="brand-mark"
          decoding="async"
        />
      </span>
    )
  }

  return (
    <span className={`brand-lockup brand-lockup--${size} ${className}`.trim()}>
      <img
        src="/brand/as-logo.png"
        alt="Analytic Sages"
        height={h}
        width={Math.round(h * 3.45)}
        className="brand-logo"
        decoding="async"
      />
    </span>
  )
}
