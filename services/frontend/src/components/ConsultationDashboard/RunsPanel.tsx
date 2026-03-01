import { Run } from '../../types/consultation'
import { Pagination } from './Pagination'

interface RunsPanelProps {
  runs: Run[]
  selectedRun: string | null
  runsPage: number
  totalRunPages: number
  onSelectRun: (runUuid: string) => void
  onDeleteRun: (runUuid: string) => void
  onPageChange: (page: number) => void
}

export function RunsPanel({
  runs, selectedRun, runsPage, totalRunPages,
  onSelectRun, onDeleteRun, onPageChange,
}: RunsPanelProps) {
  return (
    <>
      <h2 style={{ marginTop: 0, color: '#cccccc', fontSize: '16px' }}>Runs</h2>

      {runs.length === 0 ? (
        <p style={{ color: '#808080' }}>No runs yet...</p>
      ) : (
        <>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {runs.map((r) => (
              <div
                key={r.run_uuid}
                onClick={() => onSelectRun(r.run_uuid)}
                style={{
                  padding: '0.6rem',
                  marginBottom: '0.4rem',
                  background: selectedRun === r.run_uuid ? '#0078d4' : '#2d2d2d',
                  color: selectedRun === r.run_uuid ? '#fff' : '#cccccc',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  overflowWrap: 'break-word',
                  wordBreak: 'break-word',
                  border: '1px solid #3c3c3c',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.4rem' }}>
                  <span style={{ overflowWrap: 'break-word', wordBreak: 'break-word', minWidth: 0 }}>{r.run_uuid}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDeleteRun(r.run_uuid) }}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: selectedRun === r.run_uuid ? '#ffb4ab' : '#c42b1c',
                      fontSize: '0.85rem', padding: '0 0.2rem', flexShrink: 0,
                    }}
                    title="Delete run"
                  >
                    ✕
                  </button>
                </div>
                <div style={{ fontSize: '0.7rem', color: selectedRun === r.run_uuid ? '#ccc' : '#808080' }}>
                  {new Date(r.run_datetime).toLocaleString()}
                </div>
              </div>
            ))}
          </div>

          <Pagination
            page={runsPage}
            totalPages={totalRunPages}
            onPrev={() => onPageChange(runsPage - 1)}
            onNext={() => onPageChange(runsPage + 1)}
          />
        </>
      )}
    </>
  )
}
