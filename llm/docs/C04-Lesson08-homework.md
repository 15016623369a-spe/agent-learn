# C04 Lesson08 · 四题参考答案

1. 提供 120 个输出 Token。总预算 644 时，输入上限 524，移除 H02 后仍需 525，返回 `over_budget`，响应调用 0 次。总预算 645 时刚好容纳 525，调用 1 次并返回 `report_ready`。
2. 默认预算下最终 `source_index` 只有 D01 和 T01。引用 H02 会得到 `invalid_response` 和 `unknown_source`。
3. T01 成功且结果为空时，响应填 `{}` 得到 `report_ready`，显示「查询已完成，没有符合条件的订单。」和「依据：D01、T01」。填 `null` 会通过基础校验，但交付检查返回 `incomplete_report`。
4. 第一次响应带围栏，修正结果把销售部金额改成 12600 分，而查询结果为 12500 分。修正调用 1 次，轨迹为 `parse_error → totals_mismatch`，最终 `invalid_response`，没有可展示的报告。

四题使用课堂原脚本的函数复跑。本页为助手整理的参考答案。
