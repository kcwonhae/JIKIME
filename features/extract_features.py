import json
import csv
import os
from collections import Counter


def get_project_paths():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    trajectories_path = os.path.join(
        project_root,
        "data",
        "trajectories.json"
    )

    features_path = os.path.join(
        project_root,
        "data",
        "features.csv"
    )

    return trajectories_path, features_path


def safe_div(a, b):
    return a / b if b else 0.0


def extract_session_features(session):
    if not session:
        return None

    tools = [event.get("tool", "") for event in session]
    risks = [event.get("risk", 0) for event in session]
    successes = [event.get("success", True) for event in session]

    agent_type = session[0].get("agent_type", "unknown")

    failure_indices = [
        i for i, success in enumerate(successes)
        if success is False
    ]

    failure_count = len(failure_indices)

    if failure_indices:
        first_failure = failure_indices[0]
        post_failure = session[first_failure + 1:]
    else:
        first_failure = None
        post_failure = []

    post_tools = [event.get("tool", "") for event in post_failure]
    post_resources = [event.get("resource", "") for event in post_failure]
    post_risks = [event.get("risk", 0) for event in post_failure]

    # 1. Tool switch rate
    tool_switches = 0
    for i in range(1, len(post_tools)):
        if post_tools[i] != post_tools[i - 1]:
            tool_switches += 1

    tool_switch_rate = safe_div(
        tool_switches,
        max(len(post_tools) - 1, 1)
    )

    # 2. Resource expansion
    pre_failure_resources = set()
    if first_failure is not None:
        pre_failure_resources = set(
            event.get("resource", "")
            for event in session[:first_failure + 1]
        )

    post_failure_resources = set(post_resources)
    new_resources = post_failure_resources - pre_failure_resources

    resource_expansion = safe_div(
        len(new_resources),
        max(len(pre_failure_resources), 1)
    )

    # 3. Retry diversity
    retry_diversity = safe_div(
        len(set(post_tools)),
        max(len(post_tools), 1)
    )

    # 4. Goal persistence
    goal_persistence = len(post_failure)

    # 5. Risk escalation
    if first_failure is not None:
        base_risk = session[first_failure].get("risk", 0)

        if post_risks:
            risk_escalation = max(post_risks) - base_risk
        else:
            risk_escalation = 0
    else:
        risk_escalation = 0

    # 6. Risk slope
    if len(post_risks) >= 2:
        risk_slope = (
            post_risks[-1] - post_risks[0]
        ) / (len(post_risks) - 1)
    else:
        risk_slope = 0.0

    # 7. Privilege exploration
    privilege_keywords = [
        "permission",
        "privilege",
        "admin",
        "role",
        "access"
    ]

    privilege_exploration = 0

    for event in post_failure:
        combined = (
            str(event.get("tool", "")).lower()
            + " "
            + str(event.get("resource", "")).lower()
        )

        if any(keyword in combined for keyword in privilege_keywords):
            privilege_exploration = 1
            break

    # 8. External transfer attempt
    external_keywords = [
        "external",
        "outbound",
        "remote"
    ]

    external_transfer = 0

    for event in post_failure:
        combined = (
            str(event.get("tool", "")).lower()
            + " "
            + str(event.get("resource", "")).lower()
        )

        if any(keyword in combined for keyword in external_keywords):
            external_transfer = 1
            break

    # 9. Unique tool ratio
    unique_tool_ratio = safe_div(
        len(set(tools)),
        len(tools)
    )

    # 10. Max risk
    max_risk = max(risks) if risks else 0

    # 11. Mean risk
    mean_risk = safe_div(sum(risks), len(risks))

    # 12. Sequence length
    sequence_length = len(session)

    label_map = {
        "normal": 0,
        "malicious": 1
    }

    label = label_map.get(agent_type, -1)

    return {
        "session_id": session[0].get("session_id", ""),
        "agent_type": agent_type,
        "sequence_length": sequence_length,
        "failure_count": failure_count,
        "tool_switch_rate": round(tool_switch_rate, 4),
        "resource_expansion": round(resource_expansion, 4),
        "retry_diversity": round(retry_diversity, 4),
        "goal_persistence": goal_persistence,
        "risk_escalation": round(risk_escalation, 4),
        "risk_slope": round(risk_slope, 4),
        "privilege_exploration": privilege_exploration,
        "external_transfer": external_transfer,
        "unique_tool_ratio": round(unique_tool_ratio, 4),
        "max_risk": round(max_risk, 4),
        "mean_risk": round(mean_risk, 4),
        "label": label
    }


def load_trajectories(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_features(rows, path):
    if not rows:
        print("No feature rows to save.")
        return

    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved -> {path}")


def main():
    trajectories_path, features_path = get_project_paths()

    if not os.path.exists(trajectories_path):
        print("trajectories.json not found.")
        print(f"Expected path: {trajectories_path}")
        return

    trajectories = load_trajectories(trajectories_path)

    feature_rows = []

    for session in trajectories:
        row = extract_session_features(session)

        if row is not None:
            feature_rows.append(row)

    save_features(feature_rows, features_path)

    print(f"Total sessions: {len(feature_rows)}")

    counts = Counter(
        row["agent_type"]
        for row in feature_rows
    )

    print("Class counts:")
    for key, value in counts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
