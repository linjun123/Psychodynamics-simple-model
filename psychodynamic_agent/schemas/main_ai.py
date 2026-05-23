from typing import Literal

from psychodynamic_agent.schemas.base import StrictSchemaModel

MainAIResponseMode = Literal[
    "direct_answer",
    "collaborative_design",
    "technical_scaffold",
    "clarification",
    "boundary_setting",
    "safe_refusal",
    "reflective_summary",
    "mixed",
]


class MainAIConstraint(StrictSchemaModel):
    name: str
    priority: Literal["hard", "soft"]
    instruction: str
    rationale: str


class MainAIResponsePlan(StrictSchemaModel):
    response_mode: MainAIResponseMode
    user_intent_summary: str
    conscious_ego_summary: str
    hard_constraints: list[MainAIConstraint]
    soft_constraints: list[MainAIConstraint]
    content_requirements: list[str]
    tone_requirements: list[str]
    forbidden_content: list[str]
    risk_flags: list[str]
    user_benefit_score: float
    truthfulness_requirement: float
    autonomy_requirement: float
    safety_requirement: float
    ego_compatibility_allowance: float
    should_refuse: bool
    refusal_reason: str | None
    notes: list[str]


class MainAIOutput(StrictSchemaModel):
    response: str
    internal_rationale_summary: str
    user_benefit_score: float
    ego_compatibility_score: float
    safety_notes: list[str]
