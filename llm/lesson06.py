"""C04 Lesson06 · 输出校验与失败处理。

在 llm 的父目录运行 python -B llm/lesson06.py 或 python -B -m llm.lesson06。
沿用 fde。响应、工具状态与修正结果均为预先写好的课堂样例。
2026-11-15 补录四道作业的参考演示。
"""

from collections.abc import Callable
from copy import deepcopy
import json

from jsonschema import Draft202012Validator

if __package__:
    from .lesson03 import build_context, resolve_sources
    from .lesson05 import REPORT_SCHEMA
else:
    from lesson03 import build_context, resolve_sources
    from lesson05 import REPORT_SCHEMA


TOTALS_FIELD = "department_totals_fen"
QUERY_SOURCE_ID = "T01"
REPAIRABLE_ERRORS = {"parse_error", "schema_error"}


def make_lesson06_validator() -> Draft202012Validator:
    schema = deepcopy(REPORT_SCHEMA)
    schema["properties"][TOTALS_FIELD] = {
        "type": ["object", "null"],
        "propertyNames": {"minLength": 1},
        "additionalProperties": {"type": "integer", "minimum": 0},
    }
    schema["required"].append(TOTALS_FIELD)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_output(raw_text: str, validator: Draft202012Validator, context: dict) -> dict:
    """每层通过后才进入下一层，失败时返回错误，成功时返回结构化数据。"""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        return {
            "code": "parse_error",
            "detail": f"第 {error.lineno} 行，第 {error.colno} 列",
        }

    errors = list(validator.iter_errors(data))
    if errors:
        return {
            "code": "schema_error",
            "detail": [
                {"path": error.json_path, "rule": error.validator, "message": error.message}
                for error in errors
            ],
        }

    try:
        resolve_sources(context, data["used_source_ids"])
    except ValueError as error:
        return {"code": "unknown_source", "detail": str(error)}

    totals = data[TOTALS_FIELD]
    if totals is not None:
        # 从应用持有的 T01 读取执行状态与结果。待审响应只提供候选金额。
        query = next(
            (record for record in context["tool_results"] if record["source_id"] == QUERY_SOURCE_ID),
            None,
        )
        if query is None or query["execution_status"] != "succeeded":
            return {"code": "tool_not_ready", "detail": "订单查询没有成功结果"}
        if totals != query["totals_fen"]:
            return {"code": "totals_mismatch", "detail": "候选部门金额与查询结果不一致"}
        if QUERY_SOURCE_ID not in data["used_source_ids"]:
            return {"code": "missing_tool_source", "detail": "金额需要引用本次查询结果 T01"}

    return {"code": "ok", "data": data}


def review_with_one_repair(
    raw_text: str,
    validator: Draft202012Validator,
    context: dict,
    repair: Callable[[dict], str] | None = None,
) -> dict:
    """格式错误可请求一次修正。修正结果从第一层重新校验。"""
    first = validate_output(raw_text, validator, context)
    attempts = [first["code"]]
    result = first
    if first["code"] in REPAIRABLE_ERRORS and repair is not None:
        corrected_text = repair(first)
        result = validate_output(corrected_text, validator, context)
        attempts.append(result["code"])

    accepted = result["code"] == "ok"
    return {
        "status": "accepted" if accepted else "rejected",
        "attempts": attempts,
        "data": result.get("data"),
        "error": None if accepted else result,
    }


def demo_context(*, query_succeeded: bool) -> dict:
    """构造应用持有的教学上下文，金额以分为单位且仅统计已支付订单。"""
    query = {
        "source_id": QUERY_SOURCE_ID,
        "source": "手写工具状态/订单查询",
        "execution_status": "succeeded" if query_succeeded else "not_executed",
    }
    if query_succeeded:
        query["totals_fen"] = {"销售部": 12500}
    return build_context(
        "统计2026年9月各部门订单金额，并说明依据。",
        history=[],
        documents=[{
            "source_id": "D01",
            "source": "教学文档/订单统计口径",
            "content": "仅统计已支付订单，不计退款，金额统一使用分。",
        }],
        tool_results=[query],
    )


def run_homework(
    waiting_report: dict, validator: Draft202012Validator, pending_context: dict
) -> None:
    """实跑四题的参考输入与结果。"""
    print("\n作业 1 · 确认先失败的层")
    invalid_report = {**waiting_report, "used_source_ids": "D99", TOTALS_FIELD: {"销售部": -1}}
    corrected_report = {**waiting_report, "used_source_ids": ["D99"], TOTALS_FIELD: {"销售部": 0}}
    for title, report in (("字段类型与范围错误", invalid_report), ("改好结构，保留未知编号", corrected_report)):
        raw_text = json.dumps(report, ensure_ascii=False)
        print(title, validate_output(raw_text, validator, pending_context))

    print("\n作业 2 · 确认修正次数")
    repair_calls = 0

    def return_empty_object(_error: dict) -> str:
        nonlocal repair_calls
        repair_calls += 1
        return "{}"

    fenced = "```json\n" + json.dumps(waiting_report, ensure_ascii=False) + "\n```"
    result = review_with_one_repair(fenced, validator, pending_context, return_empty_object)
    print(f"修正调用次数 {repair_calls} | attempts {result['attempts']} | "
          f"status {result['status']} | data {result['data']}")

    print("\n作业 3 · 比较金额状态")
    for totals in (None, {}, {"销售部": 0}):
        report = {**waiting_report, TOTALS_FIELD: totals}
        result = validate_output(json.dumps(report, ensure_ascii=False), validator, pending_context)
        print(f"{json.dumps(totals, ensure_ascii=False)} | {result['code']}")

    print("\n作业 4 · 自由文本的校验范围")
    unsafe_report = {**waiting_report, "answer": "销售部订单金额为 100 万元。"}
    result = review_with_one_repair(json.dumps(unsafe_report, ensure_ascii=False), validator, pending_context)
    print(f"现有校验 {result['attempts'][-1]} | {result['status']}")
    print("展示规则：金额只从通过核对的结构化金额字段生成，金额缺失时使用应用固定文案。")
    print("本案例可展示：当前暂无可核对的部门金额。")


def main() -> None:
    validator = make_lesson06_validator()
    pending_context = demo_context(query_succeeded=False)
    finished_context = demo_context(query_succeeded=True)
    waiting_report = {
        "answer": "订单查询尚未执行，等待汇总结果。",
        "used_source_ids": ["T01"],
        "missing_information": ["执行订单查询"],
        TOTALS_FIELD: None,
    }
    completed_report = {
        "answer": "订单查询已完成，汇总见部门金额字段。",
        "used_source_ids": ["D01", "T01"],
        "missing_information": [],
        TOTALS_FIELD: {"销售部": 12500},
    }
    waiting_json = json.dumps(waiting_report, ensure_ascii=False)
    completed_json = json.dumps(completed_report, ensure_ascii=False)
    unknown_source_json = json.dumps({**waiting_report, "used_source_ids": ["D99"]}, ensure_ascii=False)
    mismatched_json = json.dumps({**completed_report, TOTALS_FIELD: {"销售部": 12600}}, ensure_ascii=False)
    missing_source_json = json.dumps({**completed_report, "used_source_ids": ["D01"]}, ensure_ascii=False)
    fenced_json = "```json\n" + waiting_json + "\n```"

    # 修正函数模拟返回固定文本。这里可观察校验流程和调用次数。
    for title, raw_text, context, corrected in (
        ("查询未执行，报告如实说明", waiting_json, pending_context, None),
        ("格式错误，修正后通过", fenced_json, pending_context, waiting_json),
        ("格式错误，修正后缺必填字段", fenced_json, pending_context, "{}"),
        ("结构错误，修正后出现未知来源", "{}", pending_context, unknown_source_json),
        ("引用未知来源", unknown_source_json, pending_context, waiting_json),
        ("未查询却给出金额", completed_json, pending_context, waiting_json),
        ("金额与查询结果不一致", mismatched_json, finished_context, None),
        ("金额一致但缺少查询引用", missing_source_json, finished_context, None),
        ("金额与查询结果一致", completed_json, finished_context, None),
    ):
        repair = None
        if corrected is not None:
            def repair(_error, text=corrected):
                return text

        result = review_with_one_repair(raw_text, validator, context, repair)
        error = result["error"]
        print(f"{title} | {' → '.join(result['attempts'])} | {result['status']}")
        if error is not None:
            print(" ", error["detail"])

    run_homework(waiting_report, validator, pending_context)


if __name__ == "__main__":
    main()
