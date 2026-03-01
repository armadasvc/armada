interface PaginationProps {
  page: number
  totalPages: number
  onPrev: () => void
  onNext: () => void
}

export function Pagination({ page, totalPages, onPrev, onNext }: PaginationProps) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      paddingTop: '0.5rem', borderTop: '1px solid #3c3c3c', fontSize: '0.8rem',
    }}>
      <button
        onClick={onPrev}
        disabled={page <= 1}
        style={{
          cursor: page <= 1 ? 'not-allowed' : 'pointer',
          background: '#3c3c3c', border: 'none', color: '#cccccc',
          padding: '4px 8px', borderRadius: '3px',
        }}
      >
        Prev
      </button>
      <span style={{ color: '#808080' }}>{page} / {totalPages}</span>
      <button
        onClick={onNext}
        disabled={page >= totalPages}
        style={{
          cursor: page >= totalPages ? 'not-allowed' : 'pointer',
          background: '#3c3c3c', border: 'none', color: '#cccccc',
          padding: '4px 8px', borderRadius: '3px',
        }}
      >
        Next
      </button>
    </div>
  )
}
