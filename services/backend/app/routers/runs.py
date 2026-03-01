"""
Runs router — GET (paginated), POST.
"""

from fastapi import APIRouter, Query
from app.db import db
from app.ws import ws_manager
from app.schemas.runs import RunCreate, RunOut, RunPage

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/", response_model=RunPage)
async def get_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100),
):
    offset = (page - 1) * page_size

    count_row = await db.fetchone("SELECT COUNT(*) AS total FROM armada_runs")
    rows = await db.fetchall(
        "SELECT run_uuid, run_datetime FROM armada_runs"
        " ORDER BY run_datetime DESC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY",
        (offset, page_size),
    )

    return {"runs": rows, "total": count_row["total"], "page": page, "page_size": page_size}


@router.post("/", response_model=RunOut, status_code=201)
async def create_run(data: RunCreate):
    await db.execute(
        " INSERT INTO armada_runs (run_uuid, run_datetime) VALUES (%s, %s)",
        (data.run_uuid, data.run_datetime),
    )

    run_data = {"run_uuid": data.run_uuid, "run_datetime": data.run_datetime}
    await ws_manager.broadcast({"type": "new_run", "data": run_data})

    return run_data


@router.delete("/{run_uuid}")
async def delete_run(run_uuid: str):
    # Delete events linked to jobs of this run
    await db.execute(
        "DELETE FROM armada_events WHERE job_uuid IN (SELECT job_uuid FROM armada_jobs WHERE run_uuid = %s)",
        (run_uuid,),
    )
    # Delete jobs of this run
    await db.execute("DELETE FROM armada_jobs WHERE run_uuid = %s", (run_uuid,))
    # Delete the run
    await db.execute("DELETE FROM armada_runs WHERE run_uuid = %s", (run_uuid,))

    await ws_manager.broadcast({"type": "delete_run", "data": {"run_uuid": run_uuid}})

    return {"ok": True}
