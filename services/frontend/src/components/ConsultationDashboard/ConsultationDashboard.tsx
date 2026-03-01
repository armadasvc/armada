import React from 'react'
import { useConsultationDashboard } from '../../hooks/useConsultationDashboard'
import { RunsPanel } from './RunsPanel'
import { JobsPanel } from './JobsPanel'
import { EventsPanel } from './EventsPanel'

const panelStyle: React.CSSProperties = {
  flex: 1,
  borderRight: '1px solid #3c3c3c',
  padding: '1rem',
  overflowY: 'auto',
  backgroundColor: '#1e1e1e',
  color: '#d4d4d4',
  minWidth: 0,
}

export function ConsultationDashboard() {
  const {
    runs, runsPage, totalRunPages, selectedRun,
    jobs, jobsPage, totalJobPages, selectedJob,
    events,
    fetchRunsPage, fetchJobsPage, selectRun, deleteRun, selectJob,
  } = useConsultationDashboard()

  return (
    <div style={{ display: 'flex', height: '100%', fontFamily: 'sans-serif' }}>
      <div style={{ ...panelStyle, display: 'flex', flexDirection: 'column' }}>
        <RunsPanel
          runs={runs}
          selectedRun={selectedRun}
          runsPage={runsPage}
          totalRunPages={totalRunPages}
          onSelectRun={selectRun}
          onDeleteRun={deleteRun}
          onPageChange={fetchRunsPage}
        />
      </div>

      <div style={{ ...panelStyle, display: 'flex', flexDirection: 'column' }}>
        <JobsPanel
          selectedRun={selectedRun}
          jobs={jobs}
          selectedJob={selectedJob}
          jobsPage={jobsPage}
          totalJobPages={totalJobPages}
          onSelectJob={selectJob}
          onPageChange={fetchJobsPage}
        />
      </div>

      <div style={{ ...panelStyle, borderRight: 'none' }}>
        <EventsPanel selectedJob={selectedJob} events={events} />
      </div>
    </div>
  )
}
