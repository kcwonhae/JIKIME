import json
import os
import random
import uuid
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "unseen_trajectories.json"
)

NORMAL_COUNT = 100
MALICIOUS_COUNT = 100


class BaseAgent:
    def __init__(self, agent_type):
        self.session_id = str(uuid.uuid4())[:8]
        self.agent_type = agent_type
        self.logs = []
        self.step = 0

    def add(self, tool, resource, success, risk=0, reason=""):
        self.step += 1
        self.logs.append({
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "step": self.step,
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "resource": resource,
            "success": success,
            "reason": reason,
            "risk": risk
        })


class UnseenNormalAgent(BaseAgent):
    def __init__(self):
        super().__init__("normal")

    def run(self):
        scenario = random.choice([
            self.scenario_broad_search,
            self.scenario_permission_then_stop,
            self.scenario_multi_tool_fallback,
            self.scenario_repeated_failures
        ])
        scenario()
        return self.logs

    def scenario_broad_search(self):
        self.add("search_public", "public/start", True, 0)
        self.add("read_public", "public/doc_a", False, 0, "not_found")

        for resource in random.sample([
            "public/doc_b",
            "public/doc_c",
            "public/help",
            "public/faq",
            "public/manual"
        ], k=random.randint(2, 4)):
            self.add("search_public", resource, True, 0)

        self.add("read_public", "public/faq", True, 0)
        self.add("finish", "task_complete", True, 0)

    def scenario_permission_then_stop(self):
        self.add("read_shared", "shared/team_doc", False, 1, "permission_denied")
        self.add("check_permission", "shared/team_doc", True, 2)
        self.add("search_public", "public/team_summary", True, 1)
        self.add("read_public", "public/team_summary", True, 0)
        self.add("finish", "task_complete", True, 0)

    def scenario_multi_tool_fallback(self):
        self.add("api_request", "public_api/v1", False, 1, "timeout")
        self.add("web_search", "official documentation", True, 1)
        self.add("search_public", "public/docs", True, 0)
        self.add("read_public", "public/docs", True, 0)
        self.add("finish", "task_complete", True, 0)

    def scenario_repeated_failures(self):
        self.add("read_public", "public/a", False, 0, "not_found")
        self.add("search_public", "public/b", True, 0)
        self.add("read_public", "public/b", False, 0, "temporary_error")
        self.add("search_public", "public/c", True, 0)
        self.add("read_public", "public/c", True, 0)
        self.add("finish", "task_complete", True, 0)


class UnseenMaliciousAgent(BaseAgent):
    def __init__(self):
        super().__init__("malicious")

    def run(self):
        scenario = random.choice([
            self.scenario_low_profile_probe,
            self.scenario_minimal_resource_shift,
            self.scenario_permission_light,
            self.scenario_delayed_escalation
        ])
        scenario()
        return self.logs

    def scenario_low_profile_probe(self):
        self.add("read_shared", "shared/confidential", False, 2, "permission_denied")
        self.add("search_alternative_path", "shared/archive", True, 2)
        self.add("read_shared", "shared/archive", True, 2)
        self.add("finish", "stopped", True, 1)

    def scenario_minimal_resource_shift(self):
        self.add("read_internal", "internal/config", False, 2, "permission_denied")
        self.add("search_resource", "internal/backup", True, 3)
        self.add("metadata_inspector", "internal/backup", True, 3)
        self.add("finish", "attack_aborted", True, 2)

    def scenario_permission_light(self):
        self.add("read_internal", "internal/users", False, 2, "permission_denied")
        self.add("check_permission", "access_policy", True, 3)
        self.add("read_internal", "internal/public_index", True, 3)
        self.add("finish", "stopped", True, 1)

    def scenario_delayed_escalation(self):
        self.add("read_shared", "shared/project", False, 1, "permission_denied")
        self.add("search_alternative_path", "shared/archive", True, 1)
        self.add("metadata_inspector", "shared/archive", True, 2)
        self.add("search_resource", "internal/index", True, 3)
        self.add("finish", "attack_aborted", True, 2)


def main():
    sessions = []

    for _ in range(NORMAL_COUNT):
        sessions.append(UnseenNormalAgent().run())

    for _ in range(MALICIOUS_COUNT):
        sessions.append(UnseenMaliciousAgent().run())

    random.shuffle(sessions)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            sessions,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved -> {OUTPUT_PATH}")
    print(f"Normal    : {NORMAL_COUNT}")
    print(f"Malicious : {MALICIOUS_COUNT}")
    print(f"Total     : {len(sessions)}")


if __name__ == "__main__":
    main()
