#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub 로그인이 필요합니다."
  echo "  gh auth login -h github.com -p https -w"
  exit 1
fi

REPO_NAME="${REPO_NAME:-golden-keyword-miner}"
VISIBILITY="${VISIBILITY:-public}"

if git remote get-url origin >/dev/null 2>&1; then
  echo "==> origin 원격이 이미 있습니다. push만 진행합니다."
  git push -u origin main
else
  echo "==> GitHub 저장소 생성 및 push: $REPO_NAME"
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
fi

echo ""
echo "완료: $(gh repo view --json url -q .url)"
