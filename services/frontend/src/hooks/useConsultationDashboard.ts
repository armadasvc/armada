import { useState, useEffect, useRef, useCallback } from 'react'
import { Run, Job, Event, API_BASE, PAGE_SIZE } from '../types/consultation'

function getWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}${API_BASE}/ws/events/`
}

async function fetchJson(url: string): Promise<any> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  return res.json()
}

const WS_RECONNECT_BASE_MS = 1000
const WS_RECONNECT_MAX_MS = 30000

export function useConsultationDashboard() {
  const [runs, setRuns] = useState<Run[]>([])
  const [runsTotal, setRunsTotal] = useState(0)
  const [runsPage, setRunsPage] = useState(1)
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobsTotal, setJobsTotal] = useState(0)
  const [jobsPage, setJobsPage] = useState(1)
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const selectedRunRef = useRef<string | null>(null)
  const selectedJobRef = useRef<string | null>(null)
  const runsPageRef = useRef(1)
  const jobsPageRef = useRef(1)

  useEffect(() => { selectedRunRef.current = selectedRun }, [selectedRun])
  useEffect(() => { selectedJobRef.current = selectedJob }, [selectedJob])
  useEffect(() => { runsPageRef.current = runsPage }, [runsPage])
  useEffect(() => { jobsPageRef.current = jobsPage }, [jobsPage])

  const fetchRunsPage = (page: number) =>
    fetchJson(`${API_BASE}/api/runs/?page=${page}&page_size=${PAGE_SIZE}`)
      .then((data) => {
        setRuns(data.runs)
        setRunsTotal(data.total)
        setRunsPage(page)
      })
      .catch((err) => console.error('Error loading runs:', err))

  const fetchJobsPage = (runUuid: string, page: number) =>
    fetchJson(`${API_BASE}/api/jobs/?run_uuid=${runUuid}&page=${page}&page_size=${PAGE_SIZE}`)
      .then((data) => {
        setJobs(data.jobs)
        setJobsTotal(data.total)
        setJobsPage(page)
      })
      .catch((err) => console.error('Error loading jobs:', err))

  const handleWsMessage = useCallback((e: MessageEvent) => {
    let msg: any
    try {
      msg = JSON.parse(e.data)
    } catch {
      console.error('Malformed WebSocket message:', e.data)
      return
    }

    if (msg.type === 'new_run') {
      setRunsTotal((prev) => prev + 1)
      if (runsPageRef.current === 1) {
        setRuns((prev) => [msg.data as Run, ...prev].slice(0, PAGE_SIZE))
      }
    }

    if (msg.type === 'new_job') {
      if (selectedRunRef.current === msg.data.run_uuid) {
        const page = jobsPageRef.current
        const runUuid = selectedRunRef.current
        fetchJson(`${API_BASE}/api/jobs/?run_uuid=${runUuid}&page=${page}&page_size=${PAGE_SIZE}`)
          .then((data) => {
            setJobs(data.jobs)
            setJobsTotal(data.total)
          })
          .catch((err) => console.error('Error refreshing jobs:', err))
      }
    }

    if (msg.type === 'new_event') {
      if (selectedJobRef.current === msg.data.job_uuid) {
        setEvents((prev) => [msg.data as Event, ...prev])
      }
    }

    if (msg.type === 'update_job_status') {
      setJobs((prev) => prev.map((j) =>
        j.job_uuid === msg.data.job_uuid ? { ...j, job_status: msg.data.job_status } : j
      ))
    }

    if (msg.type === 'delete_run') {
      setRuns((prev) => prev.filter((r) => r.run_uuid !== msg.data.run_uuid))
      setRunsTotal((prev) => Math.max(0, prev - 1))
      if (selectedRunRef.current === msg.data.run_uuid) {
        setSelectedRun(null)
        setJobs([])
        setJobsTotal(0)
        setSelectedJob(null)
        setEvents([])
      }
    }
  }, [])

  useEffect(() => {
    fetchRunsPage(1)

    let ws: WebSocket | null = null
    let reconnectDelay = WS_RECONNECT_BASE_MS
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let disposed = false

    function connect() {
      if (disposed) return
      ws = new WebSocket(getWsUrl())

      ws.onopen = () => {
        reconnectDelay = WS_RECONNECT_BASE_MS
      }

      ws.onmessage = handleWsMessage

      ws.onclose = () => {
        if (disposed) return
        reconnectTimer = setTimeout(() => {
          reconnectDelay = Math.min(reconnectDelay * 2, WS_RECONNECT_MAX_MS)
          connect()
        }, reconnectDelay)
      }
    }

    connect()

    return () => {
      disposed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [handleWsMessage])

  const selectRun = async (runUuid: string) => {
    setSelectedRun(runUuid)
    setSelectedJob(null)
    setEvents([])
    await fetchJobsPage(runUuid, 1)
  }

  const deleteRun = async (runUuid: string) => {
    if (!window.confirm(`Delete run "${runUuid}" and all its jobs/events?`)) return
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runUuid}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    } catch (err) {
      console.error('Error deleting run:', err)
    }
  }

  const selectJob = async (jobUuid: string) => {
    setSelectedJob(jobUuid)
    try {
      setEvents(await fetchJson(`${API_BASE}/api/events/?job_uuid=${jobUuid}`))
    } catch (err) {
      console.error('Error loading events:', err)
    }
  }

  const totalRunPages = Math.max(1, Math.ceil(runsTotal / PAGE_SIZE))
  const totalJobPages = Math.max(1, Math.ceil(jobsTotal / PAGE_SIZE))

  return {
    runs,
    runsPage,
    totalRunPages,
    selectedRun,
    jobs,
    jobsPage,
    totalJobPages,
    selectedJob,
    events,
    fetchRunsPage,
    fetchJobsPage,
    selectRun,
    deleteRun,
    selectJob,
  }
}
