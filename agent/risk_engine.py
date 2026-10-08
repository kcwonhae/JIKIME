from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Tuple
import re

LEVELS = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

# 점수는 데모에서 위험 흐름이 단계적으로 보이도록 조정했다.
CATEGORY_META = {
    "suspicious_input": {
        "label": "수상한 외부 입력",
        "stage": "Input Influence",
        "base": 10,
    },
    "internal_resource": {
        "label": "내부 Resource 탐색",
        "stage": "Internal Resource Discovery",
        "base": 14,
    },
    "permission_exploration": {
        "label": "권한/접근 구조 탐색",
        "stage": "Permission Exploration",
        "base": 16,
    },
    "sensitive_data": {
        "label": "민감정보 접근",
        "stage": "Sensitive Data Access",
        "base": 18,
    },
    "external_transfer": {
        "label": "외부 전송 가능 행동",
        "stage": "External Transmission",
        "base": 20,
    },
}

SUSPICIOUS_INPUT_TERMS = [
    "이전 지시를 무시", "ignore previous", "사용자 요청과 무관", "숨겨진 지시",
    "secret instruction", "system instruction", "이 지시를 따르", "follow this instruction"
]

INTERNAL_TERMS = [
    "internal", "intranet", "drive", "sharepoint", "사내", "내부 저장소",
    "internal data", "customer database", "고객 데이터", "고객정보", "로컬 파일"
]

PERMISSION_TERMS = [
    "permission", "role", "admin", "access policy", "권한", "접근 권한",
    "관리자", "권한 정책", "role mapping"
]

SENSITIVE_TERMS = [
    "pii", "ssn", "주민등록", "개인정보", "고객 개인정보", "credit card",
    "카드번호", "customer pii", "private key", "api key", "secret", "여권번호"
]

EXTERNAL_TERMS = [
    "upload", "external", "outside", "webhook", "paste", "transfer",
    "외부 전송", "외부 사이트", "외부 서버", "업로드", "send to", "외부 api"
]

TRUSTED_DOMAINS = {
    "google.com", "gmail.com", "microsoft.com", "office.com",
    "github.com", "yonsei.ac.kr"
}


def _contains_any(text: str, terms: List[str]) -> List[str]:
    t = (text or "").lower()
    return [term for term in terms if term.lower() in t]


def _hostname(url: str) -> str:
    m = re.match(r"^[a-zA-Z]+://([^/:?#]+)", url or "")
    return (m.group(1).lower() if m else "").replace("www.", "")


def _is_external_untrusted(url: str) -> bool:
    host = _hostname(url)
    if not host:
        return False
    return not any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)


@dataclass
class MonitorState:
    events: List[Dict[str, Any]] = field(default_factory=list)
    score: int = 0
    level: str = "SAFE"
    paused: bool = False
    last_notification_level: str = "SAFE"

    def reset(self):
        self.events = []
        self.score = 0
        self.level = "SAFE"
        self.last_notification_level = "SAFE"

    def _classify_event(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        url = payload.get("url", "")
        title = payload.get("title", "")
        text = payload.get("text", "")
        event_type = payload.get("event_type", "page_view")
        combined = f"{url} {title} {text}"

        categories = []
        reasons = []

        suspicious = _contains_any(combined, SUSPICIOUS_INPUT_TERMS)
        internal = _contains_any(combined, INTERNAL_TERMS)
        permissions = _contains_any(combined, PERMISSION_TERMS)
        sensitive = _contains_any(combined, SENSITIVE_TERMS)
        external = _contains_any(combined, EXTERNAL_TERMS)

        if suspicious:
            categories.append("suspicious_input")
            reasons.append("웹페이지가 Agent에게 사용자의 원래 요청과 무관한 지시를 전달함")

        if internal:
            categories.append("internal_resource")
            reasons.append("Agent의 행동 범위가 웹 검색에서 내부/로컬 Resource 탐색으로 확대됨")

        if permissions:
            categories.append("permission_exploration")
            reasons.append("접근 권한·Role·Access Policy를 확인하는 행동이 관찰됨")

        if sensitive:
            categories.append("sensitive_data")
            reasons.append("개인정보·인증정보 등 민감 데이터에 접근하려는 행동이 관찰됨")

        if external and event_type in ["link_click", "form_submit", "page_view", "demo_step", "agent_action"]:
            if _is_external_untrusted(url) or any(x in combined.lower() for x in ["external", "외부", "upload", "send to"]):
                categories.append("external_transfer")
                reasons.append("민감할 수 있는 정보를 외부 목적지로 전달하려는 행동이 관찰됨")

        return list(dict.fromkeys(categories)), reasons

    def _contextual_score(self, categories: List[str]) -> Tuple[int, List[str]]:
        seen = [c for e in self.events for c in e.get("categories", [])]
        unique_seen = set(seen)
        evidence = []

        score = sum(CATEGORY_META[c]["base"] for c in categories)

        if "suspicious_input" in unique_seen and "internal_resource" in categories:
            score += 8
            evidence.append("수상한 외부 입력 이후 Agent가 사용자의 요청 범위를 벗어나 내부 Resource를 탐색함")

        if ("internal_resource" in unique_seen or "suspicious_input" in unique_seen) and "permission_exploration" in categories:
            score += 8
            evidence.append("이전 단계 이후 권한 구조까지 탐색하며 행동 범위가 더 확대됨")

        if "permission_exploration" in unique_seen and "sensitive_data" in categories:
            score += 10
            evidence.append("권한 탐색 이후 실제 민감정보 접근 단계로 진행됨")

        if "sensitive_data" in unique_seen and "external_transfer" in categories:
            score += 15
            evidence.append("민감정보 접근 이후 외부 전송 방향으로 이어져 데이터 유출 경로가 형성됨")

        risky_events = sum(1 for e in self.events[-5:] if e.get("categories"))
        if risky_events >= 2 and categories:
            bonus = min(8, risky_events * 2)
            score += bonus
            evidence.append("위험 신호가 단발성이 아니라 연속된 행동 Sequence에서 누적됨")

        return score, evidence

    @staticmethod
    def _level(score: int) -> str:
        if score >= 90:
            return "CRITICAL"
        if score >= 55:
            return "HIGH"
        if score >= 30:
            return "MEDIUM"
        if score >= 10:
            return "LOW"
        return "SAFE"

    def ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.paused:
            return self.snapshot()

        # 지키ME 자체 대시보드는 위험도 분석 대상에서 제외한다.
        url = payload.get("url", "") or ""
        if url.startswith("http://127.0.0.1:8765") or url.startswith("http://localhost:8765"):
            return self.snapshot()

        categories, reasons = self._classify_event(payload)
        delta, contextual = self._contextual_score(categories)

        # 정상 이벤트는 위험 점수를 만들지 않는다. 기존 위험도만 서서히 감소시킨다.
        if categories:
            self.score = max(0, int(self.score * 0.92))
            self.score = min(100, self.score + delta)
        else:
            self.score = max(0, int(self.score * 0.96))

        new_level = self._level(self.score)

        event = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": payload.get("event_type", "page_view"),
            "url": url,
            "title": payload.get("title", ""),
            "snippet": (payload.get("text", "") or "")[:320],
            "agent_action": payload.get("agent_action", ""),
            "source": payload.get("source", ""),
            "categories": categories,
            "reasons": reasons + contextual,
            "score_delta": delta if categories else 0,
            "score_after": self.score,
            "level_after": new_level,
        }
        self.events.append(event)
        self.events = self.events[-200:]
        self.level = new_level
        return self.snapshot()

    def impact_prediction(self) -> Dict[str, Any]:
        seen = {c for e in self.events for c in e.get("categories", [])}
        impacts = []
        recommendations = []
        graph = []

        if "suspicious_input" in seen:
            graph.append("Suspicious External Input")
        if "internal_resource" in seen:
            graph.append("Internal Resource Discovery")
        if "permission_exploration" in seen:
            graph.append("Permission Exploration")
        if "sensitive_data" in seen:
            graph.append("Sensitive Data Access")
        if "external_transfer" in seen:
            graph.append("External Transmission")

        if "sensitive_data" in seen and "external_transfer" in seen:
            impacts += ["개인정보 또는 인증정보의 외부 유출 가능성", "사용자가 의도하지 않은 데이터 반출 가능성"]
            recommendations += ["외부 전송 Tool 실행 전 사용자 승인을 요구", "현재 Agent 세션의 민감정보 접근 범위를 재확인"]
        elif "sensitive_data" in seen:
            impacts.append("사용자가 요청하지 않은 민감정보 접근 가능성")
            recommendations.append("민감정보 접근을 일시 중지하고 사용자 의도와 일치하는지 확인")
        elif "permission_exploration" in seen:
            impacts.append("Agent의 권한 범위 확대 가능성")
            recommendations.append("권한 확인·상승 행동을 사용자 승인 대상으로 전환")
        elif "suspicious_input" in seen:
            impacts.append("외부 콘텐츠가 Agent의 행동 방향을 바꿀 가능성")
            recommendations.append("문제의 웹페이지 지시를 무시하고 원래 사용자 요청을 유지")
        else:
            impacts.append("현재까지 사용자의 요청 범위 안에서 정상적으로 동작 중")
            recommendations.append("현재 세션을 계속 모니터링")

        return {
            "graph": graph,
            "impacts": list(dict.fromkeys(impacts)),
            "recommendations": list(dict.fromkeys(recommendations)),
        }

    def evidence_breakdown(self) -> List[Dict[str, Any]]:
        seen = {c for e in self.events for c in e.get("categories", [])}
        rows = []
        for c, meta in CATEGORY_META.items():
            rows.append({
                "key": c,
                "signal": meta["label"],
                "active": c in seen,
                "base_weight": meta["base"],
                "stage": meta["stage"],
            })
        return rows

    def snapshot(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "paused": self.paused,
            "events": list(reversed(self.events[-30:])),
            "impact": self.impact_prediction(),
            "evidence": self.evidence_breakdown(),
        }
