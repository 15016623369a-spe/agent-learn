# C01 Lesson03：服务分层、任务提示词与最小运行记录

授课日期：2026-10-14；完成日期：2026-10-15。Lesson02、Lesson03 均已完成；本课邮件草稿作业已提交实际代码并检查通过。沿用 Conda fde，无新增第三方依赖。

教学顺序：先讲知识点 → 教师示例 → 易错点 → 统一布置作业。课后答案按用户请求提供；用户请求答案表示已私下完成并希望对照。

## 1. 本课解决什么问题

第二课的一个文件同时负责字段校验、报告规则、模型 HTTP 请求、错误处理与接口返回。新增会议任务时，还复用了报告助手的 system 提示词。

第三课保留已跑通的模型协议，把职责拆开：

```text
浏览器 JSON
  → schemas.py：检查字段
  → api.py：收到 HTTP 请求，调用业务函数
  → services.py：决定报告或会议任务，选择 system 与 user 内容
  → llm.py：组织 payload、读取配置、调用模型、检查响应
  → services.py：返回文本
  → api.py：包装响应，记录运行结果
```

你应能解释每一步，并能增加一种任务而不复制整段网络调用。

## 2. 文件为什么这样拆

| 文件 | 负责的问题 | 常见改动 |
|---|---|---|
| schemas.py | 输入输出长什么样 | 新增字段、长度约束、响应契约 |
| services.py | 用户到底要做什么 | 提示词、任务组合、后续检索与计算 |
| llm.py | 怎样与模型服务通信 | 地址、认证、超时、响应解析 |
| api.py | 怎样提供 HTTP 接口 | 路由、请求追踪、返回结构 |

分层的判断依据是职责，而不是文件数量。单文件在第二课完全可以运行；拆分让后续改动更容易定位。正式大项目还可以拆路由，但本课不引入 APIRouter。

本课仍在 llm.py 中沿用 HTTPException。它已拆开任务规则与网络请求，但没有实现完全独立于 FastAPI 的模型客户端；后续再用自定义异常隔离 HTTP 状态映射。

## 3. 两种任务共享什么

```python
def call_llm(system_prompt: str, user_content: str) -> str:
    ...

def generate_report(requirement: str) -> str:
    return call_llm(REPORT_SYSTEM_PROMPT, requirement)

def generate_meeting(topic: str) -> str:
    task = f"请为会议主题“{topic}”准备议程与会前资料清单。"
    return call_llm(MEETING_SYSTEM_PROMPT, task)
```

两种任务共享读取配置、认证、超时、网络请求和解析；各自定义模型角色、输出要求和用户任务。payload 在 call_llm 内部构造，两条消息随同一次请求一起发送。仅构造字典不会发请求。

提示词能表达任务要求，但不是强制执行的安全规则。HTTP 200 与提示词“不要编造”都不能证明内容正确；后续评估与数据工具会继续解决这个问题。

## 4. Python 包与 import

教师代码在 `examples/lesson03/`，两个目录都有 `__init__.py`。空文件也可以用于声明普通 Python 包。

`from .llm import call_llm` 中的点表示“当前包”，即同一个 lesson03 目录中的 llm.py。`from .services import generate_report` 表示拿到函数；没有括号，所以此时不会执行 generate_report。

运行 `examples.lesson03.api:app`：examples 是目录包，lesson03 是子包，api 对应 api.py，app 是该模块中的 FastAPI 对象。必须在项目根目录启动，不能把 api.py 当普通独立脚本运行。

依赖方向：api → services → llm，api → schemas。不要在 llm.py 中反过来 import api，否则容易循环导入。

## 5. request_id 与耗时

```python
request_id = uuid4().hex
started = perf_counter()
text = generate(user_input)
duration_ms = (perf_counter() - started) * 1000
```

uuid4 生成一次任务的随机编号，hex 变成 32 位十六进制字符串。它用来对应响应与日志；不是用户 ID、任务数据库记录，也不是防重复执行的幂等键。

perf_counter 用来测量经过时间，两次读取相减得到秒数，再乘 1000 变成毫秒。它不是日历时间。本例测量路由调用业务函数的耗时，包括模型请求；不包含 FastAPI 解析请求与最终响应序列化全过程。

成功响应在 JSON 中含 request_id。失败响应仍保持第二课的 detail 结构，把编号放进 `X-Request-ID` 响应头。/health 和输入校验失败的 422 不经过 run_task，因此当前没有这条业务日志或业务编号；全请求追踪留待中间件课程。

## 6. 把函数传给另一个函数

```python
text, request_id = run_task("report", generate_report, request.requirement)
```

三个参数分别是任务名、要执行的函数、用户输入。

`generate_report` 没有括号，传进去的是函数对象。在 run_task 内部执行 `generate(user_input)`，才真正调用它。

如果写成 `generate_report(request.requirement)` 再传入，就会在 run_task 开始前执行，并且传入结果字符串，导致日志无法包住调用、字符串也无法再次当函数调用。

`return text, request_id` 返回二元素元组；左侧两个变量接收它，叫解包。

## 7. 日志与 finally

`logging.basicConfig` 在模块初始化时设置默认控制台日志，logger 是有名字的日志记录器。调用 logger.info / logger.error 记录事件；Uvicorn 和 HTTPX 也可能输出自己的日志，不必误认成重复业务调用。

业务事件先用字典组织，再通过 json.dumps 转成一行 JSON。ensure_ascii=False 保留中文可读性。日志只记固定任务类型、编号、状态、耗时、输入字符数与异常类型，不记录 Key、完整用户需求或模型回答。

```python
try:
    text = generate(user_input)
    status_code = 200
    return text, request_id
except HTTPException as exc:
    status_code = exc.status_code
    # 保留原状态，附加本次编号后重新抛出。
finally:
    # 成功 return 或异常 raise 时，都会先执行这里。
    logger.info(...)
```

finally 在正常成功与 Python 异常离开时执行；进程被强制终止并不保证留下日志。不要在 finally 中 return，否则会覆盖成功结果或吞掉异常。

教师代码把已知 HTTPException 保留原状态，未知异常在最外层 HTTP 边界转为通用 500，并记录异常类名。这个教学版本没有堆栈诊断和日志落盘，不能称为完整 Observability。

status_code 初始为 500，只有生成成功才改为 200；已知错误改为对应码。logger.error 记录失败，logger.info 记录成功。

## 8. 响应契约的小改进

```python
mode: Literal["llm"] = "llm"
request_id: str
```

Literal 限制该字段只能为指定值；本课真实生成接口允许 llm，并设置默认值。所以构造 ReportResponse 时可以省略 mode。模型外部回复依旧是自由文本，这并不把 LLM 输出变成结构化 JSON。

## 9. 已完成实践怎么运行

本课实践位于 examples/lesson03，包含用户完成的邮件草稿接口；Lesson01 和 Lesson02 原代码保留。不要创建新虚拟环境，不需重复安装依赖。

```bash
conda activate fde
cd /Users/jace/office-agent-learning
python -c "import sys; print(sys.executable)"
python -m uvicorn examples.lesson03.api:app --reload --env-file .env --port 8001
```

解释器应为 `/Users/jace/miniforge3/envs/fde/bin/python`。端口 8001 用于这节课，可以与第二课的 8000 区分。继续使用根目录现有 .env；模型名沿用第二课已跑通的配置。不要公开真实 Key。

打开 http://127.0.0.1:8001/docs。本课提供 /health、/report-draft、/meeting-agenda、/email-draft；mock 接口仍可在旧课运行。

报告输入：

```json
{"requirement": "准备上周订单与退款分析报告，只给提纲和资料清单，目前没有真实数据。"}
```

会议输入：

```json
{"topic": "下周产品上线协调会"}
```

成功响应包含任务文本、mode 和 request_id。在终端业务 JSON 日志中找到相同编号，比较 report 与 meeting 的任务类型。真实生成会调用平台 API；离线检查不调用：

```bash
python -m unittest discover -s tests -p test_lesson03.py -v
```

本课 10 项离线测试通过（原有 4 项、邮件 6 项），覆盖三类任务、编号关联、字段独立、输入边界、缺配置与超时等。用户已自行完成本课作业并对照答案；离线结果不冒充真实模型实验。

## 10. 易错点

- 包路径与执行位置：从项目根目录用 Uvicorn 启动，避免 `python examples/lesson03/api.py` 的相对导入错误。
- 职责混放：业务函数负责选择任务提示词，llm.py 不硬编码“所有任务都是报告”。
- 函数与结果混淆：传 generate_report，不是先传 generate_report(...) 的结果。
- 模型成功与任务正确混淆：日志 200 表示生成函数正常返回，不等于业务答案正确。
- 日志与状态保存混淆：终端日志不会提供断点续跑，request_id 也没有自动创建数据库任务。
- 422 与模型错误混淆：无效输入被 Pydantic 拦下，没有进入本例业务日志。
- 原始异常与公开诊断混淆：不打印 Authorization、payload 全文或原始模型错误正文。

## 11. 课后作业（已完成，保留原题供复习）

四项作业均已完成并对照解析；新增邮件接口已通过实际代码检查。详见 [作业与理解记录](C01-Lesson03-作业与理解记录.md)。

### 作业一：画出调用流程

用自己的话说明：浏览器请求会议议程时，经过哪些文件、哪个函数选择 system 提示词、哪一行真正发送网络请求？至少说明 schemas、api、services、llm 各自职责。

### 作业二：运行与日志关联

分别运行一个报告任务与会议任务，记录两个成功响应的 request_id，以及终端对应的 task_finished 事件。解释为什么两个编号不同、为什么日志没有完整用户需求、duration_ms 包含哪些时间。提交时去掉密钥。

### 作业三：新增邮件草稿任务

在教师示例上添加 `POST /email-draft`：输入字段 requirement（1–1000 字符，拒绝纯空白），输出字段 draft、mode=llm、request_id。为邮件任务写单独的 system 提示词，复用 call_llm 与 run_task。

邮件只生成草稿，不能声称已发送；未提供的姓名、时间等使用待补占位。不得复制整个 HTTP 请求与错误处理，也不要调用真实发信服务。

### 作业四：失败路径与解释

1. 纯空白输入为什么返回 422，而且看不到该任务的 task_finished？
2. 缺密钥的正常输入会在哪一层停下？响应头编号与日志编号是否一致？
3. 若 HTTPX 抛出超时，经过哪些函数回到浏览器？finally 为什么仍执行？
4. 本课日志、完整链路追踪、数据库状态保存分别有什么区别？

可以在没有 Key 的独立新进程中运行失败实验，不必删除现有 .env；`env -u DEEPSEEK_API_KEY python -m uvicorn examples.lesson03.api:app --port 8002`（不加 --env-file）会使用缺密钥状态。

### 交付与验收

交付修改后的代码位置与运行结果或完成说明。验收重点：能解释分层、任务提示词独立、模型调用复用、日志与响应可关联、无效输入不触发模型、密钥未泄露。

本课已按用户明确请求整理完成记录并同步 GitHub。后续先上课；只有用户明确说“同步到 GitHub”才统一上传。用户索要答案默认表示已先自行完成。

## 12. 官方参考

- [FastAPI：多个文件组织应用](https://fastapi.tiangolo.com/tutorial/bigger-applications/)：本课只采用包与 import，APIRouter 后续再用。
- [FastAPI：HTTP 错误处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)。
- [Python 3.11：Logging HOWTO](https://docs.python.org/3.11/howto/logging.html)。
- [Python 3.11：perf_counter](https://docs.python.org/3.11/library/time.html#time.perf_counter)。
- [HTTPX：Timeouts](https://www.python-httpx.org/advanced/timeouts/)：网络阶段超时不等于业务总时长上限。

## 13. 本课完整实践代码（已完成）

以下与当前项目文件一致，包含本课邮件草稿作业。

### examples/lesson03/__init__.py

```python
"""C01 Lesson03：已完成的课程实践——服务分层、任务提示词与运行记录。"""
```

### examples/lesson03/schemas.py

```python
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

#新增
class EmailRequest(BaseModel):
    requirement : str = Field(min_length=1, max_length=1000)

    @field_validator("requirement")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("requirement 不能只有空白")
        return value

class EmailResponse(BaseModel):
    draft: str
    mode: Literal["llm"] = "llm"
    request_id: str
```

### examples/lesson03/services.py

```python
from .llm import call_llm

# 报告与会议使用不同的任务规则，共享同一个网络调用函数。
REPORT_SYSTEM_PROMPT = (
    "你是办公报告草稿助手。用中文回答，包含报告提纲和所需资料清单。"
    "未提供数据时，只给分析计划；不要编造金额、比例或经营结论。"
    "不要声称已查询数据库或读取文件。保持简短。"
)

MEETING_SYSTEM_PROMPT = (
    "你是会议筹备助手。用中文回答，包含会议目标、建议议程和会前资料清单。"
    "可以提出建议，但不能声称会议已召开、人员已确认或资料已读取。"
    "未提供的信息标为待确认，不要编造姓名、业务数字或已达成的结论。保持简短。"
)
#新增
EMAIL_SYSTEM_PROMPT = (
    "你是办公邮件草稿助手。根据用户需求，用中文生成邮件主题和正文草稿。"
    "未提供的收件人姓名、日期、地点等信息使用[待补]占位，"
    "不要编造业务数字、事实或已确认事项。"
    "只生成草稿，不声称已经发送邮件。保持简短。"
)

def generate_report(requirement: str) -> str:
    return call_llm(REPORT_SYSTEM_PROMPT, requirement)


def generate_meeting(topic: str) -> str:
    task = f"请为会议主题“{topic}”准备议程与会前资料清单。"
    return call_llm(MEETING_SYSTEM_PROMPT, task)

def generate_email(requirement: str) -> str:
    return call_llm(EMAIL_SYSTEM_PROMPT, requirement)
```

### examples/lesson03/llm.py

```python
import os

import httpx
from fastapi import HTTPException


def call_llm(system_prompt: str, user_content: str) -> str:
    # Uvicorn 的 --env-file 将 .env 加载到进程环境中。
    #读取配置：从运行环境中取得密钥和模型名称
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="服务尚未配置模型密钥")
    if not model:
        raise HTTPException(status_code=503, detail="服务尚未配置模型名称")
    #payload：组织模型应该收到的任务
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "thinking": {"type": "disabled"},
        "max_tokens": 800,
        "stream": False,#非流式返回：程序等待这次完整响应，再处理其中的文本。本次不会把生成过程逐段推送给浏览器
    }
    #这是请求头字典；给请求附上认证信息，使用 f-string，把变量内容填入字符串。
    headers = {"Authorization": f"Bearer {api_key}"}
    #发送请求并管理客户端
    try:
        #这个with..as client 表示在这个代码块中使用客户端。离开代码块时，无论正常结束还是出现异常，客户端都会执行相应的资源清理。
        #这里是在进行超时配置：建立连接阶段使用 10 秒等待上限，其他网络阶段使用 60 秒。
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:#创建 HTTP 客户端，被保存到client
            #response保存收到的 HTTP 响应对象
            response = client.post(#这里是真正发出请求
                "https://api.deepseek.com/chat/completions",
                headers=headers,#附上认证请求头
                json=payload,#将字典编码为 JSON 请求体
            )
            response.raise_for_status()#检查 HTTP 状态
            #上面这一段是实际的网络调用。
            #分别要处理哪一类失败
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="等待模型响应超时") from None
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="无法连接模型服务") from None
    except httpx.HTTPStatusError as exc:
        upstream_status = exc.response.status_code
        if upstream_status in (401, 403):
            status, detail = 503, "模型服务认证失败，请检查本地密钥配置"
        elif upstream_status == 402:
            status, detail = 503, "模型服务余额不足"
        elif upstream_status == 429:
            status, detail = 503, "模型服务限流，请稍后再试"
        else:
            status, detail = 502, f"模型服务返回错误（上游状态码 {upstream_status}）"
        raise HTTPException(status_code=status, detail=detail) from None
    #第二个 try：解析模型响应
    try:
        data = response.json()#解析JSON，把响应的json解析成python字典、列表等数据
        choice = data["choices"][0]#先得到 choices 列表，再取第一个元素。Python 列表下标从 0 开始。
        content = choice["message"]["content"]#取模型回答
        finish_reason = choice["finish_reason"]#取生成停止的原因
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="模型响应格式异常") from None

    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=502, detail="模型没有返回有效文本")
    if finish_reason != "stop":
        raise HTTPException(status_code=502, detail="模型未正常完成回答，请调整任务或输出长度")
    return content.strip()
```

### examples/lesson03/api.py

```python
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
```
