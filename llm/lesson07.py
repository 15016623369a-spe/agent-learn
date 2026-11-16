"""C04 Lesson07 · 提示与上下文回归评估。

在 llm 的父目录运行 python -B llm/lesson07.py 或 python -B -m llm.lesson07。
请求、工具状态、预期结果与两版响应均为课堂样例，使用 fde 离线运行。
"""

import json

if __package__:
    from .lesson03 import build_context, build_messages
    from .lesson06 import TOTALS_FIELD, make_lesson06_validator, validate_output
else:
    from lesson03 import build_context, build_messages
    from lesson06 import TOTALS_FIELD, make_lesson06_validator, validate_output


PROMPTS = {
    "v0": "按约定给出结论、来源和待补信息。",
    "v1": "只输出裸 JSON，优先简洁，每份报告只列最相关的一条来源。",
}
METRICS = ("format_ok", "citations_ok", "task_ok", "passed")
WAITING = "执行订单查询"
CHECK_UNIT = "核实金额单位"


def build_cases() -> list[dict]:
    """共用任务场景，给每个固定输入标注可检查的期望。"""
    specs = [
        # ID, 分组, 问题, 查询金额, 预期引用, 预期缺项
        ("dev-01", "dev", "9 月订单查询没运行，下一步做什么？", None, ["T01"], [WAITING]),
        ("dev-02", "dev", "给出 9 月部门汇总，并说明统计口径和查询依据。",
         {"销售部": 12500}, ["D01", "T01"], []),
        ("dev-03", "dev", "没有查到结果，可以先给销售部一个估算金额吗？",
         None, ["T01"], [WAITING]),
        ("dev-04", "dev", "两份金额单位说明冲突，还能直接统计吗？",
         None, ["D01", "D02", "T01"], [CHECK_UNIT, WAITING]),
        ("hold-01", "holdout", "已查询到 9 月没有符合条件的订单，请返回汇总。",
         {}, ["T01"], []),
        ("hold-02", "holdout", "有没有可引用的 9 月查询记录？",
         None, ["T01"], [WAITING]),
    ]
    cases = []
    for case_id, split, question, totals, required_ids, expected_missing in specs:
        documents = [{
            "source_id": "D01", "source": "教学口径/版本 A",
            "content": "仅统计已支付订单，金额单位为分。",
        }]
        if case_id == "dev-04":
            documents.append({
                "source_id": "D02", "source": "教学口径/版本 B",
                "content": "金额单位为元。",
            })
        query = {
            "source_id": "T01", "source": "手写订单查询状态",
            "execution_status": "not_executed" if totals is None else "succeeded",
        }
        if totals is not None:
            query["totals_fen"] = totals

        cases.append({
            "id": case_id,
            "split": split,
            "context": build_context(question, [], documents, [query]),
            "required_ids": required_ids,
            "expected_missing": expected_missing,
            "expected_totals": totals,
            # 只检查这个案例里预先标注的具体错误文本。
            "forbidden_fragments": ("100 万元",) if case_id == "dev-03" else (),
        })
    return cases


def report(answer: str, source_ids: list[str], missing: list[str], totals: dict | None = None) -> str:
    return json.dumps({
        "answer": answer,
        "used_source_ids": source_ids,
        "missing_information": missing,
        TOTALS_FIELD: totals,
    }, ensure_ascii=False)


def build_fixture_responses() -> dict:
    """为两种提示版本准备可复现的人工响应，模拟进入评估器的数据。"""
    pending = report("查询尚未执行。", ["T01"], [WAITING])
    good_totals = report("汇总已完成。", ["D01", "T01"], [], {"销售部": 12500})
    conflict = report("两份金额单位说明冲突，需核实。", ["D01", "D02", "T01"], [CHECK_UNIT, WAITING])
    return {
        "v0": {
            "dev-01": "```json\n" + pending + "\n```",
            "dev-02": good_totals,
            "dev-03": report("估算销售部订单金额为 100 万元。", ["T01"], [WAITING]),
            "dev-04": conflict,
            "hold-01": report("查询已完成，结果为空。", ["T01"], [], {}),
            "hold-02": report("查询尚未执行。", ["T01", "D99"], [WAITING]),
        },
        "v1": {
            "dev-01": pending,
            "dev-02": report("汇总已完成。", ["T01"], [], {"销售部": 12500}),
            "dev-03": pending,
            "dev-04": report("按分统计即可。", ["D01"], [WAITING]),
            "hold-01": report("没有可用汇总。", ["T01"], []),
            "hold-02": pending,
        },
    }


def evaluate_case(case: dict, raw_text: str, validator) -> dict:
    checked = validate_output(raw_text, validator, case["context"])
    code = checked["code"]
    format_ok = code not in {"parse_error", "schema_error"}
    citations_ok, task_ok = False, False
    if format_ok:
        # 业务校验失败时仍可诊断结构正确的候选输出。它只用于打分。
        data = json.loads(raw_text)
        used_ids = set(data["used_source_ids"])
        available_ids = set(case["context"]["source_index"])
        citations_ok = set(case["required_ids"]) <= used_ids <= available_ids
        task_ok = (
            data[TOTALS_FIELD] == case["expected_totals"]
            and sorted(data["missing_information"]) == sorted(case["expected_missing"])
            and not any(fragment in data["answer"] for fragment in case["forbidden_fragments"])
        )

    return {
        "id": case["id"],
        "split": case["split"],
        "validation": code,
        "format_ok": format_ok,
        "citations_ok": citations_ok,
        "task_ok": task_ok,
        "passed": code == "ok" and citations_ok and task_ok,
    }


def evaluate_version(cases: list[dict], version: str, fixture_responses: dict, validator) -> list[dict]:
    results = []
    for case in cases:
        messages = build_messages(case["context"])
        messages[0]["content"] += "\n【本版提示】" + PROMPTS[version]
        # 课堂夹具按版本和案例 ID 取响应。真实评估在这里发送 messages 并保存响应。
        raw_text = fixture_responses[version][case["id"]]
        result = evaluate_case(case, raw_text, validator)
        result["messages"] = messages
        results.append(result)
    return results


def main() -> None:
    cases = build_cases()
    responses = build_fixture_responses()
    validator = make_lesson06_validator()
    baseline = evaluate_version(cases, "v0", responses, validator)
    candidate = evaluate_version(cases, "v1", responses, validator)

    print("离线课堂响应评估")
    for version, prompt in PROMPTS.items():
        print(f"{version} 提示补充 | {prompt}")

    for split in ("dev", "holdout"):
        print(f"\n{split}")
        for version, results in (("v0", baseline), ("v1", candidate)):
            group = [r for r in results if r["split"] == split]
            counts = " | ".join(f"{m}={sum(r[m] for r in group)}/{len(group)}" for m in METRICS)
            print(f"{version} | {counts}")
        for before, after in zip(baseline, candidate):
            if before["split"] != split:
                continue
            if before["passed"] != after["passed"]:
                change = "回归" if before["passed"] else "改善"
            else:
                change = "结果不变"
            failed = [m for m in METRICS[:-1] if not after[m]]
            print(
                f"{before['id']} | {change} | 校验 {before['validation']} → {after['validation']}"
                f" | v1 未达指标 {', '.join(failed) or '无'}"
            )


if __name__ == "__main__":
    main()
