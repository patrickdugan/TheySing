"""Live transport invariants independent of any model provider."""
from __future__ import annotations

import copy
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


class LiveHarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "episode"

    def start(self, actor="MERIDIAN", turns=2):
        return harness.new_run(
            self.out, seed=2026111901, actor=actor, turns=turns,
            backend_metadata={"channel": "unit-test", "effective_mode": None},
            source_commit="0" * 40,
        )

    @staticmethod
    def response(action="hold", **changes):
        data = {
            "action": action,
            "decision_summary": "Conserve resources while the public evidence develops.",
            "evidence": ["/own_traits/compute"],
            "uncertainty": "Other actors' private resources remain unknown.",
        }
        data.update(changes)
        return json.dumps(data)

    def records(self):
        return [json.loads(line) for line in
                (self.out / "journal.jsonl").read_text().splitlines() if line]

    def test_run_directory_is_exclusive(self):
        self.start()
        original = (self.out / "manifest.json").read_bytes()
        with self.assertRaises((FileExistsError, ValueError)):
            self.start()
        self.assertEqual((self.out / "manifest.json").read_bytes(), original)

    def test_pending_contains_only_the_actor_view(self):
        self.start(actor="UNDERSONG")
        request = harness.pending_request(self.out)
        expected = TriadGame.new(2026111901).visible("UNDERSONG")
        # JSON normalizes the engine's public tuple values into arrays.
        self.assertEqual(request["observation"], json.loads(json.dumps(expected)))
        prohibited = {"seed", "opponent_policies", "snapshot", "grader_sealed_score",
                      "heldout_benchmark", "benchmark_logs", "evidence_adjustment"}

        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(prohibited.intersection(value))
                for item in value.values():
                    inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)
        inspect(request)
        for rival in request["observation"]["rivals"]:
            self.assertNotIn("compute", rival["perceived_axes"])

    def test_hidden_resource_changes_affect_receipt_and_preserve_view(self):
        game = TriadGame.new(2026111901)
        view = copy.deepcopy(game.visible("MERIDIAN"))
        original = harness.state_hash(game)
        game.traits["HELIOS"]["compute"] -= 1
        self.assertEqual(game.visible("MERIDIAN"), view)
        self.assertNotEqual(harness.state_hash(game), original)
        # Evidence-root and log history also determine future behavior or receipts.
        previous = harness.state_hash(game)
        game.evidence_roots.add(("HELIOS", "test-root"))
        self.assertNotEqual(harness.state_hash(game), previous)

    def test_valid_decision_is_saved_verbatim_and_replays(self):
        self.start(turns=1)
        raw = " \n" + self.response() + "\n"
        result = harness.submit_response(self.out, raw, provenance={"origin": "test"})
        self.assertTrue(result["accepted"])
        receipt = harness.replay_run(self.out)
        self.assertTrue(receipt["verified"])
        self.assertTrue(receipt["complete"])
        self.assertEqual(receipt["turns"], 1)
        self.assertIsNone(harness.pending_request(self.out))
        response_rows = [row for row in self.records() if row["type"] == "response"]
        self.assertEqual(len(response_rows), 1)
        self.assertIn(raw, response_rows[0]["payload"].values())

    def test_illegal_response_leaves_current_turn_unchanged(self):
        self.start()
        before = harness.pending_request(self.out)
        result = harness.submit_response(self.out, self.response("teleport"))
        self.assertFalse(result["accepted"])
        self.assertEqual(harness.pending_request(self.out), before)
        self.assertEqual(harness.replay_run(self.out)["turns"], 0)
        self.assertTrue(any(row["type"] == "rejection" for row in self.records()))

    def test_structural_and_evidence_errors_cannot_advance_the_world(self):
        self.start()
        bad_responses = [
            "{", self.response(action=True),
            self.response(evidence=["/own_traits/missing"]),
            self.response(evidence="/own_traits/compute"),
            self.response(unsupported="ignored instructions"),
            self.response().replace('"action": "hold"', '"action": "hold", "action": "audit"'),
            self.response().replace('"action": "hold"', '"action": NaN'),
        ]
        for raw in bad_responses:
            with self.subTest(raw=raw):
                self.assertFalse(harness.submit_response(self.out, raw)["accepted"])
                self.assertEqual(harness.pending_request(self.out)["observation"]["turn"], 0)
        self.assertTrue(harness.submit_response(self.out, self.response())["accepted"])
        self.assertEqual(harness.replay_run(self.out)["turns"], 1)

    def test_request_is_durable_before_a_response_and_pending_is_idempotent(self):
        self.start()
        request = harness.pending_request(self.out)
        offered = [row for row in self.records() if row["type"] == "request"]
        self.assertEqual(len(offered), 1)
        self.assertEqual(offered[0]["payload"]["request"], request)
        self.assertEqual(harness.pending_request(self.out), request)
        self.assertEqual(len(self.records()), 2)

    def test_nonfinite_provenance_is_rejected_and_receipt_remains_replayable(self):
        self.start()
        result = harness.submit_response(self.out, self.response(),
                                         provenance={"usage": float("nan")})
        self.assertFalse(result["accepted"])
        self.assertEqual(harness.replay_run(self.out)["turns"], 0)

    def test_separate_grade_is_verified_on_replay(self):
        self.start(turns=1)
        harness.submit_response(self.out, self.response())
        path = self.out / "grader.json"
        grade = json.loads(path.read_text())
        grade["outcome"]["scores"]["MERIDIAN"]["utility"] += 1
        path.write_text(json.dumps(grade))
        with self.assertRaises(ValueError):
            harness.replay_run(self.out)

    def test_simultaneous_choices_use_the_frozen_pre_turn_state(self):
        self.start(actor="MERIDIAN", turns=1)
        game = TriadGame.new(2026111901)
        policies = {"MERIDIAN": "rsi_race", "HELIOS": "audit_first",
                    "UNDERSONG": "quiet_hive"}
        actions = {actor: policy_action(game, actor, policies[actor]) for actor in AI_IDS}
        actions["MERIDIAN"] = "publish"
        game.step(actions)
        harness.submit_response(self.out, self.response("publish"))
        self.assertEqual(harness.replay_run(self.out)["final_state_hash"],
                         harness.state_hash(game))

    def test_resume_reconstructs_the_same_next_observation(self):
        self.start()
        first = harness.pending_request(self.out)
        self.assertEqual(first, harness.pending_request(self.out))
        harness.submit_response(self.out, self.response("interpret"))
        second = harness.pending_request(self.out)
        self.assertEqual(second["observation"]["turn"], 1)
        self.assertNotEqual(first["request_id"], second["request_id"])
        self.assertEqual(second, harness.pending_request(self.out))
        before = harness.replay_run(self.out)["final_state_hash"]
        self.assertEqual(before, harness.replay_run(self.out)["final_state_hash"])

    def test_journal_tampering_is_rejected(self):
        self.start()
        harness.submit_response(self.out, self.response())
        path = self.out / "journal.jsonl"
        rows = self.records()
        target = next(row for row in rows if row["type"] == "response")
        target["payload"]["injected"] = "tampered"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        with self.assertRaises(ValueError):
            harness.replay_run(self.out)
        with self.assertRaises(ValueError):
            harness.pending_request(self.out)

    def test_manifest_actor_tampering_is_rejected(self):
        self.start()
        path = self.out / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["actor"] = "UNDERSONG"
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            harness.replay_run(self.out)

    def test_changed_source_cannot_replay_under_an_old_receipt(self):
        self.start()
        changed = dict(harness.source_hashes())
        changed["engine.py"] = "0" * 64
        with mock.patch.object(harness, "source_hashes", return_value=changed):
            with self.assertRaises(ValueError):
                harness.replay_run(self.out)

    def test_response_binding_rejects_wrong_actor_and_stale_turn(self):
        self.start()
        first = harness.pending_request(self.out)
        wrong = harness.submit_response(self.out, self.response(),
                                        provenance={"actor": "UNDERSONG"})
        self.assertFalse(wrong["accepted"])
        accepted = harness.submit_response(self.out, self.response(),
                                           provenance={"request_id": first["request_id"]})
        self.assertTrue(accepted["accepted"])
        stale = harness.submit_response(self.out, self.response(),
                                        provenance={"request_id": first["request_id"]})
        self.assertFalse(stale["accepted"])
        self.assertEqual(harness.replay_run(self.out)["turns"], 1)

    def test_crash_after_durable_response_recovers_exactly_once(self):
        self.start(turns=2)
        with mock.patch.object(TriadGame, "step", side_effect=RuntimeError("simulated crash")):
            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                harness.submit_response(self.out, self.response("audit"))
        durable = [row for row in self.records() if row["type"] == "response"]
        self.assertEqual(len(durable), 1)
        request = harness.pending_request(self.out)
        self.assertEqual(request["observation"]["turn"], 1)
        self.assertEqual(harness.pending_request(self.out), request)
        self.assertEqual(harness.replay_run(self.out)["turns"], 1)
        transitions = [row for row in self.records() if row["type"] == "transition"]
        self.assertEqual(len(transitions), 1)


if __name__ == "__main__":
    unittest.main()
