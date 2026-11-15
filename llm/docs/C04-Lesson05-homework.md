# C04 Lesson05 · 四题参考答案

参考实现由助手补录到原课堂脚本。以下结果来自手写样例的离线运行。

1. **区分解析和校验。** `{"answer": "示例",}` 在第 1 行第 17 列触发解析错误。`{}` 能解析，在根路径 `$` 触发三条 `required`，分别缺少 `answer`、`used_source_ids`、`missing_information`。`[]` 能解析，在 `$` 触发 `type`，因为顶层要求对象。
2. **检查数组边界。** `[]` 通过，因为 Schema 允许空数组。`["D01", "D01"]` 在 `$.used_source_ids` 触发 `uniqueItems`。`[""]` 在 `$.used_source_ids[0]` 触发 `minLength`。
3. **扩展 Schema。** 在副本的 `properties` 添加 `status`，定义为字符串，`enum` 为 `["needs_info", "ready_for_calculation"]`，并把它加入 `required`。`needs_info` 通过，`need_info` 在 `$.status` 触发 `enum`，省略字段在 `$` 触发 `required`。
4. **找出结构校验的边界。** 两条响应都声称“已经算出销售部订单金额 100 万元”，待补信息均为空数组，分别引用 `["D99"]` 和 `["T01"]`，两条都通过 Schema。应用应先查本次请求的来源索引，发现 D99 不存在。T01 存在，但它记录查询尚未执行，应用还需要核对工具状态和可追溯的统计结果。
