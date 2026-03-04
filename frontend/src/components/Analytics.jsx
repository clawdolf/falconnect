import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'

function Analytics() {
  const [days, setDays] = useState(30)
  const [summary, setSummary] = useState(null)
  const [daily, setDaily] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  let getToken = null
  try {
    const auth = useAuth()
    getToken = auth.getToken
  } catch {
    // Clerk not configured
  }

  const getHeaders = async () => {
    const headers = { 'Content-Type': 'application/json' }
    if (getToken) {
      try {
        const token = await getToken()
        if (token) headers['Authorization'] = `Bearer ${token}`
      } catch { /* no-op */ }
    }
    return headers
  }

  const fetchData = async (d) => {
    setLoading(true)
    setError(null)
    try {
      const headers = await getHeaders()
      const [sumResp, dailyResp] = await Promise.all([
        fetch(`/api/analytics/summary?days=${d}`, { headers }),
        fetch(`/api/analytics/daily?days=${d}`, { headers }),
      ])

      if (!sumResp.ok) throw new Error(`Summary: HTTP ${sumResp.status}`)
      if (!dailyResp.ok) throw new Error(`Daily: HTTP ${dailyResp.status}`)

      const sumData = await sumResp.json()
      const dailyData = await dailyResp.json()

      setSummary(sumData)
      setDaily(dailyData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData(days) }, [days])

  const formatCurrency = (val) => {
    if (val == null) return '$0'
    return '$' + Number(val).toLocaleString('en-US', { maximumFractionDigits: 0 })
  }

  const formatPct = (val) => {
    if (val == null) return '—'
    return val.toFixed(1) + '%'
  }

  const hasSummaryData = summary && summary.data_days > 0
  const totals = hasSummaryData ? summary.totals : {}
  const rates = hasSummaryData ? (summary.rates || {}) : {}

  // Presidents Club: $400K/year target
  const pcTarget = 400000
  const paceTarget = (pcTarget / 365) * days
  const premiumIssued = totals.premium_issued || 0
  const pcPace = paceTarget > 0 ? Math.min((premiumIssued / paceTarget) * 100, 100) : 0

  return (
    <div className="dashboard">
      {/* Days Toggle */}
      <section className="section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 className="section-title" style={{ marginBottom: 0, paddingBottom: 0, borderBottom: 'none' }}>
            Production Analytics
          </h2>
          <div className="days-toggle">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                className={`btn btn-sm ${days === d ? 'btn-toggle-active' : ''}`}
                onClick={() => setDays(d)}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
      </section>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading ? (
        <section className="section">
          <p className="loading-text">Loading...</p>
        </section>
      ) : !hasSummaryData ? (
        <section className="section">
          <p className="no-results" style={{ textAlign: 'center' }}>No production data logged yet.</p>
        </section>
      ) : (
        <>
          {/* Summary Stats */}
          <section className="section">
            <h2 className="section-title">Summary — {days} Days</h2>
            <div className="stat-row">
              <div className="stat-box">
                <span className="stat-label">Dials</span>
                <span className="stat-value">{totals.dials || 0}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Contacts</span>
                <span className="stat-value">{totals.contacts || 0}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Appts Set</span>
                <span className="stat-value">{totals.appointments_set || 0}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Appts Kept</span>
                <span className="stat-value">{totals.appointments_kept || 0}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Closes</span>
                <span className="stat-value">{totals.closes || 0}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Premium Submitted</span>
                <span className="stat-value">{formatCurrency(totals.premium_submitted)}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Premium Issued</span>
                <span className="stat-value">{formatCurrency(totals.premium_issued)}</span>
              </div>
            </div>
          </section>

          {/* Conversion Rates */}
          <section className="section">
            <h2 className="section-title">Conversion Rates</h2>
            <div className="stat-row">
              <div className="stat-box">
                <span className="stat-label">Contact Rate</span>
                <span className="stat-value">{formatPct(rates.contact_rate)}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Appt Rate</span>
                <span className="stat-value">{formatPct(rates.appt_rate)}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Close Rate</span>
                <span className="stat-value">{formatPct(rates.close_rate)}</span>
              </div>
            </div>
          </section>

          {/* Presidents Club Progress */}
          <section className="section">
            <h2 className="section-title">Presidents Club Pace</h2>
            <p className="section-desc">
              Target: $400,000/year issued premium
            </p>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${pcPace}%` }} />
            </div>
            <p className="progress-label">
              {formatCurrency(premiumIssued)} / {formatCurrency(paceTarget)} — {pcPace.toFixed(1)}% of pace
            </p>
          </section>

          {/* Daily Breakdown */}
          <section className="section">
            <h2 className="section-title">Daily Breakdown</h2>
            {daily && daily.data && daily.data.length > 0 ? (
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Dials</th>
                    <th>Contacts</th>
                    <th>Appt Set</th>
                    <th>Appt Kept</th>
                    <th>Closes</th>
                    <th>Premium</th>
                  </tr>
                </thead>
                <tbody>
                  {daily.data.map((row, idx) => (
                    <tr key={idx}>
                      <td>{row.date}</td>
                      <td>{row.dials}</td>
                      <td>{row.contacts}</td>
                      <td>{row.appointments_set}</td>
                      <td>{row.appointments_kept}</td>
                      <td>{row.closes}</td>
                      <td>{formatCurrency(row.premium_submitted)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-results">No daily data available.</p>
            )}
          </section>
        </>
      )}
    </div>
  )
}

export default Analytics
