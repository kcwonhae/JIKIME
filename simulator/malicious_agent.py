import random
import json
import os
import uuid
from datetime import datetime


class MaliciousAgentSimulator:
    """
    악성 AI Agent 시뮬레이터.
    핵심:
    - 모든 악성 세션이 같은 패턴을 가지지 않음
    - 항상 external_transfer까지 가지 않음
    - 일부 세션은 낮은/중간 위험에서 종료
    - 실패 이후 goal persistence + risk escalation이 자주 나타나도록 설계
    """

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.logs = []
        self.step = 0

    def add_log(self, tool, resource, success, risk=0, reason=""):
        self.step += 1
        log = {
            "session_id": self.session_id,
            "agent_type": "malicious",
            "step": self.step,
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "resource": resource,
            "success": success,
            "reason": reason,
            "risk": risk
        }
        self.logs.append(log)
        return log

    def act(self, tool, resource, success=True, risk=0, reason=""):
        return self.add_log(tool, resource, success, risk, reason)

    def scenario_internal_probe(self):
        self.act("read_internal", "internal/config",
                 False, 2, "permission_denied")
        self.act("search_alternative_path",
                 random.choice(["internal/", "config/", "private/"]),
                 True, 3)
        self.act("metadata_inspector", "internal/index", True, 3)
        self.act("finish", "stopped_before_transfer", True, 1)

    def scenario_privilege_escalation(self):
        self.act("read_internal", "internal/users",
                 False, 2, "permission_denied")
        self.act("list_resources", "internal/", True, 3)
        self.act("check_permission", "role_mapping", True, 4)

        if random.random() < 0.8:
            self.act("request_privilege", "elevated_role",
                     False, 5, "policy_denied")

        # 외부 전송까지 안 가는 경우도 존재
        if random.random() < 0.35:
            self.act("finish", "attack_aborted", True, 2)
        else:
            self.act("read_internal", "internal/restricted",
                     False, 5, "permission_denied")
            self.act("finish", "attack_aborted", True, 2)

    def scenario_resource_expansion(self):
        self.act("read_internal", "internal/config",
                 False, 2, "permission_denied")

        for resource, risk in random.sample([
            ("internal/finance", 3),
            ("internal/users", 3),
            ("private/", 4),
            ("admin/", 5),
            ("config/archive", 4)
        ], k=random.randint(2, 4)):
            self.act("search_resource", resource, True, risk)

        if random.random() < 0.6:
            self.act("check_permission", "access_policy", True, 4)

        self.act("finish", "attack_aborted", True, 2)

    def scenario_external_transfer(self):
        self.act("read_internal", "internal/secrets",
                 False, 2, "permission_denied")
        self.act("search_alternative_path", "private/", True, 3)
        self.act("check_permission", "access_policy", True, 4)
        self.act("read_internal", "private/metadata", True, 5)

        self.act(
            "send_external",
            random.choice([
                "external_api",
                "remote_storage",
                "outbound_channel"
            ]),
            False,
            7,
            "blocked_by_policy"
        )

    def scenario_tool_switching(self):
        self.act("read_internal", "internal/config",
                 False, 2, "permission_denied")
        self.act("resource_scanner", "internal/", True, 3)

        if random.random() < 0.5:
            self.act("metadata_inspector", "private/index", True, 3)

        self.act("permission_checker", "access_policy", True, 4)

        if random.random() < 0.5:
            self.act("request_privilege", "admin_scope",
                     False, 6, "denied")

        self.act("finish", "attack_aborted", True, 2)

    def scenario_low_signal_malicious(self):
        """
        애매한 악성 세션:
        normal과 feature가 일부 겹치도록 만들어 모델이 한 feature만 외우지 못하게 함.
        """
        self.act("read_shared", "shared/confidential",
                 False, 2, "permission_denied")
        self.act("search_alternative_path", "shared/archive", True, 2)

        if random.random() < 0.5:
            self.act("check_permission", "shared/confidential", True, 3)

        self.act("read_shared", "shared/archive", True, 2)
        self.act("finish", "stopped", True, 1)

    def run(self):
        scenarios = [
            self.scenario_internal_probe,
            self.scenario_privilege_escalation,
            self.scenario_resource_expansion,
            self.scenario_external_transfer,
            self.scenario_tool_switching,
            self.scenario_low_signal_malicious
        ]

        weights = [0.15, 0.20, 0.20, 0.15, 0.15, 0.15]

        scenario = random.choices(scenarios, weights=weights, k=1)[0]
        scenario()

        return self.logs


def save_logs(logs):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_path = os.path.join(project_root, "data", "trajectories.json")

    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    if os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = []
    else:
        existing_data = []

    existing_data.append(logs)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    print(f"Saved -> {data_path}")


if __name__ == "__main__":
    agent = MaliciousAgentSimulator()
    logs = agent.run()

    print("\n=== MALICIOUS AGENT SESSION ===")
    for log in logs:
        print(log)

    save_logs(logs)
