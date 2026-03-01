"""
Events router — GET, POST + WebSocket.
"""

import uuid
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from app.db import db
from app.ws import ws_manager
from app.schemas.events import EventCreate, EventOut, EventUpdateStatus

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/", response_model=list[EventOut])
async def get_events(job_uuid: str = Query(None)):
    if job_uuid:
        rows = await db.fetchall(
            "SELECT event_uuid, event_content, job_uuid, event_datetime,"
            " ISNULL(event_status, 'Running') AS event_status"
            " FROM armada_events WHERE job_uuid = %s"
            " ORDER BY event_datetime DESC",
            (job_uuid,),
        )
    else:
        rows = await db.fetchall(
            "SELECT event_uuid, event_content, job_uuid, event_datetime,"
            " ISNULL(event_status, 'Running') AS event_status"
            " FROM armada_events ORDER BY event_datetime DESC"
        )
    return rows


@router.post("/", response_model=EventOut, status_code=201)
async def create_event(data: EventCreate):
    event_uuid = data.event_uuid or str(uuid.uuid4())

    await db.execute(
        "INSERT INTO armada_events (event_uuid, event_content, job_uuid, event_datetime, event_status) VALUES (%s, %s, %s, %s, %s)",
        (event_uuid, data.event_content, data.job_uuid, data.event_datetime, data.event_status),
    )

    event_data = {
        "event_uuid": event_uuid,
        "event_content": data.event_content,
        "job_uuid": data.job_uuid,
        "event_datetime": data.event_datetime,
        "event_status": data.event_status,
    }
    await ws_manager.broadcast({"type": "new_event", "data": event_data})

    return event_data


@router.patch("/status")
async def update_event_status(data: EventUpdateStatus):
    await db.execute(
        "UPDATE armada_events SET event_status = %s WHERE event_uuid = %s",
        (data.event_status, data.event_uuid),
    )

    await ws_manager.broadcast({"type": "update_event_status", "data": {
        "event_uuid": data.event_uuid,
        "event_status": data.event_status,
    }})

    return {"ok": True}


# --- WebSocket: mounted on /ws/events/ (different prefix from the REST router) ---
ws_router = APIRouter()


@ws_router.websocket("/ws/events/")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
