from datetime import datetime
from pydantic import BaseModel


class EventCreate(BaseModel):
    event_content: str
    job_uuid: str
    event_datetime: str
    event_status: str = "Running"
    event_uuid: str | None = None


class EventUpdateStatus(BaseModel):
    event_uuid: str
    event_status: str


class EventOut(BaseModel):
    event_uuid: str
    event_content: str
    job_uuid: str
    event_datetime: datetime | None = None
    event_status: str = "Running"
