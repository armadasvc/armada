import { v4 as uuidv4 } from 'uuid'

/**
 * Replace $env_ placeholders with values from configTune
 */
export function replaceEnvValues(
  configTemplate: unknown,
  configTune: Record<string, unknown>
): unknown {
  if (configTemplate === null || configTemplate === undefined) {
    return configTemplate
  }

  if (Array.isArray(configTemplate)) {
    return configTemplate.map(item => replaceEnvValues(item, configTune))
  }

  if (typeof configTemplate === 'object') {
    const result: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(configTemplate as Record<string, unknown>)) {
      result[key] = replaceEnvValues(value, configTune)
    }
    return result
  }

  if (typeof configTemplate === 'string' && configTemplate.startsWith('$env_')) {
    const envKey = configTemplate.slice(5) // Remove '$env_' prefix
    return configTune[envKey] ?? configTemplate
  }

  return configTemplate
}

/**
 * Add UUID and code to config for run tracking
 */
export function addUuidAndCodeToConfig(
  config: Record<string, unknown>,
  code: string
): { config: Record<string, unknown>; runId: string } {
  const runId = uuidv4()
  const result = JSON.parse(JSON.stringify(config)) // Deep clone

  if (result.default_agent_message && typeof result.default_agent_message === 'object') {
    (result.default_agent_message as Record<string, unknown>).code = code;
    (result.default_agent_message as Record<string, unknown>).run_id = runId
  }

  if (result.default_job_message && typeof result.default_job_message === 'object') {
    (result.default_job_message as Record<string, unknown>).code = code;
    (result.default_job_message as Record<string, unknown>).run_id = runId
  }

  if (result.run_message && typeof result.run_message === 'object') {
    (result.run_message as Record<string, unknown>).run_id = runId
  }

  return { config: result, runId }
}

/**
 * Process config files: replace env values and add UUID/code
 */
export function processConfig(
  configTemplateContent: string,
  configTuneContent: string,
  scriptCode: string
): { config: Record<string, unknown>; runId: string } {
  const configTemplate = JSON.parse(configTemplateContent) as Record<string, unknown>
  const configTune = JSON.parse(configTuneContent) as Record<string, unknown>

  const replaced = replaceEnvValues(configTemplate, configTune) as Record<string, unknown>
  const { config, runId } = addUuidAndCodeToConfig(replaced, scriptCode)

  return { config, runId }
}
