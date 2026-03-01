from datetime import datetime
from pydantic import BaseModel


class JobCreate(BaseModel):
    run_uuid: str
    job_datetime: str
    job_associated_agent: str = "Unknown"
    job_status: str = "Running"
    job_uuid: str | None = None


class JobUpdateStatus(BaseModel):
    job_uuid: str
    job_status: str


class JobOut(BaseModel):
    job_uuid: str
    run_uuid: str
    job_datetime: datetime | None = None
    job_associated_agent: str = "Unknown"
    job_status: str = "Running"


class JobPage(BaseModel):
    jobs: list[JobOut]
    total: int
    page: int
    page_size: int
