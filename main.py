from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="办公 Agent 学习服务")


class ReportRequest(BaseModel):
    requirement: str = Field(min_length=1, max_length=2000)


class ReportResponse(BaseModel):
    summary: str
    mode: str


def mock_report(requirement: str) -> str:
    return f"收到报告任务：{requirement}。后续将检索指标口径并计算数据。"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/report-preview", response_model=ReportResponse)
def preview_report(request: ReportRequest):
    result = mock_report(request.requirement)
    return ReportResponse(summary=result, mode="mock")
