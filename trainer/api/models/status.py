from pydantic import BaseModel


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: str | None = None
    error: str | None = None