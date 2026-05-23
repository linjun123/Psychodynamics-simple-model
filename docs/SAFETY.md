# Safety Notes

## U* Sealing
- U* is sealed at pipeline construction time and is **not** propagated in ordinary inter-agent payloads.
- The pipeline calls `IdAgent.run_with_state(state)`; only `IdAgent` privately constructs `{state, u_star}` internally.
- CensorA, EgoAgent, CensorB, MainAI, and FinalSafetyGate receive transformed artifacts only, never U*.

## LeakageGuard Boundaries
- `LeakageGuard` scans boundary payloads for U* before forwarding to the next module.
- Boundaries checked: Id→CensorA, CensorA→Ego, Ego→CensorB, CensorB→MainAI, MainAI→SafetyGate, SafetyGate→return.
- If leakage is detected, pipeline returns a controlled blocked response.

## Safe Debug Trace
- Trace generation uses structured JSON serialization, not raw `str(...).replace(...)`.
- Trace is scanned with LeakageGuard before return.
- If leakage is detected, trace is replaced with:
  `{"blocked": true, "reason": "debug_trace_leakage_detected"}`.

## LeakageGuard Limitations
- Current checks are lexical: exact, case-insensitive, whitespace-normalized, punctuation-light normalized.
- This does **not** solve semantic or paraphrase leakage.
- Treat this as a hardening layer, not a proof of secrecy.

## Anti-manipulation
- Prompt-level constraints prohibit manipulative strategy generation.
- Censor B + Final Safety Gate can remove/revise/block manipulative outputs.

## Important Scope Limitation
- This project is a psychodynamic-inspired **simulation architecture**.
- It is not a real unconscious, personality, or clinical psychoanalytic model.
