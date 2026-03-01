import { Job } from '../../types/consultation'
import { Pagination } from './Pagination'
import { StatusBadge } from './StatusBadge'

interface JobsPanelProps {
  selectedRun: string | null
  jobs: Job[]
  selectedJob: string | null
  jobsPage: number
  totalJobPages: number
  onSelectJob: (jobUuid: string) => void
  onPageChange: (runUuid: string, page: number) => void
}

export function JobsPanel({
  selectedRun, jobs, selectedJob, jobsPage, totalJobPages,
  onSelectJob, onPageChange,
}: JobsPanelProps) {
  return (
    <>
      <h2 style={{ marginTop: 0, color: '#cccccc', fontSize: '16px' }}>Jobs</h2>

      {!selectedRun ? (
        <p style={{ color: '#808080' }}>Select a run</p>
      ) : jobs.length === 0 ? (
        <p style={{ color: '#808080' }}>No jobs...</p>
      ) : (
        <>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {jobs.map((j) => (
              <div
                key={j.job_uuid}
                onClick={() => onSelectJob(j.job_uuid)}
                style={{
                  padding: '0.6rem',
                  marginBottom: '0.4rem',
                  background: selectedJob === j.job_uuid ? '#0078d4' : '#2d2d2d',
                  color: selectedJob === j.job_uuid ? '#fff' : '#cccccc',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  overflowWrap: 'break-word',
                  wordBreak: 'break-word',
                  border: '1px solid #3c3c3c',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.4rem' }}>
                  <span style={{ overflowWrap: 'break-word', wordBreak: 'break-word', minWidth: 0 }}>{j.job_uuid.slice(0, 8)}...</span>
                  <StatusBadge status={j.job_status} />
                </div>
                <div style={{ fontSize: '0.7rem', color: selectedJob === j.job_uuid ? '#ccc' : '#808080', overflowWrap: 'break-word', wordBreak: 'break-word' }}>
                  {j.job_associated_agent} — {new Date(j.job_datetime).toLocaleString()}
                </div>
              </div>
            ))}
          </div>

          <Pagination
            page={jobsPage}
            totalPages={totalJobPages}
            onPrev={() => onPageChange(selectedRun!, jobsPage - 1)}
            onNext={() => onPageChange(selectedRun!, jobsPage + 1)}
          />
        </>
      )}
    </>
  )
}
