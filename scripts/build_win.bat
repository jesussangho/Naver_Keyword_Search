@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0.."

echo ==^> 가상환경 준비
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ==^> Windows exe 빌드
pyinstaller --noconfirm --clean --windowed --onefile ^
  --name "황금키워드채굴기" ^
  --collect-all customtkinter ^
  --hidden-import openpyxl ^
  app_gui.py

if exist "dist\황금키워드채굴기.exe" (
  echo.
  echo 빌드 완료: dist\황금키워드채굴기.exe
) else (
  echo 빌드 실패
  exit /b 1
)

endlocal
