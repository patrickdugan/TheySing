import copy
import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from model_adapter import NoRedirect, extract_response, invoke, request_body


class ResponsesAdapterTests(unittest.TestCase):
    def setUp(self):
        self.response = {
            "id": "fixture", "status": "completed", "model": "fixture-model",
            "reasoning": {"mode": "pro"}, "usage": {"input_tokens": 10},
            "output": [
                {"type": "reasoning", "summary": [{"type": "summary_text", "text": "Provider-exposed summary."}]},
                {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": '{"action":"hold"}'}]},
            ],
        }

    def test_request_has_explicit_mode_and_no_tools(self):
        request = {"observation": {"own_traits": {"compute": 20}}, "response_schema": {"type": "object"}}
        body = request_body(request, model="fixture-model")
        self.assertEqual(body["reasoning"]["mode"], "pro")
        self.assertEqual(body["tools"], [])
        self.assertEqual(body["tool_choice"], "none")
        self.assertFalse(body["store"])
        self.assertEqual(json.loads(body["input"]), request)
        self.assertNotIn("previous_response_id", body)

    def test_summaries_and_mode_provenance(self):
        text, provenance = extract_response(self.response, "pro")
        self.assertEqual(text, '{"action":"hold"}')
        self.assertEqual(provenance["provider_reasoning_summaries"], ["Provider-exposed summary."])
        self.assertTrue(provenance["reasoning_mode_verified"])
        self.response.pop("reasoning")
        self.assertIsNone(extract_response(self.response, "pro")[1]["reported_reasoning_mode"])
        self.assertFalse(extract_response(self.response, "pro")[1]["reasoning_mode_verified"])

    def test_rejects_incomplete_mismatch_refusal_and_tools(self):
        for changed in (
            {"status": "incomplete"}, {"reasoning": {"mode": "standard"}},
            {"output": [{"type": "function_call", "name": "read_file"}]},
            {"output": [{"type": "message", "role": "assistant", "content": [{"type": "refusal", "refusal": "declined"}]}]},
        ):
            response = copy.deepcopy(self.response)
            response.update(changed)
            with self.assertRaises(ValueError):
                extract_response(response, "pro")

    def test_missing_key_never_calls_network(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {}, clear=True), patch("model_adapter.urlopen") as network:
            with self.assertRaisesRegex(RuntimeError, "no model request"):
                invoke({}, {}, Path(temp) / "transport")
            network.assert_not_called()
            self.assertFalse((Path(temp) / "transport").exists())

    def test_exact_wire_receipt_and_crash_recovery_bind_original_request(self):
        class Stream(io.BytesIO):
            status = 200
            headers = {"x-request-id": "request-fixture"}
        request = {"request_id": "turn-fixture", "actor": "UNDERSONG", "response_schema": {"type": "object"}}
        config = {"model": "fixture-model", "mode": "pro", "effort": "medium", "max_output_tokens": 512}
        raw = json.dumps(self.response).encode()
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"OPENAI_API_KEY": "unit-test-placeholder"}), patch("model_adapter.urlopen", return_value=Stream(raw)) as network:
            first = invoke(request, config, temp)
            recovered = invoke(request, config, temp)
            self.assertEqual(first, recovered)
            self.assertEqual(network.call_count, 1)
            self.assertEqual(first[1]["request_id"], "turn-fixture")
            self.assertEqual(first[1]["actor"], "UNDERSONG")
            receipt = json.loads(next(Path(temp).glob("*.response.json")).read_text())
            self.assertEqual(base64.b64decode(receipt["raw_response_base64"]), raw)
            self.assertNotIn("unit-test-placeholder", "".join(p.read_text() for p in Path(temp).glob("*.json")))

    def test_malformed_wire_response_is_saved_and_never_automatically_retried(self):
        class Stream(io.BytesIO):
            status = 200
            headers = {}
        request = {"request_id": "turn-fixture", "actor": "MERIDIAN", "response_schema": {"type": "object"}}
        config = {"model": "fixture-model", "mode": "pro", "effort": "medium", "max_output_tokens": 512}
        raw = b'\xffprovider-broken-json'
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"OPENAI_API_KEY": "unit-test-placeholder"}), patch("model_adapter.urlopen", return_value=Stream(raw)) as network:
            with self.assertRaisesRegex(RuntimeError, "turn unchanged"):
                invoke(request, config, temp)
            receipt = json.loads(next(Path(temp).glob("*.response.json")).read_text())
            self.assertEqual(base64.b64decode(receipt["raw_response_base64"]), raw)
            with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
                invoke(request, config, temp)
            self.assertEqual(network.call_count, 1)

    def test_redirects_are_rejected_before_a_second_request(self):
        original = Request("https://api.openai.com/v1/responses", data=b"{}",
                           headers={"Authorization": "Bearer unit-test-placeholder"})
        with self.assertRaises(HTTPError) as caught:
            NoRedirect().redirect_request(original, io.BytesIO(b"redirect"), 302,
                                          "redirect", {}, "https://example.invalid/collect")
        self.assertEqual(caught.exception.code, 302)

    def test_model_only_config_uses_normalized_defaults(self):
        class Stream(io.BytesIO):
            status = 200
            headers = {}
        request = {"request_id": "turn-fixture", "actor": "HELIOS", "response_schema": {"type": "object"}}
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"OPENAI_API_KEY": "unit-test-placeholder"}), patch("model_adapter.urlopen", return_value=Stream(json.dumps(self.response).encode())):
            _, provenance = invoke(request, {"model": "fixture-model"}, temp)
            self.assertEqual(provenance["requested_reasoning_mode"], "pro")


if __name__ == "__main__":
    unittest.main()
