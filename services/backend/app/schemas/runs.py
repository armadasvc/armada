from datetime import datetime
from pydantic import BaseModel


class RunCreate(BaseModel):
    run_uuid: str
    run_datetime: str


class RunOut(BaseModel):
    run_uuid: str
    run_datetime: datetime | None = None


class RunPage(BaseModel):
    runs: list[RunOut]
    total: int
    page: int
    page_size: int
