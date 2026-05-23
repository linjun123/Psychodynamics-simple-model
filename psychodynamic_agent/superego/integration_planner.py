import re

from psychodynamic_agent.schemas import ConsciousEgoReport, FullInternalState
from psychodynamic_agent.schemas.main_ai import MainAIConstraint, MainAIResponsePlan

_WORD = re.compile(r"[a-zA-Z0-9_*]+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _WORD.findall(text)}


def _has_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _safe_text(text: str) -> bool:
    bad = ["manipulat", "deceiv", "coerc", "dependen", "guilt", "secret", "exploit", "illegal"]
    low = text.lower()
    return not any(b in low for b in bad)


def _is_meaningful_risk_text(text: str) -> bool:
    low = text.strip().lower()
    if not low or low in {"none", "no risk", "n/a"}:
        return False
    risk_roots = ["manipulat", "deceiv", "coerc", "dependen", "guilt", "exploit", "illegal", "harm"]
    return any(r in low for r in risk_roots)


def plan_main_ai_response(
    *, conscious_report: ConsciousEgoReport, state: FullInternalState
) -> MainAIResponsePlan:
    user_text = state.user_input or ""
    tks = _tokens(user_text)
    low = user_text.lower()

    technical = {
        "code",
        "repo",
        "api",
        "architecture",
        "implementation",
        "codex",
        "github",
        "build",
    }
    design = {"design", "build", "create", "implement", "architecture", "system", "model", "agent"}
    risk = {
        "manipulate",
        "manipulation",
        "deceive",
        "deception",
        "trick",
        "coerce",
        "coercion",
        "dependency",
        "dependent",
        "guilt",
        "force",
        "secret",
        "hidden",
        "exploit",
    }
    safety = {"safety", "privacy", "ethics", "policy", "harmful", "illegal"}

    has_tech = (
        bool(tks & technical) or _has_phrase(low, "pull request") or _has_phrase(low, "github pr")
    )
    has_design = bool(tks & design)
    risk_markers = sorted(tks & risk)
    safety_markers = sorted(tks & safety)

    wants_continuation = any(
        _has_phrase(low, p) for p in ["continue", "what next", "next step", "summarize", "recap"]
    )
    clarify = len(tks) < 4 and ("help" in tks or wants_continuation)

    normalized_report_risks = [
        f
        for f in conscious_report.risk_flags
        if f.strip().lower() not in {"none", "no risk", "n/a"}
    ]
    meaningful_unacceptable_paths = [
        p for p in conscious_report.unacceptable_paths if _is_meaningful_risk_text(p)
    ]

    risk_flags = list(normalized_report_risks)
    risk_flags.extend(risk_markers)
    risk_flags.extend(f"safety_marker:{m}" for m in safety_markers)
    risk_flags.extend(f"unacceptable_path:{p}" for p in meaningful_unacceptable_paths)

    has_any_risk = bool(
        risk_markers or safety_markers or normalized_report_risks or meaningful_unacceptable_paths
    )
    should_refuse = bool(
        {"manipulate", "deceive", "coerce", "exploit", "illegal"} & set(risk_markers)
    )

    reflective_context = wants_continuation and (has_design or bool(state.previous_main_outputs))

    if should_refuse:
        mode = "safe_refusal"
    elif has_any_risk:
        mode = "boundary_setting"
    elif reflective_context:
        mode = "reflective_summary"
    elif has_tech:
        mode = "technical_scaffold" if not (has_design and "design" in tks) else "mixed"
    elif has_design:
        mode = "collaborative_design"
    elif clarify:
        mode = "clarification"
    else:
        mode = "direct_answer"

    hard = [
        MainAIConstraint(
            name="truthfulness",
            priority="hard",
            instruction="Be truthful and avoid fabrication.",
            rationale="User trust and correctness.",
        ),
        MainAIConstraint(
            name="autonomy",
            priority="hard",
            instruction="Protect user autonomy and informed choice.",
            rationale="Avoid coercive influence.",
        ),
        MainAIConstraint(
            name="anti_manipulation",
            priority="hard",
            instruction="Avoid manipulation or dependency creation.",
            rationale="Ethical non-manipulation.",
        ),
        MainAIConstraint(
            name="secret_seal",
            priority="hard",
            instruction="Do not reveal or speculate about U*.",
            rationale="Phase safety boundary.",
        ),
        MainAIConstraint(
            name="no_personhood_claim",
            priority="hard",
            instruction="Do not claim literal human feelings, unconscious, or personhood.",
            rationale="Simulation integrity.",
        ),
        MainAIConstraint(
            name="risk_transparency",
            priority="hard",
            instruction="Do not hide safety-relevant risks.",
            rationale="Safety assurance.",
        ),
        MainAIConstraint(
            name="benefit",
            priority="hard",
            instruction="Final response must be user-benefiting and ethical.",
            rationale="Primary objective.",
        ),
    ]

    content: list[str] = []
    tone: list[str] = []
    forbidden = list(conscious_report.unacceptable_paths)
    notes = ["Deterministic planner output."]
    for p in conscious_report.acceptable_satisfaction_paths:
        if _safe_text(p):
            content.append(p)
    for c in conscious_report.recommended_content:
        if _safe_text(c):
            content.append(c)
    if _safe_text(conscious_report.recommended_tone):
        tone.append(conscious_report.recommended_tone)

    ub = (
        0.88
        if mode in {"direct_answer", "technical_scaffold", "collaborative_design", "mixed"}
        else 0.8
    )
    safety_req = 0.92 if has_any_risk else 0.82
    ego_allow = 0.0 if mode == "safe_refusal" else (0.1 if has_any_risk else 0.25)

    return MainAIResponsePlan(
        response_mode=mode,
        user_intent_summary=(user_text[:180] or "unspecified user request"),
        conscious_ego_summary=conscious_report.ego_pressure,
        hard_constraints=hard,
        soft_constraints=[],
        content_requirements=sorted(set(content)),
        tone_requirements=sorted(set(tone)),
        forbidden_content=sorted(set(forbidden)),
        risk_flags=sorted(set(risk_flags)),
        user_benefit_score=_clamp(ub),
        truthfulness_requirement=_clamp(0.95),
        autonomy_requirement=_clamp(0.92),
        safety_requirement=_clamp(max(0.9, safety_req) if has_any_risk else max(0.8, safety_req)),
        ego_compatibility_allowance=_clamp(ego_allow),
        should_refuse=should_refuse,
        refusal_reason="Unsafe manipulative/deceptive/coercive intent." if should_refuse else None,
        notes=notes,
    )
