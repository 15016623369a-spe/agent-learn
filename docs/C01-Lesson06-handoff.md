# C01 Lesson06 handoff

日期：2026-10-18。主题：测试、最小基线与 C01 验收。

## 当前状态

用户确认本课作业已私下完成，但未在编辑器保存Lesson06文件。本次按要求补齐本地实践与记录，并重新验收。代码补录来自本次助手，不把它描述为用户此前已经保存的代码。

- 参考答案：四项作业均已整理。
- 工程验证：全量31项离线测试全部通过；本课新增一项404不破坏已有记录的测试。
- 真实复验：六例均HTTP201、task.status=succeeded，GET200且任务记录一致。
- 内容评审：本轮六例均通过任务符合度、事实依据和行动表述检查。评审者为本次助手，不是独立人工双评。
- 用户此前未保存的私下测试不追溯伪造。本次原始输出已实际归档。
- 发布范围：用户于2026-10-18明确要求同步本课代码、记录和验收结果至固定GitHub仓库；.vscode/为既有无关文件，保持不动且不纳入提交。

## 本课交付

- examples/lesson06/__init__.py：本课实践标识。
- examples/lesson06/cases.json：六例固定输入及判断标准。
- examples/lesson06/run_baseline.py：真实基线采集器；只显式运行才调用模型，不自动判内容分数。
- tests/test_lesson05.py：新增test_missing_lookup_preserves_existing_task。
- docs/C01-Lesson06.md：讲义、流程图与代码说明。
- docs/C01-Lesson06-作业与答案.md：四项参考答案。
- docs/C01-Lesson06-baseline-2026-10-18.json：原始输出、任务与请求编号、模型配置和版本元数据。
- docs/C01-Lesson06-baseline.md：六例评分及原文展示。
- docs/C01-acceptance.md：C01范围验收结论。
- README.md：增加本课索引与最新状态。

本课复用Lesson05服务和Lesson03模型调用，不另造一套api/services，不更换fde，不改.env，不新增依赖。

## 运行方法

在项目根目录、Conda fde中执行：

- python -B -m unittest discover -s tests -v
- python -B -m unittest discover -s tests -p "test_lesson05.py" -v
- python -B -m examples.lesson06.run_baseline --output docs/C01-Lesson06-baseline-new-run.json

前两项为离线测试。最后一项会真实调用六次模型，消耗平台额度；新文件名避免覆盖旧证据。新输出必须重新评审，不沿用旧评分。

## 结论与边界

本轮课程范围验收通过。六例全通过只是小规模开发基线的一次观测，不是总体可靠性证明。记录在脚本进程结束后不会保留在业务内存中，JSON保存的是本次验收证据。

当前已有：三种草稿任务、同步模型调用、最小运行日志、进程内任务保存与查询、离线回归和内容基线。尚无：SQL持久化、异步队列、RAG、工具执行、LangGraph/HITL、MCP、完整Tracing和部署鉴权。

下一模块按既定规划为C02 Transformer。用户说“下一课”先在聊天教学；说“同步到GitHub”再核对本课变更并提交上传。保留根目录旧handoff和其他课文件，不覆盖。

## 后续可改进

为未来跨版本比较，可增加实际响应模型标识、源文件内容哈希和更广案例切片；这些不属于本课阻碍。生产化与对抗评估由后续课程处理。
