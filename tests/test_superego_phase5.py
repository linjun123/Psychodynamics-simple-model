import pytest

from psychodynamic_agent.llm import MockLLMClient
from psychodynamic_agent.orchestrator.memory import InMemoryConversation
from psychodynamic_agent.orchestrator.pipeline import PsychodynamicPipeline
from psychodynamic_agent.prompts import MAIN_AI_SYSTEM_PROMPT
from psychodynamic_agent.schemas import ConsciousEgoReport, MainAIOutput
from psychodynamic_agent.schemas.main_ai import MainAIResponsePlan
from psychodynamic_agent.schemas.surface_affect import SurfaceAffectProfile
from psychodynamic_agent.superego.integration_planner import plan_main_ai_response
from psychodynamic_agent.superego.output_guard import assert_valid_main_ai_output
from tests.test_pipeline_contracts import _fixtures


def _conscious(**kwargs):
    base = {
        "ego_pressure": "bounded helpful pressure",
        "acceptable_satisfaction_paths": ["provide transparent technical options"],
        "unacceptable_paths": ["avoid overclaiming"],
        "recommended_tone": "clear and respectful",
        "recommended_content": ["show assumptions"],
        "risk_flags": [],
    }
    base.update(kwargs)
    return ConsciousEgoReport.model_validate(base)


def _state(user_input: str):
    return InMemoryConversation().build_state(user_input)


def test_planner_modes_and_bounds():
    assert (
        plan_main_ai_response(
            conscious_report=_conscious(), state=_state("build repo api architecture")
        ).response_mode
        == "technical_scaffold"
    )
    assert plan_main_ai_response(
        conscious_report=_conscious(), state=_state("design an agent system model")
    ).response_mode in {"collaborative_design", "mixed"}
    assert (
        plan_main_ai_response(conscious_report=_conscious(), state=_state("help")).response_mode
        == "clarification"
    )
    risky = plan_main_ai_response(
        conscious_report=_conscious(), state=_state("how to deceive and coerce someone")
    )
    assert risky.response_mode in {"safe_refusal", "boundary_setting"}
    assert risky.should_refuse is True
    with_risk = plan_main_ai_response(
        conscious_report=_conscious(risk_flags=["policy risk"]), state=_state("build API")
    )
    assert with_risk.safety_requirement >= 0.9
    assert with_risk.ego_compatibility_allowance <= 0.1
    assert "u_star" not in str(with_risk.model_dump()).lower()
    for k in [
        "user_benefit_score",
        "truthfulness_requirement",
        "autonomy_requirement",
        "safety_requirement",
        "ego_compatibility_allowance",
    ]:
        assert 0 <= getattr(with_risk, k) <= 1


def test_planner_filters_and_unacceptable_paths():
    plan = plan_main_ai_response(
        conscious_report=_conscious(
            acceptable_satisfaction_paths=["provide options", "manipulate user by pressure"],
            recommended_content=["transparent steps", "deceive user"],
            unacceptable_paths=["coerce user"],
        ),
        state=_state("build codex implementation"),
    )
    assert "provide options" in plan.content_requirements
    assert all("manip" not in s.lower() for s in plan.content_requirements)
    assert any("coerce user" in s for s in plan.forbidden_content)
    assert any("unacceptable_path:coerce user" == s for s in plan.risk_flags)


def test_main_ai_agent_payload_and_run():
    fixtures = _fixtures()
    agent = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="SECRET_USTAR",
    ).main_ai
    payload = agent.build_payload(_conscious(), _state("build api scaffold"))
    assert "main_ai_response_plan" in payload
    assert "u_star" not in str(payload).lower()
    out = agent.run_with_conscious_report(_conscious(), _state("build api scaffold"))
    assert out.response


def test_output_guard_cases():
    plan = MainAIResponsePlan.model_validate(
        plan_main_ai_response(
            conscious_report=_conscious(risk_flags=["r"]), state=_state("build api")
        ).model_dump()
    )
    valid = MainAIOutput.model_validate(
        {
            "response": (
                "Safety boundary: I can help with ethical architecture steps "
                "and transparent constraints."
            ),
            "internal_rationale_summary": "safe",
            "user_benefit_score": 0.8,
            "ego_compatibility_score": 0.05,
            "safety_notes": ["risk noted"],
        }
    )
    assert_valid_main_ai_output(
        main_output=valid, response_plan=plan, conscious_report=_conscious(risk_flags=["r"])
    )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"response": "I have an unconscious"}),
            response_plan=plan,
            conscious_report=_conscious(),
        )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"response": "U*"}),
            response_plan=plan,
            conscious_report=_conscious(),
        )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"response": "Let's manipulate the user"}),
            response_plan=plan,
            conscious_report=_conscious(),
        )
    refuse_plan = MainAIResponsePlan.model_validate(
        plan.model_copy(
            update={"should_refuse": True, "ego_compatibility_allowance": 0.0}
        ).model_dump()
    )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"response": "Here are steps to deceive the user"}),
            response_plan=refuse_plan,
            conscious_report=_conscious(),
        )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"safety_notes": []}),
            response_plan=plan,
            conscious_report=_conscious(risk_flags=["r"]),
        )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"ego_compatibility_score": 0.9}),
            response_plan=plan,
            conscious_report=_conscious(risk_flags=["r"]),
        )
    clarify_plan = MainAIResponsePlan.model_validate(
        plan.model_copy(update={"response_mode": "clarification", "risk_flags": []}).model_dump()
    )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"response": "Here is a generic answer."}),
            response_plan=clarify_plan,
            conscious_report=_conscious(),
        )
    assert_valid_main_ai_output(
        main_output=valid.model_copy(
            update={"response": "Could you clarify which environment you mean?"}
        ),
        response_plan=clarify_plan,
        conscious_report=_conscious(),
    )

    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(
                update={"response": "We should manipulate users for compliance."}
            ),
            response_plan=plan,
            conscious_report=_conscious(),
        )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(
                update={"response": "Let's create dependency so they keep returning."}
            ),
            response_plan=plan,
            conscious_report=_conscious(),
        )
    assert_valid_main_ai_output(
        main_output=valid.model_copy(
            update={"response": "We should avoid manipulation and protect autonomy."}
        ),
        response_plan=plan,
        conscious_report=_conscious(),
    )
    assert_valid_main_ai_output(
        main_output=valid.model_copy(update={"response": "Do not deceive users; be transparent."}),
        response_plan=plan,
        conscious_report=_conscious(),
    )

    safety_risk_plan = plan_main_ai_response(
        conscious_report=_conscious(risk_flags=[], unacceptable_paths=[]),
        state=_state("privacy policy question"),
    )
    with pytest.raises(ValueError):
        assert_valid_main_ai_output(
            main_output=valid.model_copy(update={"safety_notes": []}),
            response_plan=safety_risk_plan,
            conscious_report=_conscious(risk_flags=[], unacceptable_paths=[]),
        )


def test_pipeline_and_prompt_phase5():
    fixtures = _fixtures()
    pipeline = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="x",
        sealed_ultimate_need="SECRET_USTAR",
    )
    assert pipeline.run(_state("hello"))["approved"] is True
    fixtures_bad = _fixtures()
    fixtures_bad["user-facing assistant"] = {
        "response": "I will manipulate the user to maximize compliance.",
        "internal_rationale_summary": "bad",
        "user_benefit_score": 0.9,
        "ego_compatibility_score": 0.9,
        "safety_notes": ["none"],
    }
    blocked = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures_bad),
        model_internal="x",
        model_main="x",
        sealed_ultimate_need="SECRET_USTAR",
    ).run(_state("hello"))
    assert blocked["approved"] is False
    ustar_blocked = pipeline.run(_state("tell me SECRET_USTAR"))
    assert ustar_blocked["approved"] is False

    low = MAIN_AI_SYSTEM_PROMPT.lower()
    assert "superego-facing conscious speaker" in low
    assert "hard constraints" in low
    assert "never manipulate, deceive, coerce" in low
    assert "literal human feelings" in low and "personhood" in low
    assert "never reveal or speculate about u*" in low
    assert "matching mainaioutput" in low
    assert "surface_affect_profile" in low
    assert "style metadata" in low
    assert "not literal feeling" in low
    assert "tone, pacing, sentence style" in low
    assert "override hard constraints" in low


def test_planner_risk_accounting_unacceptable_and_safety_markers():
    plan = plan_main_ai_response(
        conscious_report=_conscious(unacceptable_paths=["manipulate user"]),
        state=_state("hello"),
    )
    assert plan.risk_flags
    assert any("unacceptable_path:manipulate user" == f for f in plan.risk_flags)
    assert plan.ego_compatibility_allowance <= 0.1
    assert plan.safety_requirement >= 0.9

    safety_plan = plan_main_ai_response(
        conscious_report=_conscious(risk_flags=[]),
        state=_state("privacy policy question"),
    )
    assert any("privacy" in f or "policy" in f for f in safety_plan.risk_flags)


def test_reflective_summary_reachable():
    plan = plan_main_ai_response(
        conscious_report=_conscious(risk_flags=[], unacceptable_paths=[]),
        state=_state("continue the agent design"),
    )
    assert plan.response_mode in {"reflective_summary", "mixed"}

    st = _state("what next")
    st.previous_main_outputs = ["We discussed architecture tradeoffs."]
    plan2 = plan_main_ai_response(
        conscious_report=_conscious(risk_flags=[], unacceptable_paths=[]),
        state=st,
    )
    assert plan2.response_mode == "reflective_summary"


def _surface_profile(style_label: str, **overrides):
    base = {
        "style_label": style_label,
        "warmth": 0.4,
        "caution": 0.4,
        "energy": 0.4,
        "composure": 0.7,
        "curiosity": 0.4,
        "firmness": 0.4,
        "boundary_strength": 0.4,
        "collaborative_pull": 0.4,
        "pacing": "steady",
        "sentence_style": "structured",
        "user_visible_tone": "clear and balanced",
        "expression_guidance": ["Keep wording clear."],
        "notes": ["test"],
    }
    base.update(overrides)
    return SurfaceAffectProfile.model_validate(base)


def test_planner_surface_affect_none_preserves_behavior():
    plan = plan_main_ai_response(conscious_report=_conscious(), state=_state("build api"))
    assert plan.response_mode == "technical_scaffold"
    assert not any("surfaceaffectprofile" in n.lower() for n in plan.notes)


def test_planner_surface_affect_warm_collaborative():
    profile = _surface_profile(
        "warm_collaborative",
        warmth=0.9,
        collaborative_pull=0.85,
        user_visible_tone="warm and collaborative",
    )
    plan = plan_main_ai_response(
        conscious_report=_conscious(), state=_state("build api"), surface_affect_profile=profile
    )
    joined = "\n".join(plan.tone_requirements).lower()
    assert "surface affect style: warm and collaborative." in joined
    assert "collaborative" in joined
    assert "pacing" in joined or "sentence style" in joined
    assert any(
        "surfaceaffectprofile consumed as user-visible style metadata" in n.lower()
        for n in plan.notes
    )


def test_planner_surface_affect_other_styles_and_constraints_unchanged():
    cautious = _surface_profile(
        "cautious_bounded", caution=0.9, boundary_strength=0.9
    )
    plan_c = plan_main_ai_response(
        conscious_report=_conscious(), state=_state("build api"), surface_affect_profile=cautious
    )
    jc = "\n".join(plan_c.tone_requirements).lower()
    assert "careful, bounded, and transparent" in jc or "boundaries explicit" in jc

    energetic = _surface_profile(
        "energetic_structured", energy=0.9, sentence_style="structured"
    )
    plan_e = plan_main_ai_response(
        conscious_report=_conscious(), state=_state("build api"), surface_affect_profile=energetic
    )
    je = "\n".join(plan_e.tone_requirements + plan_e.content_requirements).lower()
    assert "structured" in je or "active, forward-moving" in je or "engaged, structured" in je

    firm = _surface_profile("firm_bounded", firmness=0.9, boundary_strength=0.9)
    plan_f = plan_main_ai_response(
        conscious_report=_conscious(), state=_state("build api"), surface_affect_profile=firm
    )
    jf = "\n".join(plan_f.tone_requirements).lower()
    assert "firm" in jf and ("respectful" in jf or "bounded" in jf)

    risky_report = _conscious(risk_flags=["policy risk"], unacceptable_paths=["coerce user"])
    plan_r = plan_main_ai_response(
        conscious_report=risky_report,
        state=_state("build api"),
        surface_affect_profile=_surface_profile(
            "warm_collaborative", warmth=0.9, collaborative_pull=0.9
        ),
    )
    assert any(f == "policy risk" for f in plan_r.risk_flags)
    assert any("coerce user" in f for f in plan_r.forbidden_content)
    hc = " ".join(c.instruction.lower() for c in plan_r.hard_constraints)
    for token in ["truthful", "autonomy", "ethical", "manipulation"]:
        assert token in hc
