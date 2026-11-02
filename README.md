# Agent Learn

办公 Agent 应用开发的课程学习与实践记录。当前方向是企业知识驱动的办公分析与报告 Agent，已记录 C01 Lesson01–06；Lesson02–06 已完成，本轮 C01 范围验收通过；Lesson01 历史交付状态仍参照原记录。

当前可生成报告提纲、会议议程和邮件草稿，并按任务编号查询当前进程内的成功或失败记录；尚未接入真实业务数据、SQL、RAG 或自主工具循环。

新增的 **C04 LLM 工程与上下文工程** 独立放在 [`llm/`](llm/README.md)，代码与记录均与 C01 分开。2026-11-02，Lesson01–02已完成，用户完成确认、助手补录与实际离线验证分别记录；下一课为C04 Lesson03。

## C01 服务与后端：课程与进度

| 课程 | 当前实现与状态 | 记录 |
|---|---|---|
| C01 Lesson01：HTTP / JSON / FastAPI | main.py：健康检查、模拟报告预览；历史交付情况见记录 | [Lesson01 handoff](docs/C01-Lesson01-handoff.md) |
| C01 Lesson02：真实模型、配置与异常 | 已完成；lesson02.py：报告草稿、会议议程 | [Lesson02 handoff](handoff.md) |
| C01 Lesson03：分层、任务提示词与运行记录 | 已完成；examples/lesson03：报告、会议、邮件草稿，request_id 与运行日志 | [讲义与完整实践代码](docs/C01-Lesson03.md) · [作业与理解记录](docs/C01-Lesson03-作业与理解记录.md) · [Lesson03 handoff](docs/C01-Lesson03-handoff.md) |
| C01 Lesson04：Git、项目配置与可复现运行 | 已完成；本地版本练习、启动说明、忽略规则与课程交接 | [学习与作业记录](docs/C01-lesson04-notes.md) · [启动说明](docs/C01-Lesson04-runbook.md) · [Lesson04 handoff](docs/C01-Lesson04-handoff.md) |
| C01 Lesson05：最小任务提交与查询 | 已完成；同步执行、task_id / request_id、内存记录与失败查询 | [讲义与实际代码](docs/C01-Lesson05.md) · [作业记录](docs/C01-Lesson05-作业与理解记录.md) · [Lesson05 handoff](docs/C01-Lesson05-handoff.md) |
| C01 Lesson06：测试、最小基线与 C01 验收 | 已完成；用户确认作业完成，本地代码补齐并复验：31项离线测试、6例真实基线 | [讲义](docs/C01-Lesson06.md) · [参考答案](docs/C01-Lesson06-作业与答案.md) · [真实基线](docs/C01-Lesson06-baseline.md) · [C01验收](docs/C01-acceptance.md) · [handoff](docs/C01-Lesson06-handoff.md) |

Lesson03 目录保留原路径，内容已由教师示例整理为用户完成的课程实践，包含新增邮件作业及学习注释。

## C04 LLM 工程与上下文工程

| 课程 | 当前实现与状态 | 记录 |
|---|---|---|
| C04 Lesson01：从文本生成到 LLM 应用的输入输出设计 | 已完成；任务契约、四项缺失检查、消息构造、手写期望输出；本轮为离线验证 | [LLM模块入口](llm/README.md) · [课堂代码](llm/lesson01.py) · [讲义](llm/docs/C04-Lesson01-notes.md) · [作业与参考答案](llm/docs/C04-Lesson01-homework.md) · [handoff](llm/docs/C04-Lesson01-handoff.md) |
| C04 Lesson02：提示结构与示例 | 已完成；V0无示例，V1三组示例；四题答案已补入原文件，真实生成效果待验证 | [代码](llm/lesson02.py) · [讲义](llm/docs/C04-Lesson02-notes.md) · [四题答案](llm/docs/C04-Lesson02-homework.md) · [handoff](llm/docs/C04-Lesson02-handoff.md) |

```bash
# 仓库根目录，沿用Conda fde；本课仅使用Python标准库
python -B llm/lesson01.py
python -B -m llm.lesson01
python -B llm/lesson02.py
python -B -m llm.lesson02
```

本课不启动FastAPI、不读取.env、不调用模型、不读取订单或执行统计。输出包括程序生成的输入检查结果、待发送消息，以及明确标注为手写的参考JSON。Lesson02已完成三组示例构造与四题作业；真实模型效果尚未比较。C04 Lesson03–08尚未授课；RAG预习与正式模块均未开始。

## C01 环境与启动

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

# Lesson05，使用 8002 端口
python -m uvicorn examples.lesson05.api:app --reload --env-file .env --port 8002
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


## Lesson05 接口

| 接口 | 输入 | 响应约定 |
|---|---|---|
| POST /tasks | task_type=report / meeting / email；requirement，1–1000 字符 | 201；request_id 与 task，task.status 为 succeeded 或 failed |
| GET /tasks/{task_id} | 路径中的任务编号 | 找到返回 200 与已保存记录；不存在返回 404 |
| GET /health | 无 | status=ok |

Lesson05 页面：http://127.0.0.1:8002/docs 。POST 同步执行并保存结果，GET 不重新调用模型；重复提交相同需求会创建新任务。task_id 标识业务任务，request_id 每次提交或查询重新生成。输入无效返回 422 且不创建记录。

任务创建成功与任务执行成功分别表达：HTTP 201 也可能包含 task.status=failed，任务内 error_code 是失败原因。内存记录不会随 Git 上传，重启或自动重载后丢失。

## 验证与完成记录

```bash
python -B -m unittest discover -s tests -v
```

2026-10-17，复核 21 项测试通过：Lesson01–02 共 11 项、Lesson03 原有 4 项、邮件作业 6 项，包含多个子案例。使用 unittest 与 HTTPX 模拟，不加载真实 .env、不发外部模型请求、不产生模型费用。

用户已确认 Lesson02 作业完成；Lesson03 作业已自行完成并对照答案，邮件实现已提交实际代码且检查通过。真实模型实验、用户完成确认和自动模拟验证分别记录，不将模拟回答描述为真实模型输出。

Lesson04 用户已确认四项作业完成；已检查启动说明、Git 本地提交与忽略规则。另对用户既有提交中的 Lesson01 `/document-preview` 完成 1 项正常输入与 3 项无效输入离线检查，均通过。本次未请求真实模型。

2026-10-18，Lesson05 实际代码检查通过，用户已确认四项作业完成；新增九项离线回归后，整套 **30 项测试全部通过**。本次未请求真实模型，保留用户注释并修正包入口文件名。

2026-10-18，Lesson06已按用户确认登记完成并补齐本地代码与记录：新增“404查询不破坏已有任务”回归后，全量 **31项测试通过**。另真实调用六个开发案例，生成成功6/6、保存任务查询一致6/6，助手逐例内容复核通过6/6；原始输出和评分依据已归档。六例结果仅描述本轮开发验收，不推断总体可靠性。

Lesson06复用Lesson05服务。基线采集器位于examples/lesson06/run_baseline.py，显式运行才会调用模型；不自动判内容分数，不覆盖已有结果文件。

## 实现边界

- Lesson02 的会议任务曾复用报告提示词；Lesson03 已拆成报告、会议、邮件各自的提示词与共享调用。
- HTTP 200 和 mode=llm 不能证明回答事实正确。
- 当前有最小控制台业务日志与 Lesson05 进程内任务记录，没有完整 Tracing、数据库状态保存、重试或任务恢复。
- 网络阶段超时不是任务总时长硬截止；duration_ms 也不是完整 HTTP 生命周期耗时。
- 第一课历史实现仅有长度校验，纯空白仍返回 200；后两课增加了拒绝空白规则。
- RAG、SQL、原生 Agent、部署等后续课程不因本课完成而登记为完成。

## 后续记录方式

先在聊天中上课、做作业并对答案；用户明确要求“同步到 GitHub”后，再统一整理代码、handoff、作业记录和课程进度并上传到本仓库。2026-10-18 的 C01 交接将下一模块记为 C02 Transformer；该历史记录保留。当前接续位置已更新为 C04 Lesson03，C04 内容独立保存于 llm/；异步和数据库状态保存留待后续对应课程。2026-10-31、2026-11-02用户分别明确要求同步C04 Lesson01和Lesson02，同时保留原C01内容。

真实 .env、API Key、虚拟环境与缓存始终排除，只提交空密钥的 .env.example。
