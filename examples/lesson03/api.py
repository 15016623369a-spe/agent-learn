import json
import logging
from time import perf_counter
#假设连续运行三个任务，后来发现其中一个失败了。我们需要知道：
#这个失败响应，对应终端里的哪条记录？
from uuid import uuid4

from fastapi import FastAPI, HTTPException
#有新增修改
from .schemas import MeetingRequest, MeetingResponse, ReportRequest, ReportResponse, EmailRequest, EmailResponse
from .services import generate_meeting, generate_report, generate_email

app = FastAPI(title="办公 Agent 学习服务 · Lesson03 已完成实践")

# 最小控制台日志：每个进程配置一次，不在每个请求里添加 handler。
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("office_agent.lesson03")
logger.setLevel(logging.INFO)


def run_task(task_type: str, generate, user_input: str) -> tuple[str, str]:#元组：有序不可变序列
    """执行传入的业务函数，返回文本与本次任务编号。"""
    request_id = uuid4().hex
    started = perf_counter()
    status_code = 500
    error_type = None
    try:
        text = generate(user_input)
        status_code = 200
        return text, request_id
    except HTTPException as exc:
        status_code = exc.status_code
        error_type = "HTTPException"
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
            headers={"X-Request-ID": request_id},
        ) from None
    except Exception as exc:
        # 仅在这个 HTTP 边界处理意外错误，不公开原始异常文本。
        error_type = type(exc).__name__
        raise HTTPException(
            status_code=500,
            detail="服务内部错误，请根据请求编号排查",
            headers={"X-Request-ID": request_id},
        ) from None
    finally:#一次模型调用可能成功，也可能超时或认证失败。我们希望这些路径都留下记
        # 不记录密钥、完整输入、完整模型回复或上游原始错误正文。
        event = {
            "event": "task_finished",
            "request_id": request_id,
            "task_type": task_type,
            "status_code": status_code,
            #损耗计时
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "input_chars": len(user_input),
            "error_type": error_type,
        }
        line = json.dumps(event, ensure_ascii=False)
        if status_code >= 500:
            logger.error(line)
        else:
            logger.info(line)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/report-draft", response_model=ReportResponse)
def report_draft(request: ReportRequest):
    #report：给日志标明任务类型、generate_report：把要执行的函数传进去
    #request.requirement:交给这个函数的输入
    text, request_id = run_task("report", generate_report, request.requirement)
    return ReportResponse(summary=text, request_id=request_id)


@app.post("/meeting-agenda", response_model=MeetingResponse)
def meeting_agenda(request: MeetingRequest):
    text, request_id = run_task("meeting", generate_meeting, request.topic)
    return MeetingResponse(agenda=text, request_id=request_id)
#新增
@app.post("/email-draft", response_model=EmailResponse)
def email_draft(request: EmailRequest):
    text, request_id = run_task("email", generate_email, request.requirement)
    return EmailResponse(draft=text, request_id=request_id)
