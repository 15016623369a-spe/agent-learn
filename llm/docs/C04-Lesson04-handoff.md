# C04 Lesson04 · 交接

2026-11-15。Lesson04《Token 预算与信息取舍》已授课，用户已索要答案并明确要求同步。第 5 课接续《JSON 与 Schema》。

课堂代码沿用 Lesson03 的上下文构造和来源索引。用本地缓存的聊天模板和分词器测量实际输入长度，预留输出空间，按顺序移除可选资料，保留金额单位冲突及工具未执行状态。剩余资料超限时停止发送。本次在线发布的材料记录的是离线计数和手写资料。

从仓库根目录运行 `python -B llm/lesson04.py` 或 `python -B -m llm.lesson04`，沿用 `fde`。本轮复核两种入口的输出一致，并复跑四题。详细结果见 [讲义](C04-Lesson04-notes.md) 和 [参考答案](C04-Lesson04-homework.md)。

Lesson05 可沿用 `answer`、`used_source_ids`、`missing_information` 三个字段，先观察 JSON 语法错误，再用 Schema 检查必填字段和类型。引用是否存在、能否支持结论及失败处理留到 Lesson06 深入。
