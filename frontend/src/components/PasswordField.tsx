import { useState } from 'react'

type PasswordFieldProps = {
  label: string
  value: string
  onChange: (value: string) => void
  autoComplete: string
  minLength?: number
  required?: boolean
}

export function PasswordField({
  label,
  value,
  onChange,
  autoComplete,
  minLength,
  required = false,
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false)

  return (
    <label>
      {label}
      <span className="password-field-row">
        <input
          type={visible ? 'text' : 'password'}
          autoComplete={autoComplete}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          minLength={minLength}
          required={required}
        />
        <button
          type="button"
          className="password-visibility-toggle"
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
          onClick={() => setVisible((current) => !current)}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </span>
    </label>
  )
}