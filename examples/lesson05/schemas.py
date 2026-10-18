from typing import Literal

from pydantic import BaseModel, Field, field_validator

TaskType = Literal["report", "meeting", "email"]
TaskStatus = Literal["running", "succeeded", "failed"]


class TaskCreate(BaseModel):
    task_type: TaskType
    requirement: str = Field(min_length=1, max_length=1000)

    @field_validator("requirement")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("requirement 不能只有空白")
        return value


class TaskRecord(BaseModel):
    task_id: str
    task_type: TaskType
    status: TaskStatus
    result: str | None = None
    error_code: int | None = None
    error_message: str | None = None


class TaskResponse(BaseModel):
    request_id: str
    task: TaskRecord
