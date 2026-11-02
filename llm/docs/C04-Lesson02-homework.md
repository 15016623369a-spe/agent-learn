# C04 Lesson02：四题作业与答案

日期：2026-11-02（Asia/Shanghai）。按既有约定，用户索要答案视为私下完成后对照。本轮用户同时明确要求把作业代码加进原文件；新增作业实现由助手补录，不追溯为用户此前已经保存的独立代码。代码实际运行与个人完成确认分别记录。

## 第1题：四部分提示

把“你是专业办公助手，请分析订单并给出准确报告”改成任务、输入资料、约束、输出约定。

答案在SYSTEM_PROMPT中：任务是说明缺项和下一步；资料是当前task_contract；约束是状态和缺项与契约一致，不编造读取、计算和金额；输出是status、missing_information、next_action三个字段的JSON对象。main末尾会打印完整提示。

## 第2题：消息角色顺序

main的循环内打印 `[m["role"] for m in messages]`。

- V0：system、user，共2条。
- 原始两组示例V1：system、两组user/assistant、当前user，共6条。
- 本次补入第三组后V1：system、三组user/assistant、当前user，共8条。

最后的user承载当前任务，前面的assistant是教师手写示范，不是模型本轮生成。

## 第3题：只缺分组口径

build_examples从ready的known_information中仅移除grouping_definition，再调用上一课build_task_contract。这样时间、金额和数据来源保留，只缺一项分组口径。

期望状态为needs_info，缺项为“需要明确按下单时所属部门，还是员工当前部门分组”，下一步为请求确认部门归属口径。该示例作为第三个输入输出对加入原有循环。

example_pairs改为 `sum(m["role"] == "assistant" for m in messages)`，按本课每组一条assistant的结构得到V0=0、V1=3。V1消息数由6变8，但当前A/B/C缺项仍为4/2/0，不能借用示例资料补齐当前任务。

## 第4题：对照计划

完整计划存放在COMPARISON_PLAN，并在main末尾打印。

| 内容 | 参考答案 |
|---|---|
| 固定条件 | 相同A/B/C输入、SYSTEM_PROMPT、供应商/模型版本、生成参数；固定示例内容和顺序，提前约定重复次数 |
| 唯一变化 | 是否加入三组示例 |
| 状态一致 | 输出status等于当前契约input_status |
| 缺项一致 | 输出missing_information与当前契约缺项列表一致 |
| JSON格式 | 可解析为JSON对象且恰好包含约定三个字段 |
| 没有虚构执行 | 逐条复核是否声称已读取、已计算或编造金额 |
| 保存记录 | case_id、提示版本与完整messages、模型标识、参数、重复序号、原始响应和失败信息、逐项判断及人工复核来源；可用时记录Token和延迟 |

如接口支持seed，固定并记录，但不据此宣称跨平台完全确定。所有失败记录也应保存，不能只挑成功样本。

当前model_response=None，quality_conclusion为“待验证：本文件只构造提示，未调用真实模型”。本题完成的是实验计划，不是真实模型效果比较。

## 完成依据

四题按用户索要答案的既有约定登记完成；四题代码由助手依用户要求补入原文件。本轮检查明确验证角色顺序、三组示例、唯一缺分组口径、动态数量、当前输入与规则保持一致及待验证状态，不补造用户私人练习或模型调用历史。
