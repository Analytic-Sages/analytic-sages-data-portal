import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { BrandLockup } from './BrandLockup'

const NAV_ITEMS = [
  { to: '/catalog', label: 'Catalog' },
  { to: '/labs', label: 'Labs' },
  { to: '/query', label: 'Query' },
  { to: '/visualizations', label: 'Visualizations' },
  { to: '/dashboards', label: 'Dashboards' },
  { to: '/explore', label: 'Explore' },
] as const

export function Layout() {
  const [navOpen, setNavOpen] = useState(false)
  const { user, state, logout, loading } = useAuth()

  function closeNav() {
    setNavOpen(false)
  }

  return (
    <>
      <header className="site-header">
        <div className="shell inner header-inner">
          <NavLink to="/" className="brand" aria-label="Analytic Sages home" onClick={closeNav}>
            <BrandLockup size="sm" />
          </NavLink>
          <button
            type="button"
            className="nav-toggle"
            aria-expanded={navOpen}
            aria-controls="site-nav"
            onClick={() => setNavOpen((v) => !v)}
          >
            <span className="nav-toggle-bar" />
            <span className="nav-toggle-bar" />
            <span className="nav-toggle-bar" />
            <span className="sr-only">{navOpen ? 'Close menu' : 'Open menu'}</span>
          </button>
          <nav id="site-nav" className={`nav ${navOpen ? 'nav-open' : ''}`}>
            {NAV_ITEMS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => (isActive ? 'active' : undefined)}
                onClick={closeNav}
              >
                {label}
              </NavLink>
            ))}
            <div className="nav-auth">
              {!loading && state === 'anonymous' && (
                <>
                  <Link to="/login" className="nav-auth-link" onClick={closeNav}>
                    Sign in
                  </Link>
                  <Link to="/signup" className="btn btn-primary nav-cta" onClick={closeNav}>
                    Early access
                  </Link>
                </>
              )}
              {!loading && user && (
                <>
                  <Link
                    to={state === 'approved' ? '/query' : '/early-access'}
                    className="nav-auth-link"
                    onClick={closeNav}
                    title={user.email}
                  >
                    {state === 'approved' ? 'Approved' : 'Waitlist'}
                  </Link>
                  <button
                    type="button"
                    className="btn btn-ghost nav-cta"
                    onClick={() => {
                      closeNav()
                      void logout()
                    }}
                  >
                    Sign out
                  </button>
                </>
              )}
            </div>
          </nav>
        </div>
      </header>
      <Outlet />
      <footer className="site-footer">
        <div className="shell footer-inner">
          <BrandLockup size="sm" />
          <p>
            <strong>Analytic Sages Data Portal.</strong> Query curated blockchain data, visualize in
            the browser, and build learner dashboards.
          </p>
        </div>
      </footer>
    </>
  )
}
