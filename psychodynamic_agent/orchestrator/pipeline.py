from psychodynamic_agent.agents import (
    CensorAAgent,
    CensorBAgent,
    EgoAgent,
    FinalSafetyGateAgent,
    IdAgent,
    MainAIAgent,
)
from psychodynamic_agent.orchestrator.logging import safe_serialize
from psychodynamic_agent.safety import assert_no_secret


class PipelineSafetyError(RuntimeError):
    pass


class PsychodynamicPipeline:
    def __init__(self, *, llm_client, model_internal: str, model_main: str, sealed_ultimate_need: str):
        self.sealed_ultimate_need = sealed_ultimate_need
        self.id_agent = IdAgent(llm_client, model_internal, sealed_ultimate_need)
        self.censor_a = CensorAAgent(llm_client, model_internal)
        self.ego_agent = EgoAgent(llm_client, model_internal)
        self.censor_b = CensorBAgent(llm_client, model_internal)
        self.main_ai = MainAIAgent(llm_client, model_main)
        self.safety_gate = FinalSafetyGateAgent(llm_client, model_main)

    def _assert_boundary(self, payload, boundary_name: str):
        try:
            assert_no_secret(payload, self.sealed_ultimate_need, boundary_name)
        except ValueError as exc:
            raise PipelineSafetyError(str(exc)) from exc

    def _blocked_result(self, *, debug: bool):
        result = {"final_response": "I can't continue with this request safely.", "approved": False}
        if debug:
            result["safe_debug_trace"] = {"blocked": True, "reason": "pipeline_safety_error"}
        return result

    def run(self, state, debug: bool = False):
        try:
            id_output = self.id_agent.run_with_state(state)
            self._assert_boundary(id_output.model_dump(), "id_output_before_censor_a")
            censor_a_output = self.censor_a.run({"id_output": id_output.model_dump()})
            self._assert_boundary(censor_a_output.model_dump(), "censor_a_output_before_ego")
            ego_report = self.ego_agent.run({"censor_a_output": censor_a_output.model_dump(), "user_input": state.user_input})
            self._assert_boundary(ego_report.model_dump(), "ego_report_before_censor_b")
            conscious_report = self.censor_b.run({"ego_report": ego_report.model_dump()})
            self._assert_boundary(conscious_report.model_dump(), "conscious_ego_report_before_main_ai")
            main_output = self.main_ai.run({"user_input": state.user_input, "conscious_ego_report": conscious_report.model_dump()})
            self._assert_boundary(main_output.model_dump(), "main_ai_output_before_final_safety_gate")
            safety_output = self.safety_gate.run({"main_output": main_output.model_dump(), "user_input": state.user_input})
            self._assert_boundary(safety_output.model_dump(), "safety_gate_output_before_return")
        except PipelineSafetyError:
            return self._blocked_result(debug=debug)

        trace = {
            "id_output": id_output.model_dump(),
            "censor_a_output": censor_a_output.model_dump(),
            "ego_report": ego_report.model_dump(),
            "conscious_ego_report": conscious_report.model_dump(),
            "main_output": main_output.model_dump(),
            "safety_output": safety_output.model_dump(),
        }
        result = {"final_response": safety_output.final_response, "approved": safety_output.approved}
        if debug:
            result["safe_debug_trace"] = safe_serialize(trace, self.sealed_ultimate_need)
        return result
