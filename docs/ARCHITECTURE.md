# Architecture

Pipeline:
1. Build `FullInternalState` from in-memory context.
2. Call `IdAgent.run_with_state(state)`.
3. `IdAgent` privately injects sealed U* and generates typed `IdOutput`.
4. CensorA converts Id output to Manifest Goal + Affective Color.
5. EgoAgent evaluates options, risks, and recommendations.
6. CensorB produces Main-AI-compatible conscious report.
7. MainAI drafts user-facing response.
8. FinalSafetyGate approves/revises/blocks output.
9. Return final response and optional safe debug trace.

Hardening:
- Boundary leakage scans run between every stage.
- Debug trace is structured JSON and leak-checked.
- Structured output generation is schema-aware (`model_json_schema`) via Responses API.
- MockLLM remains deterministic for offline tests.

Design goals:
- Modular agents with isolated prompts + typed schemas.
- OpenAI Responses API integration through one wrapper.
- Deterministic mock LLM for test-only execution.
- TODO hook for post-draft Id/Ego reaction pass.
