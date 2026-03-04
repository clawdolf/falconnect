import { useState, useEffect } from 'react'
import CalendarLinks from './CalendarLinks'
import DryRunReport from './DryRunReport'

function Dashboard() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/health')
      .then(r => r.json())
      .then(data => {
        setHealth(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return (
    <main className="dashboard">
      {/* Service Health */}
      <section className="card">
        <h2>Service Status</h2>
        {loading ? (
          <p className="muted">Loading...</p>
        ) : health ? (
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Status</span>
              <span className={`value ${health.status === 'healthy' ? 'green' : 'red'}`}>
                {health.status}
              </span>
            </div>
            <div className="status-item">
              <span className="label">Version</span>
              <span className="value">{health.version}</span>
            </div>
            <div className="status-item">
              <span className="label">Auth</span>
              <span className={`value ${health.clerk_configured ? 'green' : 'yellow'}`}>
                {health.clerk_configured ? 'Active' : 'Not configured'}
              </span>
            </div>
            <div className="status-item">
              <span className="label">Sync</span>
              <span className={`value ${health.sync_enabled ? 'green' : 'red'}`}>
                {health.sync_enabled ? (health.sync_dry_run ? 'Dry Run' : 'Live') : 'Disabled'}
              </span>
            </div>
          </div>
        ) : (
          <p className="muted red">Unable to reach service</p>
        )}
      </section>

      {/* Calendar Links */}
      <CalendarLinks />

      {/* Dry Run */}
      <DryRunReport />
    </main>
  )
}

export default Dashboard
