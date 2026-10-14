# C01 Lesson01 · HTTP / JSON / FastAPI 交接

> 记录日期：2026-10-14（Asia/Shanghai）  
> 实现文件：main.py  
> 状态：基础接口实现与自动检查通过；原独立作业仍保留待验收

## 已有实现

- `app = FastAPI(...)` 创建服务应用。
- `ReportRequest` 定义必填 requirement，长度 1–2000。
- `ReportResponse` 定义 summary、mode。
- `mock_report()` 按固定模板拼接需求。
- `GET /health` 返回 `{"status":"ok"}`。
- `POST /report-preview` 校验输入、调用 mock 函数并返回 mode=mock。

## 启动与检查

沿用 Conda fde、Python 3.11.16，依赖见仓库 requirements.txt：

```bash
conda activate fde
python -m uvicorn main:app --reload
```

接口文档：http://127.0.0.1:8000/docs。

2026-10-14 自动检查：健康检查、普通需求、缺字段、空字符串和超长需求符合预期。第一课没有自定义拒绝空白规则，所以纯空格仍返回 200；保留这个历史实现，第二课通过 field_validator 改进。

## 交付边界与待补

该文件是模拟服务，没有真实模型、数据库、资料检索和数字计算。

用户此前已提交服务启动截图并完成相关讲解；原作业要求的独立 `/document-preview` 接口、完整概念题与独立解释仍未完整交付，不因教师检查通过而登记整课独立验收完成。

第二课在 lesson02.py 中接入 DeepSeek，并新增会议议程任务。后续状态以仓库根目录 handoff.md 为准。
