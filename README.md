# Agent Learn

办公 Agent 应用开发的课程学习与实践记录。当前方向是企业知识驱动的办公分析与报告 Agent，已记录 C01 Lesson01–04；Lesson02、Lesson03、Lesson04 已完成。

当前可生成报告提纲、会议议程和邮件草稿；尚未接入真实业务数据、SQL、RAG 或自主工具循环。

## 课程与进度

| 课程 | 当前实现与状态 | 记录 |
|---|---|---|
| C01 Lesson01：HTTP / JSON / FastAPI | main.py：健康检查、模拟报告预览；历史交付情况见记录 | [Lesson01 handoff](docs/C01-Lesson01-handoff.md) |
| C01 Lesson02：真实模型、配置与异常 | 已完成；lesson02.py：报告草稿、会议议程 | [Lesson02 handoff](handoff.md) |
| C01 Lesson03：分层、任务提示词与运行记录 | 已完成；examples/lesson03：报告、会议、邮件草稿，request_id 与运行日志 | [讲义与完整实践代码](docs/C01-Lesson03.md) · [作业与理解记录](docs/C01-Lesson03-作业与理解记录.md) · [Lesson03 handoff](docs/C01-Lesson03-handoff.md) |
| C01 Lesson04：Git、项目配置与可复现运行 | 已完成；本地版本练习、启动说明、忽略规则与课程交接 | [学习与作业记录](docs/C01-lesson04-notes.md) · [启动说明](docs/C01-Lesson04-runbook.md) · [Lesson04 handoff](docs/C01-Lesson04-handoff.md) |

Lesson03 目录保留原路径，内容已由教师示例整理为用户完成的课程实践，包含新增邮件作业及学习注释。

## 环境与启动

沿用现有 Conda fde。直接依赖来自已验证的 Python 3.11.16 环境；不提交虚拟环境本身。首次准备依赖时可执行：

```bash
conda activate fde
python -m pip install -r requirements.txt
python -m pip check
```

在项目根目录运行：

```bash
# Lesson01，不需要模型配置
python -m uvicorn main:app --reload

# Lesson02
python -m uvicorn lesson02:app --reload --env-file .env

# Lesson03，使用 8001 端口
python -m uvicorn examples.lesson03.api:app --reload --env-file .env --port 8001
```

以上命令分别启动对应课程，按需选择。前两课默认均为 8000，切换时先停止旧服务。直接运行 Python 源文件不会自动启动 Uvicorn。

首次配置时把 .env.example 复制为 .env，只在本地填写 Key，沿用已跑通的模型名称。修改配置后完全停止并重启服务；编辑器解释器与终端解释器均应选择 fde。

Lesson03 测试页面：http://127.0.0.1:8001/docs 。

## Lesson03 接口

| 方法与路径 | 输入 | 成功响应 |
|---|---|---|
| GET /health | 无 | status=ok |
| POST /report-draft | requirement，1–2000 字符 | summary、mode=llm、request_id |
| POST /meeting-agenda | topic，1–200 字符 | agenda、mode=llm、request_id |
| POST /email-draft | requirement，1–1000 字符 | draft、mode=llm、request_id |

输入会清理首尾空白并拒绝纯空白。不同输入模型的 requirement 和同名校验方法各自独立。

```json
{"requirement": "写一封会议邀请邮件，未知的姓名、日期和地点使用待补占位。"}
```

邮件接口只生成草稿，没有发信或删除邮件功能。成功响应编号与 task_finished 日志一致；进入业务函数后的失败将编号放在 X-Request-ID 响应头。输入校验的 422 不经过本例业务日志。

## 验证与完成记录

```bash
python -B -m unittest discover -s tests -v
```

2026-10-17，复核 21 项测试通过：Lesson01–02 共 11 项、Lesson03 原有 4 项、邮件作业 6 项，包含多个子案例。使用 unittest 与 HTTPX 模拟，不加载真实 .env、不发外部模型请求、不产生模型费用。

用户已确认 Lesson02 作业完成；Lesson03 作业已自行完成并对照答案，邮件实现已提交实际代码且检查通过。真实模型实验、用户完成确认和自动模拟验证分别记录，不将模拟回答描述为真实模型输出。

Lesson04 用户已确认四项作业完成；已检查启动说明、Git 本地提交与忽略规则。另对用户既有提交中的 Lesson01 `/document-preview` 完成 1 项正常输入与 3 项无效输入离线检查，均通过。本次未请求真实模型。

## 实现边界

- Lesson02 的会议任务曾复用报告提示词；Lesson03 已拆成报告、会议、邮件各自的提示词与共享调用。
- HTTP 200 和 mode=llm 不能证明回答事实正确。
- 当前仅有最小控制台业务日志，没有完整 Tracing、数据库状态保存、重试或任务恢复。
- 网络阶段超时不是任务总时长硬截止；duration_ms 也不是完整 HTTP 生命周期耗时。
- 第一课历史实现仅有长度校验，纯空白仍返回 200；后两课增加了拒绝空白规则。
- RAG、SQL、原生 Agent、部署等后续课程不因本课完成而登记为完成。

## 后续记录方式

先在聊天中上课、做作业并对答案；用户明确要求“同步到 GitHub”后，再统一整理代码、handoff、作业记录和课程进度并上传到本仓库。下一课为 C01 Lesson05：最小任务提交与查询（同步执行、内存结果），随后 Lesson06：测试与 C01 验收；异步和数据库状态保存留待后续对应课程。

真实 .env、API Key、虚拟环境与缓存始终排除，只提交空密钥的 .env.example。
