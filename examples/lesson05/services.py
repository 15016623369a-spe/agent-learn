import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException

from examples.lesson03.services import (
    generate_email,
    generate_meeting,
    generate_report,
)

from .schemas import TaskCreate, TaskRecord
from .store import save_task

logger = logging.getLogger("office_agent.lesson05")

GENERATORS = {
    "report": generate_report,
    "meeting": generate_meeting,
    "email": generate_email,
}

ERROR_MESSAGES = {
    503: "模型配置或上游服务暂不可用",
    504: "模型调用超时",
    502: "模型通信或响应异常",
}


def execute_task(request: TaskCreate, request_id: str) -> TaskRecord:
    task_id = uuid4().hex
    started = perf_counter()

    task = TaskRecord(
        task_id=task_id,
        task_type=request.task_type,
        status="running",
    )
    save_task(task)

    try:
        generate = GENERATORS[request.task_type]
        text = generate(request.requirement)
    except HTTPException as exc:
        task = TaskRecord(
            task_id=task_id,
            task_type=request.task_type,
            status="failed",
            error_code=exc.status_code,
            error_message=ERROR_MESSAGES.get(
                exc.status_code, "任务执行失败"
            ),
        )
    except Exception:
        task = TaskRecord(
            task_id=task_id,
            task_type=request.task_type,
            status="failed",
            error_code=500,
            error_message="任务执行发生内部错误",
        )
    else:
        task = TaskRecord(
            task_id=task_id,
            task_type=request.task_type,
            status="succeeded",
            result=text,
        )

    save_task(task)

    event = {
        "event": "task_finished",
        "request_id": request_id,
        "task_id": task_id,
        "task_type": task.task_type,
        "task_status": task.status,
        "error_code": task.error_code,
        "duration_ms": round((perf_counter() - started) * 1000, 2),
    }
    line = json.dumps(event, ensure_ascii=False)
    if task.status == "failed":
        logger.error(line)
    else:
        logger.info(line)

    return task
