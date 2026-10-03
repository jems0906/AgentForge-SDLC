# Sandbox security model

The API accepts a command name, not a command line. The name must exactly match `COMMANDS` in `backend/app/sandbox/allowlist.py`; arguments are fixed by the server. The runner uses `subprocess.run` with `shell=False`, sets `cwd` to the bundled `sample_repo`, enforces a 30-second timeout, limits captured output, strips environment variables other than basic process paths, and redacts common secret assignments in logs.

No user-uploaded repository or arbitrary path is accepted. Provider keys are not forwarded to child processes. The Docker images run the bundled sample only, but the current subprocess runner is **not** a security boundary against malicious code: it shares the service's OS identity and network namespace. A production runner should use disposable non-root containers or microVMs, read-only source mounts, resource limits, no network egress, and per-task cleanup. Do not execute untrusted code with this MVP.
