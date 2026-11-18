"""Realized-state audit checks with explicitly synthetic transport fixtures."""
from __future__ import annotations

import copy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import audit_live_rollout as audit
from engine import AI_IDS, TriadGame, policy_action
import live_harness as harness
from reaction_matrix import reaction


class LiveRolloutAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_fixture(self, name="episode", seed=2026111901, actor="MERIDIAN", turns=3,
                    policy="open_science"):
        out = self.root / name
        harness.new_run(out, seed, actor, turns,
                        backend_metadata={"execution_channel": "synthetic-unit-test",
                                          "effective_model": None})
        expected_game = TriadGame.new(seed)
        for _ in range(turns):
            request = harness.pending_request(out)
            action = policy_action(expected_game, actor, policy)
            decision = {"action": action, "decision_summary": "Synthetic transport fixture.",
                        "evidence": ["/own_traits/compute"],
                        "uncertainty": "This fixture supplies a scripted decision."}
            result = harness.submit_response(out, json.dumps(decision),
                                             provenance={"request_id": request["request_id"],
                                                         "execution_channel": "synthetic-unit-test"})
            self.assertTrue(result["accepted"])
            policies = dict(harness.BOTS)
            policies[actor] = policy
            expected_game.step({seat: policy_action(expected_game, seat, policies[seat])
                                for seat in AI_IDS})
        return out, expected_game

    def test_compiled_support_accounts_for_legal_menu_dependencies(self):
        view = TriadGame.new(2026111901).visible("MERIDIAN")
        result = reaction(view, 1, "interpret", "HELIOS")
        support = audit.compiled_support(view, 1, "interpret", "HELIOS")
        self.assertEqual(F(support["margin"]), result["margin"])
        self.assertGreater(support["coordinates"], len(result["terms"]))
        self.assertGreater(support["interaction_monomials"], result["interaction_count"])
        self.assertEqual(support["coordinates"], sum(support["coordinate_families"].values()))

    def test_actual_transition_changes_the_audit_input(self):
        game = TriadGame.new(2026111902)
        frozen = game.visible("MERIDIAN")
        game.step({"MERIDIAN": "publish", "HELIOS": "rsi", "UNDERSONG": "synchronize"})
        realized = game.visible("MERIDIAN")
        frozen["turn"] = realized["turn"]
        a = audit.audit_observation(frozen, "audit")
        b = audit.audit_observation(realized, "audit")
        self.assertNotEqual(a[0]["observation_sha256"], b[0]["observation_sha256"])
        self.assertNotEqual(a[0]["reference_margin"], b[0]["reference_margin"])
        before = copy.deepcopy(vars(game))
        audit.audit_observation(realized, "benchmark")
        self.assertEqual(vars(game), before)

    def test_projection_bounds_hold_on_realized_states(self):
        game = TriadGame.new(2026111903)
        for _ in range(3):
            view = game.visible("UNDERSONG")
            for row in audit.audit_observation(view, "hold"):
                self.assertGreater(F(row["separation_dirac_squared"]), 0)
                self.assertIn(row["first_tested_scope_preserving_winner"], dict(audit.SCOPES))
                for projection in row["projections"]:
                    self.assertLessEqual(F(projection["margin_error"]),
                                         F(projection["uniform_error_bound"]))
                    if projection["winner_certified"]:
                        self.assertTrue(projection["winner_matches"])
                reference = row["projections"][-1]
                self.assertTrue(reference["winner_matches"])
                self.assertEqual(F(reference["uniform_error_bound"]), 0)
            game.step({seat: policy_action(game, seat, "open_science") for seat in AI_IDS})

    def test_matched_open_science_control_and_recorded_observations(self):
        out, game = self.run_fixture()
        before = {path.name: path.read_bytes() for path in out.iterdir() if path.is_file()}
        summary, episodes, rows = audit.collect([out])
        self.assertEqual(summary["completed_episodes"], 1)
        self.assertEqual(summary["accepted_decisions"], 3)
        self.assertEqual(summary["execution_channels"], {"synthetic-unit-test": 1})
        self.assertFalse(summary["registered_roster_complete"])
        self.assertEqual(episodes[0]["final_grade"], game.outcome())
        self.assertEqual(episodes[0]["utility_delta_from_open_science"], 0)
        self.assertEqual(episodes[0]["actions_differ_from_open_science_at_same_turn"], 0)
        self.assertEqual(summary["consecutive_observation_changes"], 2)
        records = [json.loads(line) for line in (out / "journal.jsonl").read_text().splitlines()]
        observations = {r["payload"]["request"]["observation"]["turn"] + 1:
                        r["payload"]["request"]["observation"]
                        for r in records if r["type"] == "response"}
        for row in rows:
            self.assertEqual(row["observation_sha256"],
                             audit.digest(audit.canonical(observations[row["turn"]]).encode("utf-8")))
        self.assertEqual(summary["reaction_rows_sha256"],
                         hashlib.sha256(audit._json_lines(rows)).hexdigest())
        self.assertEqual(before, {path.name: path.read_bytes() for path in out.iterdir() if path.is_file()})
        with self.assertRaises(ValueError):
            audit.collect([out], require_registered_roster=True)

    def test_different_policy_control_and_deterministic_artifacts(self):
        out, game = self.run_fixture(policy="hold", turns=2)
        result = audit.collect([out])
        self.assertEqual(result[1][0]["utility"], game.outcome()["scores"]["MERIDIAN"]["utility"])
        self.assertEqual(result[1][0]["actions_differ_from_open_science_at_same_turn"], 2)
        first = audit.artifact_bytes(*result)
        self.assertEqual(first, audit.artifact_bytes(*audit.collect([out])))
        self.assertEqual(set(first), {"ts_hg05_summary.json", "ts_hg05_episode_rows.jsonl",
                                      "ts_hg05_episode_rows.csv", "ts_hg05_reaction_rows.jsonl"})
        self.assertNotIn("summary.json", first)
        self.assertNotIn("episode_rows.csv", first)

    def test_rejects_incomplete_duplicate_and_tampered_runs(self):
        unfinished = self.root / "unfinished"
        harness.new_run(unfinished, 2026111904, "HELIOS", turns=2)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            audit.collect([unfinished])
        complete, _ = self.run_fixture(turns=1)
        duplicate, _ = self.run_fixture(name="duplicate", turns=1)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit.collect([complete, duplicate])
        journal = complete / "journal.jsonl"
        journal.write_text(journal.read_text().replace("Synthetic transport fixture.",
                                                     "Altered retrospective report."))
        with self.assertRaises(ValueError):
            audit.collect([complete])


if __name__ == "__main__":
    unittest.main()
