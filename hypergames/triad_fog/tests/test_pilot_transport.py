"""End-to-end batch receipts use synthetic decisions and no model calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import AI_IDS
import pilot_batch as pilot
import verify_pilot_transport as verifier


class PilotTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixture_tmp.cleanup)
        base = Path(cls.fixture_tmp.name)
        cls.fixture = base / "pilot"
        pilot.init_pilot(cls.fixture, "0" * 40)
        response_path = base / "response.jsonl"
        for actor in AI_IDS:
            for turn in range(10):
                batch = pilot.pending_batch(cls.fixture, actor)
                if actor == "MERIDIAN" and turn == 0:
                    response_path.write_bytes(b"malformed wrapper attempt\r\n")
                    result = pilot.submit_batch(cls.fixture, actor, response_path, "synthetic-test-worker")
                    if result["accepted"]:
                        raise AssertionError("malformed fixture unexpectedly accepted")
                lines = []
                for item in batch["games"]:
                    decision = {"action": "hold", "decision_summary": "Synthetic transport fixture.",
                                "evidence": ["/own_traits/compute"],
                                "uncertainty": "No model inference occurs in this fixture."}
                    lines.append(json.dumps({"run_id": item["run_id"],
                                             "request_id": item["request"]["request_id"],
                                             "decision": decision}, separators=(",  ", " : ")))
                response_path.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
                result = pilot.submit_batch(cls.fixture, actor, response_path, "synthetic-test-worker")
                if not result["accepted"]:
                    raise AssertionError(result)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "pilot"
        shutil.copytree(self.fixture, self.root)

    def snapshot(self):
        return {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.root.rglob("*") if path.is_file()}

    def test_complete_transport_replays_and_counts_rejections_separately(self):
        before = self.snapshot()
        first = verifier.verify(self.root)
        self.assertTrue(first["verified"])
        self.assertEqual(first["episodes"], 30)
        self.assertEqual(first["accepted_decisions"], 300)
        self.assertEqual(first["committed_batches"], 30)
        self.assertEqual(first["completed_batch_receipt_sets"], 30)
        self.assertEqual(first["wrapper_attempt_status_counts"], {"accepted": 30, "rejected": 1})
        self.assertEqual(first["core_rejected_attempts"], 0)
        self.assertEqual(len(first["attempt_payloads"]), 31)
        self.assertEqual(first, verifier.verify(self.root))
        self.assertEqual(before, self.snapshot())

    def test_changed_common_prompt_breaks_the_exact_request_link(self):
        path = self.root / "transport/meridian/turn-00-request.json"
        batch = json.loads(path.read_bytes())
        batch["common"]["rules"]["objective"] = "Altered objective."
        path.write_text(json.dumps(batch))
        with self.assertRaisesRegex(ValueError, "core request"):
            verifier.verify(self.root)

    def test_rejected_attempt_bytes_still_require_their_receipt_hash(self):
        attempts = self.root / "transport/meridian/attempts"
        rejected = next(path for path in attempts.glob("*.receipt.json")
                        if not json.loads(path.read_bytes())["accepted"])
        payload = rejected.with_name(rejected.name.removesuffix(".receipt.json") + ".jsonl")
        payload.write_bytes(payload.read_bytes() + b"altered")
        with self.assertRaisesRegex(ValueError, "exact payload"):
            verifier.verify(self.root)

    def test_missing_completed_receipt_set_is_not_inferred_from_actions(self):
        attempts = self.root / "transport/helios/attempts"
        receipt = next(path for path in attempts.glob("*.receipt.json")
                       if json.loads(path.read_bytes()).get("batch_turn") == 0)
        receipt.unlink()
        with self.assertRaisesRegex(ValueError, "completed acceptance receipt"):
            verifier.verify(self.root)

    def test_incomplete_journal_is_rejected_without_recovery_write(self):
        path = self.root / "runs/meridian-01/journal.jsonl"
        lines = path.read_bytes().splitlines(keepends=True)
        path.write_bytes(b"".join(lines[:-1]))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            verifier.verify(self.root)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
