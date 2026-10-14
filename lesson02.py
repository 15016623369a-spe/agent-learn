import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="办公 Agent 学习服务 · Lesson02")


class ReportRequest(BaseModel):
    requirement: str = Field(min_length=1, max_length=2000)
    #装饰器1:校验 requirement 字段时，使用下面这个函数
    @field_validator("requirement")
    #装饰器2:将函数定义为类方法，第一个参数接收类对象，习惯命名为cls
    @classmethod
    def reject_blank(cls, value: str) -> str:#拒绝空白
        value = value.strip()
        if not value:
            raise ValueError("requirement 不能只有空白")
        return value


class ReportResponse(BaseModel):
    summary: str
    mode: str


def generate_draft(requirement: str) -> str:
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
            {
                "role": "system",
                "content": (
                    "你是办公报告草稿助手。用中文回答，包含报告提纲和所需资料清单。"
                    "未提供数据时，只给分析计划；不要编造金额、比例或经营结论，"
                    "不要声称已经查询数据库或读取文件。保持简短。"
                ),
            },
            {"role": "user", "content": requirement},
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

#健康检查：请求这个地址时，FastAPI 执行 health()，把返回字典转换为 JSON。
@app.get("/health")
def health():
    return {"status": "ok"}

#模拟报告接口
@app.post("/report-preview", response_model=ReportResponse)
def preview_report(request: ReportRequest):
    result = f"收到报告任务：{request.requirement}。后续将检索指标口径并计算数据。"
    return ReportResponse(summary=result, mode="mock")

#真实模型接口
@app.post("/report-draft", response_model=ReportResponse)
def report_draft(request: ReportRequest):
    result = generate_draft(request.requirement)
    return ReportResponse(summary=result, mode="llm")


# 定义会议任务的输入
class MeetingAgendaRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)

    @field_validator("topic")
    @classmethod
    def reject_blank_topic(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("topic 不能只有空白")
        return value


# 定义会议任务的输出
class MeetingAgendaResponse(BaseModel):
    agenda: str
    mode: str


# 注册会议议程接口
@app.post("/meeting-agenda", response_model=MeetingAgendaResponse)
def meeting_agenda(request: MeetingAgendaRequest):
    # 把用户输入的主题，组织成具体的模型任务
    requirement = (
        f"请围绕会议主题“{request.topic}”，"
        "生成会议议程和会前资料清单。"
        "当前没有提供实际资料，"
        "不要编造参会人员、业务数字或会议结论。"
    )

    # 复用已有的模型调用函数
    result = generate_draft(requirement)

    # 使用本接口规定的结构返回
    return MeetingAgendaResponse(
        agenda=result,
        mode="llm",
    )