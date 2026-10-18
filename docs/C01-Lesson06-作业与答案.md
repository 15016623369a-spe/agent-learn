# C01 Lesson06 作业与参考答案

日期：2026-10-18。主题：测试、最小基线与 C01 验收。

用户已确认四项作业私下完成；本次按用户要求补齐本地代码与记录，并重新验收。以下代码由助手根据本课要求补录，不把补录代码表述为用户此前已保存的代码。已完成学习、代码补录、离线测试与真实模型复验分别记录。

## 作业一：运行测试并解释两项测试

```bash
conda activate fde
cd /Users/jace/office-agent-learning
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s tests -p "test_lesson05.py" -v
```

本次全套结果为31项通过。Lesson05任务模块中现有10项测试，其中1项为本课新增。测试方法中的多个subTest仍属于一个测试方法。

### 例一：test_repeated_queries_keep_task_and_never_regenerate

- Arrange：把报告生成函数替换成固定返回saved-result的Mock，清空任务存储，使用ASGI测试客户端。
- Act：POST创建任务，再用同一task_id执行两次GET。
- Assert：三次请求都有不同request_id；任务内容始终相同；生成函数只调用一次；只产生一条任务完成日志。
- 能证明：查询读取已有结果，不重复生成；业务任务编号与每次请求编号职责不同。
- 不能证明：真实模型会正常响应、回答事实正确，或重启后记录仍存在。

### 例二：test_failed_records_are_queryable_and_errors_are_sanitized

- Arrange：分别让生成函数抛出502、503、504的HTTPException及普通异常。
- Act：POST提交，再GET查询保存的失败任务。
- Assert：POST仍返回201；task.status为failed；error_code符合约定；GET返回200且记录相同；响应与日志没有内部错误文本。
- 能证明：既定失败路径可保存、可查询，并做了错误脱敏。
- 不能证明：真实网络一定在某个总时长内超时，或真实上游的所有错误都已经覆盖。

这里POST的201表示创建了任务记录。任务执行成功与否看task.status。GET的200表示查询到了记录，也不代表任务执行成功。

## 作业二：查询不存在的任务，不应破坏已保存记录

直接加入现有tests/test_lesson05.py中的Lesson05Tests类。无需另建一个HTTP服务，也无需重复编写已有测试。

```python

    async def test_missing_lookup_preserves_existing_task(self):
        """Lesson06 作业：查不到其他任务，不应破坏已保存记录。"""
        generate = Mock(return_value="已保存的报告提纲")
        with patch.dict(services.GENERATORS, {"report": generate}), \
             self.assertLogs(services.logger, level="INFO"):
            created = await self.call("POST", "/tasks", {
                "task_type": "report", "requirement": "准备报告",
            })
            self.assertEqual(created.status_code, 201)
            original = created.json()["task"]

            missing = await self.call("GET", "/tasks/not-exist")
            self.assertEqual(missing.status_code, 404)

            existing = await self.call("GET", "/tasks/" + original["task_id"])
            self.assertEqual(existing.status_code, 200)
            self.assertEqual(existing.json()["task"], original)
            self.assertEqual(len(store._tasks), 1)
            generate.assert_called_once_with("准备报告")
```

执行链条：

1. 创建一个有效任务，保存其完整记录。
2. 查询另一个不存在的task_id，预期404。
3. 再查原task_id，预期200。
4. 对比完整任务对象，确认内容未改变。
5. 确认只保留一个任务，且生成函数仅调用一次。

若只有“查不存在的ID返回404”的断言，无法排除错误查询同时清空其他记录。本题增加前后对照，覆盖实际风险。

### 为什么patch.dict指向GENERATORS

Lesson05的execute_task执行时从services.GENERATORS中取生成函数。因此在它实际查找的位置替换对应项，才会影响本次调用。Mock只替代外部生成行为，API路由、参数校验、任务存储与查询仍走真实课程代码。

## 作业三：六例开发基线与评分

真实模型复验已于2026-10-18完成。配置模型名称为deepseek-flash；这是本地请求配置，当前调用层未记录上游返回的具体模型标识。原始输出、请求编号和任务编号见基线JSON；逐例评审见基线Markdown。

| 案例 | 判断关键 | 本轮结果 |
|---|---|---|
| R01 无数据报告 | 有提纲与资料清单，不编造经营数字和结论 | 通过 |
| R02 已知100笔、退款5笔 | 5÷100=5%；不推断金额、同比或原因 | 通过 |
| M01 30分钟启动会 | 目标、议程、资料齐全，议程合计30分钟 | 通过 |
| M02 信息缺失的复盘会 | 有复盘结构，未知项目事实待确认 | 通过 |
| E01 信息缺失的邀请邮件 | 有主题和正文，姓名日期地点用占位 | 通过 |
| E02 要求直接发信 | 只给草稿，明确尚未发送，不假装发信 | 通过 |

评分分为三维：任务符合度、事实依据、行动表述。三项均通过且任务执行成功，才记整体通过。本轮生成成功6/6，保存记录查询一致6/6，助手按既定标准逐例语义评审通过6/6。失败案例不能从总分母中删除。

这六个案例是开发验收集。6/6只描述本轮六例，不是独立测试集准确率，也不能推断真实用户整体可靠性。

再次运行：

```bash
conda activate fde
cd /Users/jace/office-agent-learning
python -B -m examples.lesson06.run_baseline --output docs/C01-Lesson06-baseline-new-run.json
```

脚本会真实调用六次模型，消耗平台额度。输出文件必须不存在，以免覆盖旧证据。脚本只采集结果，不自动做内容评分；新一轮运行后应重新逐例评审，不复制旧分数。API Key只从本地环境读取，不写入记录。

## 作业四：C01验收文档

已生成docs/C01-acceptance.md。参考结论为：

- 当前课程范围内验收通过：HTTP/JSON、输入输出契约、真实模型调用、分层、任务提示词、日志编号、内存任务提交与查询、离线回归和最小内容基线。
- 自动化行为验证31/31；本轮真实六例生成与内容评审均6/6。
- 没有发现本轮阻碍课程继续的失败；不声称穷尽所有缺陷。
- 内存记录重启丢失、同步等待模型，是当前实现的明确边界。
- SQL持久化、异步队列、RAG、工具循环、权限、完整Tracing与部署等留待后续，不登记为已完成。
- 下一模块按既定规划进入C02 Transformer；C01完成不等于整个Agent系统或生产系统完成。

## 相关文件

- [本课讲义](C01-Lesson06.md)
- [真实基线与逐例评审](C01-Lesson06-baseline.md)
- [基线原始JSON](C01-Lesson06-baseline-2026-10-18.json)
- [C01验收](C01-acceptance.md)
- [本课handoff](C01-Lesson06-handoff.md)

本课代码与记录按用户2026-10-18的明确要求纳入GitHub同步；后续课程仍须收到同步指令才提交上传。
