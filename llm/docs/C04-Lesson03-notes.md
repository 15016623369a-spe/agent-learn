# C04 Lesson03：上下文组织

更新日期：2026-11-09（Asia/Shanghai）。本课已完成，唯一实现见 [lesson03.py](../lesson03.py)。

## 核心知识

上下文应明确区分应用规则、当前问题、对话历史、参考文档和工具信息。应用规则定义允许的行为；业务文档说明事实与口径，不能授权伪造执行结果。历史也可能过时或冲突，工具状态要区分尚未执行、失败与成功。

每条资料保留source_id、source和content。source_id是当前上下文中的引用编号，source说明来源位置，content保存正文。来源元数据并不证明真实性、版本有效性或事实正确。

build_context用deepcopy保存嵌套资料副本；检查空问题、编号类型/空白与跨类别重复，再建立source_index。索引保存类别和位置，正文仍在原分组中。函数不判断文档有效性和冲突，也没有完整Schema校验。

build_messages只构造system与user两条消息；应用规则进system，问题、history、documents、tool_results与索引以JSON资料进user。教学历史不是实际多轮消息，手写工具状态也不是工具协议的真实响应。

resolve_sources只检查编号存在并返回类别和来源位置。引用编号有效不等于内容支持结论。

## 本次最终输入与结果

用户在原文件中已加入D03，保留其代码和注释。当前包含H01一条历史、D01/D02/D03三条文档、T01一条未执行工具状态。D01写金额单位为分，D03写为元，且二者目前标注相同来源位置；需要核实，不应擅自把其中一个当权威版本。

最终来源编号H01、D01、D02、D03、T01；角色system、user；generation_executed=false。本课开课时两条文档的历史输出不作为当前最终输出。

D02的不可信指令保留在文档资料中，不进入system。这里只能证明代码按类别组织，不证明模型已抵抗注入。T01明确标not_executed，不能作为完成查询或汇总的证据。

## 作业补录

用户索要答案按既有约定登记私下完成后对照。本轮run_homework由助手补录：打印五种信息身份，追踪D03，在副本中制造重复编号并恢复正常追踪，查询D99，以及打印手写期望回答与错误引用反例的人工分析。

没有改变build_context或resolve_sources的语义，也没有添加自动冲突裁决或语义支持校验。手写答案明确标注不是模型响应。

## 运行与边界

沿用Conda fde，无新增依赖。在仓库根目录执行：

```bash
python -B llm/lesson03.py
python -B -m llm.lesson03
```

编辑器使用fde直接运行同一文件。日常课堂文件固定保存在 /Users/jace/agent学习/llm/；仓库llm/是用户要求保留的同步副本。

本轮实际stdout见 [运行输出](C04-Lesson03-output.txt)，环境、检查和哈希见 [验证记录](C04-Lesson03-verification.json)。没有读取订单、计算金额、调用模型或验证引用支持/抗注入效果，也没有执行RAG。
