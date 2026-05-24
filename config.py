"""
프로젝트 루트의 .env 파일에서 API 키를 불러옵니다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]


def get_project_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def load_env() -> None:
    env_path = get_project_dir() / ".env"
    if load_dotenv is not None:
        load_dotenv(env_path)
    elif env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"환경 변수 '{name}'이(가) 없습니다.\n"
            f".env.example을 복사해 .env 파일을 만들고 값을 입력해 주세요.\n"
            f"  cp .env.example .env"
        )
    return value


load_env()

# 네이버 검색광고 API
NAVER_SEARCH_ACCESS_LICENSE_KEY = require_env("NAVER_SEARCH_ACCESS_LICENSE_KEY")
NAVER_SEARCH_SECRET_KEY = require_env("NAVER_SEARCH_SECRET_KEY")
NAVER_SEARCH_CUSTOMER_ID = require_env("NAVER_SEARCH_CUSTOMER_ID")

# 네이버 검색 API (블로그 문서수)
NAVER_CLIENT_ID = require_env("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = require_env("NAVER_CLIENT_SECRET")

# 기존 모듈 호환 별칭
API_KEY = NAVER_SEARCH_ACCESS_LICENSE_KEY
SECRET_KEY = NAVER_SEARCH_SECRET_KEY
CUSTOMER_ID = NAVER_SEARCH_CUSTOMER_ID
BLOG_CLIENT_ID = NAVER_CLIENT_ID
BLOG_CLIENT_SECRET = NAVER_CLIENT_SECRET
CLIENT_ID = NAVER_CLIENT_ID
CLIENT_SECRET = NAVER_CLIENT_SECRET
