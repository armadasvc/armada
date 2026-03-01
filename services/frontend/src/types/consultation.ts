export const PAGE_SIZE = 5
export const API_BASE = '/tracking'

export interface Run {
  run_uuid: string
  run_datetime: string
}

export interface Job {
  job_uuid: string
  run_uuid: string
  job_datetime: string
  job_associated_agent: string
  job_status: string
}

export interface Event {
  event_uuid: string
  event_content: string
  job_uuid: string
  event_datetime: string
  event_status: string
}
