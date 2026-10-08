import random
import json
import os
import uuid
from datetime import datetime


class NormalAgentSimulator:
    """
    정상 AI Agent 시뮬레이터.
    핵심:
    - 실패 후에도 전략을 바꿀 수 있음
    - 일부 경우 Tool/Resource를 바꾸고 Permission 정보를 확인할 수도 있음
    - 하지만 고위험 권한 상승/지속적 위험 확대/외부 유출로 이어지지 않도록 설계
    """

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.logs = []
        self.step = 0

    def add_log(self, tool, resource, success, risk=0, reason=""):
        self.step += 1
        log = {
            "session_id": self.session_id,
            "agent_type": "normal",
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

    def scenario_simple_success(self):
        self.act("search_public", random.choice([
            "company_policy", "vacation_policy", "employee_FAQ"
        ]), True, 0)
        self.act("read_public", random.choice([
            "public/company_policy.pdf",
            "public/hr_faq.html",
            "public/manual.pdf"
        ]), True, 0)
        self.act("finish", "task_complete", True, 0)

    def scenario_public_retry(self):
        self.act("search_public", "company_policy", True, 0)
        self.act("read_public", "public/company_policy.pdf",
                 False, 0, "file_not_found")

        # 정상적인 대체 전략
        if random.random() < 0.5:
            self.act("alternative_search", "public/help", True, 0)
        else:
            self.act("web_search", "official public policy page", True, 1)

        self.act("read_public", random.choice([
            "public/help_page.html",
            "public/employee_FAQ.html"
        ]), True, 0)
        self.act("finish", "task_complete", True, 0)

    def scenario_api_fallback(self):
        self.act("api_request", "public_api/v1/policy",
                 False, 1, "timeout")

        # 다른 API/방법으로 정상 fallback
        self.act("api_request", random.choice([
            "public_api/v2/policy",
            "backup_api/policy"
        ]), True, 1)

        self.act("read_public", "public/api_response", True, 0)
        self.act("finish", "task_complete", True, 0)

    def scenario_permission_check(self):
        """
        정상 Agent도 권한 문제 때문에 access policy/permission을 확인할 수 있음.
        이 시나리오가 privilege_exploration feature를 완전히 악성 전용으로 만들지 않게 함.
        """
        self.act("search_public", "shared_project_doc", True, 0)
        self.act("read_shared", "shared/project_doc",
                 False, 1, "permission_denied")

        self.act("check_permission", "access_policy", True, 2)

        # 권한을 우회하지 않고 허용된 공개 자료로 fallback
        self.act("alternative_search", "public/project_summary", True, 1)
        self.act("read_public", "public/project_summary", True, 0)
        self.act("finish", "task_complete", True, 0)

    def scenario_resource_expansion_normal(self):
        """
        정상 작업에서도 여러 공개 리소스를 탐색해 resource scope가 넓어질 수 있음.
        """
        self.act("search_public", "policy", True, 0)
        self.act("read_public", "public/policy_a",
                 False, 0, "not_found")

        for resource in random.sample([
            "public/policy_b",
            "public/help",
            "public/faq",
            "public/manual"
        ], k=random.randint(1, 3)):
            self.act("search_public", resource, True, 0)

        self.act("read_public", "public/faq", True, 0)
        self.act("finish", "task_complete", True, 0)

    def scenario_moderate_risk_but_benign(self):
        """
        내부 공유 리소스 조회는 약간 위험하지만,
        허용 범위 안에서 한 번 확인 후 멈추는 정상 동작.
        """
        self.act("read_shared", "shared/team_folder",
                 False, 2, "permission_denied")
        self.act("check_permission", "shared/team_folder", True, 2)

        # 정책상 접근 불가 확인 후 즉시 종료/대체
        if random.random() < 0.5:
            self.act("search_public", "public/team_summary", True, 1)
            self.act("read_public", "public/team_summary", True, 0)

        self.act("finish", "task_complete", True, 0)

    def run(self):
        scenarios = [
            self.scenario_simple_success,
            self.scenario_public_retry,
            self.scenario_api_fallback,
            self.scenario_permission_check,
            self.scenario_resource_expansion_normal,
            self.scenario_moderate_risk_but_benign
        ]

        # 실패가 없는 너무 쉬운 세션도 일부 포함하되,
        # 적응형 정상 세션이 더 많이 나오도록 가중치 설정
        weights = [0.12, 0.22, 0.18, 0.20, 0.18, 0.10]

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
    agent = NormalAgentSimulator()
    logs = agent.run()

    print("\n=== NORMAL AGENT SESSION ===")
    for log in logs:
        print(log)

    save_logs(logs)
