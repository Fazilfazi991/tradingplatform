# LLM provider configuration

Set credentials only through environment variables. Never commit or print them.

| Provider | Credential | Model |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL` |
| GLM | `GLM_API_KEY` | `GLM_MODEL` |
| Qwen/DashScope | `DASHSCOPE_API_KEY` | `QWEN_MODEL` |
| Moonshot | `MOONSHOT_API_KEY` | `MOONSHOT_MODEL` |

One credential is sufficient. Routes are configurable; do not embed provider preference in business logic. Validate first with a routine fixture, then a grounded official event. Confirm schema success, source-reference containment, token/cost telemetry and cache behavior. Simulate timeout, rate limit, invalid JSON and total unavailability before enabling a recurring job.

If no provider is configured, collection continues and semantic outputs remain `UNKNOWN`/`INSUFFICIENT_EVIDENCE`.

