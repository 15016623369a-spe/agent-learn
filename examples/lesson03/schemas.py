from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ReportRequest(BaseModel):
    requirement: str = Field(min_length=1, max_length=2000)

    @field_validator("requirement")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("requirement 不能只有空白")
        return value


class ReportResponse(BaseModel):
    summary: str
    mode: Literal["llm"] = "llm"
    request_id: str


class MeetingRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)

    @field_validator("topic")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("topic 不能只有空白")
        return value


class MeetingResponse(BaseModel):
    agenda: str
    mode: Literal["llm"] = "llm"
    request_id: str
