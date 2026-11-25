"""Batch transport preserves evidence and validates every seat decision first."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import AI_IDS, TriadGame, policy_action
import live_harness as harness
import pilot_batch as pilot


class PilotBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "pilot"
        self.root.mkdir()
        self.rows = []
        for index, seed in enumerate(pilot.SEEDS, 1):
            run_id = f"meridian-{index:02d}"
            harness.new_run(self.root / "runs" / run_id, seed, "MERIDIAN",
                            backend_metadata=pilot.METADATA, source_commit="0" * 40)
            self.rows.append({"run_id": run_id, "seed": seed, "actor": "MERIDIAN"})
        manifest = {
            "schema": "TS-HG-05/pilot/v1", "source_commit": "0" * 40,
            "episodes_registered": 10, "decisions_registered": 100,
            "turns_per_episode": 10, "seed_roots": list(pilot.SEEDS),
            "backend_metadata": pilot.METADATA, "runs": self.rows,
        }
        (self.root / "pilot_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.file_count = 0

    @staticmethod
    def decision(action="hold", summary="Keep resources available while evidence develops."):
        return {
            "action": action, "decision_summary": summary,
            "evidence": ["/own_traits/compute"],
            "uncertainty": "Other actors' private budgets remain unknown.",
        }

    def response_file(self, batch, decisions=None, *, crlf=False, edit_rows=None):
        decisions = decisions or [json.dumps(self.decision()) for _ in batch["games"]]
        rows = [{"run_id": item["run_id"], "request_id": item["request"]["request_id"]}
                for item in batch["games"]]
        if edit_rows:
            edit_rows(rows)
        lines = ['{"run_id": ' + json.dumps(row["run_id"]) + ', "request_id": ' +
                 json.dumps(row["request_id"]) + ', "decision": ' + decision + '}'
                 for row, decision in zip(rows, decisions)]
        ending = "\r\n" if crlf else "\n"
        raw = (ending.join(lines) + ending).encode("utf-8")
        return self.raw_file(raw), raw, decisions

    def raw_file(self, raw):
        self.file_count += 1
        path = Path(self.tmp.name) / f"response-{self.file_count:02d}.jsonl"
        path.write_bytes(raw)
        return path

    def turns(self):
        return [harness.replay_run(self.root / "runs" / row["run_id"])["turns"]
                for row in self.rows]

    def attempts(self):
        return list((self.root / "transport" / "meridian" / "attempts").glob("*.jsonl"))

    def assert_archived(self, raw):
        matches = [path for path in self.attempts() if path.read_bytes() == raw]
        self.assertTrue(matches, "the exact submitted bytes must survive validation failure")
        return matches

    def response_records(self, run_id):
        path = self.root / "runs" / run_id / "journal.jsonl"
        return [record for record in map(json.loads, path.read_text().splitlines())
                if record["type"] == "response"]

    def test_pending_returns_ten_correct_private_views_idempotently(self):
        batch = pilot.pending_batch(self.root, "MERIDIAN")
        self.assertEqual(batch["actor"], "MERIDIAN")
        self.assertEqual(batch["turn"], 0)
        self.assertEqual(len(batch["games"]), 10)
        self.assertEqual(set(batch["common"]), {"rules", "scene", "response_schema"})
        for row, game in zip(self.rows, batch["games"]):
            self.assertEqual(row["run_id"], game["run_id"])
            expected = TriadGame.new(row["seed"]).visible("MERIDIAN")
            self.assertEqual(game["request"]["observation"], json.loads(json.dumps(expected)))
            self.assertNotIn("seed", game["request"])
            self.assertNotIn("opponent_policies", game["request"])
            complete = {**game["request"], **batch["common"]}
            self.assertEqual(complete, harness.pending_request(self.root / "runs" / row["run_id"]))
        request_path = self.root / "transport" / "meridian" / "turn-00-request.json"
        original = request_path.read_bytes()
        self.assertEqual(pilot.pending_batch(self.root, "MERIDIAN"), batch)
        self.assertEqual(request_path.read_bytes(), original)

    def test_valid_batch_uses_each_worlds_pre_turn_state_and_preserves_exact_bytes(self):
        batch = pilot.pending_batch(self.root, "MERIDIAN")
        decisions = [json.dumps(self.decision("publish"), separators=(",  ", " : "))
                     for _ in range(10)]
        path, raw, _ = self.response_file(batch, decisions, crlf=True)
        result = pilot.submit_batch(self.root, "MERIDIAN", path, "test-worker")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["accepted_count"], 10)
        self.assertEqual(self.turns(), [1] * 10)
        self.assert_archived(raw)
        frozen = self.root / "transport" / "meridian" / "turn-00-response.jsonl"
        self.assertEqual(frozen.read_bytes(), raw)
        policies = {"MERIDIAN": "rsi_race", "HELIOS": "audit_first", "UNDERSONG": "quiet_hive"}
        for row, exact in zip(self.rows, decisions):
            records = self.response_records(row["run_id"])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["payload"]["raw_response"], exact)
            game = TriadGame.new(row["seed"])
            actions = {actor: policy_action(game, actor, policies[actor]) for actor in AI_IDS}
            actions["MERIDIAN"] = "publish"
            game.step(actions)
            actual = harness.replay_run(self.root / "runs" / row["run_id"])
            self.assertEqual(actual["final_state_hash"], harness.state_hash(game))

    def test_illegal_last_response_archives_rejection_and_correction_preserves_it(self):
        batch = pilot.pending_batch(self.root, "MERIDIAN")
        decisions = [json.dumps(self.decision()) for _ in range(9)]
        decisions.append(json.dumps(self.decision("conceal")))
        bad_path, bad_raw, _ = self.response_file(batch, decisions, crlf=True)
        rejected = pilot.submit_batch(self.root, "MERIDIAN", bad_path, "test-worker")
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["accepted_count"], 0)
        self.assertTrue(rejected["attempt_id"])
        self.assertEqual(self.turns(), [0] * 10)
        attempts = self.assert_archived(bad_raw)
        for path in attempts:
            receipt = json.loads(path.with_suffix(".receipt.json").read_text())
            self.assertFalse(receipt["accepted"])
        self.assertFalse((self.root / "transport" / "meridian" / "turn-00-response.jsonl").exists())
        good_path, _, _ = self.response_file(batch)
        accepted = pilot.submit_batch(self.root, "MERIDIAN", good_path, "test-worker")
        self.assertTrue(accepted["accepted"])
        self.assertEqual(self.turns(), [1] * 10)
        self.assert_archived(bad_raw)

    def test_duplicate_json_keys_are_rejected_after_raw_archive(self):
        batch = pilot.pending_batch(self.root, "MERIDIAN")
        path, raw, _ = self.response_file(batch)
        duplicate = raw.replace(b'"action": "hold"', b'"action": "hold", "action": "publish"', 1)
        path.write_bytes(duplicate)
        result = pilot.submit_batch(self.root, "MERIDIAN", path, "test-worker")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["accepted_count"], 0)
        self.assertEqual(self.turns(), [0] * 10)
        self.assert_archived(duplicate)

    def test_cross_seat_and_mixed_stale_request_ids_do_not_advance(self):
        batch = pilot.pending_batch(self.root, "MERIDIAN")
        wrong_path, wrong_raw, _ = self.response_file(
            batch, edit_rows=lambda rows: rows[0].update(run_id="helios-01"))
        self.assertFalse(pilot.submit_batch(self.root, "MERIDIAN", wrong_path, "worker")["accepted"])
        self.assertEqual(self.turns(), [0] * 10)
        self.assert_archived(wrong_raw)
        valid_path, _, _ = self.response_file(batch)
        self.assertTrue(pilot.submit_batch(self.root, "MERIDIAN", valid_path, "worker")["accepted"])
        second = pilot.pending_batch(self.root, "MERIDIAN")
        stale_path, stale_raw, _ = self.response_file(
            second, edit_rows=lambda rows: rows[0].update(request_id=batch["games"][0]["request"]["request_id"]))
        self.assertFalse(pilot.submit_batch(self.root, "MERIDIAN", stale_path, "worker")["accepted"])
        self.assertEqual(self.turns(), [1] * 10)
        self.assert_archived(stale_raw)

    def test_partial_interruption_resumes_identical_bytes_once_and_rejects_replacement(self):
        batch = pilot.pending_batch(self.root, "MERIDIAN")
        path, raw, _ = self.response_file(batch, crlf=True)
        original_submit = pilot.submit_response
        accepted = 0

        def interrupt_after_three(*args, **kwargs):
            nonlocal accepted
            if accepted == 3:
                raise RuntimeError("injected transport interruption")
            result = original_submit(*args, **kwargs)
            accepted += int(result["accepted"])
            return result

        with mock.patch.object(pilot, "submit_response", side_effect=interrupt_after_three):
            with self.assertRaisesRegex(RuntimeError, "injected transport interruption"):
                pilot.submit_batch(self.root, "MERIDIAN", path, "original-worker")
        self.assertEqual(self.turns(), [1] * 3 + [0] * 7)
        self.assert_archived(raw)
        replacement = [json.dumps(self.decision(summary="This is a replacement response.")) for _ in range(10)]
        new_path, new_raw, _ = self.response_file(batch, replacement)
        refused = pilot.submit_batch(self.root, "MERIDIAN", new_path, "different-worker")
        self.assertFalse(refused["accepted"])
        self.assertEqual(self.turns(), [1] * 3 + [0] * 7)
        self.assert_archived(new_raw)
        resumed = pilot.submit_batch(self.root, "MERIDIAN", path, "retry-worker")
        self.assertTrue(resumed["accepted"])
        self.assertEqual(resumed["accepted_count"], 10)
        self.assertEqual(self.turns(), [1] * 10)
        for row in self.rows:
            records = self.response_records(row["run_id"])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["payload"]["provenance"]["worker_task"], "original-worker")


if __name__ == "__main__":
    unittest.main()
