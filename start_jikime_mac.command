#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo "먼저 install_mac.command 를 실행하세요."
  read -n 1 -s -r -p "아무 키나 누르면 종료합니다..."
  exit 1
fi
source .venv/bin/activate
python3 agent/app.py
