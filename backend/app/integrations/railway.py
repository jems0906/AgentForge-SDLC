import json
import os
import time
import urllib.error
import urllib.request


API_URL = "https://backboard.railway.com/graphql/v2"
TERMINAL_STATES = {"SUCCESS", "FAILED", "CRASHED", "REMOVED", "SKIPPED"}


def _configuration():
    token = os.getenv("RAILWAY_PROJECT_TOKEN") or os.getenv("RAILWAY_TOKEN")
    project_id = os.getenv("RAILWAY_PROJECT_ID")
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID")
    service_id = os.getenv("RAILWAY_SERVICE_ID")
    if not all((token, project_id, environment_id, service_id)):
        return None
    token_header = "Project-Access-Token" if os.getenv("RAILWAY_PROJECT_TOKEN") else "Authorization"
    token_value = token if token_header == "Project-Access-Token" else f"Bearer {token}"
    return token_header, token_value, project_id, environment_id, service_id


def is_configured() -> bool:
    return _configuration() is not None


def _graphql(query: str, variables: dict, configuration=None) -> dict:
    config = configuration or _configuration()
    if config is None:
        raise RuntimeError("Configure Railway token, project, environment, and service IDs before deploying.")
    token_header, token_value, *_ = config
    request = urllib.request.Request(
        API_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={token_header: token_value, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("Railway API request failed; check token access and service IDs.") from error
    if result.get("errors"):
        raise RuntimeError(f"Railway API rejected the operation: {result['errors'][0].get('message', 'unknown error')}")
    return result.get("data", {})


def _wait_for_latest_deployment(configuration, previous_id: str | None, timeout_seconds: int = 180) -> dict:
    _, _, project_id, environment_id, service_id = configuration
    query = "query($input: DeploymentListInput!, $first: Int) { deployments(input: $input, first: $first) { edges { node { id status url createdAt } } } }"
    variables = {"input": {"projectId": project_id, "serviceId": service_id, "environmentId": environment_id}, "first": 1}
    deadline = time.monotonic() + timeout_seconds
    deployment = None
    while time.monotonic() < deadline:
        result = _graphql(query, variables, configuration)
        edges = result.get("deployments", {}).get("edges", [])
        if edges:
            deployment = edges[0]["node"]
            if deployment["id"] != previous_id and deployment["status"] in TERMINAL_STATES:
                return deployment
        time.sleep(3)
    raise RuntimeError(f"Railway deployment did not finish within {timeout_seconds} seconds. Last state: {deployment}")


def deploy() -> dict:
    configuration = _configuration()
    if configuration is None:
        raise RuntimeError("Configure Railway token, project, environment, and service IDs before deploying.")
    _, _, project_id, environment_id, service_id = configuration
    latest_query = "query($input: DeploymentListInput!, $first: Int) { deployments(input: $input, first: $first) { edges { node { id } } } }"
    deployment_input = {"projectId": project_id, "serviceId": service_id, "environmentId": environment_id}
    latest = _graphql(latest_query, {"input": deployment_input, "first": 1}, configuration)
    edges = latest.get("deployments", {}).get("edges", [])
    previous_id = edges[0]["node"]["id"] if edges else None
    mutation = "mutation($input: EnvironmentTriggersDeployInput!) { environmentTriggersDeploy(input: $input) }"
    _graphql(mutation, {"input": {"environmentId": environment_id, "projectId": project_id, "serviceId": service_id}}, configuration)
    result = _wait_for_latest_deployment(configuration, previous_id)
    if result.get("status") != "SUCCESS":
        raise RuntimeError(f"Railway deployment finished in state {result.get('status')}.")
    return result


def rollback() -> dict:
    configuration = _configuration()
    if configuration is None:
        raise RuntimeError("Configure Railway token, project, environment, and service IDs before rollback.")
    _, _, project_id, environment_id, service_id = configuration
    query = "query($input: DeploymentListInput!, $first: Int) { deployments(input: $input, first: $first) { edges { node { id status } } } }"
    variables = {
        "input": {"projectId": project_id, "serviceId": service_id, "environmentId": environment_id, "status": {"successfulOnly": True}},
        "first": 2,
    }
    edges = _graphql(query, variables, configuration).get("deployments", {}).get("edges", [])
    if len(edges) < 2:
        raise RuntimeError("Railway has no previous successful deployment to roll back to.")
    target_id = edges[1]["node"]["id"]
    deployment_query = "query($id: String!) { deployment(id: $id) { id canRollback } }"
    target = _graphql(deployment_query, {"id": target_id}, configuration).get("deployment")
    if not target or not target.get("canRollback"):
        raise RuntimeError("Railway reports that the previous deployment cannot be rolled back.")
    mutation = "mutation($id: String!) { deploymentRollback(id: $id) { id status } }"
    result = _graphql(mutation, {"id": target_id}, configuration).get("deploymentRollback")
    if not result:
        raise RuntimeError("Railway rejected the rollback request.")
    if result.get("status") == "SUCCESS":
        return result
    deployment_query = "query($id: String!) { deployment(id: $id) { id status url } }"
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        current = _graphql(deployment_query, {"id": result["id"]}, configuration).get("deployment")
        if current and current.get("status") in TERMINAL_STATES:
            if current["status"] != "SUCCESS":
                raise RuntimeError(f"Railway rollback finished in state {current['status']}.")
            return current
        time.sleep(3)
    raise RuntimeError("Railway rollback did not finish within 180 seconds.")
