import { CertificateStatus as CertStatus } from '../../types/launcher'
import './CertificateStatus.css'

interface CertificateStatusProps {
  status: CertStatus
  visible: boolean
}

const STATUS_CONFIG: Record<CertStatus, { icon: string; message: string }> = {
  unknown: { icon: '🔒', message: 'Certificate not yet verified' },
  checking: { icon: '⏳', message: 'Checking certificate...' },
  accepted: { icon: '✅', message: 'Certificate accepted' },
  pending: { icon: '⚠️', message: 'Please accept the certificate in the new tab, then click Launch again' }
}

export function CertificateStatus({ status, visible }: CertificateStatusProps) {
  if (!visible) return null

  const config = STATUS_CONFIG[status]

  return (
    <div className={`cert-status ${status}`}>
      <span>{config.icon} {config.message}</span>
    </div>
  )
}
