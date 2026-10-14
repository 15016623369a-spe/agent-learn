"""通过本地 ASGI 与模拟模型响应检查课程接口；不读取 .env、不调用外部 API。"""
import json
import os
import unittest
from unittest.mock import patch

import httpx

import main
import lesson02


class LessonTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, app, method, path, body=None):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://lesson.test"
        ) as client:
            return await client.request(method, path, json=body)

    async def model_call(self, path, body, handler):
        original_client = httpx.Client

        def factory(**kwargs):
            return original_client(transport=httpx.MockTransport(handler), **kwargs)

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-test-key"}, clear=True):
            with patch.object(lesson02.httpx, "Client", factory):
                return await self.call(lesson02.app, "POST", path, body)

    async def test_health_for_both_lessons(self):
        for app in (main.app, lesson02.app):
            with self.subTest(app=app.title):
                response = await self.call(app, "GET", "/health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok"})

    async def test_lesson01_mock_and_original_whitespace_behavior(self):
        for value in ("经营报告", "   "):
            with self.subTest(value=value):
                response = await self.call(main.app, "POST", "/report-preview", {"requirement": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {
                    "summary": f"收到报告任务：{value}。后续将检索指标口径并计算数据。",
                    "mode": "mock",
                })
        for body in ({}, {"requirement": ""}, {"requirement": "x" * 2001}):
            response = await self.call(main.app, "POST", "/report-preview", body)
            self.assertEqual(response.status_code, 422)

    async def test_lesson02_invalid_inputs_stop_before_generation(self):
        cases = {
            "/report-draft": [{}, {"requirement": ""}, {"requirement": "   "}, {"requirement": "x" * 2001}],
            "/meeting-agenda": [{}, {"topic": ""}, {"topic": "   "}, {"topic": "x" * 201}],
        }
        with patch.object(lesson02, "generate_draft") as generate:
            for path, bodies in cases.items():
                for body in bodies:
                    with self.subTest(path=path, body_size=len(str(body))):
                        response = await self.call(lesson02.app, "POST", path, body)
                        self.assertEqual(response.status_code, 422)
            generate.assert_not_called()

    async def test_lesson02_mock_trims_input(self):
        response = await self.call(lesson02.app, "POST", "/report-preview", {"requirement": "  经营报告  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "mock")
        self.assertIn("任务：经营报告。", response.json()["summary"])

    async def test_missing_key_and_model_do_not_send_request(self):
        for env, detail in [({}, "服务尚未配置模型密钥"),
                            ({"DEEPSEEK_API_KEY": "offline-test-key", "DEEPSEEK_MODEL": " "}, "服务尚未配置模型名称")]:
            with self.subTest(detail=detail):
                with patch.dict(os.environ, env, clear=True):
                    with patch.object(lesson02.httpx, "Client") as client:
                        response = await self.call(lesson02.app, "POST", "/report-draft", {"requirement": "经营报告"})
                        self.assertEqual(response.status_code, 503)
                        self.assertEqual(response.json(), {"detail": detail})
                        client.assert_not_called()

    async def test_report_request_and_response_contract(self):
        def handler(request):
            payload = json.loads(request.content)
            self.assertEqual(str(request.url), "https://api.deepseek.com/chat/completions")
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.headers["authorization"], "Bearer offline-test-key")
            self.assertEqual(payload["model"], "deepseek-flash")
            self.assertEqual(payload["messages"][0]["role"], "system")
            self.assertIn("不要编造", payload["messages"][0]["content"])
            self.assertEqual(payload["messages"][1], {"role": "user", "content": "经营报告"})
            self.assertEqual(payload["thinking"], {"type": "disabled"})
            self.assertEqual(payload["max_tokens"], 800)
            self.assertIs(payload["stream"], False)
            self.assertEqual(request.extensions["timeout"]["connect"], 10.0)
            self.assertEqual(request.extensions["timeout"]["read"], 60.0)
            return httpx.Response(200, json={"choices": [{"message": {"content": "  报告提纲：待提供数据。  "}, "finish_reason": "stop"}]})

        response = await self.model_call("/report-draft", {"requirement": "  经营报告  "}, handler)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"summary": "报告提纲：待提供数据。", "mode": "llm"})

    async def test_meeting_topic_reaches_model_and_agenda_is_returned(self):
        def handler(request):
            task = json.loads(request.content)["messages"][1]["content"]
            self.assertIn("下周产品上线协调会", task)
            self.assertIn("会议议程和会前资料清单", task)
            return httpx.Response(200, json={"choices": [{"message": {"content": "会议议程：核查上线准备。"}, "finish_reason": "stop"}]})

        response = await self.model_call("/meeting-agenda", {"topic": "  下周产品上线协调会  "}, handler)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"agenda": "会议议程：核查上线准备。", "mode": "llm"})

    async def test_maximum_input_lengths_are_accepted(self):
        for path, field, length in [("/report-draft", "requirement", 2000), ("/meeting-agenda", "topic", 200)]:
            with self.subTest(path=path):
                with patch.object(lesson02, "generate_draft", return_value="示例") as generate:
                    response = await self.call(lesson02.app, "POST", path, {field: "x" * length})
                    self.assertEqual(response.status_code, 200)
                    generate.assert_called_once()

    async def test_upstream_status_mapping(self):
        cases = [(401, 503), (403, 503), (402, 503), (429, 503), (400, 502), (422, 502), (500, 502), (503, 502)]
        for upstream, expected in cases:
            with self.subTest(upstream=upstream):
                response = await self.model_call("/report-draft", {"requirement": "经营报告"},
                    lambda request, code=upstream: httpx.Response(code, json={"error": "offline-provider-error"}))
                self.assertEqual(response.status_code, expected)
                self.assertNotIn("offline-test-key", response.text)
                self.assertNotIn("offline-provider-error", response.text)

    async def test_timeout_and_connection_error_mapping(self):
        for error, expected in [(httpx.ReadTimeout, 504), (httpx.ConnectTimeout, 504), (httpx.ConnectError, 502)]:
            with self.subTest(error=error.__name__):
                def handler(request):
                    raise error("offline failure", request=request)
                response = await self.model_call("/report-draft", {"requirement": "经营报告"}, handler)
                self.assertEqual(response.status_code, expected)

    async def test_malformed_empty_and_incomplete_responses(self):
        bodies = [{}, {"choices": []}, {"choices": None},
                  {"choices": [{"message": {"content": "text"}}]}]
        for content in (None, "", "   ", 12):
            bodies.append({"choices": [{"message": {"content": content}, "finish_reason": "stop"}]})
        for reason in ("length", "content_filter", "aborted", "tool_calls"):
            bodies.append({"choices": [{"message": {"content": "partial"}, "finish_reason": reason}]})
        for body in bodies:
            with self.subTest(body=body):
                response = await self.model_call("/report-draft", {"requirement": "经营报告"},
                    lambda request, b=body: httpx.Response(200, json=b))
                self.assertEqual(response.status_code, 502)
        response = await self.model_call("/report-draft", {"requirement": "经营报告"},
            lambda request: httpx.Response(200, text="not JSON"))
        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
