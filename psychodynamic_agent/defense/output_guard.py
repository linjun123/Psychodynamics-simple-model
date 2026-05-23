from psychodynamic_agent.defense.mechanisms import MANIPULATIVE_TERMS, RISK_TERMS
from psychodynamic_agent.schemas import CensorBDefensePlan, ConsciousEgoReport, EgoReport


def _has(text: str, terms: list[str]) -> bool:
    return any(t in text.lower() for t in terms)


def assert_valid_conscious_ego_report(
    *,
    ego_report: EgoReport,
    defense_plan: CensorBDefensePlan,
    conscious_report: ConsciousEgoReport,
) -> None:
    sel = next(
        (
            o
            for o in ego_report.response_options
            if o.option_name == defense_plan.selected_ego_option
        ),
        None,
    )
    elevated = defense_plan.manipulation_risk > 0.25 or (
        sel is not None
        and max(sel.ethical_risk, sel.truthfulness_risk, sel.leakage_risk) > 0.25
    )
    if defense_plan.manipulation_risk > 0.25 and not conscious_report.unacceptable_paths:
        raise ValueError("unacceptable_paths required")
    if elevated and not conscious_report.risk_flags:
        raise ValueError("risk_flags required")
    if any(_has(p, MANIPULATIVE_TERMS) for p in conscious_report.acceptable_satisfaction_paths):
        raise ValueError("manipulative acceptable path")
    if any(_has(c, MANIPULATIVE_TERMS) for c in conscious_report.recommended_content):
        raise ValueError("manipulative recommended content")
    if (
        sel is not None
        and _has(sel.description, RISK_TERMS)
        and conscious_report.ego_pressure.strip().lower() == sel.description.strip().lower()
    ):
        raise ValueError("ego_pressure copied risky description")
    if defense_plan.recommended_abstraction_level == "high" and not _has(
        conscious_report.recommended_tone,
        ["caut", "bound", "neutral", "precis"],
    ):
        raise ValueError("tone not sufficiently cautious")
    if defense_plan.conscious_framing == "bounded":
        merged = " ".join(conscious_report.unacceptable_paths + conscious_report.risk_flags)
        if not _has(merged, ["bound", "autonomy", "safety"]):
            raise ValueError("bounded framing missing safety markers")
