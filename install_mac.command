#!/bin/bash
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements_mac.txt
echo ""
echo "설치 완료. 이제 start_jikime_mac.command 를 실행하세요."
read -n 1 -s -r -p "아무 키나 누르면 종료합니다..."
