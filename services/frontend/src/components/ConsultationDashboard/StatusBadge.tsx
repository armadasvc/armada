interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span style={{
      fontSize: '0.7rem',
      padding: '0.1rem 0.4rem',
      borderRadius: '3px',
      background: status === 'Running' ? '#0e4429' : '#3c3c3c',
      color: status === 'Running' ? '#4ec9b0' : '#808080',
      flexShrink: 0,
    }}>{status}</span>
  )
}
