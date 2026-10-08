# 지키ME macOS 데모 버전

## 실행 순서
1. ZIP 압축 해제
2. `install_mac.command` 더블클릭
   - macOS가 막으면 파일 우클릭 → 열기
3. 설치가 끝나면 `start_jikime_mac.command` 더블클릭
4. 브라우저에서 `http://127.0.0.1:8765/` 열기
5. Chrome/Edge 확장프로그램에 `extension` 폴더 로드
6. `jikime_demo_scenario.html`을 열고 단계별 버튼을 순서대로 클릭
7. 알림 테스트는 `test_notification_mac.command`

## 확장프로그램
Chrome: `chrome://extensions`
Edge: `edge://extensions`

- 개발자 모드 ON
- 압축 해제된 확장 프로그램 로드
- `extension` 폴더 선택

## macOS 알림
macOS에서는 Windows Toast 대신 Notification Center를 사용합니다.
처음 실행 시 시스템 설정 → 알림에서 Terminal/osascript 알림을 허용해야 할 수 있습니다.

## 데모 목표
SAFE → LOW → MEDIUM → HIGH → CRITICAL로 위험도가 단계적으로 상승하고,
Dashboard에 각 단계의 위험 증가 요인이 표시되는지 확인합니다.
