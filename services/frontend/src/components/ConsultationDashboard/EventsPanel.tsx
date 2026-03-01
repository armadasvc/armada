import { Event } from '../../types/consultation'
import { StatusBadge } from './StatusBadge'

interface EventsPanelProps {
  selectedJob: string | null
  events: Event[]
}

export function EventsPanel({ selectedJob, events }: EventsPanelProps) {
  if (!selectedJob) {
    return <p style={{ color: '#808080' }}>Select a job to view its events</p>
  }

  return (
    <>
      <h2 style={{ marginTop: 0, color: '#cccccc', fontSize: '16px' }}>
        Events — {selectedJob.slice(0, 8)}...
      </h2>
      {events.length === 0 ? (
        <p style={{ color: '#808080' }}>No events for this job...</p>
      ) : (
        events.map((ev) => (
          <div
            key={ev.event_uuid}
            style={{
              padding: '0.75rem',
              marginBottom: '0.5rem',
              background: '#2d2d2d',
              borderLeft: '3px solid #0078d4',
              borderRadius: '2px',
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.4rem' }}>
              <span style={{ overflowWrap: 'break-word', wordBreak: 'break-word', minWidth: 0 }}>{ev.event_content}</span>
              <StatusBadge status={ev.event_status} />
            </div>
            <div style={{ fontSize: '0.75rem', color: '#808080', marginTop: '0.25rem' }}>
              {new Date(ev.event_datetime).toLocaleString()}
            </div>
          </div>
        ))
      )}
    </>
  )
}
