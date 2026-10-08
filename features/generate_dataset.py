import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from simulator.normal_agent import NormalAgentSimulator
from simulator.malicious_agent import MaliciousAgentSimulator


NORMAL_COUNT = 500
MALICIOUS_COUNT = 500


def get_data_path():
    return os.path.join(
        PROJECT_ROOT,
        "data",
        "trajectories.json"
    )


def generate_normal_sessions(count):
    sessions = []

    for i in range(count):
        agent = NormalAgentSimulator()
        logs = agent.run()
        sessions.append(logs)

        if (i + 1) % 50 == 0:
            print(f"[Normal] {i + 1}/{count} generated")

    return sessions


def generate_malicious_sessions(count):
    sessions = []

    for i in range(count):
        agent = MaliciousAgentSimulator()
        logs = agent.run()
        sessions.append(logs)

        if (i + 1) % 50 == 0:
            print(f"[Malicious] {i + 1}/{count} generated")

    return sessions


def save_all_sessions(sessions):
    data_path = get_data_path()
    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(
            sessions,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nSaved -> {data_path}")


def main():
    print("===================================")
    print(" AgentGuard Dataset Generator")
    print("===================================\n")

    print(f"Normal sessions    : {NORMAL_COUNT}")
    print(f"Malicious sessions : {MALICIOUS_COUNT}")
    print(f"Total              : {NORMAL_COUNT + MALICIOUS_COUNT}\n")

    normal_sessions = generate_normal_sessions(NORMAL_COUNT)
    malicious_sessions = generate_malicious_sessions(MALICIOUS_COUNT)

    all_sessions = normal_sessions + malicious_sessions

    save_all_sessions(all_sessions)

    print("\nDataset generation complete.")
    print(f"Total sessions saved: {len(all_sessions)}")


if __name__ == "__main__":
    main()
