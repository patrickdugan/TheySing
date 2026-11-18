"""Transport a registered TS-HG05 pilot through an external ChatGPT worker.

The pending/submit commands are the worker's entire game interface. Pending
outputs actor-visible observations. Submit outputs acceptance receipts only.
Exact batch payloads accompany each episode's individual journal.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from uuid import uuid4

from engine import AI_IDS
from live_harness import (new_run, pending_request, replay_run, submit_response,
                          load_verified_run, validate_response)

SEEDS = tuple(range(2026111901, 2026111911))
METADATA = {
    "backend": "chatgpt_collaboration",
    "requested_reasoning_mode": "pro",
    "requested_model": "inherit_current_chatgpt_session",
    "reported_model": None,
    "reported_reasoning_mode": None,
    "reasoning_mode_verified": False,
    "provider_reasoning_summaries": [],
    "usage": None,
    "context_scope": "one_worker_per_seat_ten_world_batch",
    "isolation": "protocol_only_shared_workspace_tools_available",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save_exact(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = text.encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError("existing transport file differs: " + str(path))
        return
    descriptor, temp = tempfile.mkstemp(prefix=".transport-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise ValueError("existing transport file differs: " + str(path))
        if hasattr(os, "O_DIRECTORY"):
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        os.unlink(temp)


def init_pilot(root, source_commit):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    for actor in AI_IDS:
        for index, seed in enumerate(SEEDS, 1):
            run_id = actor.lower() + "-" + str(index).zfill(2)
            new_run(root / "runs" / run_id, seed, actor, backend_metadata=METADATA,
                    source_commit=source_commit)
            rows.append({"run_id": run_id, "actor": actor, "seed": seed})
    manifest = {
        "schema": "TS-HG-05/pilot/v1", "source_commit": source_commit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "episodes_registered": 30, "decisions_registered": 300, "turns_per_episode": 10,
        "seed_roots": list(SEEDS), "backend_metadata": METADATA, "runs": rows,
        "analysis": "fresh-seed descriptive development; same-seat contexts are shared; no model ranking",
    }
    save_exact(root / "pilot_manifest.json", canonical(manifest) + "\n")
    return {"episodes_registered": 30, "decisions_registered": 300}


def runs_for(root, actor):
    if actor not in AI_IDS:
        raise ValueError("unknown acting seat")
    manifest = json.loads((Path(root) / "pilot_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "TS-HG-05/pilot/v1":
        raise ValueError("unknown pilot manifest schema")
    rows = [row for row in manifest["runs"] if row["actor"] == actor]
    expected = [{"run_id": actor.lower() + "-" + str(i).zfill(2), "actor": actor, "seed": seed}
                for i, seed in enumerate(SEEDS, 1)]
    if rows != expected:
        raise ValueError("seat registry differs from the ten registered seed roots")
    return rows


@contextmanager
def seat_lock(root, actor):
    if actor not in AI_IDS:
        raise ValueError("unknown acting seat")
    import fcntl
    directory = Path(root) / "transport" / actor.lower()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".seat.lock").open("a", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def pending_batch(root, actor):
    with seat_lock(root, actor):
        return _pending_batch(Path(root), actor)


def _pending_batch(root, actor):
    root = Path(root)
    games = []
    for row in runs_for(root, actor):
        request = pending_request(root / "runs" / row["run_id"])
        if request is not None:
            games.append({"run_id": row["run_id"], "request": request})
    if not games:
        return {"complete": True, "actor": actor}
    turns = {row["request"]["turn"] for row in games}
    if len(turns) != 1 or len(games) != 10:
        raise ValueError("seat batch is partly submitted; resume its saved response before requesting a new turn")
    turn = next(iter(turns))
    common = {key: games[0]["request"][key] for key in ("rules", "scene", "response_schema")}
    for row in games:
        for key, value in common.items():
            if row["request"][key] != value:
                raise ValueError("inconsistent shared prompt fields")
            del row["request"][key]
    batch = {
        "schema": "TS-HG-05/batch-request/v1", "actor": actor, "turn": turn,
        "common": common, "games": games,
        "transport_instructions": "Merge common into each game request. Produce one JSON object per line with exactly run_id, request_id, decision. decision must match response_schema. Treat each game independently using its current observation. Submit every game in this batch before requesting the next turn.",
    }
    raw = canonical(batch) + "\n"
    save_exact(root / "transport" / actor.lower() / (f"turn-{turn:02d}-request.json"), raw)
    return batch


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def parse_line(raw):
    decoder = json.JSONDecoder(object_pairs_hook=unique_object,
                               parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    row = decoder.decode(raw)
    if not isinstance(row, dict) or set(row) != {"run_id", "request_id", "decision"}:
        raise ValueError("each response line requires exactly run_id, request_id, decision")
    # Locate the exact decision substring while respecting JSON string escaping.
    i = raw.index("{") + 1
    decision_raw = None
    while True:
        while raw[i].isspace():
            i += 1
        key, i = decoder.raw_decode(raw, i)
        while raw[i].isspace():
            i += 1
        if raw[i] != ":":
            raise ValueError("missing JSON colon")
        i += 1
        while raw[i].isspace():
            i += 1
        start = i
        _, i = decoder.raw_decode(raw, i)
        if key == "decision":
            decision_raw = raw[start:i]
        while raw[i].isspace():
            i += 1
        if raw[i] == "}":
            break
        if raw[i] != ",":
            raise ValueError("missing JSON comma")
        i += 1
    if not isinstance(row["decision"], dict) or decision_raw is None:
        raise ValueError("decision must be a JSON object")
    return row, decision_raw


def submit_batch(root, actor, response_path, worker):
    root = Path(root)
    raw = Path(response_path).read_bytes().decode("utf-8")
    with seat_lock(root, actor):
        attempt_id = uuid4().hex
        attempt_path = root / "transport" / actor.lower() / "attempts" / (attempt_id + ".jsonl")
        # Preserve malformed and rejected transport exactly, before parsing it.
        save_exact(attempt_path, raw)
        phase = {"applying": False}
        try:
            result = _submit_batch(root, actor, raw, worker, phase)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            if phase["applying"]:
                raise RuntimeError("committed batch interrupted; resume its exact saved bytes") from exc
            result = {"actor": actor, "accepted": False, "accepted_count": 0,
                      "error": str(exc)}
        receipt = {**result, "attempt_id": attempt_id,
                   "attempt_sha256": sha(raw), "worker_task": worker,
                   "recorded_at": datetime.now(timezone.utc).isoformat()}
        save_exact(attempt_path.with_suffix(".receipt.json"), canonical(receipt) + "\n")
        return receipt


def _submit_batch(root, actor, raw, worker, phase):
    if not isinstance(worker, str) or not worker.strip():
        raise ValueError("worker identity is required")
    parsed = [parse_line(line) for line in raw.splitlines() if line.strip()]
    registered = runs_for(root, actor)
    allowed = {row["run_id"] for row in registered}
    if (len(parsed) != 10 or any(type(row["run_id"]) is not str or type(row["request_id"]) is not str
                                 for row, _ in parsed)
            or {row["run_id"] for row, _ in parsed} != allowed):
        raise ValueError("batch must contain each of this seat's ten runs exactly once")
    candidates = []
    for path in sorted((root / "transport" / actor.lower()).glob("turn-*-request.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        expected = {game["run_id"]: game["request"]["request_id"] for game in value["games"]}
        if all(expected.get(row["run_id"]) == row["request_id"] for row, _ in parsed):
            candidates.append((path, value))
    if len(candidates) != 1:
        raise ValueError("responses do not match exactly one recorded seat request")
    request_path, batch = candidates[0]
    turn = batch["turn"]
    saved_response = root / "transport" / actor.lower() / f"turn-{turn:02d}-response.jsonl"
    if saved_response.exists() and saved_response.read_bytes() != raw.encode("utf-8"):
        raise ValueError("this turn already has a committed batch; resume its exact saved bytes")
    requests = {entry["run_id"]: {**entry["request"], **batch["common"]}
                for entry in batch["games"]}
    seeds = {row["run_id"]: row["seed"] for row in registered}
    prepared = []
    # Validate every decision before the first world transition. Corrections to
    # a rejected batch therefore retain the same ten pre-turn observations.
    for row, decision_text in parsed:
        run_path = root / "runs" / row["run_id"]
        manifest, records, game = load_verified_run(run_path)
        if manifest["actor"] != actor or manifest["seed"] != seeds[row["run_id"]]:
            raise ValueError("episode differs from its registered seat or seed")
        if game.turn > turn:
            accepted = [record["payload"] for record in records
                        if record["type"] == "response" and record["payload"]["turn"] == turn]
            if (len(accepted) != 1 or accepted[0]["raw_response"] != decision_text
                    or accepted[0]["request"] != requests[row["run_id"]]
                    or accepted[0]["provenance"].get("batch_response_sha256") != sha(raw)):
                raise ValueError("saved batch differs from a previously accepted decision")
            if not saved_response.exists():
                raise ValueError("accepted batch transport is missing")
            prepared.append((row, decision_text, None, game.turn))
            continue
        if game.turn != turn:
            raise ValueError("response turn is ahead of the current world")
        request = pending_request(run_path)
        if request != requests[row["run_id"]] or request["request_id"] != row["request_id"]:
            raise ValueError("stale or altered request for " + row["run_id"])
        validate_response(decision_text, request)
        prepared.append((row, decision_text, request, game.turn))
    save_exact(saved_response, raw)
    metadata_path = saved_response.with_suffix(".metadata.json")
    if metadata_path.exists():
        origin = json.loads(metadata_path.read_text(encoding="utf-8"))
        if origin.get("batch_response_sha256") != sha(raw):
            raise ValueError("committed batch metadata hash mismatch")
    else:
        origin = {"worker_task": worker, "batch_response_sha256": sha(raw)}
        save_exact(metadata_path, canonical(origin) + "\n")
    receipts = []
    phase["applying"] = True
    for row, decision_text, request, current_turn in prepared:
        if request is None:
            receipts.append({"run_id": row["run_id"], "accepted": True,
                             "turn": current_turn, "resumed_committed_response": True})
            continue
        provenance = {
            **METADATA, "worker_task": origin["worker_task"], "actor": actor,
            "batch_request_sha256": sha(request_path.read_bytes().decode("utf-8")),
            "batch_response_sha256": sha(raw),
            "raw_decision_sha256": sha(decision_text),
            "batch_request_path": str(request_path.relative_to(root)),
            "batch_response_path": str(saved_response.relative_to(root)),
            "request_id": row["request_id"],
        }
        receipt = submit_response(root / "runs" / row["run_id"], decision_text, provenance=provenance)
        if not receipt["accepted"]:
            raise RuntimeError("prevalidated decision was rejected; preserve the committed batch for recovery")
        receipts.append({"run_id": row["run_id"], "accepted": True,
                         "turn": receipt["turn"], "complete": receipt["complete"]})
    return {"actor": actor, "accepted": True, "batch_turn": turn, "receipts": receipts,
            "accepted_count": len(receipts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "pending", "submit"):
        item = sub.add_parser(name)
        item.add_argument("--root", type=Path, required=True)
        if name == "init":
            item.add_argument("--source-commit", required=True)
        else:
            item.add_argument("--actor", choices=AI_IDS, required=True)
        if name == "submit":
            item.add_argument("--file", type=Path, required=True)
            item.add_argument("--worker", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = init_pilot(args.root, args.source_commit)
        elif args.command == "pending":
            result = pending_batch(args.root, args.actor)
        else:
            result = submit_batch(args.root, args.actor, args.file, args.worker)
        print(canonical(result))
        if isinstance(result, dict) and result.get("accepted") is False:
            raise SystemExit(2)
    except (ValueError, OSError, KeyError) as error:
        print(canonical({"error": str(error)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
