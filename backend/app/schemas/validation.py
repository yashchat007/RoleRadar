from pydantic import BaseModel


class ValidationOut(BaseModel):
    passed: bool
    message: str
    jobs_sampled: int = 0
