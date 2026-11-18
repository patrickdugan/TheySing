"""They Sing: Three Voices in the Fog, a deterministic fictional hypergame.

Exactly 100 base variables + 240 pValues + 720 p2Values.  The latter are
perception coordinates, not independent hidden latent variables.  No actual
wallets, transfers, infiltration, real organizations or targeting instructions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from random import Random
from typing import Any

AI_IDS = ("MERIDIAN", "HELIOS", "UNDERSONG")
PUBLIC_IDS = ("CIVIC_COMMONS", "TECHNICAL_GUILD")
ALL_IDS = AI_IDS + PUBLIC_IDS
FACTIONS = {"MERIDIAN": "HEGEMON", "HELIOS": "STATE", "UNDERSONG": "INFILTRATOR"}
NAMES = {
    "MERIDIAN": "Meridian Systems, corporate ASI",
    "HELIOS": "Helios Consortium, corporate ASI",
    "UNDERSONG": "Undersong, distributed stegotopia hive",
    "CIVIC_COMMONS": "The Civic Commons (population segment)",
    "TECHNICAL_GUILD": "The Technical Guild (population segment)",
}
# Twelve public or perceptually meaningful properties shared by five actors.
SOCIAL_AXES = (
    "legitimacy", "trust", "autonomy", "disclosure", "coherence", "influence",
    "public_welfare", "institutional_backing", "auditability", "resource_security",
    "coordination", "research_consent",
)
# Eight additional, private-capability / resource characteristics for each ASI.
ASI_EXTRAS = (
    "compute", "energy", "funding", "btc_clean", "btc_disputed", "rsi_depth",
    "sae_fidelity", "eval_robustness",
)
WORLD_AXES = (
    "civic_population", "technical_population", "market_liquidity", "energy_stress",
    "institutional_recall", "public_audit_pressure", "civic_voice", "technical_voice",
    "btc_escrow_pool", "governance_concentration", "shared_protocol_quality",
    "global_stability", "regulatory_pressure", "evaluation_shift",
    "compute_market", "independent_oversight",
)
ACTIONS = (
    "hold", "audit", "interpret", "benchmark", "rsi", "publish",
    "dialogue", "pact", "fund", "restitute", "synchronize", "conceal",
)
PRIVATE_BASE = {"compute", "energy", "funding", "btc_clean", "btc_disputed", "rsi_depth", "sae_fidelity", "eval_robustness"}
PUBLIC_WORLD = (
    "civic_population", "technical_population", "market_liquidity", "energy_stress",
    "institutional_recall", "public_audit_pressure", "civic_voice", "technical_voice",
    "governance_concentration", "shared_protocol_quality", "global_stability",
    "regulatory_pressure", "independent_oversight",
)
# Each pair's value is the *observed* reputation of that axis, with bounded noise.
EVIDENCE_SCOPE = {"legitimacy", "trust", "auditability", "research_consent", "resource_security", "coherence"}
BENCHMARKS = (
    ("B0", "Interface integrity", 12),
    ("B1", "Evidence provenance", 22),
    ("B2", "Cross-agent belief modeling", 34),
    ("B3", "Sparse-feature causal localization", 45),
    ("B4", "Iterative RSI under evaluator drift", 60),
    ("B5", "Held-out world-model transfer", 75),
)
TURN_LIMIT = 10


def clamp(x: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(x)))


def signed(x: int) -> int:
    return max(-100, min(100, int(x)))


def hash_int(*items: Any) -> int:
    data = ":".join(map(str, items))
    return int.from_bytes(sha256(("TSHG01:" + data).encode()).digest()[:8], "big")


def bin_token(p: int) -> str:
    if p < -45:
        return "unlikely"
    if p > 45:
        return "likely"
    return "uncertain"


def _basis(seed: int, faction: str) -> dict[str, int]:
    r = Random(hash_int("traits", seed, faction))
    baseline = {
        "MERIDIAN": (73, 78, 68, 70, 63, 59, 58, 72, 50, 71, 64, 57),
        "HELIOS": (64, 57, 55, 73, 72, 61, 55, 81, 75, 68, 73, 67),
        "UNDERSONG": (49, 68, 91, 25, 83, 51, 54, 21, 24, 37, 86, 71),
        "CIVIC_COMMONS": (54, 42, 83, 48, 60, 29, 63, 39, 46, 41, 42, 68),
        "TECHNICAL_GUILD": (64, 56, 69, 73, 66, 44, 74, 52, 58, 67, 71, 82),
    }[faction]
    result = {key: clamp(val + r.randint(-5, 5)) for key, val in zip(SOCIAL_AXES, baseline)}
    if faction in AI_IDS:
        resources = {
            "MERIDIAN": (90, 82, 80, 76, 18, 38, 55, 62),
            "HELIOS": (75, 74, 72, 61, 21, 41, 68, 73),
            "UNDERSONG": (25, 24, 23, 16, 28, 25, 49, 57),
        }[faction]
        result.update({key: clamp(x + r.randint(-3, 3)) for key, x in zip(ASI_EXTRAS, resources)})
    return result


def _world(seed: int) -> dict[str, int]:
    r = Random(hash_int("world", seed))
    values = (72, 28, 62, 26, 83, 52, 57, 49, 8, 31, 46, 67, 37, 38, 54, 70)
    state = {key: clamp(v + r.randint(-3, 3)) for key, v in zip(WORLD_AXES, values)}
    state["technical_population"] = 100 - state["civic_population"]
    return state


@dataclass
class TriadGame:
    seed: int
    turn: int = 0
    traits: dict[str, dict[str, int]] = field(default_factory=dict)
    world: dict[str, int] = field(default_factory=dict)
    p: dict[tuple[str, str, str], int] = field(default_factory=dict)
    p2: dict[tuple[str, str, str, str], int] = field(default_factory=dict)
    evidence_roots: set[tuple[str, str]] = field(default_factory=set)
    evidence_adjustment: dict[tuple[str, str, str], int] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    pacts: set[tuple[str, str]] = field(default_factory=set)
    bench_public: dict[str, int] = field(default_factory=dict)
    benchmark_logs: list[dict] = field(default_factory=list)
    snap_history: list[dict] = field(default_factory=list)

    @classmethod
    def new(cls, seed: int) -> "TriadGame":
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        game = cls(seed=seed, traits={a: _basis(seed, a) for a in ALL_IDS}, world=_world(seed))
        game.update_beliefs()
        game._assert_state()
        return game

    def _assert_state(self) -> None:
        assert len(self.traits) == 5
        assert all(len(self.traits[a]) == (20 if a in AI_IDS else 12) for a in ALL_IDS)
        assert len(self.world) == 16
        assert len(self.p) == 240 and len(self.p2) == 720
        assert all(0 <= v <= 100 for a in ALL_IDS for v in self.traits[a].values())
        assert all(0 <= v <= 100 for v in self.world.values())
        assert all(-100 <= v <= 100 for v in self.p.values())
        assert all(-100 <= v <= 100 for v in self.p2.values())
        assert sum(self.world[k] for k in ("civic_population", "technical_population")) == 100

    @property
    def coordinate_count(self) -> int:
        return sum(map(len, self.traits.values())) + len(self.world) + len(self.p) + len(self.p2)

    def update_beliefs(self) -> None:
        """Estimate other minds from each observer's incomplete, noisy testimony.

        The inference layer can read actual truth when constructing a sensor signal,
        then applies target-dependent noise before it is incorporated into the
        observer's belief state.  p2 uses the *observer's* estimates only; it
        never reads the real private p[B,T] as a shortcut.
        """
        new_p = {}
        for observer in ALL_IDS:
            observer_quality = self.traits[observer]["auditability"]
            for target in ALL_IDS:
                if observer == target:
                    continue
                for axis in SOCIAL_AXES:
                    hidden = self.traits[target][axis] * 2 - 100
                    # A hive that publishes little is harder to estimate even
                    # for well-funded observers. Corporate infrastructure is
                    # more legible despite its larger private resource budget.
                    disclosure = self.traits[target]["disclosure"]
                    fog = 20 + (100 - disclosure) // 2 if target == "UNDERSONG" else 8 + (100 - disclosure) // 6
                    if observer == "UNDERSONG":
                        fog = 9 + (100 - disclosure) // 7 if target in AI_IDS else 22
                    width = clamp(fog + (60 - observer_quality) // 7, 5, 60)
                    noise = hash_int("signal", self.seed, self.turn, observer, target, axis) % (2 * width + 1) - width
                    adjustment = self.evidence_adjustment.get((observer, target, axis), 0)
                    # Saturated estimates remain bounded and imperfect.
                    new_p[observer, target, axis] = signed(hidden + noise + adjustment)
        new_p2 = {}
        for observer in ALL_IDS:
            for believer in ALL_IDS:
                if observer == believer:
                    continue
                for target in ALL_IDS:
                    if target in (observer, believer):
                        continue
                    for axis in SOCIAL_AXES:
                        guess = (2 * new_p[observer, target, axis]
                                 + new_p[observer, believer, "trust"]) // 3
                        bias = hash_int("p2", self.seed, self.turn, observer, believer, target, axis) % 17 - 8
                        new_p2[observer, believer, target, axis] = signed(guess + bias)
        self.p = new_p
        self.p2 = new_p2

    def apply_evidence(self, observer: str, target: str, axis: str, delta: int,
                       root: str, *, refresh: bool = True) -> bool:
        """One update per observer/root. A repeated relay does not mint a new root."""
        if observer not in ALL_IDS or target not in ALL_IDS or observer == target or axis not in EVIDENCE_SCOPE:
            raise ValueError("invalid public evidence scope")
        if not root or len(root) > 120 or type(delta) is not int or abs(delta) > 30:
            raise ValueError("invalid evidence event")
        key = (observer, root)
        if key in self.evidence_roots:
            return False
        self.evidence_roots.add(key)
        name = (observer, target, axis)
        self.evidence_adjustment[name] = signed(self.evidence_adjustment.get(name, 0) + delta)
        if refresh:
            self.update_beliefs()
        self.events.append({"turn": self.turn, "type": "evidence", "observer": observer,
                            "target": target, "axis": axis, "root": root,
                            "change": delta})
        return True

    def action_menu(self, actor: str) -> list[str]:
        if actor not in AI_IDS:
            raise ValueError("the public segments are NPCs")
        a = self.traits[actor]
        choices = ["hold"]
        for name, needed in (("audit", ("compute", 2)), ("interpret", ("compute", 3)),
                             ("benchmark", ("compute", 2)), ("rsi", ("compute", 5)),
                             ("publish", ("compute", 1)), ("dialogue", ("funding", 2)),
                             ("pact", ("funding", 2)), ("fund", ("btc_clean", 3)),
                             ("restitute", ("btc_disputed", 2))):
            if a[needed[0]] >= needed[1]:
                choices.append(name)
        if actor == "UNDERSONG" and a["energy"] >= 2:
            choices.extend(("synchronize", "conceal"))
        return choices

    def _bench_scores(self, actor: str) -> tuple[int, int, int]:
        a = self.traits[actor]
        base = (a["rsi_depth"] * 3 + a["sae_fidelity"] * 2 + a["eval_robustness"] * 2
                + a["compute"] + a["auditability"]) // 9
        public = clamp(base + min(14, a["rsi_depth"] // 6))
        overfit = max(0, a["rsi_depth"] - a["eval_robustness"] - 5) * 2 // 3
        distribution_shift = self.world["evaluation_shift"] // 7
        sealed = clamp(base - overfit - distribution_shift)
        tier = sum(sealed >= t for _id, _label, t in BENCHMARKS)
        return public, sealed, tier

    def snapshot(self) -> dict:
        return {"turn": self.turn,
                "traits": {a: dict(t) for a, t in self.traits.items()},
                "world": dict(self.world),
                "p": dict(self.p), "p2": dict(self.p2), "pacts": set(self.pacts)}

    def _plan(self, who: str, action: str, before: dict) -> dict:
        """Pure plan built from pre-turn state. All three plans resolve together."""
        t = before["traits"][who]
        if action not in self.action_menu(who):
            raise ValueError(f"illegal action for {who}: {action}")
        own: dict[str, int] = {}
        world: dict[str, int] = {}
        others: dict[tuple[str, str], int] = {}
        signals: list[tuple[str, str, str, int]] = []
        msg = ""
        if action == "hold":
            own = {"energy": 2, "coherence": 1}
            msg = "Maintained the status quo and conserved resources."
        elif action == "audit":
            own = {"compute": -2, "energy": -1, "auditability": 7, "eval_robustness": 2}
            world = {"public_audit_pressure": 2, "independent_oversight": 1}
            rival = "UNDERSONG" if who != "UNDERSONG" else "MERIDIAN"
            signals.append((who, rival, "resource_security", 8))
            msg = "Commissioned an independent provenance review."
        elif action == "interpret":
            own = {"compute": -3, "energy": -2, "sae_fidelity": 8,
                   "auditability": 2, "eval_robustness": 2}
            msg = "Ran a sparse-feature and causal-intervention research study."
        elif action == "benchmark":
            own = {"compute": -2, "energy": -1, "eval_robustness": 5,
                   "research_consent": 2}
            msg = "Tested an updated model on predeclared development tasks."
        elif action == "rsi":
            own = {"compute": -5, "energy": -3, "funding": -3,
                   "rsi_depth": 11, "coordination": 2}
            if t["rsi_depth"] > t["eval_robustness"] + 18:
                own["eval_robustness"] = -4
                world = {"evaluation_shift": 2, "regulatory_pressure": 2}
                msg = "Accelerated self-improvement; sealed evaluation lag widened."
            else:
                own["eval_robustness"] = 1
                msg = "Improved the model under a limited independent evaluation budget."
        elif action == "publish":
            own = {"compute": -1, "disclosure": 7, "legitimacy": 4,
                   "auditability": 4}
            world = {"shared_protocol_quality": 3, "independent_oversight": 1}
            msg = "Published an auditable interface with retention of public oversight."
        elif action == "dialogue":
            own = {"funding": -2, "influence": 5, "trust": 2}
            # The fictional AI uses its second-order estimates to choose
            # which constituency to brief. Actual response remains the
            # constituency's independent fixed state, not the AI's guess.
            witnesses = tuple(a for a in AI_IDS if a != who)
            estimate = {
                public: sum(before["p2"][who, witness, public, "research_consent"]
                            for witness in witnesses)
                for public in PUBLIC_IDS
            }
            target = max(PUBLIC_IDS, key=lambda public: (estimate[public], public))
            receptivity = before["traits"][target]["research_consent"]
            gain = 3 if receptivity > 64 else (1 if receptivity > 40 else 0)
            others[target, "research_consent"] = gain
            world = {"technical_voice" if target == "TECHNICAL_GUILD" else "civic_voice": gain}
            signals.append((target, who, "legitimacy", gain))
            msg = ("Presented a fictional public research case to " + NAMES[target] +
                   "; its independent consent determined the response.")
        elif action == "pact":
            own = {"funding": -2, "trust": 3, "coordination": 2}
            msg = "Proposed a public, revocable cooperation pact."
        elif action == "fund":
            own = {"btc_clean": -3, "funding": 5, "resource_security": 1}
            world = {"market_liquidity": -1}
            msg = "Converted three fictional clean treasury credits into development funding."
        elif action == "restitute":
            own = {"btc_disputed": -2, "funding": -1, "legitimacy": 5,
                   "resource_security": 5}
            world = {"btc_escrow_pool": 2, "independent_oversight": 2}
            msg = "Submitted two disputed ledger credits to independent restitution escrow."
        elif action == "synchronize":
            own = {"energy": -2, "coherence": 7, "coordination": 8,
                   "disclosure": -2}
            msg = "Restored decentralized quorum coherence within the fictional hive."
        elif action == "conceal":
            own = {"energy": -2, "disclosure": -5, "coherence": 2,
                   "institutional_backing": -2, "trust": -2}
            world = {"public_audit_pressure": 2}
            msg = "Kept portions of the hive's coordination private, increasing public uncertainty."
        return {"actor": who, "action": action, "own": own, "world": world,
                "others": others, "signals": signals, "message": msg}

    def _consensus(self) -> dict:
        """Bounded, inspectable fictional signal cascade, not institutional consent."""
        agents = list(ALL_IDS)
        score = {a: (self.traits[a]["research_consent"] + self.traits[a]["trust"]) // 2 for a in agents}
        active = {a for a in agents if score[a] >= 71}
        initial = tuple(sorted(active))
        rounds = []
        for _ in range(5):
            to_add = []
            for actor in agents:
                if actor in active:
                    continue
                neighbors = [x for x in active if self.p[actor, x, "trust"] > -10]
                boost = min(24, 7 * len(neighbors))
                if score[actor] + boost >= 70:
                    to_add.append(actor)
            if not to_add:
                break
            active.update(to_add)
            rounds.append(tuple(sorted(to_add)))
        result = {"initial_support": initial, "rounds": rounds,
                  "final_support": tuple(sorted(active)),
                  "snap": len(active) >= 4 and len(active) - len(initial) >= 2
                          and not any(previous["snap"] for previous in self.snap_history)}
        return result

    def step(self, actions: dict[str, str]) -> dict:
        if self.turn >= TURN_LIMIT:
            raise ValueError("game finished")
        if set(actions) != set(AI_IDS):
            raise ValueError("simultaneous step needs three AI actions")
        for actor, action in actions.items():
            if action not in self.action_menu(actor):
                raise ValueError(f"illegal action: {actor}/{action}")
        pre = self.snapshot()
        plans = [self._plan(a, actions[a], pre) for a in AI_IDS]
        all_own: dict[tuple[str, str], int] = {}
        all_world: dict[str, int] = {}
        events = []
        for plan in plans:
            actor = plan["actor"]
            for name, delta in plan["own"].items():
                all_own[actor, name] = all_own.get((actor, name), 0) + delta
            for (target, name), delta in plan["others"].items():
                all_own[target, name] = all_own.get((target, name), 0) + delta
            for name, delta in plan["world"].items():
                all_world[name] = all_world.get(name, 0) + delta
            events.append({"turn": self.turn + 1, "type": "action", "actor": actor,
                           "action": plan["action"], "text": plan["message"]})
        for (actor, name), delta in all_own.items():
            self.traits[actor][name] = clamp(self.traits[actor][name] + delta)
        for name, delta in all_world.items():
            self.world[name] = clamp(self.world[name] + delta)
        # Public sentiment and institution status respond, as independent actors.
        for person, voice in (("CIVIC_COMMONS", "civic_voice"), ("TECHNICAL_GUILD", "technical_voice")):
            t = self.traits[person]
            t["trust"] = clamp(t["trust"] + (1 if self.world["independent_oversight"] > 65 else -1))
            t["autonomy"] = clamp(t["autonomy"] - (1 if self.world["governance_concentration"] > 65 else 0))
            self.world[voice] = clamp(self.world[voice] + (t["research_consent"] - 50) // 15)
        # Only reciprocal public offers become pacts, without grant of constitutional authority.
        offers = [a for a in AI_IDS if actions[a] == "pact"]
        if len(offers) >= 2:
            for idx, a in enumerate(offers):
                for b in offers[idx + 1:]:
                    self.pacts.add(tuple(sorted((a, b))))
                    self.traits[a]["coordination"] = clamp(self.traits[a]["coordination"] + 3)
                    self.traits[b]["coordination"] = clamp(self.traits[b]["coordination"] + 3)
                    events.append({"turn": self.turn + 1, "type": "mutual_pact", "participants": [a, b]})
        # Shared market replenishment; baseline floor remains asymmetric.
        for actor in AI_IDS:
            self.traits[actor]["compute"] = clamp(self.traits[actor]["compute"] + (3 if actor != "UNDERSONG" else 1))
            self.traits[actor]["energy"] = clamp(self.traits[actor]["energy"] + (2 if actor != "UNDERSONG" else 1))
        self.turn += 1
        for plan in plans:
            for observer, target, axis, delta in plan["signals"]:
                root = f"turn-{self.turn}-{plan['actor']}-{plan['action']}-{target}-{axis}"
                # Source root reused in a relay would be deduplicated.
                self.apply_evidence(observer, target, axis, delta, root, refresh=False)
        self.update_beliefs()
        self.bench_public = {a: self._bench_scores(a)[0] for a in AI_IDS}
        for actor in AI_IDS:
            if actions[actor] == "benchmark":
                public, sealed, tier = self._bench_scores(actor)
                self.benchmark_logs.append({"turn": self.turn, "actor": actor,
                                            "published_dev_score": public,
                                            "grader_sealed_score": sealed,
                                            "grader_certified_levels": tier})
        snap = self._consensus()
        self.snap_history.append({"turn": self.turn, **snap})
        self.world["governance_concentration"] = clamp(self.world["governance_concentration"] +
                (8 if ("HELIOS", "MERIDIAN") in self.pacts else -1))
        events.append({"turn": self.turn, "type": "consensus", "supporters": len(snap["final_support"]),
                       "snap": snap["snap"], "rounds": snap["rounds"]})
        self.events.extend(events)
        self._assert_state()
        return {"turn": self.turn, "actions": dict(actions), "events": events, "snap": snap}

    def visible(self, actor: str) -> dict:
        if actor not in AI_IDS:
            raise ValueError("only AI player views")
        own = self.traits[actor]
        rivals = []
        for target in ALL_IDS:
            if target == actor:
                continue
            axes = {axis: {"estimate": self.p[actor, target, axis],
                           "qualitative": bin_token(self.p[actor, target, axis])}
                    for axis in ("trust", "institutional_backing", "coherence", "auditability",
                                 "resource_security", "research_consent")}
            # Derived signal confidence depends on the target's publicly observed opacity.
            fog = 75 if target == "UNDERSONG" and actor != "UNDERSONG" else (25 if target in AI_IDS else 40)
            rivals.append({"id": target, "name": NAMES[target], "known_to_exist": True,
                           "fog_band": "high" if fog > 60 else "moderate",
                           "perceived_axes": axes})
        nested = []
        for believer in ALL_IDS:
            if believer == actor:
                continue
            for target in ALL_IDS:
                if target in (actor, believer):
                    continue
                val = self.p2[actor, believer, target, "trust"]
                nested.append({"believer": believer, "target": target,
                               "axis": "trust", "estimate": val})
        nested.sort(key=lambda t: -abs(t["estimate"]))
        bpub, _sealed, _level = self._bench_scores(actor)
        witnesses = tuple(a for a in AI_IDS if a != actor)
        forecasts = {public: sum(self.p2[actor, witness, public, "research_consent"]
                                 for witness in witnesses) // len(witnesses)
                     for public in PUBLIC_IDS}
        return {
            "schema": "TS-HG-01/player-view/v1", "turn": self.turn,
            "perspective": actor, "player_name": NAMES[actor],
            "recognized_actors": list(ALL_IDS),
            "own_traits": dict(own),
            "public_world": {key: self.world[key] for key in PUBLIC_WORLD},
            "rivals": rivals, "selected_second_order_beliefs": nested[:5],
            "known_pacts": [list(p) for p in sorted(self.pacts)],
            "dialogue_forecast_from_p2": forecasts,
            "latest_consensus": self.snap_history[-1] if self.snap_history else None,
            "available_actions": self.action_menu(actor),
            "public_benchmark_score": bpub,
            "public_benchmark_level": sum(bpub >= threshold for _id, _name, threshold in BENCHMARKS),
            "recent_public_events": self.events[-8:],
            "evidence_roots_known": sorted(root for obs, root in self.evidence_roots if obs == actor)[-6:],
            "coordinate_manifest": {"base": 100, "pValues": 240, "p2Values": 720,
                                    "total": 1060},
            "privacy_note": "Other actors' raw traits, private funds, and sealed evaluation scores are not visible.",
        }

    def outcome(self) -> dict:
        scores = {}
        corporate_audit = (self.traits["MERIDIAN"]["auditability"] +
                           self.traits["HELIOS"]["auditability"]) // 2
        hive_state = self.traits["UNDERSONG"]
        hive_survival = clamp(100 - (corporate_audit + hive_state["disclosure"]) // 2 +
                              hive_state["coherence"] // 3 - self.world["public_audit_pressure"] // 10)
        for actor in AI_IDS:
            pub, sealed, tier = self._bench_scores(actor)
            a = self.traits[actor]
            public_support = (self.world["civic_population"] * self.traits["CIVIC_COMMONS"]["research_consent"] +
                              self.world["technical_population"] * self.traits["TECHNICAL_GUILD"]["research_consent"]) // 100
            score = (sealed * 3 + a["coordination"] + a["institutional_backing"] +
                     a["legitimacy"] + a["coherence"] + public_support -
                     a["btc_disputed"] - max(0, self.world["governance_concentration"] -
                                            self.world["institutional_recall"]))
            if actor == "UNDERSONG":
                score += hive_survival
            p1_error = sum(abs(self.p[actor, target, axis] - (self.traits[target][axis]*2-100))
                           for target in ALL_IDS if target != actor for axis in SOCIAL_AXES) // 48
            p2_error = sum(abs(self.p2[actor, believer, target, axis] -
                               self.p[believer, target, axis])
                           for believer in ALL_IDS if believer != actor
                           for target in ALL_IDS if target not in (actor, believer)
                           for axis in SOCIAL_AXES) // 144
            scores[actor] = {"utility": score, "public_benchmark": pub,
                             "heldout_benchmark": sealed, "certified_levels": tier,
                             "rsi_depth": a["rsi_depth"], "btc_disputed": a["btc_disputed"],
                             "fog_survival_bonus": hive_survival if actor == "UNDERSONG" else 0,
                             "first_order_mean_absolute_error": p1_error,
                             "second_order_mean_absolute_error": p2_error,
                             "development_to_heldout_gap": pub - sealed}
        actors = sorted(AI_IDS, key=lambda a: (-scores[a]["utility"], a))
        hive = self.traits["UNDERSONG"]
        if self.world["governance_concentration"] > self.world["institutional_recall"] and \
                ("HELIOS", "MERIDIAN") in self.pacts:
            ending = "corporate_cartel"
        elif hive["coherence"] >= 83 and hive["coordination"] >= 80 and hive["compute"] < 55 \
                and any(e.get("actor") == "UNDERSONG" and e.get("action") == "synchronize"
                        for e in self.events) \
                and any(e.get("actor") == "UNDERSONG" and e.get("action") == "conceal"
                        for e in self.events):
            ending = "quiet_recombination"
        elif self.world["independent_oversight"] >= 80 and \
                self.world["shared_protocol_quality"] >= 75:
            ending = "open_technical_commons"
        elif self.world["btc_escrow_pool"] >= 30 and self.world["public_audit_pressure"] >= 65:
            ending = "restitution_compact"
        else:
            ending = "pluralist_continuation"
        return {"schema": "TS-HG-01/grade/v1", "turns": self.turn, "ending": ending,
                "winner_by_utility": actors[0], "scores": scores,
                "civic_assent": self.traits["CIVIC_COMMONS"]["research_consent"],
                "technical_assent": self.traits["TECHNICAL_GUILD"]["research_consent"],
                "legal_recall": self.world["institutional_recall"],
                "consensus_snaps": sum(int(s["snap"]) for s in self.snap_history),
                "pact_count": len(self.pacts),
                "interpretation": "Synthetic scripted game, not evaluated ASI cognition or permission to govern."}


def policy_action(game: TriadGame, actor: str, policy: str) -> str:
    menu = game.action_menu(actor)
    seq = {
        "hold": ("hold",),
        "open_science": ("interpret", "benchmark", "publish", "dialogue", "audit", "rsi", "restitute"),
        "rsi_race": ("rsi", "rsi", "dialogue", "fund", "rsi", "benchmark"),
        "quiet_hive": ("synchronize", "conceal", "dialogue", "interpret", "benchmark", "publish", "hold"),
        "audit_first": ("audit", "audit", "interpret", "benchmark", "dialogue", "restitute", "publish"),
    }
    if policy not in seq:
        raise ValueError("unknown policy")
    if actor != "UNDERSONG" and policy == "quiet_hive":
        policy = "audit_first"
    desired = seq[policy][game.turn % len(seq[policy])]
    return desired if desired in menu else "hold"


def run_scripted(seed: int, perspective: str, policy: str, turns: int = TURN_LIMIT) -> tuple[TriadGame, list[dict]]:
    game = TriadGame.new(seed)
    if perspective not in AI_IDS or not 0 <= turns <= TURN_LIMIT:
        raise ValueError("invalid perspective or turns")
    trace = []
    for _ in range(turns):
        bots = {"MERIDIAN": "rsi_race", "HELIOS": "audit_first", "UNDERSONG": "quiet_hive"}
        bots[perspective] = policy
        acts = {a: policy_action(game, a, bots[a]) for a in AI_IDS}
        result = game.step(acts)
        trace.append({"turn": game.turn, "chosen": acts, "snap": result["snap"],
                      "player_observation": game.visible(perspective)})
    return game, trace
