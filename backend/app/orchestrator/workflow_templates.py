WORKFLOWS = {
    "feature": {
        "name": "Feature delivery",
        "description": "Plan, implement, test, review, then wait for human approval.",
        "steps": ["plan", "implement", "test", "review", "approval"],
    },
    "bugfix": {
        "name": "Bug fix",
        "description": "Reproduce the bug, patch it, validate, then request review.",
        "steps": ["reproduce", "patch", "test", "review", "approval"],
    },
    "refactor": {
        "name": "Refactor",
        "description": "Assess risk, refactor, validate, and present a review checklist.",
        "steps": ["risk_analysis", "refactor", "test", "review", "approval"],
    },
    "test": {
        "name": "Test coverage",
        "description": "Inspect coverage gaps, add tests, validate, then request review.",
        "steps": ["inspect", "implement", "test", "review", "approval"],
    },
    "integration": {
        "name": "Integration",
        "description": "Plan the integration boundary, implement, validate, and review.",
        "steps": ["plan", "implement", "test", "review", "approval"],
    },
}
