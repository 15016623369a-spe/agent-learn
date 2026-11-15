# C04 Lesson05 · JSON 与 Schema

订单分析示例沿用三个输出字段。应用从 `answer` 读取结论，从 `used_source_ids` 读取引用编号，从 `missing_information` 读取待补信息。

1. `json.loads()` 把 JSON 文本转成 Python 数据。带 Markdown 围栏的文本会触发 `JSONDecodeError`。
2. `Draft202012Validator.iter_errors()` 对解析后的数据检查结构。本课要求顶层为对象、三个字段都出现，且拒绝额外字段。引用数组中的每项必须是非空字符串，引用编号不可重复。
3. 通过结构校验之后，应用还需核对来源索引和引用内容。Lesson06 将接着实现业务校验和失败处理。

课堂实测覆盖六条手写响应。完整示例通过，Markdown 围栏触发解析错误，缺字段、引用类型错误和多余字段分别触发 `required`、`type`、`additionalProperties`。带 `D99` 的金额结论也通过结构校验，因为规则只检查来源编号的形状。

`properties` 规定字段存在时如何检查，`required` 规定字段是否必须出现。例如缺少 `missing_information` 会失败，而空数组符合当前约定。错误路径 `$` 表示根对象，`$.used_source_ids[0]` 表示来源数组的第一个元素。 [JSON Schema 对象规则](https://json-schema.org/understanding-json-schema/reference/object)
