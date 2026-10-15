"""邮件草稿作业回归检查：模拟模型响应，不加载本地 .env。"""
import json
import os
import unittest
from unittest.mock import patch

import httpx
from pydantic import ValidationError

from examples.lesson03 import api, llm, services
from examples.lesson03.schemas import EmailRequest, ReportRequest


class EmailHomeworkTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, body, path="/email-draft"):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api.app), base_url="http://lesson.test"
        ) as client:
            return await client.post(path, json=body)

    async def test_email_prompt_response_and_correlated_log(self):
        original_client = httpx.Client

        def handler(request):
            payload = json.loads(request.content)
            self.assertEqual(payload["messages"][0]["content"], services.EMAIL_SYSTEM_PROMPT)
            self.assertEqual(payload["messages"][1]["content"], "写一封会议邀请邮件")
            self.assertIn("[待补]", payload["messages"][0]["content"])
            self.assertIn("不声称已经发送邮件", payload["messages"][0]["content"])
            return httpx.Response(200, json={"choices": [{
                "message": {"content": "  主题：[待补]\n正文：邮件草稿  "},
                "finish_reason": "stop",
            }]})

        def factory(**kwargs):
            return original_client(transport=httpx.MockTransport(handler), **kwargs)

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-test-key"}, clear=True), \
             patch.object(llm.httpx, "Client", factory), \
             self.assertLogs(api.logger, level="INFO") as logs:
            response = await self.call({"requirement": "  写一封会议邀请邮件  "})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), {"draft", "mode", "request_id"})
        self.assertEqual(data["draft"], "主题：[待补]\n正文：邮件草稿")
        self.assertEqual(data["mode"], "llm")
        self.assertEqual(len(data["request_id"]), 32)
        event = json.loads(logs.records[0].getMessage())
        self.assertEqual(event["task_type"], "email")
        self.assertEqual(event["status_code"], 200)
        self.assertEqual(event["request_id"], data["request_id"])

    async def test_invalid_inputs_never_invoke_model(self):
        cases = [{}, {"requirement": ""}, {"requirement": "   "},
                 {"requirement": "x" * 1001}, {"requirement": None}, {"requirement": 123}]
        with patch.object(services, "call_llm") as model:
            for index, body in enumerate(cases):
                with self.subTest(case=index):
                    response = await self.call(body)
                    self.assertEqual(response.status_code, 422)
            model.assert_not_called()

    async def test_minimum_and_maximum_lengths(self):
        with patch.object(services, "call_llm", return_value="草稿") as model, \
             self.assertLogs(api.logger, level="INFO"):
            for value in ("x", "x" * 1000):
                response = await self.call({"requirement": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(model.call_args.args, (services.EMAIL_SYSTEM_PROMPT, value))

    async def test_same_field_and_validator_names_remain_independent(self):
        report = ReportRequest(requirement="报告需求")
        email = EmailRequest(requirement="邮件需求")
        self.assertEqual(report.requirement, "报告需求")
        self.assertEqual(email.requirement, "邮件需求")
        self.assertIs(ReportRequest.reject_blank.__self__, ReportRequest)
        self.assertIs(EmailRequest.reject_blank.__self__, EmailRequest)
        self.assertEqual(len(ReportRequest(requirement="x" * 1500).requirement), 1500)
        with self.assertRaises(ValidationError):
            EmailRequest(requirement="x" * 1500)
        with patch.object(services, "call_llm", return_value="报告") as model, \
             self.assertLogs(api.logger, level="INFO"):
            report_response = await self.call({"requirement": "x" * 1500}, "/report-draft")
            self.assertEqual(report_response.status_code, 200)
            self.assertEqual(model.call_args.args[0], services.REPORT_SYSTEM_PROMPT)
            email_response = await self.call({"requirement": "x" * 1500})
            self.assertEqual(email_response.status_code, 422)
            self.assertEqual(model.call_count, 1)

    async def test_missing_key_has_matching_error_log_id(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(llm.httpx, "Client") as client, \
             self.assertLogs(api.logger, level="ERROR") as logs:
            response = await self.call({"requirement": "邮件需求"})
        self.assertEqual(response.status_code, 503)
        client.assert_not_called()
        event = json.loads(logs.records[0].getMessage())
        self.assertEqual(event["task_type"], "email")
        self.assertEqual(event["request_id"], response.headers["X-Request-ID"])

    async def test_timeout_reuses_shared_error_handling(self):
        original_client = httpx.Client

        def handler(request):
            raise httpx.ReadTimeout("offline timeout", request=request)

        def factory(**kwargs):
            return original_client(transport=httpx.MockTransport(handler), **kwargs)

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-test-key"}, clear=True), \
             patch.object(llm.httpx, "Client", factory), \
             self.assertLogs(api.logger, level="ERROR") as logs:
            response = await self.call({"requirement": "邮件需求"})
        self.assertEqual(response.status_code, 504)
        event = json.loads(logs.records[0].getMessage())
        self.assertEqual(event["status_code"], 504)
        self.assertEqual(event["request_id"], response.headers["X-Request-ID"])


if __name__ == "__main__":
    unittest.main()
