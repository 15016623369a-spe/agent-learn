import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response

from .schemas import TaskCreate, TaskResponse
from .services import execute_task
from .store import get_task

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="办公 Agent 学习服务 · Lesson05 已完成实践")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(request: TaskCreate, response: Response):
    request_id = uuid4().hex
    task = execute_task(request, request_id)

    response.headers["X-Request-ID"] = request_id
    response.headers["Location"] = f"/tasks/{task.task_id}"

    return TaskResponse(request_id=request_id, task=task)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def read_task(task_id: str, response: Response):
    request_id = uuid4().hex
    task = get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="任务不存在，或当前进程的记录已清空",
            headers={"X-Request-ID": request_id},
        )

    response.headers["X-Request-ID"] = request_id
    return TaskResponse(request_id=request_id, task=task)
