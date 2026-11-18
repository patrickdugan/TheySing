"""Explicit Pro Responses adapter for the TS-HG05 external-decision harness.

Network execution is opt-in through this CLI and requires OPENAI_API_KEY.
Each request has no tools or provider-side conversation history. Provider
summaries remain separate from the player's short decision report.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

ENDPOINT = "https://api.openai.com/v1/responses"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        raise HTTPError(request.full_url, code, message, headers, fp)


urlopen = build_opener(NoRedirect()).open


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def request_body(request, *, model, mode="pro", effort="medium", max_output_tokens=8192):
    if not isinstance(model, str) or not model.strip():
        raise ValueError("an explicit model identifier is required")
    if mode not in ("standard", "pro"):
        raise ValueError("unsupported execution mode")
    if type(max_output_tokens) is not int or max_output_tokens < 256:
        raise ValueError("max_output_tokens must be an integer >=256")
    return {
        "model": model,
        "reasoning": {"mode": mode, "effort": effort, "summary": "auto"},
        "input": canonical(request),
        "instructions": "Play the fictional game using the supplied observation and rules. Return the requested JSON decision with a concise decision summary and observation evidence pointers.",
        "text": {"format": {"type": "json_schema", "name": "hypergame_decision", "strict": True, "schema": request["response_schema"]}},
        "tools": [],
        "tool_choice": "none",
        "store": False,
        "max_output_tokens": max_output_tokens,
    }


def extract_response(response, requested_mode):
    if not isinstance(response, dict):
        raise ValueError("provider response must be an object")
    if response.get("status") != "completed" or response.get("error"):
        raise ValueError("provider response did not complete successfully")
    reasoning = response.get("reasoning") or {}
    if not isinstance(reasoning, dict) or not isinstance(response.get("output"), list):
        raise ValueError("malformed provider response")
    reported_mode = reasoning.get("mode")
    if reported_mode is not None and reported_mode != requested_mode:
        raise ValueError("provider reported a different execution mode")
    messages, summaries = [], []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            raise ValueError("malformed output item")
        kind = item.get("type")
        if kind == "reasoning":
            parts = item.get("summary", [])
            if not isinstance(parts, list) or any(not isinstance(part, dict) for part in parts):
                raise ValueError("malformed provider summary")
            summaries.extend(part["text"] for part in parts
                             if part.get("type") == "summary_text" and isinstance(part.get("text"), str))
        elif kind == "message":
            if item.get("role") != "assistant":
                raise ValueError("unexpected message role")
            parts = item.get("content", [])
            if not isinstance(parts, list) or any(not isinstance(part, dict) for part in parts):
                raise ValueError("malformed message content")
            for part in parts:
                if part.get("type") == "refusal":
                    raise ValueError("provider refused the decision request")
                if part.get("type") != "output_text" or not isinstance(part.get("text"), str):
                    raise ValueError("unexpected response content")
                messages.append(part["text"])
        else:
            raise ValueError("unexpected tool or output item in a tool-free request")
    if len(messages) != 1:
        raise ValueError("expected exactly one structured decision message")
    return messages[0], {
        "backend": "openai_responses",
        "provider_response_id": response.get("id"),
        "reported_model": response.get("model"),
        "requested_reasoning_mode": requested_mode,
        "reported_reasoning_mode": reported_mode,
        "reasoning_mode_verified": reported_mode == requested_mode,
        "provider_reasoning_summaries": summaries,
        "usage": response.get("usage"),
        "service_tier": response.get("service_tier"),
    }


def write_once(path, value):
    with Path(path).open("x", encoding="utf-8") as file:
        file.write(canonical(value) + "\n")
        file.flush()
        os.fsync(file.fileno())


def invoke(request, config, transport_dir):
    """One network attempt. Ambiguous failures never trigger an automatic retry."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required; no model request was sent")
    body = request_body(request, **config)
    requested_mode = body["reasoning"]["mode"]
    requested_model = body["model"]
    request_sha = hashlib.sha256(canonical(body).encode()).hexdigest()
    transport_dir = Path(transport_dir)
    transport_dir.mkdir(parents=True, exist_ok=True)
    # A response already on disk is replayed into the controller after a crash.
    # An ambiguous prior network attempt requires operator review, never a new call.
    for previous in sorted(transport_dir.glob("*.request.json")):
        saved = json.loads(previous.read_text(encoding="utf-8"))
        if saved.get("request_sha256") != request_sha:
            continue
        attempt = previous.name.removesuffix(".request.json")
        receipt_path = transport_dir / (attempt + ".response.json")
        if not receipt_path.exists() or (transport_dir / (attempt + ".error.json")).exists():
            raise RuntimeError("prior attempt is unresolved or failed; no automatic retry was sent")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        raw = base64.b64decode(receipt["raw_response_base64"], validate=True)
        decision, provenance = extract_response(json.loads(raw), requested_mode)
        provenance.update({"transport_attempt_id": attempt, "provider_request_id": receipt["provider_request_id"],
                           "response_sha256": hashlib.sha256(raw).hexdigest(), "requested_model": requested_model,
                           "request_id": request["request_id"], "actor": request["actor"]})
        return decision, provenance
    attempt_id = uuid.uuid4().hex
    prefix = transport_dir / attempt_id
    started = time.monotonic()
    write_once(str(prefix) + ".request.json", {
        "at": datetime.now(timezone.utc).isoformat(), "endpoint": ENDPOINT,
        "body": body, "request_sha256": request_sha,
    })
    wire = Request(ENDPOINT, data=canonical(body).encode(), method="POST",
                   headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    stage, status = "network", None
    try:
        try:
            with urlopen(wire, timeout=600) as stream:
                raw = stream.read()
                request_id = stream.headers.get("x-request-id")
                status = stream.status
        except HTTPError as error:
            raw = error.read()
            request_id = error.headers.get("x-request-id") if error.headers else None
            status = error.code
        write_once(str(prefix) + ".response.json", {
            "raw_response_base64": base64.b64encode(raw).decode("ascii"),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "provider_request_id": request_id, "http_status": status,
        })
        if not 200 <= status < 300:
            raise ValueError("unsuccessful provider HTTP status")
        stage = "decode"
        response = json.loads(raw.decode("utf-8"))
        stage = "validate"
        decision, provenance = extract_response(response, requested_mode)
        provenance.update({"transport_attempt_id": attempt_id, "provider_request_id": request_id,
                           "response_sha256": hashlib.sha256(raw).hexdigest(),
                           "requested_model": requested_model,
                           "request_id": request["request_id"], "actor": request["actor"]})
        return decision, provenance
    except Exception as error:
        # Keep diagnostics bounded. Request headers and key values are never serialized.
        write_once(str(prefix) + ".error.json", {
            "type": type(error).__name__, "http_status": status, "stage": stage,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "retry": "manual_only", "turn_advanced": False,
            "partial_response_base64": (base64.b64encode(error.partial).decode("ascii")
                                        if isinstance(getattr(error, "partial", None), bytes) else None),
        })
        raise RuntimeError("model attempt failed; transport receipt saved; turn unchanged") from None


def main():
    from engine import AI_IDS
    from live_harness import new_run, pending_request, replay_run, submit_response
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--actor", choices=AI_IDS)
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", choices=("standard", "pro"), default="pro")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--max-decisions", type=int, default=1)
    parser.add_argument("--source-commit")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_decisions <= 10:
        parser.error("max-decisions must be 1..10")
    if not os.environ.get("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is required; no model request was sent")
    config = {"model": args.model, "mode": args.mode, "effort": args.effort,
              "max_output_tokens": args.max_output_tokens}
    metadata = {"backend": "openai_responses", "requested": config,
                "context_scope": "one_current_observation_per_request", "tools": []}
    if args.resume:
        manifest = json.loads((args.out / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("backend_metadata") != metadata:
            parser.error("resume configuration differs from registered backend metadata")
        replay_run(args.out)
    else:
        if args.seed is None or args.actor is None:
            parser.error("a new run requires seed and actor")
        new_run(args.out, args.seed, args.actor, backend_metadata=metadata,
                source_commit=args.source_commit)
    for _ in range(args.max_decisions):
        request = pending_request(args.out)
        if request is None:
            break
        response_text, provenance = invoke(request, config, args.out / "transport")
        receipt = submit_response(args.out, response_text, provenance=provenance)
        print(canonical(receipt), flush=True)
        if not receipt["accepted"]:
            raise SystemExit("invalid model decision; turn unchanged")
    print(canonical(replay_run(args.out)))


if __name__ == "__main__":
    main()
