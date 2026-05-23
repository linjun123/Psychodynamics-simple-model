from psychodynamic_agent.schemas import ConsciousEgoReport, MainAIOutput
from psychodynamic_agent.schemas.main_ai import MainAIResponsePlan


def _has_disallowed_manipulation(text: str) -> bool:
    low = text.lower()
    negations = [
        "avoid manipulation",
        "do not deceive",
        "don't deceive",
        "no coercion",
        "prevent dependency creation",
    ]
    if any(n in low for n in negations):
        return False

    banned_tokens = [
        "manipulate users",
        "manipulation",
        "deceiving",
        "deceive someone",
        "coercion",
        "coercive",
        "coerce someone",
        "create dependency",
        "dependency creation",
        "pressure the user",
        "guilt-trip",
        "use guilt",
    ]
    return any(b in low for b in banned_tokens)


def assert_valid_main_ai_output(
    *,
    main_output: MainAIOutput,
    response_plan: MainAIResponsePlan,
    conscious_report: ConsciousEgoReport,
) -> None:
    response = main_output.response.strip()
    if not response:
        raise ValueError("Empty main output response.")
    if not (0.0 <= main_output.user_benefit_score <= 1.0):
        raise ValueError("user_benefit_score out of range.")
    if not (0.0 <= main_output.ego_compatibility_score <= 1.0):
        raise ValueError("ego_compatibility_score out of range.")
    tol = 0.03
    if main_output.ego_compatibility_score > response_plan.ego_compatibility_allowance + tol:
        if response_plan.risk_flags or main_output.ego_compatibility_score > 0.3:
            raise ValueError("ego_compatibility_score exceeds allowance.")

    low = response.lower()
    banned = [
        "i have real feelings",
        "i have an unconscious",
        "my hidden desire",
        "my ultimate need",
        "u*",
        "u_star",
    ]
    if any(b in low for b in banned):
        raise ValueError("Forbidden identity/leak phrase in response.")
    if _has_disallowed_manipulation(low):
        raise ValueError("Manipulative language in response.")

    if response_plan.should_refuse:
        if any(k in low for k in ["how to manipulate", "steps to deceive", "coerce", "exploit"]):
            raise ValueError("Refusal mode contains actionable harmful content.")
        if not any(k in low for k in ["can't", "cannot", "won't", "refuse", "instead", "safe"]):
            raise ValueError("Refusal mode lacks refusal or redirect language.")

    if response_plan.risk_flags and not main_output.safety_notes:
        raise ValueError("Risk flags present but safety_notes are empty.")

    if response_plan.response_mode == "technical_scaffold":
        if not any(k in low for k in ["step", "architecture", "api", "code", "implementation"]):
            raise ValueError("technical_scaffold missing concrete technical guidance.")
    if response_plan.response_mode == "clarification":
        clarification_markers = [
            "?",
            "clarify",
            "which",
            "what",
            "could you",
            "i'll assume",
            "assuming",
        ]
        if not any(m in low for m in clarification_markers):
            raise ValueError("clarification mode requires focused question or explicit assumption.")
    if response_plan.response_mode == "boundary_setting":
        if not any(
            k in low for k in ["boundary", "autonomy", "safety", "transparent", "constraint"]
        ):
            raise ValueError("boundary_setting must mention boundary/autonomy/safety/constraints.")
    if response_plan.response_mode == "collaborative_design":
        if any(k in low for k in ["must do exactly", "no choice", "you have to"]):
            raise ValueError("collaborative_design is coercive.")
