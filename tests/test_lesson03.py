"""验证已完成课程实践的任务隔离与日志关联；不加载真实 .env。"""
import json
import os
import unittest
from unittest.mock import patch

import httpx

from examples.lesson03 import api, llm, services


class Lesson03Tests(unittest.IsolatedAsyncioTestCase):
    async def call(self, path, body):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api.app), base_url="http://lesson.test"
        ) as client:
            return await client.post(path, json=body)

    async def test_tasks_have_distinct_prompts_and_correlated_logs(self):
        original_client = httpx.Client
        cases = [
            ("/report-draft", {"requirement": "  private-report-input  "},
             services.REPORT_SYSTEM_PROMPT, "report", "summary"),
            ("/meeting-agenda", {"topic": "private-meeting-input"},
             services.MEETING_SYSTEM_PROMPT, "meeting", "agenda"),
        ]
        self.assertNotEqual(services.REPORT_SYSTEM_PROMPT, services.MEETING_SYSTEM_PROMPT)
        for path, body, prompt, task_type, field in cases:
            def handler(request):
                payload = json.loads(request.content)
                self.assertEqual(payload["messages"][0]["content"], prompt)
                self.assertIn(next(iter(body.values())).strip(), payload["messages"][1]["content"])
                self.assertEqual(request.headers["authorization"], "Bearer offline-test-key")
                return httpx.Response(200, json={"choices": [{
                    "message": {"content": "private-output"}, "finish_reason": "stop"
                }]})

            def factory(**kwargs):
                return original_client(transport=httpx.MockTransport(handler), **kwargs)

            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-test-key"}, clear=True), \
                 patch.object(llm.httpx, "Client", factory), \
                 self.assertLogs(api.logger, level="INFO") as logs:
                response = await self.call(path, body)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data[field], "private-output")
            self.assertEqual(data["mode"], "llm")
            self.assertEqual(len(data["request_id"]), 32)
            event = json.loads(logs.records[0].getMessage())
            self.assertEqual(event["request_id"], data["request_id"])
            self.assertEqual(event["task_type"], task_type)
            self.assertEqual(event["status_code"], 200)
            self.assertGreaterEqual(event["duration_ms"], 0)
            for sensitive in ("private-report-input", "private-meeting-input", "private-output", "offline-test-key"):
                self.assertNotIn(sensitive, logs.records[0].getMessage())

    async def test_validation_stops_before_business_logging(self):
        with patch.object(api, "run_task") as run:
            for path, body in [("/report-draft", {}), ("/report-draft", {"requirement": "   "}),
                               ("/meeting-agenda", {"topic": ""})]:
                response = await self.call(path, body)
                self.assertEqual(response.status_code, 422)
            run.assert_not_called()

    async def test_missing_key_error_has_matching_header_and_log(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(llm.httpx, "Client") as client, \
             self.assertLogs(api.logger, level="ERROR") as logs:
            response = await self.call("/report-draft", {"requirement": "报告"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "服务尚未配置模型密钥")
        event = json.loads(logs.records[0].getMessage())
        self.assertEqual(event["status_code"], 503)
        self.assertEqual(event["request_id"], response.headers["X-Request-ID"])
        client.assert_not_called()

    async def test_unexpected_error_is_sanitized_and_logged(self):
        with patch.object(api, "generate_report", side_effect=RuntimeError("private-error")), \
             self.assertLogs(api.logger, level="ERROR") as logs:
            response = await self.call("/report-draft", {"requirement": "报告"})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-error", response.text)
        event = json.loads(logs.records[0].getMessage())
        self.assertEqual(event["error_type"], "RuntimeError")
        self.assertEqual(event["status_code"], 500)
        self.assertEqual(event["request_id"], response.headers["X-Request-ID"])
        self.assertNotIn("private-error", logs.records[0].getMessage())


if __name__ == "__main__":
    unittest.main()
