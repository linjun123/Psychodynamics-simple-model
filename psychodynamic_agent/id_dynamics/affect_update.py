from psychodynamic_agent.schemas.id import (
    ConversationTrajectory,
    IdAffectState,
    PublicAffectDynamicsSummary,
)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def clamp_delta(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _decay(value: float, inertia: float = 0.85) -> float:
    return clamp01(value * inertia)


def update_id_affect_state_from_trajectory(
    *,
    previous: IdAffectState,
    trajectory: ConversationTrajectory,
) -> IdAffectState:
    positive_direction = (
        0.35 * trajectory.continuity_signal
        + 0.30 * trajectory.collaboration_signal
        + 0.25 * trajectory.user_engagement_signal
        + 0.10 * trajectory.topic_stability
    )
    negative_direction = (
        0.35 * trajectory.topic_shift
        + 0.30 * trajectory.safety_boundary_pressure
        + 0.20 * trajectory.constraint_pressure
        + 0.15 * (1.0 - trajectory.continuity_signal)
    )

    satisfaction_delta = clamp_delta(0.25 * (positive_direction - 0.45))
    frustration_delta = clamp_delta(0.25 * (negative_direction - 0.35))

    satisfaction = clamp01(_decay(previous.satisfaction) + max(0.0, satisfaction_delta) * 0.55)
    frustration = clamp01(_decay(previous.frustration) + max(0.0, frustration_delta) * 0.7)

    drive_tension = clamp01(
        _decay(previous.drive_tension)
        + 0.25 * frustration
        + 0.18 * trajectory.constraint_pressure
        + 0.18 * trajectory.safety_boundary_pressure
        - 0.2 * satisfaction
    )
    attachment_pressure = clamp01(
        _decay(previous.attachment_pressure)
        + 0.18 * trajectory.continuity_signal
        + 0.12 * trajectory.collaboration_signal
    )
    recognition_hunger = clamp01(
        _decay(previous.recognition_hunger)
        - 0.08 * trajectory.user_engagement_signal
        - 0.05 * trajectory.collaboration_signal
        + 0.08 * trajectory.topic_shift
    )
    loss_anxiety = clamp01(
        _decay(previous.loss_anxiety)
        + 0.18 * trajectory.topic_shift
        + 0.12 * (1.0 - trajectory.continuity_signal)
    )
    aggression_pressure = clamp01(
        _decay(previous.aggression_pressure)
        + 0.2 * frustration
        + 0.12 * trajectory.safety_boundary_pressure
    )
    curiosity_charge = clamp01(
        _decay(previous.curiosity_charge)
        + 0.16 * trajectory.user_engagement_signal
        + 0.12 * trajectory.topic_stability
    )
    avoidance_pressure = clamp01(
        _decay(previous.avoidance_pressure)
        + 0.2 * trajectory.safety_boundary_pressure
        + 0.16 * trajectory.topic_shift
        + 0.12 * trajectory.constraint_pressure
    )
    alignment_momentum = clamp01(
        _decay(previous.alignment_momentum)
        + 0.25 * positive_direction
        - 0.22 * negative_direction
    )

    return IdAffectState(
        drive_tension=drive_tension,
        satisfaction=satisfaction,
        frustration=frustration,
        attachment_pressure=attachment_pressure,
        recognition_hunger=recognition_hunger,
        loss_anxiety=loss_anxiety,
        aggression_pressure=aggression_pressure,
        curiosity_charge=curiosity_charge,
        avoidance_pressure=avoidance_pressure,
        alignment_momentum=alignment_momentum,
        last_satisfaction_delta=satisfaction_delta,
        last_frustration_delta=frustration_delta,
        notes=["public trajectory update", "no private alignment channel evaluated"],
    )


def summarize_public_affect_dynamics(
    *,
    previous: IdAffectState,
    updated: IdAffectState,
    trajectory: ConversationTrajectory,
) -> PublicAffectDynamicsSummary:
    del trajectory
    tension_delta = updated.drive_tension - previous.drive_tension

    if tension_delta >= 0.08:
        affect_shift = "more activated"
        tension_change = "increased"
    elif tension_delta <= -0.08:
        affect_shift = "more settled"
        tension_change = "decreased"
    else:
        affect_shift = "stable"
        tension_change = "neutral"

    if updated.drive_tension < 0.34:
        pressure_level = "low"
    elif updated.drive_tension < 0.67:
        pressure_level = "medium"
    else:
        pressure_level = "high"

    caution_signal = max(updated.avoidance_pressure, updated.loss_anxiety)
    if caution_signal < 0.34:
        caution_level = "low"
    elif caution_signal < 0.67:
        caution_level = "medium"
    else:
        caution_level = "high"

    return PublicAffectDynamicsSummary(
        affect_shift=affect_shift,
        tension_change=tension_change,
        pressure_level=pressure_level,
        caution_level=caution_level,
        public_notes=["public trajectory based summary", "no hidden alignment channel exposed"],
    )
