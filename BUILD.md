# 실행 파일 빌드 가이드

## GUI 앱 실행 (개발)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app_gui.py
```

## macOS (.app)

먼저 tkinter 지원 Python이 필요합니다.

```bash
brew install python-tk@3.13
chmod +x scripts/build_mac.sh
./scripts/build_mac.sh
```

결과: `dist/황금키워드채굴기.app`

실행:

```bash
open dist/황금키워드채굴기.app
```

## Windows (.exe)

**Windows PC**에서 아래를 실행하세요. (Mac에서는 exe를 직접 만들 수 없습니다.)

```bat
scripts\build_win.bat
```

결과: `dist\황금키워드채굴기.exe`

## API 키 (.env)

빌드 후 실행 파일과 **같은 폴더**에 `.env`를 복사합니다.

```bash
cp .env.example dist/황금키워드채굴기.app/Contents/MacOS/.env   # macOS 앱 내부
# 또는 dist 폴더 옆에 .env 배치 (onedir 빌드 시 실행 파일 위치 기준)
```

Windows:

```bat
copy .env.example dist\.env
```

## 참고

- 엑셀 파일은 실행 파일이 있는 폴더에 저장됩니다.
- macOS에서 처음 실행 시 보안 경고가 나오면: 시스템 설정 → 개인정보 보호 및 보안 → 허용
- `.env`는 Git에 포함되지 않습니다. `.env.example`만 저장소에 올라갑니다.
