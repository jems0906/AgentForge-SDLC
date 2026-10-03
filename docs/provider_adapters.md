# Provider adapters

`AgentProvider` defines `generate_plan(task)`, `generate_code(task, plan)`, and `review_code(diff)`. The mock implementation is deterministic and requires no key. Remote adapters call the provider's text-generation API from the server and return a structured plan, proposed unified diff, and review comments. Proposals are for inspection only; this version never applies LLM output to disk or executes it.

Configure `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` on both API and worker services. Optional model names can be set with `ANTHROPIC_MODEL`, `OPENAI_MODEL`, and `GEMINI_MODEL`. A provider appears configured only when its corresponding key exists. The browser never receives provider secrets.
