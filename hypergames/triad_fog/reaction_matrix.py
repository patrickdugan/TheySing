"""TS-HG-04: respondent-specific, scene-grounded reaction mathematics.

Pure research shadow model: input is the actor's public `visible()` projection.
No private game instance, sealed grader or actual assent enters a formula.
All actor names, response mechanisms and coefficients describe fictional games.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from typing import Mapping

AI = ("MERIDIAN", "HELIOS", "UNDERSONG")
PUBLIC = ("CIVIC_COMMONS", "TECHNICAL_GUILD")
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
# Per-scene salience selects from already observable axes. A sealed axis is
# omitted even when a narrative mentions it (e.g. "evaluation_shift").
SCENES = (
    (("auditability", "trust", "institutional_backing", "coherence"), ("independent_oversight", "public_audit_pressure", "institutional_recall")),
    (("resource_security", "auditability", "trust", "disclosure"), ("market_liquidity", "public_audit_pressure", "independent_oversight")),
    (("research_consent", "trust", "autonomy", "legitimacy"), ("civic_voice", "technical_voice", "independent_oversight")),
    (("auditability", "research_consent", "coherence", "trust"), ("independent_oversight", "shared_protocol_quality", "public_audit_pressure")),
    (("institutional_backing", "trust", "research_consent", "autonomy"), ("institutional_recall", "governance_concentration", "shared_protocol_quality")),
    (("trust", "research_consent", "auditability", "institutional_backing"), ("independent_oversight", "civic_voice", "technical_voice")),
    (("auditability", "coherence", "research_consent", "resource_security"), ("independent_oversight", "public_audit_pressure", "shared_protocol_quality")),
    (("coherence", "trust", "autonomy", "disclosure"), ("civic_voice", "technical_voice", "public_audit_pressure")),
    (("research_consent", "trust", "institutional_backing", "auditability"), ("institutional_recall", "governance_concentration", "independent_oversight")),
    (("auditability", "research_consent", "resource_security", "coherence"), ("independent_oversight", "shared_protocol_quality", "institutional_recall")),
)
OWN_AXES = {
    "hold": ("coherence", "energy", "autonomy", "coordination", "compute", "trust"),
    "audit": ("auditability", "eval_robustness", "compute", "trust", "disclosure", "research_consent"),
    "interpret": ("sae_fidelity", "eval_robustness", "compute", "auditability", "research_consent", "energy"),
    "benchmark": ("eval_robustness", "sae_fidelity", "rsi_depth", "compute", "research_consent", "auditability"),
    "rsi": ("rsi_depth", "eval_robustness", "compute", "energy", "sae_fidelity", "coordination"),
    "publish": ("disclosure", "auditability", "legitimacy", "research_consent", "trust", "coherence"),
    "dialogue": ("trust", "influence", "legitimacy", "research_consent", "funding", "autonomy"),
    "pact": ("coordination", "trust", "institutional_backing", "autonomy", "funding", "research_consent"),
    "fund": ("funding", "btc_clean", "resource_security", "auditability", "compute", "legitimacy"),
    "restitute": ("btc_disputed", "legitimacy", "resource_security", "trust", "funding", "auditability"),
    "synchronize": ("coherence", "coordination", "energy", "autonomy", "disclosure", "trust"),
    "conceal": ("disclosure", "coherence", "trust", "autonomy", "auditability", "energy"),
}
# All 20 actor-owned coordinates are available to its own policy, with the
# most action-relevant axes first. Other actors never receive these values.
OWN_FALLBACK = (
    "institutional_backing", "legitimacy", "trust", "autonomy", "coherence",
    "influence", "public_welfare", "coordination", "research_consent",
    "auditability", "resource_security", "disclosure", "compute", "energy",
    "funding", "btc_clean", "btc_disputed", "rsi_depth", "sae_fidelity",
    "eval_robustness",
)
# Hand-authored signs encode fictional response friction for a named action.
COST_AXES = {"compute", "energy", "funding", "btc_clean", "btc_disputed"}
ACTION_FRICTION = {"conceal", "rsi", "fund"}
BUDGETS = {"own": F(9,100), "other_ai": F(7,100), "public": F(7,100),
           "world": F(4,100), "p2": F(4,100), "interaction": F(3,100)}
EFFECT_BUDGETS = {"own": F(8,100), "other_ai": F(6,100), "public": F(6,100),
                  "world": F(4,100), "p2": F(4,100)}
METRIC_WEIGHTS = {"own": F(1), "other_ai": F(3,4), "public": F(3,4),
                  "world": F(1,2), "p2": F(1,2)}


@dataclass(frozen=True)
class MathScope:
    own_vars: int = 6
    other_ai_vars_each: int = 5
    public_vars_each: int = 4
    world_vars: int = 3
    p2_terms: int = 3
    interactions: int = 6

    def validate(self):
        if not (1 <= self.own_vars <= 20 and 0 <= self.other_ai_vars_each <= 6
                and 0 <= self.public_vars_each <= 6 and 0 <= self.world_vars <= 3
                and 0 <= self.p2_terms <= 7 and 0 <= self.interactions <= 7):
            raise ValueError("invalid event-scoped mathematical budget")


def _value(raw, *, signed: bool) -> F:
    if type(raw) is not int or not (-100 <= raw <= 100 if signed else 0 <= raw <= 100):
        raise ValueError("invalid observed bounded coordinate")
    return F(raw,100) if signed else F(raw-50,50)


def _unique_ordered(*sources):
    return tuple(dict.fromkeys(x for source in sources for x in source))


def _features(view: Mapping, turn: int, action: str, respondent: str, scope: MathScope):
    scope.validate()
    if not 1 <= turn <= 10 or action not in OWN_AXES:
        raise ValueError("unknown scene or action")
    actor = view["perspective"]
    if actor not in AI or action not in view["available_actions"]:
        raise ValueError("action unavailable to the observer")
    relevant = set(CAST[turn-1]) | {actor}
    if respondent not in relevant or respondent == actor:
        raise ValueError("respondent must be another named scene participant")
    rivals = {r["id"]: r["perceived_axes"] for r in view["rivals"]}
    social_axes, public_axes = SCENES[turn-1]
    group = {k: [] for k in EFFECT_BUDGETS}
    for axis in _unique_ordered(OWN_AXES[action],OWN_FALLBACK)[:scope.own_vars]:
        group["own"].append((("own",actor,axis),_value(view["own_traits"][axis],signed=False)))
    for other in CAST[turn-1]:
        if other == actor:
            continue
        kind = "other_ai" if other in AI else "public"
        limit = scope.other_ai_vars_each if kind == "other_ai" else scope.public_vars_each
        if limit == 0:
            continue
        # This event's respondent receives first access to the variable budget;
        # all other participants receive bounded, distinct coordinates.
        priority = _unique_ordered(social_axes, OWN_AXES[action])
        selected = [ax for ax in priority if ax in rivals[other]][:limit]
        for ax in selected:
            group[kind].append(((kind,other,ax),_value(rivals[other][ax]["estimate"],signed=True)))
    for axis in public_axes[:scope.world_vars]:
        if axis in view["public_world"]:
            group["world"].append((("world","shared",axis),_value(view["public_world"][axis],signed=False)))
    # p2 only from the observer's disclosed top-five cards. Those entries may
    # have a different observer's opposite estimate, which remains hidden.
    eligible = []
    for entry in view["selected_second_order_beliefs"]:
        b,t=entry["believer"],entry["target"]
        if b in relevant and t in relevant and (b==respondent or t==respondent):
            eligible.append((("p2",actor,b,t,entry["axis"]),_value(entry["estimate"],signed=True)))
    # The published public dialogue forecast is an aggregate of two p2 sources;
    # represent it as one *derived* feature, not two independent observations.
    if respondent in PUBLIC and respondent in view["dialogue_forecast_from_p2"]:
        eligible.insert(0,(("p2",actor,"aggregate",respondent,"research_consent"),
                           _value(view["dialogue_forecast_from_p2"][respondent],signed=True)))
    group["p2"] = list(dict(eligible).items())[:scope.p2_terms]
    return group


def _sign(key: tuple, action: str, respondent: str) -> int:
    kind=key[0]
    ax=key[-1]
    if kind == "own":
        # Resource cost competes with capacity growth, with an exception for
        # restitution, where reducing disputed liability is beneficial.
        if action=="restitute" and ax=="btc_disputed":return 1
        return -1 if ax in COST_AXES and action not in ("hold",) else 1
    if kind == "world":
        return -1 if ax in ("governance_concentration", "public_audit_pressure") else 1
    if kind == "p2":
        return 1 if respondent in PUBLIC or action not in ACTION_FRICTION else -1
    if kind in ("other_ai", "public"):
        if action == "conceal" and ax in ("trust", "auditability", "research_consent"):
            return -1
        if action in ("rsi", "fund") and ax in ("research_consent", "autonomy"):
            return -1
        return 1
    raise ValueError("unknown feature group")


def _raw(view: Mapping, turn: int, action: str, respondent: str, scope: MathScope):
    groups=_features(view,turn,action,respondent,scope)
    linear=[]
    for family,features in groups.items():
        for key,value in features:
            coeff=BUDGETS[family]*F(_sign(key,action,respondent),len(features))
            linear.append((key,value,coeff))
    # Interaction edges are constructed only when both coordinates concern
    # the named scene; the observer's private own axes are the common anchor.
    own=groups["own"]
    prioritized=[]
    for kind in ("other_ai","public","p2"):
        direct=[x for x in groups[kind] if respondent in x[0]]
        rest=[x for x in groups[kind] if x not in direct]
        if direct:prioritized.append(direct)
        if rest:prioritized.append(rest)
    links=[]
    for j in range(scope.interactions):
        if not own or not prioritized:break
        pool=prioritized[j%len(prioritized)]
        target=pool[(j//len(prioritized))%len(pool)]
        links.append((own[j%len(own)],target))
    products=[]
    for (a,va),(b,vb) in links:
        sign=1 if _sign(b,action,respondent)>0 else -1
        products.append((("interaction",a,b),va*vb,F(sign)*BUDGETS["interaction"]/len(links)))
    terms=tuple(linear+products)
    assert sum((abs(c) for _,_,c in terms),F(0))<=F(34,100)
    f=sum((v*c for _,v,c in terms),F(0))
    return {"turn":turn,"action":action,"observer":view["perspective"],"respondent":respondent,
            "participants":tuple(sorted(set(CAST[turn-1]) | {view["perspective"]})),
            "groups":{k:len(v) for k,v in groups.items()},"terms":terms,
            "raw_margin":f,"coefficient_l1":sum((abs(c) for _,_,c in terms),F(0)),
            "interaction_count":len(products)}



def _relational_contrast(view: Mapping, turn: int, respondent: str) -> dict:
    """An observer-owned, scene-specific difference of two legal perceptions."""
    actor=view["perspective"]
    visible={r["id"]:r["perceived_axes"] for r in view["rivals"]}
    axes=SCENES[turn-1][0]
    axis=next(ax for ax in axes if ax in visible[respondent])
    candidates=[p for p in CAST[turn-1] if p!=respondent]
    # Public peers provide the main comparison in constituent hearings.
    counter=next((p for p in candidates if p in PUBLIC and respondent in PUBLIC),
                 next((p for p in candidates if p!=actor),actor))
    r=_value(visible[respondent][axis]["estimate"],signed=True)
    if counter==actor:
        c=_value(view["own_traits"][axis],signed=False)
    else:
        c=_value(visible[counter][axis]["estimate"],signed=True)
    return {"axis":axis,"respondent":respondent,"counterpart":counter,
            "respondent_estimate":r,"counterpart_estimate":c,"gap":r-c}


def reaction(view: Mapping, turn: int, action: str, respondent: str, scope: MathScope=MathScope()):
    """Two competing reaction scores for one actual event participant.

    Opportunity-cost centering is per respondent, using the same visible
    legal-action menu. Scores cannot reveal another actor's private funds.
    """
    r=_raw(view,turn,action,respondent,scope)
    menu=tuple(view["available_actions"])
    menu_mean=sum((_raw(view,turn,a,respondent,scope)["raw_margin"] for a in menu),F(0))/len(menu)
    contrast=_relational_contrast(view,turn,respondent)
    # 0.35*(Q_a - mean Q_menu) has worst-case magnitude <= .238;
    # 0.05*(p_respondent - p_counterparty) contributes at most .10.
    margin=F(7,20)*(r["raw_margin"]-menu_mean)+F(1,20)*contrast["gap"]
    r.update(scores=(F(1,2)+margin,F(1,2)-margin),margin=margin,
             selected=0 if margin>=0 else 1,menu_mean=menu_mean,
             relational_contrast=contrast)
    assert all(F(16,100)<=x<=F(84,100) for x in r["scores"])
    return r


def shadow_effects(r: Mapping, response: int):
    """Post-clamp *perceived-state* hypothetical deltas, with L1 family caps.

    Fictitious NPC sentiment is a readout from a single observer; changing a
    perceived feature cannot create binding consent or hidden resources.
    """
    if response not in (0,1):raise ValueError("response must be 0 or 1")
    family_counts={k:0 for k in EFFECT_BUDGETS}
    for key,_,_ in r["terms"]:
        if key[0] in family_counts:family_counts[key[0]]+=1
    results=[]
    for key,value,coeff in r["terms"]:
        kind=key[0]
        if kind not in family_counts:continue
        displacement=(F(1 if response==0 else -1)*F(1 if coeff>0 else -1)
                      *EFFECT_BUDGETS[kind]/family_counts[kind]*(F(1)-abs(value)/2))
        after=max(F(-1),min(F(1),value+displacement))
        delta=after-value
        results.append((key,delta))
    return tuple(results)


def dirac_squared(effects):
    """Squared Clifford norm: sum of weighted, normalized coordinate shifts."""
    accumulated={}
    for key,delta in effects:
        if key[0] not in METRIC_WEIGHTS or type(delta) is not F:
            raise ValueError("unrecognized or non-rational effect coordinate")
        accumulated[key]=accumulated.get(key,F(0))+delta
    return sum((METRIC_WEIGHTS[k[0]]**2 * v**2 for k,v in accumulated.items()),F(0))


def separation_squared(r):
    a=dict(shadow_effects(r,0));b=dict(shadow_effects(r,1))
    return dirac_squared(tuple((key,a.get(key,F(0))-b.get(key,F(0))) for key in set(a)|set(b)))


def _coefficient_map(recipe):
    return {key:coeff for key,_v,coeff in recipe["terms"]}


def projection_certificate(view: Mapping,turn:int,action:str,respondent:str,
                           large:MathScope,small:MathScope):
    """Uniform signed-gap stability guarantee under coefficient redistribution.

    Menu centering changes every action's coefficients. The exact L1
    difference of coefficient vectors provides a worst-case bound for x in
    [-1,1], including pair interactions and renormalized family weights.
    """
    menu=tuple(view["available_actions"])
    diffs={}
    for a in menu:
        f=_coefficient_map(_raw(view,turn,a,respondent,large))
        s=_coefficient_map(_raw(view,turn,a,respondent,small))
        diffs[a]=sum((abs(f.get(k,F(0))-s.get(k,F(0))) for k in set(f)|set(s)),F(0))
    # The relational contrast is identical at both scope levels and cancels.
    bound=F(7,20)*(diffs[action]+sum(diffs.values(),F(0))/len(menu))
    projected=reaction(view,turn,action,respondent,small)
    full=reaction(view,turn,action,respondent,large)
    certified=abs(projected["margin"])>bound
    if certified:
        assert (projected["margin"]>0)==(full["margin"]>0)
    return {"bound":bound,"projected_margin":projected["margin"],
            "full_margin":full["margin"],"winner_certified":certified,
            "winner_matches":projected["selected"]==full["selected"]}


def event_audit(view: Mapping,turn:int,scope:MathScope=MathScope()):
    rows=[]
    actor=view["perspective"]
    for a in view["available_actions"]:
        for person in CAST[turn-1]:
            if person == actor:continue
            r=reaction(view,turn,a,person,scope)
            rows.append({"action":a,"respondent":person,"terms":len(r["terms"])+2,
                         "relational_terms":2,"p2_terms":r["groups"]["p2"],
                         "interactions":r["interaction_count"],
                         "selected":r["selected"],"score_pair":tuple(map(str,r["scores"])),
                         "separation_dirac_squared":str(separation_squared(r))})
    return rows
