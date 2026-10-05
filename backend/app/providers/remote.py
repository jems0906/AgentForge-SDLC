import json
import os
import urllib.error
import urllib.request


class RemoteProvider:
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key

    def _complete(self, prompt: str) -> str:
        if self.name == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            body = {"model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"), "max_tokens": 1400, "messages": [{"role": "user", "content": prompt}]}
        elif self.name == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            body = {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": [{"role": "user", "content": prompt}], "max_tokens": 1400}
        elif self.name == "gemini":
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            headers = {}
            body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 1400}}
        else:
            raise ValueError(f"Unsupported provider: {self.name}")
        request = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers}, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError(f"{self.name} request failed or timed out; check provider configuration and service logs.") from error
        if self.name == "anthropic":
            return "\n".join(item.get("text", "") for item in result.get("content", []))
        if self.name == "openai":
            return result["choices"][0]["message"]["content"]
        return "\n".join(part.get("text", "") for part in result["candidates"][0]["content"]["parts"])

    @staticmethod
    def _json(text: str, fallback):
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return fallback

    def generate_plan(self, task: dict) -> list[dict]:
        prompt = f"Return only JSON: {{\"steps\":[{{\"title\":string,\"detail\":string}}]}}. Create a concise safe implementation plan for a task in a property-management Python application. Task: {json.dumps(task)}"
        text = self._complete(prompt)
        return self._json(text, {"steps": [{"title": "Review provider response", "detail": text[:1000]}]}).get("steps", [])

    def generate_code(self, task: dict, plan: list[dict]) -> dict:
        prompt = f"Return only JSON with a string summary and a files array of {{path, content}} entries. Each content value must be the complete updated Python file. Paths must be relative to the sample repository and limited to app/ or tests/. Do not use absolute paths, parent traversal, symlinks, shell scripts, or binary data. Make a focused change using the supplied source context. Task: {json.dumps(task)} Plan: {json.dumps(plan)}"
        text = self._complete(prompt)
        result = self._json(text, {"summary": f"{self.name} proposed a change for review", "files": []})
        return {"summary": str(result.get("summary", "Change proposal")), "files": result.get("files", [])}

    def review_code(self, diff: str) -> list[dict]:
        prompt = f"Review this proposed unified diff. Return only JSON: {{\"comments\":[{{\"severity\":\"info|warning|error\",\"file\":string,\"line\":number|null,\"comment\":string}}]}}. Be specific and do not assert tests ran. Diff:\n{diff[:12000]}"
        text = self._complete(prompt)
        return self._json(text, {"comments": [{"severity": "warning", "file": "review", "line": None, "comment": text[:1000]}]}).get("comments", [])
