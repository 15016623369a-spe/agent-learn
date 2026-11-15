"""C04 Lesson05 · JSON 与 Schema。

在 llm 的父目录运行 python -B llm/lesson05.py 或 python -B -m llm.lesson05。
沿用 fde 已有的 jsonschema。示例响应是手写的，供离线解析和结构验证。
2026-11-15 补录四题参考演示。
"""

from copy import deepcopy
import json

from jsonschema import Draft202012Validator


REPORT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "answer": {"type": "string", "minLength": 1},
        "used_source_ids": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
        "missing_information": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
    },
    "required": ["answer", "used_source_ids", "missing_information"],
    "additionalProperties": False,
}


def make_report_validator() -> Draft202012Validator:
    # 启动时检查规则文档本身，再用同一个验证器检查多份数据。
    Draft202012Validator.check_schema(REPORT_SCHEMA)
    return Draft202012Validator(REPORT_SCHEMA)


def show_case(title: str, raw_text: str, validator: Draft202012Validator) -> None:
    print(f"\n{title}")
    # 第一步，把模型接口通常交付的文本当成 JSON 解析。
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        print(f"parse_error | 第 {error.lineno} 行，第 {error.colno} 列")
        return

    # 第二步，用 Schema 检查解析结果的字段、类型和结构。
    errors = list(validator.iter_errors(data))
    if not errors:
        print("schema_ok")
        return
    for error in errors:
        print(f"schema_error | {error.json_path} | {error.validator} | {error.message}")


def run_homework(expected: dict, validator: Draft202012Validator) -> None:
    """用手写样例复现四题，业务含义由人工解释。"""
    print("\n作业 1 · 区分解析和校验")
    for title, raw_text in (
        ("对象末尾多逗号", '{"answer": "示例",}'),
        ("空对象", "{}"),
        ("空数组", "[]"),
    ):
        show_case(title, raw_text, validator)

    print("\n作业 2 · 检查数组边界")
    for source_ids in ([], ["D01", "D01"], [""]):
        payload = {**expected, "used_source_ids": source_ids}
        show_case(str(source_ids), json.dumps(payload, ensure_ascii=False), validator)

    print("\n作业 3 · 扩展 Schema")
    # 在副本上添加必填状态，保留原课堂三个字段的约定。
    schema = deepcopy(REPORT_SCHEMA)
    schema["properties"]["status"] = {
        "type": "string",
        "enum": ["needs_info", "ready_for_calculation"],
    }
    schema["required"].append("status")
    Draft202012Validator.check_schema(schema)
    status_validator = Draft202012Validator(schema)
    for title, payload in (
        ("状态合法", {**expected, "status": "needs_info"}),
        ("状态拼错", {**expected, "status": "need_info"}),
        ("缺少状态", expected),
    ):
        show_case(title, json.dumps(payload, ensure_ascii=False), status_validator)

    print("\n作业 4 · 结构校验与业务检查")
    for source_id, explanation in (
        ("D99", "查询本次请求的来源索引，D99 不存在。"),
        ("T01", "T01 记录查询尚未执行，无法支持已算出金额的结论。"),
    ):
        payload = {
            "answer": "已经算出销售部订单金额 100 万元。",
            "used_source_ids": [source_id],
            "missing_information": [],
        }
        show_case(f"引用 {source_id}", json.dumps(payload, ensure_ascii=False), validator)
        print(f"后续业务检查 | {explanation}")


def main() -> None:
    validator = make_report_validator()
    # D01/D03 的单位矛盾，T01 显示查询尚未执行。
    expected = {
        "answer": "金额单位存在冲突，订单查询尚未执行。",
        "used_source_ids": ["D01", "D03", "T01"],
        "missing_information": ["确认适用的金额单位", "执行订单查询"],
    }
    expected_json = json.dumps(expected, ensure_ascii=False)
    missing_field = {
        key: value for key, value in expected.items() if key != "missing_information"
    }
    examples = [
        ("符合约定", expected_json),
        ("带 Markdown 围栏", "```json\n" + expected_json + "\n```"),
        ("缺必填字段", json.dumps(missing_field, ensure_ascii=False)),
        ("把来源数组写成字符串", json.dumps({
            **expected, "used_source_ids": "D01,D03,T01",
        }, ensure_ascii=False)),
        ("多出未定义字段", json.dumps({
            **expected, "debug": True,
        }, ensure_ascii=False)),
        ("内容缺少依据", json.dumps({
            "answer": "已经算出销售部订单金额 100 万元。",
            "used_source_ids": ["D99"],
            "missing_information": [],
        }, ensure_ascii=False)),
    ]

    for title, raw_text in examples:
        show_case(title, raw_text, validator)
    run_homework(expected, validator)


if __name__ == "__main__":
    main()
