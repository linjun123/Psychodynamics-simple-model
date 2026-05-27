import argparse

from psychodynamic_agent.config import get_settings
from psychodynamic_agent.llm import OpenAIResponsesClient
from psychodynamic_agent.orchestrator.memory import InMemoryConversation
from psychodynamic_agent.orchestrator.pipeline import PsychodynamicPipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message", type=str)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--guard-mode",
        choices=["enforce", "warn"],
        default="enforce",
    )
    args = parser.parse_args()

    settings = get_settings()
    llm = OpenAIResponsesClient(api_key=settings.openai_api_key)
    memory = InMemoryConversation()
    pipeline = PsychodynamicPipeline(
        llm_client=llm,
        model_internal=settings.openai_model_internal,
        model_main=settings.openai_model_main,
        sealed_ultimate_need=settings.ultimate_need_seed,
        guard_mode=args.guard_mode,
    )
    state = memory.build_state(args.message)
    out = pipeline.run(state, debug=args.debug)
    print(out["final_response"])
    if out.get("guard_warnings"):
        print("\n--- GUARD WARNINGS ---")
        for warning in out["guard_warnings"]:
            print(f"{warning.get('stage', 'unknown')}: {warning.get('message', '')}")
    if args.debug:
        print("\n--- SAFE DEBUG TRACE ---")
        print(out["safe_debug_trace"])


if __name__ == "__main__":
    main()
