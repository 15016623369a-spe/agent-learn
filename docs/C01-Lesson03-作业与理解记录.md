# C01 Lesson03：作业与理解记录

日期：2026-10-15。状态：本课作业已完成并对照答案；邮件代码已通过离线检查。

## 作业一：会议请求流程

```text
浏览器在 /docs 点击 Execute
→ POST http://127.0.0.1:8001/meeting-agenda
→ Uvicorn 接收请求
→ FastAPI 匹配方法与路径，使用 MeetingRequest 校验输入
→ api.meeting_agenda(request)
→ api.run_task("meeting", generate_meeting, request.topic)
→ services.generate_meeting(topic)
→ llm.call_llm(MEETING_SYSTEM_PROMPT, task)
→ HTTPX client.post 请求 DeepSeek
→ 解析回答，沿 call_llm → generate_meeting → run_task 返回
→ finally 记录执行结果
→ 路由构造 MeetingResponse
→ FastAPI 编码 JSON，经 Uvicorn 返回浏览器
```

VS Code 用于编辑保存文件，终端可启动服务、显示日志；请求不会让编辑器重新运行整个文件。Python 各层之间是函数调用，两处 HTTP 通信分别位于浏览器与本地服务之间、本地服务与 DeepSeek 之间。

schemas 定义格式，api 提供 HTTP 入口，services 选择任务规则，llm 负责模型通信。会议提示词由 generate_meeting 选择，真正的网络请求在 call_llm 内的 client.post。

## 作业二：响应、日志与计时

成功响应中的 request_id 与本次 task_finished 日志中的 request_id 相同。报告、会议和邮件的 task_type 分别为 report、meeting、email。

每次进入 run_task 都调用 uuid4().hex 产生新编号，用于区分执行。编号不自动创建数据库任务，也不防止相同请求重复执行。

日志只记录固定任务类型、编号、状态、耗时、输入字符数和异常类型，不保存完整需求、回答或密钥。input_chars 是字符数，不是 token 数。

duration_ms 由 perf_counter 的差值计算，主要覆盖业务函数、请求组织、模型等待与响应解析，不包含完整输入校验、响应编码及网络往返全过程。

## 作业三：邮件草稿接口

实际完成代码位于 examples/lesson03：

- EmailRequest：requirement 1–1000 字符，strip 后拒绝纯空白。
- EmailResponse：draft、mode=llm、request_id。
- EMAIL_SYSTEM_PROMPT：生成邮件主题和正文，缺信息用 [待补]，不编造事实、不声称已发送。
- generate_email：复用 call_llm，不复制网络请求与错误处理。
- POST /email-draft：使用 EmailRequest，通过 run_task("email", generate_email, request.requirement) 执行，返回 EmailResponse。

完整代码见 [课程讲义中的实践代码](C01-Lesson03.md#13-本课完整实践代码已完成)。

## 同名字段与函数为什么不冲突

```python
report = ReportRequest(requirement="报告需求")
email = EmailRequest(requirement="邮件需求")
```

report.requirement 与 email.requirement 是不同对象上的值；两个模型的长度规则独立。1500 字符在 ReportRequest 中通过，在 EmailRequest 中失败。

ReportRequest.reject_blank 与 EmailRequest.reject_blank 是两个类中的不同方法。各路由的 request 是各自函数的局部参数。FastAPI 根据请求方法和路径选择接口，再根据参数类型选择输入模型，不会仅凭 JSON 中出现 requirement 就混用模型。

若在同一个类内重复定义同名方法，后面的定义会覆盖前面的定义；本课是不同类，不存在这种覆盖。

## 作业四：失败路径

1. **纯空白返回 422**：Pydantic 校验发生在路由执行之前，未进入 run_task，因此没有该任务的业务日志与编号。
2. **缺密钥返回 503**：合法输入进入 run_task，生成编号；call_llm 在配置检查处抛异常，尚未发请求。run_task 保留状态并在 X-Request-ID 响应头附编号，finally 日志编号相同。
3. **模型超时返回 504**：HTTPX 超时由 call_llm 转为 HTTPException(504)，经过业务函数传播至 run_task，附编号后继续交给 FastAPI。正常返回或 Python 异常离开时都会执行 finally；强制终止进程等情况不保证执行。
4. **日志 / Tracing / 状态保存**：日志记录事件；Tracing 组织一次请求各步骤之间的关系与耗时；持久化保存任务进度，支持后续查询或恢复。当前实现只有最小业务日志。

## 完成与验证依据

按用户约定，请求作业答案表示已先私下完成，再对照解析。邮件接口另有实际代码交付及 6 项离线检查，原 Lesson03 的 4 项检查也通过。不把这些模拟响应记作用户真实模型实验。
