import json
import urllib.error
import urllib.request
from pathlib import Path


def main():
    samples = json.loads((Path(__file__).resolve().parents[1] / "data_samples" / "agent_tasks.json").read_text(encoding="utf-8"))
    for sample in samples:
        request = urllib.request.Request(
            "http://127.0.0.1:8000/api/tasks", data=json.dumps(sample).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                created = json.loads(response.read().decode("utf-8"))
                print(f"Queued AG-{created['id']:04d}: {created['title']}")
        except urllib.error.URLError as error:
            raise SystemExit("Start the API at http://127.0.0.1:8000 before generating sample tasks.") from error


if __name__ == "__main__":
    main()
