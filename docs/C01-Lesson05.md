# C01 Lesson05：最小任务提交与查询

状态：已完成的课程实践，2026-10-18。聊天是主要授课位置，本文件用于复习并保存实际代码快照。

## 目标与范围

为报告、会议、邮件任务生成 task_id，在当前进程内保存执行记录，并按编号查询。提交采用同步执行：请求等待生成结束再返回；未实现后台队列、数据库、任务恢复或幂等。

## 编号与状态

- task_id 标识一个业务任务；后续查询保持相同。
- request_id 标识一次进入提交或查询路由的请求；每次重新生成。
- running 表示开始执行，随后更新为 succeeded 或 failed。提交返回时通常已是终态。

## 分层与调用

```text
POST /tasks
  api.py → services.execute_task
    → store.save_task(running)
    → Lesson03 generate_report / generate_meeting / generate_email
      → Lesson03 llm.call_llm
    → store.save_task(succeeded / failed)
    → task_finished 日志
  → 返回 TaskResponse

GET /tasks/{task_id}
  api.py → store.get_task → 返回记录或 404
  不调用模型，不输出新的 task_finished 业务日志
```

## 接口约定

| 接口与情况 | HTTP | 任务状态 |
|---|---|---|
| POST /tasks，执行成功 | 201 | succeeded |
| POST /tasks，执行失败且已记录 | 201 | failed |
| POST /tasks，无效输入 | 422 | 不创建 |
| GET /tasks/{task_id}，存在 | 200 | 返回保存的状态 |
| GET /tasks/{task_id}，不存在 | 404 | 无记录 |

新入口统一使用 task_type 和 requirement（1–1000 字符），允许 report / meeting / email。输入清理首尾空白并拒绝纯空白；响应由 request_id 与嵌套 task 组成。任务结果统一放 result。响应 Location 给出查询路径。

HTTP 201 表示任务记录创建，调用方还须检查 task.status。业务 error_code 是失败原因，不能与 HTTP 状态混淆。

## 启动

```bash
conda activate fde
cd /Users/jace/office-agent-learning
python -m uvicorn examples.lesson05.api:app --reload --env-file .env --port 8002
```

接口文档：http://127.0.0.1:8002/docs
健康检查：http://127.0.0.1:8002/health

继续使用现有本地 .env 与依赖，无需新建环境。POST 会实际使用已配置的模型平台；GET 查询已有记录不会重新生成。

提交示例：

```json
{"task_type":"report","requirement":"准备订单与退款分析报告提纲，尚未提供真实数据。"}
```

复制响应中的 task.task_id，再在 GET 接口中查询两次，比较任务不变与请求编号变化。

## 易错点与边界

- 同样需求重复 POST 会产生新任务，当前没有去重。
- GET 读取已有结果，成功与失败记录都可查询。
- 刷新浏览器不清空服务内存；服务重启、自动重载后记录消失；多个进程不共享这份字典。
- 本例未实现容量清理、用户隔离、持久化或完整 Tracing。任务编号不是权限凭证。
- 422 不经过路由，当前没有业务 request_id；404 有 X-Request-ID。
- 继续复用 Lesson03 的同步模型调用及 HTTPException；生成成功并不能证明事实正确。

## 完整实际代码

### examples/lesson05/__init__.py

```python
"""C01 Lesson05：已完成课程实践——最小任务提交与查询。"""
```

### examples/lesson05/schemas.py

```python
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
```

### examples/lesson05/store.py

```python
from .schemas import TaskRecord
#前面的下划线 _ 表示这是一个内部私有变量，别人别随便动。
#：这是类型注解。它在告诉你：“这个仓库是一个字典（dict）”。
_tasks: dict[str, TaskRecord] = {}
#保存
#我这个函数执行完之后，不会返回任何有价值的数据
def save_task(task: TaskRecord) -> None:
    _tasks[task.task_id] = task

#查询
def get_task(task_id: str) -> TaskRecord | None:
    return _tasks.get(task_id)
```

### examples/lesson05/services.py

```python
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
```

### examples/lesson05/api.py

```python
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
```

## 作业与接续

四项作业及答案要点见 [作业与理解记录](C01-Lesson05-作业与理解记录.md)。检查结果与交接见 [Lesson05 handoff](C01-Lesson05-handoff.md)。下一课 Lesson06：测试、最小基线与 C01 验收。
