PRIORITY_RANK = {"low": 1, "normal": 2, "high": 3, "urgent": 4}


def normalize_priority(priority: str) -> str:
    normalized = priority.strip().lower()
    if normalized not in PRIORITY_RANK:
        raise ValueError("Priority must be low, normal, high, or urgent")
    return normalized
