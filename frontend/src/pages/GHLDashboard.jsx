import { useState, useEffect } from 'react'

const API = '/api/ghl-dashboard'

const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'compliance', label: 'Compliance' },
  { key: 'pipelines', label: 'Pipelines' },
  { key: 'activity', label: 'Activity' },
]

function useAPI(path, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`${API}${path}`)
      .then(r => { if (!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.json() })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return { data, loading, error }
}

function Card({ label, value, sub }) {
  return (
    <div style={{ background: 'var(--bg-secondary, #1a1a2e)', border: '1px solid var(--border, #2a2a3e)', borderRadius: 6, padding: '1rem 1.25rem', minWidth: 140 }}>
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #888)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text, #e0e0e0)' }}>{value ?? '—'}</div>
      {sub && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #888)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function Loading() {
  return <div style={{ padding: '2rem', color: 'var(--text-muted, #888)', fontSize: '0.85rem' }}>Loading...</div>
}

function ErrorMsg({ msg }) {
  return <div style={{ padding: '2rem', color: '#e55', fontSize: '0.85rem' }}>Error: {msg}</div>
}

function OverviewTab() {
  const { data, loading, error } = useAPI('/summary')
  if (loading) return <Loading />
  if (error) return <ErrorMsg msg={error} />
  return (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', padding: '1.25rem 0' }}>
      <Card label="Total Contacts" value={data?.contact_count} />
      <Card label="Pipelines" value={data?.pipeline_count} />
      <Card label="Compliance Score" value={data?.compliance_score != null ? `${data.compliance_score}%` : '—'} sub="last run" />
      <Card label="Last Sync" value={data?.last_sync ? new Date(data.last_sync).toLocaleTimeString() : 'Never'} />
    </div>
  )
}

function ContactsTab() {
  const [page, setPage] = useState(1)
  const { data, loading, error } = useAPI(`/contacts?limit=50&page=${page}`, [page])
  if (loading) return <Loading />
  if (error) return <ErrorMsg msg={error} />
  const contacts = data?.contacts || []
  return (
    <div style={{ padding: '1.25rem 0' }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #888)', marginBottom: '0.75rem' }}>
        {data?.total ?? contacts.length} contacts
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border, #2a2a3e)', color: 'var(--text-muted, #888)' }}>
              {['Name', 'Email', 'Phone', 'Tags', 'DND'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '0.4rem 0.75rem', fontWeight: 500 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {contacts.length === 0 && (
              <tr><td colSpan={5} style={{ padding: '1rem 0.75rem', color: 'var(--text-muted, #888)' }}>No contacts found.</td></tr>
            )}
            {contacts.map((c, i) => (
              <tr key={c.id || i} style={{ borderBottom: '1px solid var(--border, #2a2a3e)' }}>
                <td style={{ padding: '0.4rem 0.75rem' }}>{c.contactName || c.firstName ? `${c.firstName || ''} ${c.lastName || ''}`.trim() : '—'}</td>
                <td style={{ padding: '0.4rem 0.75rem', color: 'var(--text-muted, #888)' }}>{c.email || '—'}</td>
                <td style={{ padding: '0.4rem 0.75rem', color: 'var(--text-muted, #888)' }}>{c.phone || '—'}</td>
                <td style={{ padding: '0.4rem 0.75rem', color: 'var(--text-muted, #888)', fontSize: '0.72rem' }}>
                  {Array.isArray(c.tags) ? c.tags.slice(0, 3).join(', ') || '—' : '—'}
                </td>
                <td style={{ padding: '0.4rem 0.75rem', color: c.dnd ? '#e55' : 'var(--text-muted, #888)' }}>
                  {c.dnd ? 'DND' : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
          style={{ padding: '0.3rem 0.75rem', fontSize: '0.78rem', cursor: page === 1 ? 'default' : 'pointer', opacity: page === 1 ? 0.4 : 1 }}>
          Prev
        </button>
        <span style={{ fontSize: '0.78rem', padding: '0.3rem 0.5rem', color: 'var(--text-muted, #888)' }}>Page {page}</span>
        <button onClick={() => setPage(p => p + 1)}
          style={{ padding: '0.3rem 0.75rem', fontSize: '0.78rem', cursor: 'pointer' }}>
          Next
        </button>
      </div>
    </div>
  )
}

function ComplianceTab() {
  const { data, loading, error } = useAPI('/contacts/compliance')
  if (loading) return <Loading />
  if (error) return <ErrorMsg msg={error} />
  const issues = data?.issues || []
  return (
    <div style={{ padding: '1.25rem 0' }}>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <Card label="Total Checked" value={data?.total} />
        <Card label="Compliant" value={data?.compliant} sub={data?.total ? `${Math.round((data.compliant / data.total) * 100)}%` : ''} />
        <Card label="Issues" value={data?.total != null && data?.compliant != null ? data.total - data.compliant : '—'} />
      </div>
      {issues.length > 0 && (
        <div>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted, #888)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Issues
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border, #2a2a3e)', color: 'var(--text-muted, #888)' }}>
                  {['Contact', 'Flags'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '0.4rem 0.75rem', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {issues.map((issue, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border, #2a2a3e)' }}>
                    <td style={{ padding: '0.4rem 0.75rem' }}>{issue.name || issue.contact_id || '—'}</td>
                    <td style={{ padding: '0.4rem 0.75rem', color: '#e55', fontSize: '0.72rem' }}>
                      {Object.entries(issue)
                        .filter(([k, v]) => ['has_phone', 'has_email', 'has_tag', 'not_dnd', 'has_activity_90d', 'has_first_name'].includes(k) && !v)
                        .map(([k]) => k.replace(/_/g, ' '))
                        .join(', ') || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function PipelinesTab() {
  const { data, loading, error } = useAPI('/pipelines')
  const [selectedPipeline, setSelectedPipeline] = useState(null)
  const { data: opps, loading: oppsLoading } = useAPI(
    selectedPipeline ? `/pipelines/${selectedPipeline}/opportunities` : null,
    [selectedPipeline]
  )
  if (loading) return <Loading />
  if (error) return <ErrorMsg msg={error} />
  const pipelines = data?.pipelines || []
  return (
    <div style={{ padding: '1.25rem 0' }}>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        {pipelines.map(p => (
          <button key={p.id} onClick={() => setSelectedPipeline(p.id)}
            style={{
              padding: '0.35rem 0.9rem', fontSize: '0.78rem', cursor: 'pointer', borderRadius: 4,
              background: selectedPipeline === p.id ? 'var(--accent, #4f6ef7)' : 'var(--bg-secondary, #1a1a2e)',
              color: selectedPipeline === p.id ? '#fff' : 'var(--text, #e0e0e0)',
              border: '1px solid var(--border, #2a2a3e)',
            }}>
            {p.name}
          </button>
        ))}
        {pipelines.length === 0 && <div style={{ color: 'var(--text-muted, #888)', fontSize: '0.85rem' }}>No pipelines found.</div>}
      </div>
      {selectedPipeline && (
        <div>
          {oppsLoading ? <Loading /> : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border, #2a2a3e)', color: 'var(--text-muted, #888)' }}>
                  {['Name', 'Stage', 'Value', 'Status'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '0.4rem 0.75rem', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(opps?.opportunities || []).map((o, i) => (
                  <tr key={o.id || i} style={{ borderBottom: '1px solid var(--border, #2a2a3e)' }}>
                    <td style={{ padding: '0.4rem 0.75rem' }}>{o.name || '—'}</td>
                    <td style={{ padding: '0.4rem 0.75rem', color: 'var(--text-muted, #888)' }}>{o.pipelineStageId || o.stage?.name || '—'}</td>
                    <td style={{ padding: '0.4rem 0.75rem' }}>{o.monetaryValue ? `$${o.monetaryValue.toLocaleString()}` : '—'}</td>
                    <td style={{ padding: '0.4rem 0.75rem', color: 'var(--text-muted, #888)' }}>{o.status || '—'}</td>
                  </tr>
                ))}
                {(opps?.opportunities || []).length === 0 && (
                  <tr><td colSpan={4} style={{ padding: '1rem 0.75rem', color: 'var(--text-muted, #888)' }}>No opportunities in this pipeline.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

function ActivityTab() {
  const { data, loading, error } = useAPI('/conversations')
  if (loading) return <Loading />
  if (error) return <ErrorMsg msg={error} />
  const convos = data?.conversations || []
  return (
    <div style={{ padding: '1.25rem 0' }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #888)', marginBottom: '0.75rem' }}>
        {convos.length} recent conversations
      </div>
      {convos.length === 0 && <div style={{ color: 'var(--text-muted, #888)', fontSize: '0.85rem' }}>No conversations found.</div>}
      {convos.map((c, i) => (
        <div key={c.id || i} style={{
          borderBottom: '1px solid var(--border, #2a2a3e)', padding: '0.6rem 0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'
        }}>
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 500 }}>{c.contactName || c.fullName || 'Unknown'}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #888)', marginTop: 2 }}>
              {c.lastMessage || c.type || '—'}
            </div>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #888)', flexShrink: 0, marginLeft: '1rem' }}>
            {c.lastMessageDate ? new Date(c.lastMessageDate).toLocaleDateString() : '—'}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function GHLDashboard() {
  const [tab, setTab] = useState('overview')
  const [syncing, setSyncing] = useState(false)

  const triggerSync = async () => {
    setSyncing(true)
    try {
      await fetch(`${API}/sync/trigger`, { method: 'POST' })
    } finally {
      setTimeout(() => setSyncing(false), 2000)
    }
  }

  return (
    <div style={{ padding: '1.5rem', maxWidth: 1100 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>GHL Intel</h2>
        <button onClick={triggerSync} disabled={syncing}
          style={{ padding: '0.35rem 0.9rem', fontSize: '0.78rem', cursor: syncing ? 'default' : 'pointer', opacity: syncing ? 0.6 : 1, borderRadius: 4 }}>
          {syncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border, #2a2a3e)', marginBottom: 0 }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{
              padding: '0.5rem 1rem', fontSize: '0.82rem', cursor: 'pointer', background: 'none',
              border: 'none', borderBottom: tab === t.key ? '2px solid var(--accent, #4f6ef7)' : '2px solid transparent',
              color: tab === t.key ? 'var(--text, #e0e0e0)' : 'var(--text-muted, #888)',
              fontWeight: tab === t.key ? 600 : 400, marginBottom: -1,
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <OverviewTab />}
      {tab === 'contacts' && <ContactsTab />}
      {tab === 'compliance' && <ComplianceTab />}
      {tab === 'pipelines' && <PipelinesTab />}
      {tab === 'activity' && <ActivityTab />}
    </div>
  )
}
