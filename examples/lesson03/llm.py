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

