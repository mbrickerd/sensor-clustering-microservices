
from pydantic import BaseModel
from typing import Any


class TrainingRequest(BaseModel):
    parameters: dict[str, Any] | None = None
    

class TrainingResponse(BaseModel):
    job_id: str
    status: str
    message: str