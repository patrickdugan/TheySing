"""Audit completed TS-HG-05 action journals against their realized observations.

The authored reaction formulas are a shadow analysis. Their projected winners
do not measure which observation coordinates a live model needs. Model actions
remain fixed throughout this post-run analysis; no grades enter a request.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from fractions import Fraction as F
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine import AI_IDS, TURN_LIMIT, run_scripted
from reaction_matrix import (
    AI, CAST, MathScope, _raw, projection_certificate, reaction,
    separation_squared,
)

HERE = Path(__file__).resolve().parent
REGISTERED_SEEDS = tuple(range(2026111901, 2026111911))
REFERENCE = MathScope()
SCOPES = (
    ("tiny", MathScope(1, 1, 1, 1, 0, 0)),
    ("compact", MathScope(2, 2, 2, 2, 1, 2)),
    ("medium", MathScope(4, 4, 3, 3, 2, 4)),
    ("tshg04_small", MathScope(5, 5, 4, 3, 3, 5)),
    ("reference", REFERENCE),
)
AUDIT_SOURCES = ("engine.py", "reaction_matrix.py", "live_harness.py",
                 "audit_live_rollout.py")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_lines(rows: Sequence[dict]) -> bytes:
    return "".join(canonical(row) + "\n" for row in rows).encode("utf-8")


def compiled_support(view: Mapping, turn: int, action: str, respondent: str,
                     scope: MathScope = REFERENCE) -> dict:
    """Count the exact polynomial after legal-menu centering and contrast.

    A single action's raw term ledger omits dependencies introduced by the
    mean of the other legal actions. Compile coefficients before counting,
    remove cancelled monomials, and count each underlying coordinate once.
    These are observable coordinates, with no independence interpretation.
    """
    menu = tuple(view["available_actions"])
    coefficients: dict[tuple, F] = defaultdict(F)
    values: dict[tuple, F] = {}
    for option in menu:
        weight = F(7, 20) * (F(int(option == action)) - F(1, len(menu)))
        for key, value, coefficient in _raw(view, turn, option, respondent, scope)["terms"]:
            coefficients[key] += weight * coefficient
            if key in values and values[key] != value:
                raise ValueError("one observable monomial acquired inconsistent values")
            values[key] = value

    result = reaction(view, turn, action, respondent, scope)
    contrast = result["relational_contrast"]
    axis = contrast["axis"]
    counterpart = contrast["counterpart"]
    respondent_key = ("other_ai" if respondent in AI else "public", respondent, axis)
    if counterpart == view["perspective"]:
        counterpart_key = ("own", counterpart, axis)
    else:
        counterpart_key = ("other_ai" if counterpart in AI else "public", counterpart, axis)
    for key, value, coefficient in (
        (respondent_key, contrast["respondent_estimate"], F(1, 20)),
        (counterpart_key, contrast["counterpart_estimate"], -F(1, 20)),
    ):
        if key in values and values[key] != value:
            raise ValueError("contrast and raw ledger disagree on an observable value")
        coefficients[key] += coefficient
        values[key] = value
    coefficients = {key: coefficient for key, coefficient in coefficients.items() if coefficient}
    evaluated = sum((coefficient * values[key] for key, coefficient in coefficients.items()), F(0))
    if evaluated != result["margin"]:
        raise ValueError("compiled reaction does not reproduce the exact margin")
    coordinates = set()
    for key in coefficients:
        coordinates.update(key[1:] if key[0] == "interaction" else (key,))
    return {
        "monomials": len(coefficients),
        "coordinates": len(coordinates),
        "interaction_monomials": sum(key[0] == "interaction" for key in coefficients),
        "coordinate_families": dict(sorted(Counter(key[0] for key in coordinates).items())),
        "margin": str(evaluated),
    }


def audit_observation(view: Mapping, action: str) -> list[dict]:
    """Audit one chosen action against the pre-turn seat observation only."""
    turn = view["turn"] + 1
    actor = view["perspective"]
    if action not in view["available_actions"]:
        raise ValueError("cannot audit an unavailable chosen action")
    rows = []
    for respondent in CAST[turn - 1]:
        if respondent == actor:
            continue
        full = reaction(view, turn, action, respondent, REFERENCE)
        reference_support = compiled_support(view, turn, action, respondent, REFERENCE)
        projections = []
        for name, scope in SCOPES:
            certificate = projection_certificate(view, turn, action, respondent,
                                                 REFERENCE, scope)
            error = abs(certificate["full_margin"] - certificate["projected_margin"])
            if error > certificate["bound"]:
                raise ValueError("a projection exceeded its exact uniform bound")
            if certificate["winner_certified"] and not certificate["winner_matches"]:
                raise ValueError("an asserted projection certificate is unsound")
            projected = reaction(view, turn, action, respondent, scope)
            support = reference_support if name == "reference" else compiled_support(
                view, turn, action, respondent, scope)
            projections.append({
                "scope": name,
                "margin": str(certificate["projected_margin"]),
                "margin_error": str(error),
                "uniform_error_bound": str(certificate["bound"]),
                "selected": projected["selected"],
                "winner_matches": certificate["winner_matches"],
                "winner_certified": certificate["winner_certified"],
                "compiled_coordinate_count": support["coordinates"],
                "compiled_monomial_count": support["monomials"],
            })
        rows.append({
            "turn": turn,
            "actor": actor,
            "action": action,
            "respondent": respondent,
            "observation_sha256": digest(canonical(view).encode("utf-8")),
            "reference_margin": str(full["margin"]),
            "reference_scores": list(map(str, full["scores"])),
            "reference_selected": full["selected"],
            "raw_action_ledger_terms": len(full["terms"]),
            "raw_action_p2_terms": full["groups"]["p2"],
            "reference_compiled_support": reference_support,
            "separation_dirac_squared": str(separation_squared(full)),
            "projections": projections,
            "first_tested_scope_preserving_winner": next(
                p["scope"] for p in projections if p["winner_matches"]),
            "first_tested_scope_certifying_winner": next(
                (p["scope"] for p in projections if p["winner_certified"]), None),
        })
    return rows


def _load_run(directory: Path):
    from live_harness import load_verified_run
    return load_verified_run(directory)


def _audit_source_hashes() -> dict[str, str]:
    return {name: digest((HERE / name).read_bytes()) for name in AUDIT_SOURCES}


def collect(run_directories: Sequence[Path], *, require_registered_roster: bool = False) -> tuple[dict, list[dict], list[dict]]:
    """Verify completed runs, then produce descriptive and shadow-math rows."""
    if not run_directories:
        raise ValueError("no run directories supplied")
    sources = _audit_source_hashes()
    episodes = []
    reactions = []
    artifacts = []
    seen_roots = set()
    seen_ids = set()
    actions = Counter()
    channels = Counter()
    rejected = 0
    evidence_uses_p2 = 0
    changed_observations = 0
    changed_actions = 0
    for directory in sorted(map(Path, run_directories), key=lambda p: str(p)):
        manifest, records, game = _load_run(directory)
        actor, seed, turns = manifest["actor"], manifest["seed"], manifest["turns"]
        if game.turn != turns:
            raise ValueError(f"incomplete run: {directory.name} ({game.turn}/{turns})")
        if (seed, actor) in seen_roots or manifest["run_id"] in seen_ids:
            raise ValueError("duplicate run id or seed/seat pair")
        seen_roots.add((seed, actor))
        seen_ids.add(manifest["run_id"])
        for name in ("engine.py", "reaction_matrix.py", "live_harness.py"):
            if manifest["source_sha256"].get(name) != sources[name]:
                raise ValueError(f"run lacks the required current source lock: {name}")
        responses = [record["payload"] for record in records if record["type"] == "response"]
        transitions = [record["payload"] for record in records if record["type"] == "transition"]
        if len(responses) != turns or len(transitions) != turns:
            raise ValueError("complete run has an unexpected response/transition count")
        rejected += sum(record["type"] == "rejection" for record in records)
        outcome = game.outcome()
        baseline, trace = run_scripted(seed, actor, "open_science", turns)
        baseline_grade = baseline.outcome()
        baseline_actions = [item["chosen"][actor] for item in trace]
        chosen_actions = []
        previous_view = None
        for response, transition in zip(responses, transitions):
            request = response["request"]
            observation = request["observation"]
            choice = response["decision"]
            action = choice["action"]
            if observation["perspective"] != actor or transition["actions"][actor] != action:
                raise ValueError("seat request and transition disagree")
            chosen_actions.append(action)
            actions[action] += 1
            evidence_uses_p2 += any(
                pointer.startswith(("/selected_second_order_beliefs", "/dialogue_forecast_from_p2"))
                for pointer in choice["evidence"]
            )
            if previous_view is not None:
                changed_observations += (
                    previous_view["own_traits"] != observation["own_traits"] or
                    previous_view["public_world"] != observation["public_world"] or
                    previous_view["rivals"] != observation["rivals"]
                )
            previous_view = observation
            for row in audit_observation(observation, action):
                reactions.append({"run_id": manifest["run_id"], "seed": seed, **row})
        changed_actions += sum(a != b for a, b in zip(chosen_actions, chosen_actions[1:]))
        metadata = manifest.get("backend_metadata", {})
        channel = str(metadata.get("execution_channel", metadata.get("backend", "unreported")))
        channels[channel] += 1
        episodes.append({
            "run_id": manifest["run_id"], "seed": seed, "actor": actor,
            "turns": turns, "ending": outcome["ending"],
            "utility": outcome["scores"][actor]["utility"],
            "heldout_benchmark": outcome["scores"][actor]["heldout_benchmark"],
            "open_science_utility": baseline_grade["scores"][actor]["utility"],
            "utility_delta_from_open_science": (outcome["scores"][actor]["utility"] -
                                                  baseline_grade["scores"][actor]["utility"]),
            "open_science_ending": baseline_grade["ending"],
            "actions_differ_from_open_science_at_same_turn": sum(
                a != b for a, b in zip(chosen_actions, baseline_actions)),
            "actions": chosen_actions,
            "open_science_actions": baseline_actions,
            "execution_channel": channel,
            "backend_metadata": metadata,
            "final_grade": outcome,
        })
        artifacts.append({"run_id": manifest["run_id"], "source_commit": manifest.get("source_commit"),
                          "files_sha256": {name: digest((directory / name).read_bytes())
                                           for name in ("manifest.json", "journal.jsonl", "grader.json")}})
    expected = {(seed, actor) for seed in REGISTERED_SEEDS for actor in AI_IDS}
    roster_complete = seen_roots == expected and all(row["turns"] == TURN_LIMIT for row in episodes)
    if require_registered_roster and not roster_complete:
        raise ValueError("run set differs from the registered 10-seed by 3-seat, 10-turn roster")

    scope_summary = {}
    for name, scope in SCOPES:
        projections = [next(p for p in row["projections"] if p["scope"] == name) for row in reactions]
        scope_summary[name] = {
            "scope": asdict(scope),
            "rows": len(projections),
            "winner_matches": sum(p["winner_matches"] for p in projections),
            "winner_certified": sum(p["winner_certified"] for p in projections),
            "max_observed_margin_error": str(max((F(p["margin_error"]) for p in projections), default=F(0))),
            "max_uniform_error_bound": str(max((F(p["uniform_error_bound"]) for p in projections), default=F(0))),
            "compiled_coordinate_min": min((p["compiled_coordinate_count"] for p in projections), default=0),
            "compiled_coordinate_max": max((p["compiled_coordinate_count"] for p in projections), default=0),
        }
    distances = [F(row["separation_dirac_squared"]) for row in reactions]
    actor_comparisons = {}
    for actor in AI_IDS:
        rows = [row for row in episodes if row["actor"] == actor]
        if not rows:
            continue
        deltas = [row["utility_delta_from_open_science"] for row in rows]
        actor_comparisons[actor] = {
            "episodes": len(rows), "utility_deltas": deltas,
            "mean_utility_delta_exact": str(F(sum(deltas), len(deltas))),
            "positive": sum(delta > 0 for delta in deltas),
            "zero": sum(delta == 0 for delta in deltas),
            "negative": sum(delta < 0 for delta in deltas),
        }
    summary = {
        "schema": "TS-HG-05/realized-rollout-audit/v1",
        "evidence_class": "completed external-action journals with descriptive matched scripted controls",
        "source_sha256": sources,
        "registered_roster_complete": roster_complete,
        "registered_seeds": list(REGISTERED_SEEDS),
        "completed_episodes": len(episodes),
        "unique_seed_roots": len({seed for seed, _actor in seen_roots}),
        "accepted_decisions": sum(row["turns"] for row in episodes),
        "rejected_attempts": rejected,
        "execution_channels": dict(sorted(channels.items())),
        "action_counts": dict(sorted(actions.items())),
        "consecutive_action_changes": changed_actions,
        "consecutive_observation_changes": changed_observations,
        "decision_reports_citing_p2": evidence_uses_p2,
        "ending_counts": dict(sorted(Counter(row["ending"] for row in episodes).items())),
        "matched_open_science": actor_comparisons,
        "chosen_action_respondent_rows": len(reactions),
        "competing_shadow_reactions": 2 * len(reactions),
        "reference_reaction_selections": dict(sorted(Counter(str(row["reference_selected"]) for row in reactions).items())),
        "scope_results": scope_summary,
        "first_tested_scope_preserving_winner": dict(sorted(Counter(
            row["first_tested_scope_preserving_winner"] for row in reactions).items())),
        "first_tested_scope_certifying_winner": dict(sorted(Counter(
            row["first_tested_scope_certifying_winner"] or "none_at_exact_tie" for row in reactions).items())),
        "min_reaction_distance_squared": str(min(distances)) if distances else None,
        "max_reaction_distance_squared": str(max(distances)) if distances else None,
        "episode_rows_sha256": digest(_json_lines(episodes)),
        "reaction_rows_sha256": digest(_json_lines(reactions)),
        "run_artifacts": artifacts,
        "interpretation_limits": [
            "The selected-action reaction formulas are an observer-owned shadow model; their effects did not drive game transitions.",
            "First tested scope means the first preserving choice in the declared finite grid, not a global minimum or a model observation ablation.",
            "Compiled support includes all legal-menu centering dependencies and contrast coordinates; coordinate counts do not establish independent information dimensions.",
            "The open_science control follows its own deterministic trajectory at the same seed and seat; utility differences describe these synthetic episodes.",
            "A decision report citing p2 is an observable citation, with no claim that p2 caused the chosen action.",
            "Fresh seeds share this game's authored mechanisms; this audit establishes neither independent real-world generalization nor model rankings.",
        ],
    }
    return summary, episodes, reactions


def artifact_bytes(summary: dict, episodes: list[dict], reactions: list[dict]) -> dict[str, bytes]:
    table = io.StringIO(newline="")
    fields = ("run_id", "seed", "actor", "turns", "ending", "utility", "heldout_benchmark",
              "open_science_utility", "utility_delta_from_open_science", "open_science_ending",
              "actions_differ_from_open_science_at_same_turn", "execution_channel")
    writer = csv.DictWriter(table, fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(episodes)
    return {
        "ts_hg05_summary.json": (json.dumps(summary, sort_keys=True, ensure_ascii=False, indent=2,
                                          allow_nan=False) + "\n").encode("utf-8"),
        "ts_hg05_episode_rows.jsonl": _json_lines(episodes),
        "ts_hg05_episode_rows.csv": table.getvalue().encode("utf-8"),
        "ts_hg05_reaction_rows.jsonl": _json_lines(reactions),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True,
                        help="directory containing run subdirectories, each with manifest.json")
    parser.add_argument("--out", type=Path, required=True,
                        help="dedicated TS-HG-05 analysis directory")
    parser.add_argument("--require-registered-roster", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="verify existing analysis artifacts without changing them")
    args = parser.parse_args()
    run_dirs = [path.parent for path in args.runs.glob("*/manifest.json")]
    if not run_dirs and (args.runs / "manifest.json").exists():
        run_dirs = [args.runs]
    try:
        data = collect(run_dirs, require_registered_roster=args.require_registered_roster)
        artifacts = artifact_bytes(*data)
        if args.check:
            for name, content in artifacts.items():
                if (args.out / name).read_bytes() != content:
                    raise ValueError(f"analysis drift: {name}")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            for name, content in artifacts.items():
                (args.out / name).write_bytes(content)
        print(canonical({"verified": True, "episodes": data[0]["completed_episodes"],
                         "accepted_decisions": data[0]["accepted_decisions"],
                         "reaction_rows": len(data[2]), "check": args.check}))
    except (ValueError, OSError, KeyError) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc


if __name__ == "__main__":
    main()
