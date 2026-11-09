# C04 Lesson03 handoff

更新日期：2026-11-09（Asia/Shanghai）。主题：上下文组织。本课已完成，下一课 **C04 Lesson04：Token预算与信息取舍**。

## 完成与证据来源

用户要求本课答案并同步GitHub；按既有索要答案约定登记本课完成后对照。用户提供文件已加入D03冲突样例。本轮保留该实现及原有注释，助手补入run_homework演示：信息身份、D03来源追踪、副本中的重复编号、未知编号、手写期望回答与错误引用分析。

本次日常课堂文件与仓库同步副本内容一致，实际执行和校验结果见 [验证](C04-Lesson03-verification.json)、[输出](C04-Lesson03-output.txt)。完整 [讲义](C04-Lesson03-notes.md) 与 [四题答案](C04-Lesson03-homework.md) 已整理。

## 当前实现

上下文包含history1、documents3、tool_results1，编号H01、D01、D02、D03、T01，待发送角色system/user。D01单位分、D03单位元，且来源位置元数据相同；需要核实，不自动裁决。D02仅为资料中的不可信指令，T01明确标not_executed。

build_context进行分组、深复制与编号检查；resolve_sources只验证编号存在，不判断内容支持。没有完整Schema、自动版本有效性判断、自动冲突处理或语义验证器。所有课堂历史、文档、工具状态、期望回答均为手写样例，不是检索结果或真实运行日志。

本轮没有模型调用、订单读取、金额汇总、检索或RAG；不登记模型效果和注入防护通过。

## 文件与同步约定

日常代码固定放在 /Users/jace/agent学习/llm/，仓库 /Users/jace/agent学习/office-agent-learning/llm/ 作为用户明确保留的同步副本。每课一份课堂实现，不另生成答案脚本；用户明确要求同步后再更新仓库。

本次仅提交Lesson03代码、讲义、作业、输出、验证、交接及两份README索引。保留C01与Lesson01/02，排除原有examples/lesson05/api.py修改和.vscode/。

沿用Conda fde，使用Python标准库，无新增依赖。直接运行python -B llm/lesson03.py，模块运行python -B -m llm.lesson03，均在相应llm父目录执行；编辑器可直接运行固定课堂文件。

## 下一课接续

Lesson04先讲实际格式化输入的Token计数、预留输出空间与预算检查，再做明确的超限处理，保留关键规则、当前问题及来源。不能以汉字数代替Token数，不能沿用其他模型的上下文配置。先核对已有Tokenizer与缓存；没有实际测量不得写成测量完成。

继续中文聊天详细讲解、教师代码和解释、实测与易错点、最后统一四题作业。用户说下一课仅触发教学，不自动发布或新建聊天。

C04 Lesson04–08尚未授课，RAG预习尚未执行，正式RAG未开始。C03补充练习仍单列保留，主项目和2027年1月投递目标继续沿用。
