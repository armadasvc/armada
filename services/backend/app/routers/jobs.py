"""
Router jobs — GET, POST.
"""

import uuid
from fastapi import APIRouter, Query
from app.db import db
from app.ws import ws_manager
from app.schemas.jobs import JobCreate, JobOut, JobPage, JobUpdateStatus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/", response_model=JobPage)
async def get_jobs(
    run_uuid: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100),
):
    offset = (page - 1) * page_size

    if run_uuid:
        count_row = await db.fetchone(
            "SELECT COUNT(*) AS total FROM armada_jobs WHERE run_uuid = %s",
            (run_uuid,),
        )
        rows = await db.fetchall(
            "SELECT job_uuid, run_uuid, job_datetime,"
            " ISNULL(job_associated_agent, 'Unknown') AS job_associated_agent,"
            " ISNULL(job_status, 'Running') AS job_status"
            " FROM armada_jobs WHERE run_uuid = %s"
            " ORDER BY job_datetime DESC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY",
            (run_uuid, offset, page_size),
        )
    else:
        count_row = await db.fetchone("SELECT COUNT(*) AS total FROM armada_jobs")
        rows = await db.fetchall(
            "SELECT job_uuid, run_uuid, job_datetime,"
            " ISNULL(job_associated_agent, 'Unknown') AS job_associated_agent,"
            " ISNULL(job_status, 'Running') AS job_status"
            " FROM armada_jobs"
            " ORDER BY job_datetime DESC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY",
            (offset, page_size),
        )

    return {"jobs": rows, "total": count_row["total"], "page": page, "page_size": page_size}


@router.post("/", response_model=JobOut, status_code=201)
async def create_job(data: JobCreate):
    job_uuid = data.job_uuid or str(uuid.uuid4())

    await db.execute(
        "INSERT INTO armada_jobs (job_uuid, run_uuid, job_datetime, job_associated_agent, job_status)"
        " VALUES (%s, %s, %s, %s, %s)",
        (job_uuid, data.run_uuid, data.job_datetime, data.job_associated_agent, data.job_status),
    )

    job_data = {
        "job_uuid": job_uuid,
        "run_uuid": data.run_uuid,
        "job_datetime": data.job_datetime,
        "job_associated_agent": data.job_associated_agent,
        "job_status": data.job_status,
    }
    await ws_manager.broadcast({"type": "new_job", "data": job_data})

    return job_data


@router.patch("/status")
async def update_job_status(data: JobUpdateStatus):
    await db.execute(
        "UPDATE armada_jobs SET job_status = %s WHERE job_uuid = %s",
        (data.job_status, data.job_uuid),
    )

    await ws_manager.broadcast({"type": "update_job_status", "data": {
        "job_uuid": data.job_uuid,
        "job_status": data.job_status,
    }})

    return {"ok": True}
