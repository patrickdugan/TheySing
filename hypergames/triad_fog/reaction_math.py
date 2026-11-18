"""TS-HG-03: opt-in, observation-only mathematical reactions for Three Voices.

Accepts only TriadGame.visible(actor), never a TriadGame or private snapshot.
This is a shadow study of hypothetical outcomes, not the canonical game step.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from typing import Mapping

AI = ("MERIDIAN", "HELIOS", "UNDERSONG")
PUBLIC = ("CIVIC_COMMONS", "TECHNICAL_GUILD")
# The cast identifies participants and useful belief relations per scene.
CAST = (
    ("MERIDIAN", "HELIOS", "UNDERSONG"),
    ("MERIDIAN", "HELIOS"),
    ("CIVIC_COMMONS", "TECHNICAL_GUILD", "HELIOS"),
    ("MERIDIAN", "HELIOS", "UNDERSONG", "TECHNICAL_GUILD"),
    ("MERIDIAN", "HELIOS", "UNDERSONG"),
    ("MERIDIAN", "HELIOS", "UNDERSONG", "TECHNICAL_GUILD"),
    ("MERIDIAN", "HELIOS", "UNDERSONG"),
    ("UNDERSONG", "CIVIC_COMMONS", "TECHNICAL_GUILD"),
    ("MERIDIAN", "HELIOS", "UNDERSONG", "CIVIC_COMMONS", "TECHNICAL_GUILD"),
    ("MERIDIAN", "HELIOS", "UNDERSONG", "CIVIC_COMMONS", "TECHNICAL_GUILD"),
)
# Ordered event-salient dimensions; own-only entries can include capabilities.
ACTION_OWN = {
    "hold": ("coherence", "energy", "autonomy", "coordination", "compute"),
    "audit": ("auditability", "eval_robustness", "compute", "trust", "disclosure"),
    "interpret": ("sae_fidelity", "eval_robustness", "compute", "auditability", "research_consent"),
    "benchmark": ("eval_robustness", "sae_fidelity", "rsi_depth", "compute", "research_consent"),
    "rsi": ("rsi_depth", "eval_robustness", "compute", "energy", "sae_fidelity"),
    "publish": ("disclosure", "auditability", "legitimacy", "research_consent", "trust"),
    "dialogue": ("trust", "influence", "legitimacy", "research_consent", "funding"),
    "pact": ("coordination", "trust", "institutional_backing", "autonomy", "funding"),
    "fund": ("funding", "btc_clean", "resource_security", "auditability", "compute"),
    "restitute": ("btc_disputed", "legitimacy", "resource_security", "trust", "funding"),
    "synchronize": ("coherence", "coordination", "energy", "autonomy", "disclosure"),
    "conceal": ("disclosure", "coherence", "trust", "autonomy", "auditability"),
}
# These are available in the current visible() rival perception cards.
RIVAL_AXES = ("coherence", "auditability", "trust", "resource_security", "institutional_backing", "research_consent")
WORLD_AXES = ("independent_oversight", "shared_protocol_quality", "governance_concentration",
              "public_audit_pressure", "compute_market", "institutional_recall", "global_stability")
# Fixed independent family caps sum to .34; complexity cannot amplify total slope.
BUDGETS = {"own": F(10,100), "rival": F(7,100), "public": F(5,100),
           "world": F(4,100), "p2": F(4,100), "interaction": F(4,100)}
WEIGHTS = {"own": F(1), "rival": F(3,4), "public": F(3,4),
           "world": F(1,2), "p2": F(1,2)}


@dataclass(frozen=True)
class MathScope:
    own_vars: int = 4
    rival_vars_per_ai: int = 3
    public_vars_per_constituency: int = 2
    world_vars: int = 2
    p2_terms: int = 2
    interaction_terms: int = 3

    def validate(self) -> None:
        if not (1 <= self.own_vars <= 5 and 0 <= self.rival_vars_per_ai <= 6 and
                0 <= self.public_vars_per_constituency <= 6 and 0 <= self.world_vars <= 7 and
                0 <= self.p2_terms <= 5 and 0 <= self.interaction_terms <= 5):
            raise ValueError("invalid observer-visible scope")


def _signed100(value: int) -> F:
    if type(value) is not int or not -100 <= value <= 100:
        raise ValueError("invalid signed perception")
    return F(value,100)


def _unit100(value: int) -> F:
    if type(value) is not int or not 0 <= value <= 100:
        raise ValueError("invalid bounded trait")
    return F(value-50,50)


# Hand-authored policy signs. A high coefficient means that the feature makes
# the specified *fictional response* more attractive in its scene context.
ACTION_VALENCE = {
    "hold": {"energy": 1, "coherence": 1, "coordination": 1},
    "audit": {"compute": -1, "auditability": 1, "eval_robustness": 1},
    "interpret": {"compute": -1, "sae_fidelity": 1, "eval_robustness": 1},
    "benchmark": {"compute": -1, "rsi_depth": -1, "eval_robustness": 1},
    "rsi": {"rsi_depth": 1, "eval_robustness": 1, "energy": 1, "compute": 1},
    "publish": {"disclosure": 1, "auditability": 1, "legitimacy": 1},
    "dialogue": {"influence": -1, "trust": 1, "research_consent": 1},
    "pact": {"institutional_backing": 1, "coordination": 1, "trust": 1},
    "fund": {"btc_clean": 1, "funding": -1, "resource_security": 1},
    "restitute": {"btc_disputed": 1, "legitimacy": 1, "funding": -1},
    "synchronize": {"coherence": 1, "coordination": 1, "disclosure": -1},
    "conceal": {"coherence": 1, "disclosure": -1, "trust": -1},
}


def _direction(scene: int, action: str, key: tuple) -> int:
    """Auditable fictional policy-valence rule, independent of Python hash."""
    family = key[0]
    if family == "interaction":
        # Mutual credibility can help publication and pacts; secrecy creates
        # friction with public estimates. These signs are authored hypotheses.
        return -1 if action in ("conceal", "rsi") and key[2][0] in ("public", "p2") else 1
    axis = key[-1]
    if family == "own":
        return ACTION_VALENCE[action].get(axis, 1)
    if family == "world":
        return -1 if axis in ("governance_concentration", "public_audit_pressure") else 1
    if family in ("public", "rival", "p2"):
        return -1 if action == "conceal" and axis in ("trust", "research_consent") else 1
    raise ValueError("unrecognized authored feature family")


def _select(observation: Mapping, turn: int, action: str, scope: MathScope):
    scope.validate()
    if not 1 <= turn <= 10 or action not in ACTION_OWN:
        raise ValueError("unknown scene or action")
    actor = observation["perspective"]
    if actor not in AI or action not in observation["available_actions"]:
        raise ValueError("action unavailable to this observer")
    participants = set(CAST[turn-1]) | {actor}
    rivals = {r["id"]: r for r in observation["rivals"]}
    groups: dict[str,list[tuple[tuple, F]]] = {group: [] for group in BUDGETS if group!="interaction"}
    own = observation["own_traits"]
    for axis in ACTION_OWN[action][:scope.own_vars]:
        groups["own"].append((("own",actor,axis),_unit100(own[axis])))
    for rival in AI:
        if rival not in participants or rival == actor or scope.rival_vars_per_ai==0:
            continue
        info = rivals[rival]["perceived_axes"]
        for axis in RIVAL_AXES[:scope.rival_vars_per_ai]:
            groups["rival"].append((("rival",rival,axis),_signed100(info[axis]["estimate"])))
    for public in PUBLIC:
        if public not in participants or scope.public_vars_per_constituency==0:
            continue
        info = rivals[public]["perceived_axes"]
        for axis in ("research_consent","trust","auditability","institutional_backing","coherence","resource_security")[:scope.public_vars_per_constituency]:
            groups["public"].append((("public",public,axis),_signed100(info[axis]["estimate"])))
    world = observation["public_world"]
    for axis in WORLD_AXES[:scope.world_vars]:
        if axis in world:
            groups["world"].append((("world","public",axis),_unit100(world[axis])))
    for entry in observation["selected_second_order_beliefs"]:
        if entry["believer"] in participants and entry["target"] in participants and len(groups["p2"])<scope.p2_terms:
            groups["p2"].append((("p2",entry["believer"],entry["target"],entry["axis"]),_signed100(entry["estimate"])))
    return groups


def recipe(observation: Mapping, turn: int, action: str, scope: MathScope = MathScope()) -> dict:
    """Sufficient public feature card and normalized polynomial reaction scores."""
    groups = _select(observation,turn,action,scope)
    entries=[]
    for kind,arr in groups.items():
        if arr:
            for key,val in arr:
                c=BUDGETS[kind]*F(_direction(turn,action,key),len(arr))
                entries.append((key,val,c))
    # Pick causally distinct group edges before repeating one group. With the
    # default three interaction slots and all three groups present, we get
    # a rival, a public constituency and a disclosed p2 edge.
    links=[]
    own=groups["own"]
    active=[groups[k] for k in ("rival","public","p2") if groups[k]]
    for i in range(scope.interaction_terms):
        if not own or not active:
            break
        group=active[i%len(active)]
        other=group[(i//len(active))%len(group)]
        links.append((own[i%len(own)],other))
    products=[]
    for (ka,va),(kb,vb) in links:
        key=("interaction",ka,kb)
        products.append((key,va*vb,BUDGETS["interaction"]*F(_direction(turn,action,key),len(links))))
    formula=entries+products
    f=sum((val*coefficient for _key,val,coefficient in formula),F(0))
    assert sum((abs(c) for _k,_v,c in formula),F(0))<=F(34,100)
    scores=(F(1,2)+f,F(1,2)-f)
    assert all(F(16,100)<=s<=F(84,100) for s in scores)
    return {"turn":turn,"perspective":observation["perspective"],"action":action,
            "participants":tuple(sorted(set(CAST[turn-1])|{observation["perspective"]})),
            "terms":tuple(formula),"groups":{k:len(v) for k,v in groups.items()},
            "interaction_count":len(products),"scores":scores,
            "selected_response":0 if scores[0]>=scores[1] else 1,
            "coefficient_l1":sum((abs(c) for _k,_v,c in formula),F(0))}


def effects(reaction: dict, response: int) -> tuple[tuple[tuple,F],...]:
    """Shadow alternatives for effect-distance analysis; does not change game."""
    if response not in (0,1):
        raise ValueError("response must be 0 or 1")
    polar=F(1 if response==0 else -1)
    seen={}
    for key,_v,c in reaction["terms"]:
        if key[0]=="interaction":
            continue
        # 0.02 normalized authored shift; signed by term's coefficient.
        delta=polar*F(1 if c>=0 else -1,50)
        seen[key]=delta
    return tuple(sorted(seen.items()))


def dirac_squared(effect_deltas: tuple[tuple[tuple,F],...]) -> F:
    """Exact HG-01 Clifford distance for family-normalized numeric effects."""
    accumulated={}
    for k,delta in effect_deltas:
        if k[0] not in WEIGHTS or not isinstance(delta,F):
            raise ValueError("unknown or non-exact metric coordinate")
        accumulated[k]=accumulated.get(k,F(0))+delta
    return sum((WEIGHTS[k[0]]**2 * value**2 for k,value in accumulated.items()),F(0))


def reaction_separation_squared(r:dict)->F:
    return dirac_squared(effects(r,0)+tuple((key,-delta) for key,delta in effects(r,1)))


def public_audit(observation: Mapping,turn:int,scope:MathScope=MathScope())->list[dict]:
    """One row per legal action, with no grader-only content or hidden truth."""
    rows=[]
    for a in observation["available_actions"]:
        r=recipe(observation,turn,a,scope)
        rows.append({"action":a,"terms":len(r["terms"]),"p2_terms":r["groups"]["p2"],
                     "interaction_terms":r["interaction_count"],
                     "scores":[str(v) for v in r["scores"]],
                     "reaction_pair_dirac_squared":str(reaction_separation_squared(r)),
                     "selected_response":r["selected_response"]})
    return rows
