# C04 Lesson02 handoff

更新日期：2026-11-02（Asia/Shanghai）。主题：提示结构与示例。本课已完成，下一课为 **C04 Lesson03：上下文组织**。

## 当前状态

用户已索要四题答案，按既有约定登记私下完成后对照；同时要求助手把作业代码加入原文件。随后明确授权同步GitHub。用户完成确认、助手补录和本轮代码实际验证分别登记。

原课堂两组示例V1为6条消息，完成作业后为三组、8条消息。V0仍为2条。A/B/C缺项为4/2/0，增加示例不改变当前输入的事实。

四题答案均在唯一课堂文件llm/lesson02.py：SYSTEM_PROMPT、角色打印、第三组缺分组示例、动态示例计数、COMPARISON_PLAN。详情见 [讲义](C04-Lesson02-notes.md)、[作业答案](C04-Lesson02-homework.md)、[验证](C04-Lesson02-verification.json)、[原始输出](C04-Lesson02-output.txt)。

## 文件与环境

日常课堂代码固定保存于 `/Users/jace/agent学习/llm/`。用户已选择保留 `/Users/jace/agent学习/office-agent-learning/llm/` 作为GitHub同步副本。不要擅自迁移、删除同步副本或再生成其他课堂实现。

沿用Conda fde，实际Python3.11.16。本课复用同目录lesson01，无新增依赖。仓库根目录执行：

```bash
python -B llm/lesson02.py
python -B -m llm.lesson02
```

编辑器可直接运行固定课堂目录的lesson02.py。直接运行与模块运行采用不同导入方式，均须可用。

## 本次发布范围

本课代码、讲义、作业、实际stdout、验证记录、本交接；根README和llm/README更新索引、完成标识及下一课。保留用户代码和注释。C01代码和Lesson01既有记录保留。原有examples/lesson05/api.py工作区修改及.vscode/不纳入提交。

本次没有新增依赖、读取.env或真实调用模型。真实效果比较仍为待验证，不能登记模型成功率或V1优于V0。ready_for_calculation也不代表数据读取或金额计算完成。

## 下一课接续

从C04 Lesson03“上下文组织”开始，讲用户问题、规则、资料来源、历史与工具结果如何组合，明确资料与操作要求的边界，形成可追踪来源的上下文构造器。继续先聊天讲解、教师代码和逐段解释、实测及易错点、最后四题作业。

不自动新建聊天，不因用户说“下一课”自动同步GitHub。每课一份课堂实现，先保存固定课堂目录，明确同步时才更新仓库副本。

C04 Lesson03–08尚未授课；C03补充项继续单列保留；RAG预习尚未执行，正式RAG未开始。沿用企业知识驱动办公分析与报告Agent主项目，记住2027年1月投递起点。
