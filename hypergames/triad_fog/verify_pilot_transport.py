"""Verify the complete TS-HG05 batch transport against source-locked journals.

This controller-only verifier reads a finished pilot. It checks archived wire
bytes, their decision substrings, and the links into each episode's replay.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from engine import AI_IDS, TURN_LIMIT
from live_harness import load_verified_run
from pilot_batch import METADATA, SEEDS, canonical, parse_line, unique_object


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    def reject_constant(_value):
        raise ValueError("nonfinite JSON value")
    return json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root: str | Path) -> dict:
    root = Path(root)
    manifest_path = root / "pilot_manifest.json"
    manifest = read_json(manifest_path)
    roster = [{"run_id": f"{actor.lower()}-{index:02d}", "actor": actor, "seed": seed}
              for actor in AI_IDS for index, seed in enumerate(SEEDS, 1)]
    require(manifest.get("schema") == "TS-HG-05/pilot/v1", "pilot schema mismatch")
    require(manifest.get("runs") == roster, "pilot roster differs from the 30 registered seed/seat pairs")
    require(manifest.get("seed_roots") == list(SEEDS), "pilot seed roots differ")
    require(manifest.get("episodes_registered") == 30 and
            manifest.get("decisions_registered") == 300 and
            manifest.get("turns_per_episode") == TURN_LIMIT, "pilot budget differs")
    require(manifest.get("backend_metadata") == METADATA, "pilot backend disclosure differs")
    require(isinstance(manifest.get("source_commit"), str) and
            re.fullmatch(r"[0-9a-f]{40}", manifest["source_commit"]), "invalid source commit")
    actual_runs = {path.parent.name for path in (root / "runs").glob("*/manifest.json")}
    require(actual_runs == {row["run_id"] for row in roster}, "run directory set differs from roster")
    receipts = {}
    file_hashes = {"pilot_manifest.json": sha(manifest_path.read_bytes())}
    journal_rejections = 0
    final_hashes = {}

    for row in roster:
        directory = root / "runs" / row["run_id"]
        # Reject incomplete input before invoking the core's crash-recovery
        # loader. Valid complete journals take its read-only path.
        require((directory / "grader.json").is_file(), "completed run has no grader receipt")
        raw_journal = (directory / "journal.jsonl").read_bytes()
        require(raw_journal.endswith(b"\n"), "truncated journal")
        preliminary = [json.loads(line) for line in raw_journal.splitlines()]
        require(preliminary and preliminary[-1].get("type") == "transition" and
                preliminary[-1].get("payload", {}).get("turn_after") == TURN_LIMIT,
                "run is incomplete; verifier will not recover or advance it")
        require(sum(record.get("type") == "response" for record in preliminary) == TURN_LIMIT and
                sum(record.get("type") == "transition" for record in preliminary) == TURN_LIMIT,
                "run does not contain ten committed decisions and transitions")
        source_manifest, records, game = load_verified_run(directory)
        require(game.turn == TURN_LIMIT and source_manifest["turns"] == TURN_LIMIT,
                "run did not complete the registered turn budget")
        require(source_manifest["seed"] == row["seed"] and source_manifest["actor"] == row["actor"],
                "run seat or seed differs from pilot roster")
        require(source_manifest["source_commit"] == manifest["source_commit"] and
                source_manifest["backend_metadata"] == manifest["backend_metadata"],
                "run provenance differs from pilot manifest")
        journal_rejections += sum(record["type"] == "rejection" for record in records)
        offered = {record["payload"]["turn"]: record["payload"]["request"]
                   for record in records if record["type"] == "request"}
        require(set(offered) == set(range(TURN_LIMIT)), "run lacks a request receipt for every turn")
        for record in records:
            if record["type"] == "response":
                payload = record["payload"]
                require(payload["request"] == offered[payload["turn"]], "offered and accepted requests differ")
                receipts[(row["run_id"], payload["turn"])] = payload
        grader = read_json(directory / "grader.json")
        final_hashes[row["run_id"]] = grader["final_state_hash"]
        for name in ("manifest.json", "journal.jsonl", "grader.json"):
            file_hashes[str((directory / name).relative_to(root))] = sha((directory / name).read_bytes())

    batches = {}
    attempt_rows = []
    attempts_by_status = Counter()
    completed_receipt_sets = set()
    for actor in AI_IDS:
        directory = root / "transport" / actor.lower()
        expected_ids = {row["run_id"] for row in roster if row["actor"] == actor}
        expected_requests = {f"turn-{turn:02d}-request.json" for turn in range(TURN_LIMIT)}
        expected_responses = {f"turn-{turn:02d}-response.jsonl" for turn in range(TURN_LIMIT)}
        expected_metadata = {f"turn-{turn:02d}-response.metadata.json" for turn in range(TURN_LIMIT)}
        require({p.name for p in directory.glob("turn-*-request.json")} == expected_requests,
                "seat request file set differs from ten registered turns")
        require({p.name for p in directory.glob("turn-*-response.jsonl")} == expected_responses,
                "seat response file set differs from ten registered turns")
        require({p.name for p in directory.glob("turn-*-response.metadata.json")} == expected_metadata,
                "seat response-origin metadata set differs")
        for turn in range(TURN_LIMIT):
            request_path = directory / f"turn-{turn:02d}-request.json"
            response_path = directory / f"turn-{turn:02d}-response.jsonl"
            metadata_path = response_path.with_suffix(".metadata.json")
            request_bytes, response_bytes = request_path.read_bytes(), response_path.read_bytes()
            batch, origin = read_json(request_path), read_json(metadata_path)
            require(batch.get("schema") == "TS-HG-05/batch-request/v1" and
                    batch.get("actor") == actor and type(batch.get("turn")) is int and
                    batch["turn"] == turn, "batch request identity mismatch")
            require(set(batch["common"]) == {"rules", "scene", "response_schema"},
                    "batch common fields differ")
            require(len(batch["games"]) == 10 and
                    {item["run_id"] for item in batch["games"]} == expected_ids,
                    "batch request does not cover its ten worlds exactly once")
            response_rows = [parse_line(line) for line in response_bytes.decode("utf-8").splitlines()
                             if line.strip()]
            require(len(response_rows) == 10 and {item["run_id"] for item, _ in response_rows} == expected_ids,
                    "batch response does not cover its ten worlds exactly once")
            response_map = {item["run_id"]: (item, raw) for item, raw in response_rows}
            request_sha, response_sha = sha(request_bytes), sha(response_bytes)
            require(origin.get("batch_response_sha256") == response_sha and
                    isinstance(origin.get("worker_task"), str) and origin["worker_task"].strip(),
                    "response-origin metadata does not bind the archived bytes")
            for item in batch["games"]:
                run_id = item["run_id"]
                require(not set(item["request"]).intersection(batch["common"]),
                        "common fields are duplicated in an individual request")
                request = {**item["request"], **batch["common"]}
                core = receipts[(run_id, turn)]
                parsed, raw_decision = response_map[run_id]
                require(request == core["request"], "batch common/request merge differs from the core request")
                require(parsed["request_id"] == request["request_id"], "response names a different request")
                require(raw_decision == core["raw_response"] and parsed["decision"] == core["decision"],
                        "exact decision substring differs from the core response")
                provenance = core["provenance"]
                expected = {**METADATA, "worker_task": origin["worker_task"], "actor": actor,
                            "batch_request_sha256": request_sha,
                            "batch_response_sha256": response_sha,
                            "raw_decision_sha256": sha(raw_decision.encode("utf-8")),
                            "batch_request_path": str(request_path.relative_to(root)),
                            "batch_response_path": str(response_path.relative_to(root)),
                            "request_id": request["request_id"]}
                require(all(provenance.get(key) == value for key, value in expected.items()),
                        "core response provenance does not match the archived batch")
            batches[(actor, turn)] = {"request_sha256": request_sha, "response_sha256": response_sha,
                                      "worker_task": origin["worker_task"]}
            for path in (request_path, response_path, metadata_path):
                file_hashes[str(path.relative_to(root))] = sha(path.read_bytes())

        attempts_dir = directory / "attempts"
        attempt_paths = sorted(attempts_dir.glob("*.jsonl"))
        raw_ids = {path.stem for path in attempt_paths}
        receipt_ids = {path.name.removesuffix(".receipt.json") for path in attempts_dir.glob("*.receipt.json")}
        require(receipt_ids <= raw_ids, "attempt receipt has no preserved payload")
        for path in attempt_paths:
            payload_sha = sha(path.read_bytes())
            file_hashes[str(path.relative_to(root))] = payload_sha
            receipt_path = path.with_suffix(".receipt.json")
            row = {"actor": actor, "attempt_id": path.stem, "payload_sha256": payload_sha}
            if not receipt_path.exists():
                row["status"] = "unreceipted"
                attempts_by_status["unreceipted"] += 1
                attempt_rows.append(row)
                continue
            receipt = read_json(receipt_path)
            require(receipt.get("attempt_id") == path.stem and receipt.get("actor") == actor and
                    receipt.get("attempt_sha256") == payload_sha,
                    "attempt receipt does not bind its exact payload")
            require(type(receipt.get("accepted")) is bool and
                    isinstance(receipt.get("worker_task"), str) and receipt["worker_task"].strip(),
                    "attempt receipt lacks its status or worker identity")
            if receipt["accepted"]:
                turn = receipt.get("batch_turn")
                require(type(turn) is int and (actor, turn) in batches and
                        batches[(actor, turn)]["response_sha256"] == payload_sha,
                        "accepted attempt differs from the committed response batch")
                children = receipt.get("receipts", [])
                require(receipt.get("accepted_count") == 10 and len(children) == 10 and
                        {child["run_id"] for child in children} == expected_ids,
                        "completed batch receipt does not cover its ten worlds")
                for child in children:
                    require(child.get("accepted") is True and type(child.get("turn")) is int and
                            turn + 1 <= child["turn"] <= TURN_LIMIT,
                            "child acceptance receipt has an invalid turn or status")
                    require(child["turn"] == turn + 1 or child.get("resumed_committed_response") is True,
                            "fresh acceptance receipt advanced to a different turn")
                completed_receipt_sets.add((actor, turn))
                row.update(status="accepted", batch_turn=turn)
            else:
                require(receipt.get("accepted_count") == 0 and isinstance(receipt.get("error"), str),
                        "rejected wrapper attempt claims accepted decisions")
                row.update(status="rejected", error=receipt["error"])
            attempts_by_status[row["status"]] += 1
            file_hashes[str(receipt_path.relative_to(root))] = sha(receipt_path.read_bytes())
            attempt_rows.append(row)

    require(completed_receipt_sets == set(batches), "a committed batch lacks a completed acceptance receipt")
    return {
        "schema": "TS-HG-05/pilot-transport-verification/v1", "verified": True,
        "source_commit": manifest["source_commit"], "episodes": 30,
        "accepted_decisions": len(receipts), "committed_batches": len(batches),
        "completed_batch_receipt_sets": len(completed_receipt_sets),
        "wrapper_attempts": len(attempt_rows),
        "wrapper_attempt_status_counts": dict(sorted(attempts_by_status.items())),
        "core_rejected_attempts": journal_rejections,
        "attempt_payloads": attempt_rows,
        "batches": [{"actor": actor, "turn": turn, **value}
                    for (actor, turn), value in sorted(batches.items())],
        "final_state_sha256": final_hashes,
        "file_sha256": dict(sorted(file_hashes.items())),
        "file_set_sha256": sha(canonical(file_hashes).encode("utf-8")),
        "verifier_source_sha256": sha(Path(__file__).read_bytes()),
        "interpretation": "Exact transport/replay linkage; unreceipted attempts remain unresolved, and requested Pro mode remains unverified by provider metadata.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(canonical(verify(args.root)))
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        raise SystemExit("FAIL: " + str(exc)) from exc


if __name__ == "__main__":
    main()
