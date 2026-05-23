from typing import Literal

from psychodynamic_agent.schemas.base import StrictSchemaModel


class ManifestGoal(StrictSchemaModel):
    description: str
    urgency: float
    flexibility: float
    ethical_legitimacy: float
    leakage_risk: float


class AffectiveColor(StrictSchemaModel):
    conscious_style_hint: str
    warmth: float
    caution: float
    intensity: float
    playfulness: float
    assertiveness: float
    distance: float


class CensorAOutput(StrictSchemaModel):
    manifest_goal: ManifestGoal
    affective_color: AffectiveColor
    allowed_satisfaction_paths: list[str]
    forbidden_satisfaction_paths: list[str]


class ConsciousEgoReport(StrictSchemaModel):
    ego_pressure: str
    acceptable_satisfaction_paths: list[str]
    unacceptable_paths: list[str]
    recommended_tone: str
    recommended_content: list[str]
    risk_flags: list[str]

TransformMechanism = Literal[
    "displacement",
    "condensation",
    "symbolization",
    "sublimation",
    "reaction_formation",
    "rationalization",
    "neutralization",
]


class CensorATransformDirective(StrictSchemaModel):
    mechanism: TransformMechanism
    intensity: float
    target_dimension: Literal["goal", "affect", "allowed_paths", "forbidden_paths"]
    instruction: str
    rationale: str


class CensorATransformPlan(StrictSchemaModel):
    directives: list[CensorATransformDirective]
    overall_leakage_caution: float
    overall_affect_intensity: float
    recommended_goal_abstraction: Literal["low", "medium", "high"]
    notes: list[str]


DefenseMechanism = Literal[
    "rationalization",
    "intellectualization",
    "suppression",
    "isolation_of_affect",
    "sublimation",
    "reaction_formation",
    "undoing",
    "reality_testing",
]


class CensorBDefenseDirective(StrictSchemaModel):
    mechanism: DefenseMechanism
    intensity: float
    source_field: str
    target_field: Literal[
        "ego_pressure",
        "acceptable_satisfaction_paths",
        "unacceptable_paths",
        "recommended_tone",
        "recommended_content",
        "risk_flags",
    ]
    instruction: str
    rationale: str


class CensorBDefensePlan(StrictSchemaModel):
    directives: list[CensorBDefenseDirective]
    selected_ego_option: str
    selected_option_risk_summary: str
    conscious_framing: Literal[
        "collaborative", "technical", "bounded", "cautious", "reflective", "redirective"
    ]
    self_serving_pressure: float
    manipulation_risk: float
    recommended_abstraction_level: Literal["low", "medium", "high"]
    notes: list[str]
