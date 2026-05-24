#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub 로그인이 필요합니다."
  echo "  gh auth login -h github.com -p https -w"
  exit 1
fi

REPO_NAME="${REPO_NAME:-Naver_Keyword_Search}"
REMOTE_URL="${REMOTE_URL:-https://github.com/jesussangho/Naver_Keyword_Search.git}"
VISIBILITY="${VISIBILITY:-public}"

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REMOTE_URL"
fi

echo "==> push: $REMOTE_URL"
git push -u origin main

echo ""
echo "완료: $(gh repo view --json url -q .url)"
