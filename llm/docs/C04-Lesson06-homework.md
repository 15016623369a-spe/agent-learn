# C04 Lesson06 · 四题参考答案

脚本中的四题参考代码由助手补录。以下为手写样例的离线结果。

1. **先失败的一层。** `used_source_ids: "D99"` 在 `$.used_source_ids` 触发 `type`，销售部金额为 -1 在 `$.department_totals_fen['销售部']` 触发 `minimum`，本轮返回 `schema_error`。改为 `["D99"]` 和 0 后，结构通过，校验进入业务层并返回 `unknown_source`。金额和查询状态检查排在来源检查之后。
2. **只修一次。** 第一次对带围栏的文本返回 `parse_error`。修正函数被调用 1 次，返回 `{}`，随后产生 `schema_error`。最终 `attempts = ["parse_error", "schema_error"]`，`status = "rejected"`，`data = None`。
3. **金额的三种状态。** T01 尚未执行时，`null` 返回 `ok`，因为报告没有提供汇总。`{}` 表示提供了一个空汇总，`{"销售部": 0}` 表示销售部汇总为零。两条都提交了具体结果形态，都返回 `tool_not_ready`。
4. **自由文本。** 金额字段为 `null`、正文声称「销售部订单金额为 100 万元」的样例，当前返回 `ok` 和 `accepted`。展示层应只用已经核对的结构化数据生成金额文案。这个样例可以展示「当前暂无可核对的部门金额」，正文里的 100 万元没有展示依据。
