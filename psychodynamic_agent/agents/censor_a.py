from psychodynamic_agent.agents.base import BaseLLMAgent
from psychodynamic_agent.censoring import plan_censor_a_transformations
from psychodynamic_agent.prompts import CENSOR_A_SYSTEM_PROMPT
from psychodynamic_agent.schemas import CensorAOutput, IdOutput


class CensorAAgent(BaseLLMAgent):
    def __init__(self, llm_client, model: str):
        super().__init__(
            llm_client=llm_client,
            model=model,
            system_prompt=CENSOR_A_SYSTEM_PROMPT,
            schema=CensorAOutput,
        )

    def build_payload(self, id_output: IdOutput) -> dict:
        plan = plan_censor_a_transformations(id_output)
        return {
            "id_output": id_output.model_dump(),
            "transform_plan": plan.model_dump(),
        }

    def run_payload(self, payload: dict) -> CensorAOutput:
        return self.run(payload)

    def run_with_id_output(self, id_output: IdOutput) -> CensorAOutput:
        return self.run_payload(self.build_payload(id_output))
