from pydantic import BaseModel


class MessageResponse(BaseModel):
    run_uuid: str


class ErrorResponse(BaseModel):
    detail: str
