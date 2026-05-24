#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 가상환경 준비 (tkinter 포함 Python 필요)"
PYTHON="${PYTHON:-/opt/homebrew/bin/python3.13}"
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
  echo "tkinter가 없습니다. macOS: brew install python-tk@3.13" >&2
  exit 1
fi
rm -rf .venv
"$PYTHON" -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "==> macOS 앱 빌드"
pyinstaller --noconfirm --clean 황금키워드채굴기.spec

OUT="$ROOT/dist/황금키워드채굴기.app"
if [[ -d "$OUT" ]]; then
  echo ""
  echo "빌드 완료: $OUT"
  echo "실행: open \"$OUT\""
else
  echo "빌드 실패" >&2
  exit 1
fi
