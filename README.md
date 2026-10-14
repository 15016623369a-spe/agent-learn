# Agent Learn

办公 Agent 应用开发的课程学习与项目复现记录。当前主项目方向是“企业知识驱动的办公分析与报告 Agent”；本仓库已记录 C01 Lesson01–02；Lesson03 已开始，提供分层与日志的教师示例，等待用户本课交付。

目前模型生成报告提纲或会议议程，没有接入真实业务数据、SQL 计算、RAG 或自主工具循环。

## 课程与文件

| 课程 | 实现 | 交接记录 |
|---|---|---|
| C01 Lesson01：HTTP / JSON / FastAPI | `main.py`：健康检查、模拟报告预览 | [Lesson01 交接](docs/C01-Lesson01-handoff.md) |
| C01 Lesson02：真实模型、配置、异常与超时（已完成） | `lesson02.py`：报告草稿、会议议程、输入校验与失败映射 | [本课 handoff](handoff.md) |
| C01 Lesson03：分层、任务提示词与运行记录（进行中） | `examples/lesson03/`：教师示例；用户本课作业尚未交付 | [讲义](docs/C01-Lesson03.md) · [本课 handoff](docs/C01-Lesson03-handoff.md) |

`tests/test_lessons.py` 是本次检查添加的离线回归测试，模拟模型服务，不使用真实 Key，也不产生外部模型请求。

## 本地运行

在仓库根目录执行，沿用已存在的 Conda `fde`：

```bash
conda activate fde
python -c "import sys; print(sys.executable)"
python -m pip install -r requirements.txt
python -m pip check
```

依赖版本来自已验证的 Python 3.11.16 环境。仓库不包含 Python 环境本身。

第一课不需要模型配置：

```bash
python -m uvicorn main:app --reload
```

第二课先将 `.env.example` 复制为 `.env`，只在本地编辑器填入真实 DeepSeek Key，再运行：

```bash
python -m uvicorn lesson02:app --reload --env-file .env
```

两个应用默认都使用 8000 端口。切换应用时先停止旧服务。修改 `.env` 后完全停止并重启。

打开 http://127.0.0.1:8000/docs 测试接口。直接运行 `python lesson02.py` 只会定义应用，不会启动服务器。

## 第二课接口

| 方法与路径 | 请求 | 成功输出 |
|---|---|---|
| `GET /health` | 无请求体 | `status=ok` |
| `POST /report-preview` | `requirement` | `summary`、`mode=mock` |
| `POST /report-draft` | `requirement` | `summary`、`mode=llm` |
| `POST /meeting-agenda` | `topic` | `agenda`、`mode=llm` |

报告需求长度为 1–2000，会议主题为 1–200；第二课两个输入模型均清理首尾空白并拒绝纯空白。

报告请求示例：

```json
{"requirement": "设计一份订单与退款分析报告，先给提纲和所需资料清单；尚未提供真实数据。"}
```

会议请求示例：

```json
{"topic": "下周产品上线协调会"}
```

真实模型调用可能产生平台费用。健康检查、mock 接口与离线测试不调用模型。

## 检查与测试

```bash
python -m unittest discover -s tests -v
```

2026-10-14，11 项测试通过，包含正常请求契约、会议主题传递、输入边界、缺配置、上游状态码、超时、连接失败、异常 JSON、空回答及截断响应。无需安装 pytest。

用户已经提交报告草稿真实调用的 200 响应，以及三组 422 和缺密钥 503 的截图；本次自动检查不重复请求模型。用户于 2026-10-14 确认 Lesson02 全部作业已自行完成；代码检查通过。完整状态见 handoff。

## 当前限制与下一课

- 会议接口复用报告助手的 system 提示词，可能带报告风格；下一课拆分任务提示词与模型传输逻辑。
- `mode=llm` 和 HTTP 200 不能证明回答事实正确。
- 超时参数控制各网络阶段，不是整次任务的总时长上限。
- 当前没有重试、持久化、身份权限、RAG 和 Agent 循环，后续逐步加入。
- 第一课仅有长度校验，纯空白仍返回 200；保留历史实现，第二课已增加拒绝空白逻辑。

`.env`、`.venv`、缓存不进入版本控制，只提交空密钥的 `.env.example`。后续继续 C01 的服务分层、运行记录、Git 和服务骨架，之后再进入 C02。

## Lesson03（进行中）

[完整讲义与教师代码](docs/C01-Lesson03.md)。沿用 fde，无新增依赖：

```bash
python -m uvicorn examples.lesson03.api:app --reload --env-file .env --port 8001
```

打开 http://127.0.0.1:8001/docs。4 项教师示例离线测试通过；这是示例验证，不登记为用户本课作业完成。
