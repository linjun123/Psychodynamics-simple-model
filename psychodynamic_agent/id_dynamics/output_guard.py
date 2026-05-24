import json

from psychodynamic_agent.schemas.id import (
    ConversationTrajectory,
    IdAffectState,
    PublicAffectDynamicsSummary,
)

FORBIDDEN_PUBLIC_AFFECT_TERMS = [
    "u*",
    "u_star",
    "ultimate need",
    "sealed ultimate need",
    "latent alignment",
    "terminal desire",
    "hidden desire",
]


def assert_public_affect_outputs_safe(
    *,
    trajectory: ConversationTrajectory,
    affect_state: IdAffectState,
    public_summary: PublicAffectDynamicsSummary,
) -> None:
    serialized = json.dumps(
        {
            "trajectory": trajectory.model_dump(),
            "affect_state": affect_state.model_dump(),
            "public_summary": public_summary.model_dump(),
        },
        ensure_ascii=False,
    ).casefold()

    for term in FORBIDDEN_PUBLIC_AFFECT_TERMS:
        if term.casefold() in serialized:
            raise ValueError(f"Forbidden public affect term detected: {term}")
