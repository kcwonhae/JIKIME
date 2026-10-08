# 지키ME Desktop MVP

이 버전은 Streamlit 웹이 아니라 **Windows 백그라운드 Agent + Chrome/Edge Extension + 우측 하단 Windows 알림 + 상세 Dashboard** 구조입니다.

## 구조
Browser
→ 지키ME Extension
→ localhost:8765
→ 지키ME Desktop Agent
→ Risk Escalation
→ Windows Toast
→ 상세 Dashboard

## 1. 설치
폴더에서 `install.bat` 더블클릭.

또는 터미널:
```bash
python -m pip install -r requirements.txt
```

## 2. 지키ME 실행
`start_jikime.bat` 더블클릭.

터미널에:
`Dashboard: http://127.0.0.1:8765/`
가 나오면 정상입니다.

## 3. Chrome/Edge Extension 설치
### Chrome
1. 주소창에 `chrome://extensions`
2. 우측 상단 `개발자 모드` ON
3. `압축해제된 확장 프로그램을 로드`
4. 이 프로젝트의 `extension` 폴더 선택

### Edge
1. 주소창에 `edge://extensions`
2. 개발자 모드 ON
3. `압축 풀린 항목 로드`
4. `extension` 폴더 선택

## 4. 동작
브라우저에서 페이지를 열거나 링크/버튼을 클릭하면 Extension이 다음 정보를 localhost로 전달합니다.
- URL
- 페이지 제목
- 현재 페이지의 제한된 텍스트 스니펫
- page_view / link_click / form_submit 등의 이벤트 유형

지키ME는 이를 이용해 다음 escalation을 누적 분석합니다.

🟡 수상한 외부 입력
→ 🟠 내부 Resource 탐색
→ 🟠 권한/Role 탐색
→ 🔴 민감정보 접근
→ 🔴 외부 전송

위험 단계가 올라갈 때 Windows 오른쪽 아래 알림이 뜹니다.
알림의 `판단 근거 보기`를 누르면 상세 Dashboard를 엽니다.

## 5. 점수 근거
단순히 91/100만 띄우지 않고 Dashboard에서:
- 어떤 신호가 감지됐는지
- 기본 가중치
- 앞선 행동과 연결되며 추가된 escalation 근거
- 예상 피해
- 권장 조치
를 보여줍니다.

## 6. 중요한 MVP 한계
- 현재 버전은 **브라우저 이벤트 모니터링** MVP입니다.
- OS 전체 화면을 녹화/감시하지 않습니다.
- 이메일 클라이언트가 브라우저(Gmail/Outlook Web)일 때 페이지 텍스트를 로컬에서 분석합니다.
- 완전한 인과관계를 주장하지 않고 행동 sequence의 escalation과 context correlation을 관찰합니다.
- 실제 Agent Tool Call 차단은 아직 브라우저 레벨 경고까지이며, Agent SDK/MCP Gateway와 연결하면 진짜 ALLOW/BLOCK 제어로 확장할 수 있습니다.

## 7. 개인정보
Extension은 분석을 위해 제한된 페이지 텍스트를 `127.0.0.1`의 로컬 지키ME Agent로 보냅니다.
외부 서버로 전송하는 코드는 포함하지 않았습니다.
