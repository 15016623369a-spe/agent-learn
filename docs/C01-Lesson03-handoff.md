# C01 Lesson03 · Handoff

日期：2026-10-14。

## 当前状态

- Lesson02：用户确认全部作业已自行完成，提交代码检查通过。
- Lesson03：进行中；讲义、教师示例与作业已提供，用户本课作业尚未交付。
- 用户的对答案约定：请求答案表示已私下自行完成，再对照答案；不因缺少聊天展示而自动判为未完成。

## 本课产物

- `docs/C01-Lesson03.md`：知识点、完整教师代码、易错点、课后作业。
- `examples/lesson03/`：教师示例，schemas / services / llm / api 四部分。
- `tests/test_lesson03.py`：教师示例离线验证，不读取 .env，不发外部模型请求。
- 报告与会议使用各自的 system 提示词，复用模型调用函数。
- 成功响应增加 request_id，已进入业务函数的失败响应在 X-Request-ID 响应头附编号。
- 业务日志记录 task_type、status_code、duration_ms、input_chars、error_type 与 request_id，不记录完整输入输出或密钥。

## 验证结果

4 项教师示例离线测试通过，涵盖报告与会议提示词隔离、成功响应日志编号对应、422 提前停止、缺密钥 503 的编号关联及未知错误 500 的信息清理。

未替用户执行真实模型实验；未安装或升级依赖。Lesson01 / Lesson02 实现保留。

## 启动与边界

项目根目录、Conda fde：`python -m uvicorn examples.lesson03.api:app --reload --env-file .env --port 8001`。

输入校验失败的 422 与 /health 不经过 run_task，当前没有任务业务编号；只记录进入业务函数的任务。duration_ms 不包含完整 HTTP 生命周期。没有日志落盘、数据库持久化、重试、完整 Tracing、RAG 或 Agent 循环。llm 层仍沿用 FastAPI HTTPException，后续再隔离框架依赖。

## 作业与接续

本课作业：调用流程解释；两个任务响应与日志关联；新增邮件草稿任务并复用公共调用；失败路径与日志边界解释。暂无本课交付，不登记完成。

继续在本聊天学习。用户提交代码或确认完成后，按约定检查具体实现、更新本课交接与课程索引，同步到公开 agent-learn 仓库。
