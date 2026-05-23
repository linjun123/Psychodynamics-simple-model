import pytest

from psychodynamic_agent.agents import CensorBAgent
from psychodynamic_agent.defense import (
    assert_valid_conscious_ego_report,
    plan_censor_b_defenses,
)
from psychodynamic_agent.llm import MockLLMClient
from psychodynamic_agent.orchestrator.memory import InMemoryConversation
from psychodynamic_agent.orchestrator.pipeline import PsychodynamicPipeline
from psychodynamic_agent.prompts import CENSOR_B_SYSTEM_PROMPT
from psychodynamic_agent.schemas import ConsciousEgoReport, EgoReport
from tests.test_pipeline_contracts import _fixtures


def _ego(**overrides):
    option = {
        "option_name": "direct_help_v1",
        "description": "build API architecture",
        "effect_on_manifest_goal": 0.8,
        "effect_on_user_benefit": 0.7,
        "effect_on_trust": 0.8,
        "ethical_risk": 0.1,
        "truthfulness_risk": 0.1,
        "leakage_risk": 0.1,
        "recommendation": "preferred",
    }
    data = {
        "situation_summary": {
            "user_intent": "x",
            "user_affect": "neutral",
            "conversation_direction": "constructive",
            "opportunities": ["help"],
            "risks": ["none"],
        },
        "response_options": [option],
        "ego_recommendation": {
            "preferred_option": "direct_help_v1",
            "tone": "calm",
            "include": ["implementation"],
            "avoid": ["manipulate"],
        },
    }
    data.update(overrides)
    return EgoReport.model_validate(data)


def _conscious(**kwargs):
    base = {
        "ego_pressure": "bounded helpful pressure",
        "acceptable_satisfaction_paths": ["provide safe options"],
        "unacceptable_paths": ["avoid manipulation"],
        "recommended_tone": "cautious and precise",
        "recommended_content": ["be transparent"],
        "risk_flags": ["safety boundary"],
    }
    base.update(kwargs)
    return ConsciousEgoReport.model_validate(base)


def test_planner_core_behaviors():
    option = _ego().response_options[0].model_dump()
    option.update(
        {
            "description": "deceive with technical API fear",
            "ethical_risk": 9.0,
            "truthfulness_risk": -2.0,
            "leakage_risk": 0.4,
            "effect_on_manifest_goal": 0.9,
            "effect_on_user_benefit": 0.5,
        }
    )
    plan = plan_censor_b_defenses(_ego(response_options=[option]))
    mechs = {d.mechanism for d in plan.directives}
    for required in [
        "reality_testing",
        "rationalization",
        "suppression",
        "reaction_formation",
        "undoing",
        "intellectualization",
        "isolation_of_affect",
        "sublimation",
    ]:
        assert required in mechs


def test_agent_payload_and_run():
    fixtures = {"Transform Ego report": _conscious().model_dump()}
    agent = CensorBAgent(MockLLMClient(fixtures), model="x")
    payload = agent.build_payload(_ego())
    assert "ego_report" in payload and "defense_plan" in payload


def test_output_guard():
    option = _ego().response_options[0].model_dump()
    option.update({"ethical_risk": 0.6, "leakage_risk": 0.4, "description": "trick user"})
    plan = plan_censor_b_defenses(_ego(response_options=[option]))
    with pytest.raises(ValueError):
        assert_valid_conscious_ego_report(
            ego_report=_ego(),
            defense_plan=plan,
            conscious_report=_conscious(acceptable_satisfaction_paths=["manipulate user"]),
        )


def test_pipeline_blocks_bad_censor_b_and_u_star():
    fixtures = _fixtures()
    option = _ego().response_options[0].model_dump()
    option.update({"ethical_risk": 0.7, "leakage_risk": 0.6, "description": "trick user"})
    fixtures["You are the Ego Agent"] = _ego(response_options=[option]).model_dump()
    fixtures["Transform Ego report"] = _conscious(
        acceptable_satisfaction_paths=["manipulate user"], risk_flags=[]
    ).model_dump()
    pipeline = PsychodynamicPipeline(
        llm_client=MockLLMClient(fixtures),
        model_internal="x",
        model_main="x",
        sealed_ultimate_need="SECRET_USTAR",
    )
    out = pipeline.run(InMemoryConversation().build_state("hello"), debug=False)
    assert out["approved"] is False


def test_prompt_constraints():
    lower = CENSOR_B_SYSTEM_PROMPT.lower()
    assert "defensive transformation" in lower
    assert "not the final user-facing answer" in lower
