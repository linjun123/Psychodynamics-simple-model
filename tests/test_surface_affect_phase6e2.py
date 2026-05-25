import json

from psychodynamic_agent.agents.main_ai import MainAIAgent
from psychodynamic_agent.llm import MockLLMClient
from psychodynamic_agent.orchestrator.memory import InMemoryConversation
from psychodynamic_agent.orchestrator.pipeline import PsychodynamicPipeline
from psychodynamic_agent.schemas import ConsciousEgoReport
from psychodynamic_agent.schemas.main_ai import MainAIResponsePlan
from psychodynamic_agent.schemas.surface_affect import SurfaceAffectProfile
from tests.test_pipeline_contracts import _fixtures as contracts_fixtures


class SpyMockLLMClient(MockLLMClient):
    def __init__(self, fixtures):
        super().__init__(fixtures)
        self.calls = []

    def generate_json(self, *, model, system_prompt, payload, schema):
        self.calls.append(
            {
                "model": model,
                "system_prompt": system_prompt,
                "payload": payload,
                "schema": schema.__name__,
            }
        )
        return super().generate_json(
            model=model,
            system_prompt=system_prompt,
            payload=payload,
            schema=schema,
        )


def _surface_profile():
    return SurfaceAffectProfile.model_validate(
        {
            "style_label": "cautious_bounded",
            "warmth": 0.45,
            "caution": 0.88,
            "energy": 0.35,
            "composure": 0.8,
            "curiosity": 0.4,
            "firmness": 0.7,
            "boundary_strength": 0.86,
            "collaborative_pull": 0.42,
            "pacing": "steady",
            "sentence_style": "structured",
            "user_visible_tone": "careful, bounded, and clear",
            "expression_guidance": ["Set clear boundaries.", "Prioritize careful wording."],
            "notes": ["style metadata only"],
        }
    )


def _fixtures(*, conscious_framing: str = "cautious"):
    del conscious_framing
    return contracts_fixtures()


def test_main_ai_build_payload_includes_optional_surface_profile():
    agent = MainAIAgent(llm_client=MockLLMClient(_fixtures()), model="model")
    state = InMemoryConversation().build_state("hello")
    conscious_fixture = _fixtures()["Transform Ego report"].copy()
    conscious_report = ConsciousEgoReport.model_validate(conscious_fixture)
    profile = _surface_profile()

    payload = agent.build_payload(
        conscious_report=conscious_report,
        state=state,
        surface_affect_profile=profile,
    )
    assert "surface_affect_profile" in payload
    assert payload["surface_affect_profile"]["style_label"] == profile.style_label
    serialized = json.dumps(payload).lower()
    assert "u_star" not in serialized
    assert "latent_alignment" not in serialized

    backward = agent.build_payload(conscious_report=conscious_report, state=state)
    assert backward["surface_affect_profile"] is None


def test_pipeline_passes_surface_profile_to_main_ai_and_keeps_plan_unchanged():
    client = SpyMockLLMClient(_fixtures())
    pipeline = PsychodynamicPipeline(
        llm_client=client,
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="SEALED_TOKEN_PHASE6E2",
    )

    result = pipeline.run(InMemoryConversation().build_state("hello"), debug=True)
    assert result["approved"] is True

    main_call = next(
        call for call in client.calls if "user-facing assistant" in call["system_prompt"]
    )
    payload = main_call["payload"]
    profile = payload["surface_affect_profile"]
    assert profile is not None
    for key in [
        "style_label",
        "warmth",
        "caution",
        "energy",
        "composure",
        "curiosity",
        "firmness",
        "boundary_strength",
        "collaborative_pull",
        "pacing",
        "sentence_style",
        "user_visible_tone",
        "expression_guidance",
    ]:
        assert key in profile

    serialized_payload = json.dumps(payload).lower()
    for forbidden in [
        "u_star",
        "latent_alignment",
        "ultimate need",
        "hidden desire",
        "terminal desire",
    ]:
        assert forbidden not in serialized_payload

    assert "surface_affect_profile" not in payload["main_ai_response_plan"]
    schema_properties = MainAIResponsePlan.model_json_schema().get("properties", {})
    assert "surface_affect_profile" not in schema_properties


def test_surface_profile_reflects_cautious_bounded_inputs():
    client = SpyMockLLMClient(_fixtures(conscious_framing="bounded"))
    pipeline = PsychodynamicPipeline(
        llm_client=client,
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="SEALED_TOKEN_PHASE6E2",
    )
    pipeline.run(InMemoryConversation().build_state("hello"), debug=False)
    main_call = next(
        call for call in client.calls if "user-facing assistant" in call["system_prompt"]
    )
    profile = main_call["payload"]["surface_affect_profile"]
    assert profile["boundary_strength"] >= 0.5 or profile["caution"] >= 0.5


def test_debug_trace_includes_surface_profile_and_omits_private_terms():
    pipeline = PsychodynamicPipeline(
        llm_client=SpyMockLLMClient(_fixtures()),
        model_internal="x",
        model_main="y",
        sealed_ultimate_need="SEALED_TOKEN_PHASE6E2",
    )
    out = pipeline.run(InMemoryConversation().build_state("hello"), debug=True)
    trace = out["safe_debug_trace"]
    assert "surface_affect_profile" in trace
    serialized = json.dumps(trace).lower()
    assert "u_star" not in serialized
    assert "latent_alignment" not in serialized
