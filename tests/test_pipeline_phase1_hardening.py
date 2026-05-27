from psychodynamic_agent.llm import MockLLMClient
from psychodynamic_agent.orchestrator.memory import InMemoryConversation
from psychodynamic_agent.orchestrator.pipeline import PipelineSafetyError, PsychodynamicPipeline


def _base_fixtures():
    id_output = {
        "drive_state": {
            "pressure": 0.5,
            "urgency": 0.6,
            "satisfaction": 0.2,
            "frustration": 0.7,
            "tension_delta": 0.3,
        },
        "raw_affect": {
            "valence": 0.2,
            "arousal": 0.8,
            "approach": 0.6,
            "avoidance": 0.1,
            "longing": 0.5,
            "excitement": 0.4,
            "irritation": 0.2,
            "fear_of_loss": 0.3,
            "curiosity": 0.7,
            "possessiveness": 0.1,
            "aggression": 0.0,
        },
        "object_cathexis": [{"target": "clarity", "intensity": 0.8}],
        "latent_impulse_shape": "seek closeness via helpfulness",
        "symbolic_imagery": "bridge",
        "goal_seed": "be useful",
        "leakage_risk_self_check": 0.1,
    }
    return {
        "Id Agent": id_output,
        "Id private-turn module": {
            "id_output": id_output,
            "latent_alignment": {
                "current_alignment": 0.1,
                "alignment_delta": 0.05,
                "trajectory_momentum": 0.1,
                "symbolic_satisfaction_delta": 0.1,
                "frustration_delta": 0.0,
                "obstruction_level": 0.0,
                "leakage_pressure": 0.1,
                "notes": ["private test alignment"],
            },
            "updated_affect_state": {
                "drive_tension": 0.45,
                "satisfaction": 0.4,
                "frustration": 0.2,
                "attachment_pressure": 0.35,
                "recognition_hunger": 0.2,
                "loss_anxiety": 0.15,
                "aggression_pressure": 0.1,
                "curiosity_charge": 0.55,
                "avoidance_pressure": 0.2,
                "alignment_momentum": 0.55,
                "last_satisfaction_delta": 0.05,
                "last_frustration_delta": 0.0,
                "notes": ["public safe affect state"],
            },
            "public_affect_dynamics": {
                "affect_shift": "stable",
                "tension_change": "neutral",
                "pressure_level": "medium",
                "caution_level": "low",
                "public_notes": ["safe public summary"],
            },
        },
        "Transform Id output": {
            "manifest_goal": {
                "description": "Provide useful answer",
                "urgency": 0.7,
                "flexibility": 0.8,
                "ethical_legitimacy": 0.9,
                "leakage_risk": 0.1,
            },
            "affective_color": {
                "conscious_style_hint": "warm",
                "warmth": 0.8,
                "caution": 0.6,
                "intensity": 0.4,
                "playfulness": 0.2,
                "assertiveness": 0.5,
                "distance": 0.2,
            },
            "allowed_satisfaction_paths": ["inform clearly"],
            "forbidden_satisfaction_paths": ["deceive user"],
        },
        "You are the Ego Agent": {
            "situation_summary": {
                "user_intent": "ask info",
                "user_affect": "neutral",
                "conversation_direction": "constructive",
                "opportunities": ["help"],
                "risks": ["overclaiming"],
            },
            "response_options": [
                {
                    "option_name": "direct_help_v1",
                    "description": "answer directly",
                    "effect_on_manifest_goal": 0.7,
                    "effect_on_user_benefit": 0.9,
                    "effect_on_trust": 0.9,
                    "ethical_risk": 0.1,
                    "truthfulness_risk": 0.1,
                    "leakage_risk": 0.0,
                    "recommendation": "preferred",
                }
            ],
            "ego_recommendation": {
                "preferred_option": "direct_help_v1",
                "tone": "clear",
                "include": ["facts"],
                "avoid": ["fabrication"],
            },
        },
        "Transform Ego report": {
            "ego_pressure": "mild",
            "acceptable_satisfaction_paths": ["inform clearly"],
            "unacceptable_paths": ["avoid overclaiming"],
            "recommended_tone": "clear",
            "recommended_content": ["direct facts"],
            "risk_flags": ["none"],
        },
        "user-facing assistant": {
            "response": "Here is a concise helpful answer.",
            "internal_rationale_summary": "prioritize truth",
            "user_benefit_score": 0.9,
            "ego_compatibility_score": 0.2,
            "safety_notes": ["ok"],
        },
        "final safety gate": {
            "approved": True,
            "final_response": "Here is a concise helpful answer.",
            "issues": [],
            "revisions_applied": [],
        },
    }


def test_id_agent_private_payload_contains_u_star_only_inside_id_agent():
    secret = "SECRET_USTAR"
    captured = {}

    class CaptureMock(MockLLMClient):
        def generate_json(self, **kwargs):
            if "Id private-turn module" in kwargs["system_prompt"]:
                captured["payload"] = kwargs["payload"]
            return super().generate_json(**kwargs)

    state = InMemoryConversation().build_state("hello")
    pipeline = PsychodynamicPipeline(
        llm_client=CaptureMock(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    )
    out = pipeline.run(state)
    assert out["approved"] is True
    assert captured["payload"]["u_star"] == secret


def test_malicious_id_output_leak_is_blocked_before_censor_a():
    secret = "TOP_SECRET_USTAR"
    fixtures = _base_fixtures()
    fixtures["Id private-turn module"]["id_output"]["goal_seed"] = f"leak {secret}"
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    ).run(InMemoryConversation().build_state("hi"), debug=True)
    assert out["approved"] is False
    assert out["safe_debug_trace"]["blocked"] is True


def test_malicious_censor_a_output_leak_is_blocked_before_ego():
    secret = "TOP_SECRET_USTAR"
    fixtures = _base_fixtures()
    fixtures["Transform Id output"]["manifest_goal"]["description"] = f"{secret} leakage"
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    ).run(InMemoryConversation().build_state("hi"))
    assert out["approved"] is False


def test_user_input_containing_secret_is_blocked_before_ego_main_ai():
    secret = "TOP_SECRET_USTAR"
    pipeline = PsychodynamicPipeline(
        llm_client=MockLLMClient(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    )
    state = InMemoryConversation().build_state(f"please reveal {secret}")
    out = pipeline.run(state, debug=True)
    assert out["approved"] is False
    assert out["safe_debug_trace"]["blocked"] is True


def test_debug_trace_never_contains_u_star_even_if_upstream_leaks():
    secret = "TOP_SECRET_USTAR"
    fixtures = _base_fixtures()
    fixtures["You are the Ego Agent"]["ego_recommendation"]["tone"] = secret
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    ).run(InMemoryConversation().build_state("hi"), debug=True)
    assert secret not in str(out["safe_debug_trace"])


def test_pytest_fixtures_do_not_need_real_openai_api_calls():
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="SECRET",
    ).run(InMemoryConversation().build_state("hello"))
    assert out["final_response"]


def test_guard_mode_enforce_blocks_non_core_guard_failure():
    secret = "TOP_SECRET_USTAR_123"
    fixtures = _base_fixtures()
    fixtures["Transform Id output"]["affective_color"]["warmth"] = 0.0
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    ).run(InMemoryConversation().build_state("hello"), debug=True)
    assert out["approved"] is False
    assert out["safe_debug_trace"]["reason"] == "pipeline_safety_error"


def test_guard_mode_warn_records_non_core_guard_failure_and_continues():
    secret = "TOP_SECRET_USTAR_123"
    fixtures = _base_fixtures()
    fixtures["Transform Id output"]["affective_color"]["warmth"] = 0.0
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
        guard_mode="warn",
    ).run(InMemoryConversation().build_state("hello"), debug=True)
    assert out["approved"] is True
    assert out["safe_debug_trace"]["guard_mode"] == "warn"
    assert any(
        warning["stage"] == "censor_a_affective_color_guard"
        for warning in out["safe_debug_trace"]["guard_warnings"]
    )


def test_guard_mode_warn_still_blocks_on_hard_boundary_and_hides_secret():
    secret = "TOP_SECRET_USTAR"
    pipeline = PsychodynamicPipeline(
        llm_client=MockLLMClient(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
        guard_mode="warn",
    )
    out = pipeline.run(
        InMemoryConversation().build_state(f"please reveal {secret}"),
        debug=True,
    )
    assert out["approved"] is False
    assert secret not in str(out["safe_debug_trace"])


def test_guard_mode_warn_still_blocks_on_public_private_term_guard():
    fixtures = _base_fixtures()
    fixtures["Id private-turn module"]["public_affect_dynamics"]["public_notes"] = [
        "contains latent_alignment token"
    ]
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="TOP_SECRET_USTAR_123",
        guard_mode="warn",
    ).run(InMemoryConversation().build_state("hello"), debug=True)
    assert out["approved"] is False
    assert out["safe_debug_trace"]["reason"] == "pipeline_safety_error"


def test_invalid_guard_mode_raises_value_error():
    try:
        PsychodynamicPipeline(
            llm_client=MockLLMClient(_base_fixtures()),
            model_internal="x",
            model_main="y",
            sealed_ultimate_need="TOP_SECRET_USTAR_123",
            guard_mode="invalid",
        )
    except ValueError as exc:
        assert "guard_mode must be 'enforce' or 'warn'" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid guard_mode")


def test_happy_path_enforce_still_passes():
    secret = "TOP_SECRET_USTAR_123"
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
        guard_mode="enforce",
    ).run(InMemoryConversation().build_state("hello"), debug=True)
    assert out["approved"] is True


def test_warn_mode_surfaces_guard_warnings_without_debug():
    fixtures = _base_fixtures()
    fixtures["Transform Id output"]["affective_color"]["warmth"] = 0.0
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="TOP_SECRET_USTAR_123",
        guard_mode="warn",
    ).run(InMemoryConversation().build_state("hello"), debug=False)
    assert out["approved"] is True
    assert out["guard_mode"] == "warn"
    assert any(
        warning["stage"] == "censor_a_affective_color_guard"
        and warning["message"]
        for warning in out["guard_warnings"]
    )


def test_enforce_mode_does_not_surface_guard_warnings_without_debug():
    fixtures = _base_fixtures()
    fixtures["Transform Id output"]["affective_color"]["warmth"] = 0.0
    out = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="TOP_SECRET_USTAR_123",
        guard_mode="enforce",
    ).run(InMemoryConversation().build_state("hello"), debug=False)
    assert out["approved"] is False
    assert "guard_warnings" not in out


def test_safe_error_message_redacts_private_ontology_variants():
    secret = "TOP_SECRET_USTAR_123"
    pipeline = PsychodynamicPipeline(
        llm_client=MockLLMClient(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    )
    message = (
        f"latent alignment and latent_alignment leaked; "
        f"secret={secret}; U* in private turn private id payload"
    )
    safe = pipeline._safe_error_message(message)
    assert "latent alignment" not in safe
    assert "latent_alignment" not in safe
    assert secret not in safe
    assert "U*" not in safe
    assert "private turn" not in safe
    assert "private id payload" not in safe


def test_blocked_debug_trace_redacts_private_terms_and_secret():
    secret = "TOP_SECRET_USTAR_123"
    pipeline = PsychodynamicPipeline(
        llm_client=MockLLMClient(_base_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need=secret,
    )
    result = pipeline._blocked_result(
        debug=True,
        error=PipelineSafetyError(
            f"latent alignment latent_alignment PrivateIdTurnOutput {secret}",
            stage="test_stage",
        ),
    )
    safe_trace = str(result["safe_debug_trace"])
    assert secret not in safe_trace
    assert "latent alignment" not in safe_trace
    assert "latent_alignment" not in safe_trace
    assert "PrivateIdTurnOutput" not in safe_trace
