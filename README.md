# Naver Keyword Search (황금키워드채굴기)

네이버 키워드 분석 도구 — 월간 검색량, 연관 키워드, 블로그 문서수 조회 및 엑셀 저장.

## 기능

- **월간 검색량** — 연관 키워드 확장 조회, 문서수·경쟁율 수집
- **연관 키워드** — 검색광고 키워드 도구 연관 키워드 목록
- **문서수 조회** — 네이버 블로그 검색 문서 수

## 설정

```bash
cp .env.example .env
```

`.env` 파일에 API 키를 입력합니다. (이 파일은 Git에 올라가지 않습니다.)

## 실행 (GUI)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app_gui.py
```

## 실행 파일 빌드

자세한 내용은 [BUILD.md](BUILD.md)를 참고하세요.

- **macOS**: `./scripts/build_mac.sh` → `dist/황금키워드채굴기.app`
- **Windows**: `scripts\build_win.bat` → `dist\황금키워드채굴기.exe`

## CLI 스크립트

```bash
python 월간검색량.py
python 연관키워드검색.py
python 문서수정.py
```

## 환경 변수 (.env)

| 변수 | 설명 |
|------|------|
| `NAVER_SEARCH_ACCESS_LICENSE_KEY` | 검색광고 API 라이선스 |
| `NAVER_SEARCH_SECRET_KEY` | 검색광고 API 시크릿 |
| `NAVER_SEARCH_CUSTOMER_ID` | 광고주 ID |
| `NAVER_CLIENT_ID` | 네이버 개발자 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 개발자 Client Secret |

실행 파일(.app / .exe) 사용 시에도 **실행 파일과 같은 폴더**에 `.env`를 두세요.

## License

MIT — see [LICENSE](LICENSE).
