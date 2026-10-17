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

from typing import Literal


class DocumentRequest(BaseModel):
    document_name: str = Field(min_length=1, max_length=200)
    instruction: str = Field(min_length=1, max_length=2000)


class DocumentResponse(BaseModel):
    document_name: str
    summary: str
    mode: Literal["mock"]


def mock_document_preview(
    document_name: str,
    instruction: str,
) -> str:
    return f"收到文档任务：对《{document_name}》执行“{instruction}”。"


@app.post("/document-preview", response_model=DocumentResponse)
def preview_document(request: DocumentRequest):
    result = mock_document_preview(
        request.document_name,
        request.instruction,
    )

    return DocumentResponse(
        document_name=request.document_name,
        summary=result,
        mode="mock",
    )