from psychodynamic_agent.agents.base import BaseLLMAgent
from psychodynamic_agent.defense import plan_censor_b_defenses
from psychodynamic_agent.prompts import CENSOR_B_SYSTEM_PROMPT
from psychodynamic_agent.schemas import ConsciousEgoReport, EgoReport


class CensorBAgent(BaseLLMAgent):
    def __init__(self, llm_client, model: str):
        super().__init__(
            llm_client=llm_client,
            model=model,
            system_prompt=CENSOR_B_SYSTEM_PROMPT,
            schema=ConsciousEgoReport,
        )

    def build_payload(self, ego_report: EgoReport) -> dict:
        plan = plan_censor_b_defenses(ego_report)
        return {"ego_report": ego_report.model_dump(), "defense_plan": plan.model_dump()}

    def run_payload(self, payload: dict) -> ConsciousEgoReport:
        return self.run(payload)

    def run_with_ego_report(self, ego_report: EgoReport) -> ConsciousEgoReport:
        return self.run_payload(self.build_payload(ego_report))
