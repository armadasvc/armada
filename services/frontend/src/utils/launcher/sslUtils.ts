import { CertificateStatus } from '../../types/launcher'

/**
 * Test SSL connection to check if certificate is accepted
 */
export async function testSslConnection(
  url: string,
  onStatusChange: (status: CertificateStatus) => void
): Promise<boolean> {
  if (!url) return false

  onStatusChange('checking')

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)

    // Try with no-cors mode first (won't throw on SSL issues but response is opaque)
    await fetch(url, {
      method: 'HEAD',
      mode: 'no-cors',
      signal: controller.signal
    })

    clearTimeout(timeoutId)
    onStatusChange('accepted')
    return true
  } catch {
    // Try with regular mode to see if it's really SSL
    try {
      await fetch(url, { method: 'HEAD' })
      onStatusChange('accepted')
      return true
    } catch {
      onStatusChange('pending')
      return false
    }
  }
}

/**
 * Open URL in new tab for certificate acceptance
 */
export function openCertificateAcceptance(url: string): void {
  window.open(url, '_blank')
}

/**
 * Check if URL uses HTTPS
 */
export function isHttpsUrl(url: string): boolean {
  return url.startsWith('https://')
}

/**
 * Get user-friendly message for certificate acceptance
 */
export function getCertificateAcceptanceMessage(): string {
  return `Certificate acceptance window opened.

1. Accept the certificate in the new tab (click "Advanced" → "Proceed")
2. You may see a 401 error - that's OK!
3. Close that tab and click "Launch" again`
}
