"""Lesson05 任务生命周期回归检查：离线模拟，不读取真实 .env。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import httpx
from fastapi import HTTPException

from examples.lesson03 import llm, services as lesson03_services
from examples.lesson05 import api, services, store


class Lesson05Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        store._tasks.clear()
        self.addCleanup(store._tasks.clear)
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    async def call(self, method, path, body=None):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api.app),
            base_url="http://lesson.test",
        ) as client:
            return await client.request(method, path, json=body)

    async def test_three_types_dispatch_prompts_and_log_running_to_success(self):
        original_client = httpx.Client
        prompts = {
            "report": lesson03_services.REPORT_SYSTEM_PROMPT,
            "meeting": lesson03_services.MEETING_SYSTEM_PROMPT,
            "email": lesson03_services.EMAIL_SYSTEM_PROMPT,
        }
        for kind, expected_prompt in prompts.items():
            with self.subTest(task_type=kind):
                store._tasks.clear()
                seen_task_ids = []

                def handler(request):
                    records = list(store._tasks.values())
                    self.assertEqual(len(records), 1)
                    self.assertEqual(records[0].status, "running")
                    seen_task_ids.append(records[0].task_id)
                    payload = json.loads(request.content)
                    self.assertEqual(payload["messages"][0]["content"], expected_prompt)
                    user_content = payload["messages"][1]["content"]
                    self.assertIn("private-input", user_content)
                    if kind == "meeting":
                        self.assertIn("会议主题", user_content)
                    else:
                        self.assertEqual(user_content, "private-input")
                    return httpx.Response(200, json={"choices": [{
                        "message": {"content": "  private-output  "},
                        "finish_reason": "stop",
                    }]})

                def factory(**kwargs):
                    return original_client(transport=httpx.MockTransport(handler), **kwargs)

                with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-test-key"}, clear=True), \
                     patch.object(llm.httpx, "Client", factory), \
                     self.assertLogs(services.logger, level="INFO") as logs:
                    response = await self.call("POST", "/tasks", {
                        "task_type": kind, "requirement": "  private-input  ",
                    })
                self.assertEqual(response.status_code, 201)
                data = response.json()
                task = data["task"]
                self.assertEqual(task["task_id"], seen_task_ids[0])
                self.assertEqual(task["task_type"], kind)
                self.assertEqual(task["status"], "succeeded")
                self.assertEqual(task["result"], "private-output")
                self.assertIsNone(task["error_code"])
                self.assertIsNone(task["error_message"])
                self.assertEqual(response.headers["X-Request-ID"], data["request_id"])
                self.assertEqual(response.headers["Location"], "/tasks/" + task["task_id"])
                self.assertNotEqual(task["task_id"], data["request_id"])
                self.assertEqual(len(task["task_id"]), 32)
                event = json.loads(logs.records[0].getMessage())
                self.assertEqual(event["event"], "task_finished")
                self.assertEqual(event["request_id"], data["request_id"])
                self.assertEqual(event["task_id"], task["task_id"])
                self.assertEqual(event["task_status"], "succeeded")
                self.assertGreaterEqual(event["duration_ms"], 0)
                for value in ("private-input", "private-output", "offline-test-key"):
                    self.assertNotIn(value, logs.records[0].getMessage())

    async def test_repeated_queries_keep_task_and_never_regenerate(self):
        generate = Mock(return_value="saved-result")
        with patch.dict(services.GENERATORS, {"report": generate}), \
             self.assertLogs(services.logger, level="INFO") as logs:
            response = await self.call("POST", "/tasks", {
                "task_type": "report", "requirement": "需求",
            })
            self.assertEqual(response.status_code, 201)
            data = response.json()
            task = data["task"]
            request_ids = {data["request_id"]}
            for _ in range(2):
                query = await self.call("GET", "/tasks/" + task["task_id"])
                self.assertEqual(query.status_code, 200)
                self.assertEqual(query.json()["task"], task)
                self.assertEqual(query.headers["X-Request-ID"], query.json()["request_id"])
                request_ids.add(query.json()["request_id"])
        self.assertEqual(len(request_ids), 3)
        self.assertEqual(len(logs.records), 1)
        generate.assert_called_once_with("需求")

    async def test_repeated_submission_creates_two_independent_tasks(self):
        generate = Mock(side_effect=["first-result", "second-result"])
        records = []
        with patch.dict(services.GENERATORS, {"email": generate}), \
             self.assertLogs(services.logger, level="INFO"):
            for _ in range(2):
                response = await self.call("POST", "/tasks", {
                    "task_type": "email", "requirement": "相同需求",
                })
                self.assertEqual(response.status_code, 201)
                records.append(response.json())
        self.assertNotEqual(records[0]["task"]["task_id"], records[1]["task"]["task_id"])
        self.assertNotEqual(records[0]["request_id"], records[1]["request_id"])
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(len(store._tasks), 2)
        for expected in records:
            query = await self.call("GET", "/tasks/" + expected["task"]["task_id"])
            self.assertEqual(query.json()["task"], expected["task"])

    async def test_invalid_inputs_create_no_tasks(self):
        cases = [
            {}, {"task_type": "report"},
            {"task_type": "unknown", "requirement": "x"},
            {"task_type": "report", "requirement": ""},
            {"task_type": "report", "requirement": "   "},
            {"task_type": "report", "requirement": "x" * 1001},
            {"task_type": "report", "requirement": None},
            {"task_type": "report", "requirement": 123},
        ]
        with patch.object(api, "execute_task") as execute:
            for index, body in enumerate(cases):
                with self.subTest(case=index):
                    response = await self.call("POST", "/tasks", body)
                    self.assertEqual(response.status_code, 422)
                    self.assertNotIn("X-Request-ID", response.headers)
        execute.assert_not_called()
        self.assertEqual(store._tasks, {})

    async def test_unknown_task_returns_404_without_execution(self):
        with patch.object(api, "execute_task") as execute:
            response = await self.call("GET", "/tasks/not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(response.headers["X-Request-ID"]), 32)
        self.assertIn("任务不存在", response.json()["detail"])
        execute.assert_not_called()

    async def test_input_boundaries_and_trim(self):
        generate = Mock(return_value="result")
        with patch.dict(services.GENERATORS, {"report": generate}), \
             self.assertLogs(services.logger, level="INFO"):
            for value, expected in (("x", "x"), ("x" * 1000, "x" * 1000), ("  x  ", "x")):
                response = await self.call("POST", "/tasks", {
                    "task_type": "report", "requirement": value,
                })
                self.assertEqual(response.status_code, 201)
                self.assertEqual(generate.call_args.args, (expected,))

    async def test_failed_records_are_queryable_and_errors_are_sanitized(self):
        cases = [
            (HTTPException(502, detail="private-error"), 502),
            (HTTPException(503, detail="private-error"), 503),
            (HTTPException(504, detail="private-error"), 504),
            (RuntimeError("private-error"), 500),
        ]
        for error, code in cases:
            with self.subTest(error_code=code), \
                 patch.dict(services.GENERATORS, {"report": Mock(side_effect=error)}), \
                 self.assertLogs(services.logger, level="ERROR") as logs:
                response = await self.call("POST", "/tasks", {
                    "task_type": "report", "requirement": "需求",
                })
                self.assertEqual(response.status_code, 201)
                data = response.json()
                task = data["task"]
                self.assertEqual(task["status"], "failed")
                self.assertEqual(task["error_code"], code)
                self.assertIsNone(task["result"])
                self.assertNotIn("private-error", response.text)
                query = await self.call("GET", "/tasks/" + task["task_id"])
                self.assertEqual(query.status_code, 200)
                self.assertEqual(query.json()["task"], task)
                event = json.loads(logs.records[0].getMessage())
                self.assertEqual(event["task_status"], "failed")
                self.assertEqual(event["error_code"], code)
                self.assertEqual(event["task_id"], task["task_id"])
                self.assertEqual(event["request_id"], data["request_id"])
                self.assertNotIn("private-error", logs.records[0].getMessage())

    async def test_missing_key_is_saved_as_failure_without_network(self):
        with patch.object(llm.httpx, "Client") as client, \
             self.assertLogs(services.logger, level="ERROR"):
            response = await self.call("POST", "/tasks", {
                "task_type": "report", "requirement": "需求",
            })
        self.assertEqual(response.status_code, 201)
        task = response.json()["task"]
        self.assertEqual(task["status"], "failed")
        self.assertEqual(task["error_code"], 503)
        client.assert_not_called()
        query = await self.call("GET", "/tasks/" + task["task_id"])
        self.assertEqual(query.json()["task"], task)

    async def test_new_python_process_has_no_parent_task_memory(self):
        with patch.dict(services.GENERATORS, {"report": Mock(return_value="result")}), \
             self.assertLogs(services.logger, level="INFO"):
            response = await self.call("POST", "/tasks", {
                "task_type": "report", "requirement": "需求",
            })
        task_id = response.json()["task"]["task_id"]
        self.assertIsNotNone(store.get_task(task_id))
        root = Path(__file__).resolve().parents[1]
        code = (
            "import sys; from examples.lesson05.store import get_task; "
            "assert get_task(sys.argv[1]) is None; print('empty-new-process')"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", code, task_id],
            cwd=root, capture_output=True, text=True, timeout=15, check=True,
        )
        self.assertEqual(result.stdout.strip(), "empty-new-process")
        self.assertIsNotNone(store.get_task(task_id))


if __name__ == "__main__":
    unittest.main()
