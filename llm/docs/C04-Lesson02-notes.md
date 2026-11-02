# C04 Lesson02：提示结构与示例

更新日期：2026-11-02（Asia/Shanghai）。本课已完成，唯一课堂实现为 [lesson02.py](../lesson02.py)，复用上一课的 build_task_contract。

## 知识点

将笼统的“专业、准确”改为任务、输入资料、约束、输出约定四部分。SYSTEM_PROMPT 规定说明缺项和下一步，状态与程序契约一致，不得编造读取、计算或金额。

user_message 将契约包装在 task_contract 下并转换为字符串。JSON只负责序列化，不保证模型遵循约束，也不提供安全隔离。

V0没有输入输出示例；V1在相同规则和当前输入前加入三组示例。示例是请求上下文，不更新模型参数。三组assistant消息由教师手写，不是实际模型响应或业务执行记录。

## 最终实现

- user_message：将当前契约或示例契约包装为user消息。
- build_examples：缺数据来源、四项齐全、只缺分组口径，共三组输入输出示例。
- build_prompt：只接受v0/v1。使用extend展开示例列表，最后append当前任务，避免嵌套列表和任务位置错误。
- main：固定A/B/C三个当前输入，各构造两个版本；打印摘要、角色顺序、B/v1完整消息及第一题和第四题参考答案。
- COMPARISON_PLAN：固定条件、四项指标和待保存记录；model_response为None，质量结论为待验证。

课堂原始版本有两组示例，V1为6条消息；完成第3题后有三组，V1为8条。动态统计assistant消息数量，避免仍显示example_pairs=2。

## 最终实际输出

| 当前输入 | 状态 | 缺项数 | V0消息数/示例组数 | V1消息数/示例组数 |
|---|---|---:|---|---|
| A：只有需求 | needs_info | 4 | 2 / 0 | 8 / 3 |
| B：只有时间与金额口径 | needs_info | 2 | 2 / 0 | 8 / 3 |
| C：四项均已声明 | ready_for_calculation | 0 | 2 / 0 | 8 / 3 |

示例信息不属于当前任务，所以增加示例不改变当前缺项。C中的数据文件仍是未读取、未核验的教学占位。

V0角色顺序为system、user。V1为system、三组user/assistant、最后一条当前user，共8条。

本轮真实运行记录见 [output.txt](C04-Lesson02-output.txt)，实际检查和代码哈希见 [verification.json](C04-Lesson02-verification.json)。

## 运行与解释

沿用Conda fde，Python 3.11.16。在仓库根目录执行：

```bash
python -B llm/lesson02.py
python -B -m llm.lesson02
```

直接运行使用同目录导入lesson01，模块运行使用相对导入.lesson01。上一课入口受__name__保护，导入函数不会打印上一课课堂输出。

本地日常课堂文件固定放在 /Users/jace/agent学习/llm/；仓库中的llm/是用户明确保留的同步副本。后续新课先在固定课堂目录保存，明确要求同步后才更新仓库。

## 易错点与边界

append整个列表会制造嵌套列表，extend才会逐条追加。role=assistant只是角色标记，不证明内容来源。要求JSON不等于已收到或校验JSON。固定seed不保证跨平台完全确定。

本课未读取.env、调用模型、读取订单或执行金额汇总。没有真实模型响应，不能填入成功率或宣称V1优于V0。正式模型输出校验和回归评估留待后续课程。本次没有安装或升级依赖。

参考：课堂涉及的few-shot概念可见 https://arxiv.org/abs/2005.14165 。
