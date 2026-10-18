"""Lesson06：运行六个开发验收案例，保存真实输出，不自动判内容分数。

仅显式运行本模块才调用模型。复用 Lesson05 ASGI 应用与现有 fde 环境；
无需启动 Uvicorn，真实模型请求仍会经 Lesson03 的 HTTPX 发到外部服务。
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
from time import perf_counter

import httpx
from dotenv import load_dotenv

from examples.lesson03 import services as prompts
from examples.lesson05.api import app


ROOT = Path(__file__).resolve().parents[2]


def git_value(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True,
        check=True, timeout=10,
    ).stdout.strip()


async def collect(case_set, report, output):
    # ASGITransport 省去浏览器和本地端口；它不会模拟上游模型。
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://lesson06.local",
    ) as client:
        for case in case_set["cases"]:
            started = perf_counter()
            response = await client.post("/tasks", json={
                "task_type": case["task_type"],
                "requirement": case["requirement"],
            })
            data = response.json()
            task = data.get("task")
            query_matches = False
            query_status = None
            if task:
                query = await client.get("/tasks/" + task["task_id"])
                query_status = query.status_code
                query_matches = query.status_code == 200 and query.json()["task"] == task
            report["results"].append({
                **case,
                "http_status": response.status_code,
                "request_id": data.get("request_id"),
                "task": task,
                "query_http_status": query_status,
                "query_matches_saved_task": query_matches,
                "elapsed_seconds": round(perf_counter() - started, 3),
                "review": None,
            })
            # 每例结束即落盘，未执行的案例不伪装成已执行或已通过。
            report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            status = task["status"] if task else "no-task"
            print(f'{case["case_id"]}: HTTP {response.status_code}, task={status}, query_matches={query_matches}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    output = args.output.resolve()
    # 不覆盖此前的真实评估证据。
    if output.exists():
        parser.error("输出文件已存在，请换一个新文件名。")
    load_dotenv(args.env_file, override=False)
    if not os.getenv("DEEPSEEK_API_KEY", "").strip():
        parser.error("本地未配置 DEEPSEEK_API_KEY；未执行任何模型请求。")
    case_set = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    prompt_values = {
        "report": prompts.REPORT_SYSTEM_PROMPT,
        "meeting": prompts.MEETING_SYSTEM_PROMPT,
        "email": prompts.EMAIL_SYSTEM_PROMPT,
    }
    report = {
        "case_set_version": case_set["case_set_version"],
        "purpose": case_set["purpose"],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": git_value("rev-parse", "HEAD"),
        "working_tree_status": git_value("status", "--short"),
        "configured_model": os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip(),
        "model_name_source": "本地请求配置；当前调用层未保留上游返回的模型标识",
        "prompt_sha256": {name: hashlib.sha256(value.encode()).hexdigest() for name, value in prompt_values.items()},
        "execution": "真实模型调用；ASGI 进程内提交与查询；没有启动浏览器或 Uvicorn",
        "results": [],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as target:
        target.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # 原服务日志只含运行元数据；关闭噪声，标准输出只打印状态摘要。
    logging.getLogger("httpx").setLevel(logging.WARNING)
    asyncio.run(collect(case_set, report, output))
    print(f"已保存 {len(report['results'])} 个真实案例；内容质量仍需逐例评审。")


if __name__ == "__main__":
    main()
