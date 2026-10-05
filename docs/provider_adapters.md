# Provider adapters

`AgentProvider` defines `generate_plan(task)`, `generate_code(task, plan)`, and `review_code(diff)`. The mock implementation is deterministic and requires no key. Remote adapters return structured plans, complete Python file contents, and reviewer comments. Generated paths/content are validated and changes are written only into a disposable per-task worktree; sandbox tests run there before a review is created. No generated code is applied to the bundled source tree.

Configure `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` on both API and worker services. Optional model names can be set with `ANTHROPIC_MODEL`, `OPENAI_MODEL`, and `GEMINI_MODEL`. A provider appears configured only when its corresponding key exists. The browser never receives provider secrets.
