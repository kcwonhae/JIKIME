
import os
import sys
import json
import threading
import webbrowser
from pathlib import Path

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from risk_engine import MonitorState, LEVELS

try:
    from winotify import Notification, audio
    HAS_TOAST = True
except Exception:
    HAS_TOAST = False

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False

BASE = Path(__file__).resolve().parent
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

state = MonitorState()

def maybe_notify(previous_level, snapshot):
    current = snapshot["level"]
    if LEVELS.index(current) <= LEVELS.index(previous_level):
        return
    if current == "SAFE":
        return

    title_map = {
        "LOW": "지키ME - 수상한 입력 감지",
        "MEDIUM": "지키ME - 행동 변화 감지",
        "HIGH": "지키ME - 위험 행동 확대",
        "CRITICAL": "지키ME - CRITICAL",
    }
    msg_map = {
        "LOW": "외부 입력에서 초기 위험 신호가 감지되었습니다.",
        "MEDIUM": "행동 sequence가 정상 범위에서 벗어나기 시작했습니다.",
        "HIGH": "Resource/권한/민감정보 관련 위험 행동이 누적되고 있습니다.",
        "CRITICAL": "민감정보 외부 유출 가능성이 높습니다. 즉시 확인하세요.",
    }

    if not HAS_TOAST:
        print("[지키ME] winotify를 불러오지 못해 Windows 알림을 띄울 수 없습니다.")
        return

    try:
        # 가장 호환성 높은 최소 Toast부터 띄운다.
        toast = Notification(
            app_id="JIKIME",
            title=title_map[current],
            msg=f"{msg_map[current]} 현재 위험도 {snapshot['score']}/100",
            duration="long",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        print(f"[지키ME] Windows 알림 전송 완료: {current} {snapshot['score']}/100")
    except Exception as e:
        print(f"[지키ME] Windows 알림 오류: {type(e).__name__}: {e}")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/event", methods=["POST"])
def api_event():
    payload = request.get_json(silent=True) or {}
    prev = state.level
    snap = state.ingest(payload)
    maybe_notify(prev, snap)
    return jsonify(snap)

@app.route("/api/status")
def api_status():
    return jsonify(state.snapshot())

@app.route("/api/test-notification", methods=["POST", "GET"])
def api_test_notification():
    if not HAS_TOAST:
        return jsonify({"ok": False, "error": "winotify import failed"}), 500
    try:
        toast = Notification(
            app_id="JIKIME",
            title="지키ME 알림 테스트",
            msg="이 알림이 보이면 Windows Toast 기능은 정상입니다.",
            duration="long",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        print("[지키ME] 테스트 알림 전송 완료")
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[지키ME] 테스트 알림 오류: {type(e).__name__}: {e}")
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

@app.route("/api/reset", methods=["POST"])
def api_reset():
    state.reset()
    return jsonify(state.snapshot())

@app.route("/api/pause", methods=["POST"])
def api_pause():
    data = request.get_json(silent=True) or {}
    state.paused = bool(data.get("paused", not state.paused))
    return jsonify(state.snapshot())

def open_dashboard(icon=None, item=None):
    webbrowser.open("http://127.0.0.1:8765/")

def toggle_pause(icon=None, item=None):
    state.paused = not state.paused

def quit_app(icon=None, item=None):
    if icon:
        icon.stop()
    os._exit(0)

def run_tray():
    if not HAS_TRAY:
        return
    image = Image.open(BASE / "static" / "jikime.png")
    menu = pystray.Menu(
        pystray.MenuItem("대시보드 열기", open_dashboard),
        pystray.MenuItem("모니터링 일시정지/재개", toggle_pause),
        pystray.MenuItem("종료", quit_app),
    )
    icon = pystray.Icon("jikime", image, "지키ME", menu)
    icon.run()

if __name__ == "__main__":
    if HAS_TRAY:
        threading.Thread(target=run_tray, daemon=True).start()
    print("지키ME 백그라운드 모니터링 시작")
    print("Dashboard: http://127.0.0.1:8765/")
    app.run(host="127.0.0.1", port=8765, debug=False, threaded=True)
