# Phase History (Reference)

This file preserves the phase-by-phase development notes that were previously kept in the main README.

## Phase 3 — Ego Planner
- Added deterministic `EgoRealityPlan` scoring prior to Ego LLM realization.
- Plan is internal-only and excludes sealed `U*`.
- Ego prioritizes user benefit, truthfulness, autonomy, and safety over manifest-goal pressure.

## Phase 4 — Censor B Defense Planner
- Added deterministic defense planning + LLM realization to convert `EgoReport` into `ConsciousEgoReport`.
- Preserves risk-relevant safety signals.
- `U*` remains sealed in `IdAgent`.

## Phase 5 — MainAI / Superego Integration
- Added deterministic `SuperegoIntegrationPlanner` that feeds `MainAIResponsePlan`.
- Response planning is internal and safety-constrained.
- Conscious Ego signal influences tone/content only through transparent, autonomy-preserving paths.
- User welfare, truthfulness, autonomy, and safety override ego compatibility.
- System remains a simulation (no literal personhood/unconscious claims).

## Phase 6A-1
- Added public `ConversationTrajectory` appraisal schema + deterministic lexical appraisal helper.
- Added `IdAffectState` schema groundwork for continuous Id affect updates.
- Not yet wired into runtime pipeline in this sub-phase.

## Phase 6A-2
- Pipeline maintains continuous `IdAffectState` across turns.
- Each turn computes public `ConversationTrajectory` and deterministically updates affect control-state fields.
- Added public `PublicAffectDynamicsSummary` in debug trace.

## Phase 6A-3
- Added Id-private `run_turn` API for future private trajectory-alignment evaluation against sealed `U*`.
- Added `LatentDriveAlignment` and private/public turn output schemas.
- `run_turn` strips latent alignment and returns only public-safe outputs.

## Phase 6A-4 (runtime wiring)
- Pipeline runtime calls `IdAgent.run_turn(...)` and passes prior `IdAffectState` + public `ConversationTrajectory`.
- `LatentDriveAlignment` and sealed `U*` remain private in Id payloads.
- Pipeline commits affect state only from validated public outputs.

## Phase 6B-1 — Affect Propagation Foundation
- Added `AffectPropagationTrace` and `EgoAffectSummary` for downstream-safe affect control signals.
- Added deterministic mapper from `IdOutput.raw_affect` to downstream style/control metrics.
- Added public safety/consistency guards for affect outputs.

## Phase 6B-2 — Censor A affect payload wiring
- Censor A receives `affect_trace` and `ego_affect_summary` with `id_output` and transform plan.
- `CensorAOutput.affective_color` validated against deterministic transformed style.
- Affect remains control-signal abstraction (not literal feeling claims).

## Phase 6B-3
- Ego receives `EgoAffectSummary` and uses affect signals in strategy scoring.
- Ego still does not access `U*`, latent alignment, or terminal desire.
- Affect cannot override user benefit/truthfulness/autonomy/safety constraints.

## Phase 6D — Schema Field Descriptions
- Added concise `pydantic.Field(description=...)` metadata across `psychodynamic_agent/schemas`.
- Improves structured output schema guidance without changing runtime pipeline behavior.
