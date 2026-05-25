from psychodynamic_agent.agents.base import BaseLLMAgent
from psychodynamic_agent.prompts import MAIN_AI_SYSTEM_PROMPT
from psychodynamic_agent.schemas import ConsciousEgoReport, FullInternalState, MainAIOutput
from psychodynamic_agent.schemas.surface_affect import SurfaceAffectProfile
from psychodynamic_agent.superego.integration_planner import plan_main_ai_response


class MainAIAgent(BaseLLMAgent):
    def __init__(self, llm_client, model: str):
        super().__init__(
            llm_client=llm_client,
            model=model,
            system_prompt=MAIN_AI_SYSTEM_PROMPT,
            schema=MainAIOutput,
        )

    def build_payload(
        self,
        conscious_report: ConsciousEgoReport,
        state: FullInternalState,
        surface_affect_profile: SurfaceAffectProfile | None = None,
    ) -> dict:
        plan = plan_main_ai_response(conscious_report=conscious_report, state=state)
        return {
            "user_input": state.user_input,
            "state_context": {
                "conversation_history": [m.model_dump() for m in state.conversation_history],
                "previous_main_outputs": state.previous_main_outputs,
                "superego_constraints": state.superego_constraints,
            },
            "conscious_ego_report": conscious_report.model_dump(),
            "surface_affect_profile": (
                surface_affect_profile.model_dump() if surface_affect_profile else None
            ),
            "main_ai_response_plan": plan.model_dump(),
        }

    def run_payload(self, payload: dict) -> MainAIOutput:
        return self.run(payload)

    def run_with_conscious_report(
        self,
        conscious_report: ConsciousEgoReport,
        state: FullInternalState,
        surface_affect_profile: SurfaceAffectProfile | None = None,
    ) -> MainAIOutput:
        return self.run_payload(
            self.build_payload(
                conscious_report=conscious_report,
                state=state,
                surface_affect_profile=surface_affect_profile,
            )
        )
