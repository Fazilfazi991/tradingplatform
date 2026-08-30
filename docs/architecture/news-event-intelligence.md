# News and event intelligence

The pipeline is `source metadata → causal event → canonical cluster → deterministic/optional LLM
analysis → append-only interpretation ledger → evidence output → daily archive`. It structures what
happened without estimating a stock return.

Deterministic analysis is always available. The optional `LLMIntelligenceAnalyzer` routes tasks
through registered provider adapters. OpenAI, GLM, DeepSeek, Qwen and Moonshot have independent
runtime configurations; future providers use the same adapter contract. Routes support fallback,
validated structured output, input/prompt/model caching, token-cost and latency telemetry, and
optional multi-model consensus for ambiguous high-materiality events. No provider is enabled merely
because its configuration exists.

Source text is placed in an untrusted evidence envelope. It cannot invoke tools, request secrets,
change policy or modify model settings. Every derived output records input/output hashes, provider,
model/version, prompt version, configuration, evidence references and validation state.

Facts, source opinions, model interpretations, rumours, analyst views and market reactions are
distinct claim kinds. Full article bodies are neither required nor reproduced.
