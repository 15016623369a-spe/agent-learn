# C01 Lesson03 · Handoff

完成日期：2026-10-15（Asia/Shanghai）。

## 1. 当前结论

**本课已完成：服务分层、任务提示词与最小运行记录。** 用户已完成课后作业并对照答案；新增邮件草稿接口已提交实际代码，代码检查通过。

本次将原教师示例整理为用户已完成的课程实践，保留用户注释与实现，不改动原有 Lesson01 / Lesson02 代码。目录继续使用 `examples/lesson03/`，避免改变既有启动命令和导入关系。

## 2. 已完成的实现

| 文件 | 职责与本课产物 |
|---|---|
| `schemas.py` | 报告、会议、邮件的输入输出模型；输入长度限制与拒绝纯空白；固定 mode=llm |
| `services.py` | 报告、会议、邮件各自的 system 提示词；generate_report / generate_meeting / generate_email |
| `llm.py` | 共享 call_llm，负责配置、HTTPX 请求、超时、状态映射与回答解析 |
| `api.py` | HTTP 路由、run_task、request_id、计时、成功与失败日志 |

接口：

| 接口 | 输入 | 输出 |
|---|---|---|
| GET /health | 无 | status=ok |
| POST /report-draft | requirement，1–2000 字符 | summary、mode、request_id |
| POST /meeting-agenda | topic，1–200 字符 | agenda、mode、request_id |
| POST /email-draft | requirement，1–1000 字符 | draft、mode、request_id |

邮件提示词明确：只生成主题与正文草稿，缺失信息使用 [待补]，不编造事实，不声称已经发送邮件。代码未连接实际发信或删除邮件工具。

## 3. 作业完成记录

| 作业 | 状态 | 记录依据 |
|---|---|---|
| 一：调用流程与各层职责 | 已完成并对照解析 | 按用户约定，请求答案表示已先私下自行完成；聊天中补充了浏览器到 Python 的完整流程讲解 |
| 二：响应与日志关联 | 已完成并对照解析 | 用户完成声明；离线检查另行验证任务类型和 request_id 对应，不冒充用户真实模型实验 |
| 三：邮件草稿接口 | 已完成，实际代码检查通过 | 用户在 examples/lesson03 中实现模型、独立提示词、业务函数和路由；功能与边界检查通过 |
| 四：失败路径与概念题 | 已完成并对照解析 | 已提供 422、503、504、finally、日志 / Tracing / 状态保存的解释 |

本课完整题目、答案要点及同名字段疑问见 [作业与理解记录](C01-Lesson03-作业与理解记录.md)。

## 4. 关键理解

- VS Code 编辑文件；浏览器连接 Uvicorn 启动的 Python 服务。
- 浏览器到本地接口，以及本地服务到 DeepSeek，是两段 HTTP 通信；Python 各层之间主要是普通函数调用。
- schemas 定义规则，FastAPI 在调用路由前使用规则校验输入；services 选择任务，llm 执行模型通信。
- generate_report、generate_meeting、generate_email 是可传递的函数对象；run_task 内部才调用它们。
- ReportRequest 和 EmailRequest 的 requirement、reject_blank 分别属于各自模型，互不覆盖；1500 字符在报告模型通过、在邮件模型被拒绝。
- request_id 用来关联响应与日志，不等于任务持久化、完整链路追踪或幂等键。

## 5. 验证结果

2026-10-15，Conda fde 下执行：

```bash
python -B -m unittest discover -s tests -v
```

**21 项测试全部通过**：Lesson01 / Lesson02 共 11 项，Lesson03 原有 4 项，新增邮件作业 6 项；包含多个子案例。

邮件检查覆盖：正常输入及清理、专用提示词、draft / mode / request_id、日志编号对应、1 / 1000 字符边界、六类无效输入不触发模型、同名字段独立、缺密钥 503、超时 504。

所有自动检查均为离线模拟，不读取真实 .env、不请求外部模型、不产生模型费用。未安装或升级依赖；本记录不声称本次检查验证了真实模型输出质量。

## 6. 环境与启动

沿用 Conda fde、项目根目录现有 .env 和依赖：

```bash
conda activate fde
cd /Users/jace/office-agent-learning
python -m uvicorn examples.lesson03.api:app --reload --env-file .env --port 8001
```

浏览器：http://127.0.0.1:8001/docs 。

成功响应的编号在 JSON 中；进入 run_task 后发生的失败，编号在 X-Request-ID 响应头中，与日志一致。

## 7. 当前边界

- 输入校验失败的 422 与 /health 不经过 run_task，没有本例的业务日志或业务编号。
- duration_ms 测量业务执行区间，不包含整个 HTTP 生命周期。
- 控制台日志没有自动落盘；尚无完整 Tracing、数据库状态保存、重试或任务恢复。
- llm.py 仍沿用 FastAPI HTTPException；框架解耦可后续处理。
- 提示词与 HTTP 200 不能证明回答事实正确；RAG、SQL、原生 Agent 与综合评估尚未因此完成。

## 8. 课程接续与同步约定

本课结束后继续 C01 后续课，不跳过既定先修顺序。新课须先完整讲授知识点、教师代码、易错点，再统一布置作业；以聊天框为主要教学位置，文件用于复习。

用户说“下一课”只开始教学；明确说“同步到 GitHub”后，才统一检查、整理 handoff、更新进度并上传到 agent-learn。本次同步由用户明确请求，后续继续沿用该约定。
