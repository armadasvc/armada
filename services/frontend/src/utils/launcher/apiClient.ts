import { LaunchPayload, LaunchResult } from '../../types/launcher'

/**
 * Build FormData for launch request
 */
function buildFormData(payload: LaunchPayload): FormData {
  const { configTemplate, configTune, dataJob, dataAgent, requirementsTxt } = payload

  const formData = new FormData()

  formData.append(
    'configtemplate',
    new Blob([JSON.stringify(configTemplate)], { type: 'application/json' }),
    'configdict.json'
  )

  formData.append(
    'configtune',
    new Blob([JSON.stringify(configTune)], { type: 'application/json' }),
    'config_local.json'
  )

  formData.append(
    'data_job',
    new Blob([dataJob], { type: 'text/csv' }),
    'data_job.csv'
  )

  formData.append(
    'data_agent',
    new Blob([dataAgent], { type: 'text/csv' }),
    'data_agent.csv'
  )

  if (requirementsTxt) {
    formData.append(
      'requirements_txt',
      new Blob([requirementsTxt], { type: 'text/plain' }),
      'requirements.txt'
    )
  }

  return formData
}

/**
 * Parse error message and provide helpful context
 */
function parseErrorMessage(error: unknown): string {
  const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'

  // Detect SSL/certificate errors
  if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
    return `Network error: ${errorMessage}

This is likely a SSL certificate issue. For self-signed certificates:
1. Click "Accept Cert" button to open the API URL
2. Accept the browser security warning
3. Return here and try again`
  }

  return errorMessage
}

/**
 * Send the launch request to the API
 */
export async function sendLaunchRequest(payload: LaunchPayload): Promise<LaunchResult> {
  const { url } = payload

  const formData = buildFormData(payload)

  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData
    })

    const text = await response.text()

    if (response.ok) {
      return { success: true, message: text }
    } else {
      return { success: false, message: `Error ${response.status}: ${text}` }
    }
  } catch (error) {
    return {
      success: false,
      message: parseErrorMessage(error)
    }
  }
}
