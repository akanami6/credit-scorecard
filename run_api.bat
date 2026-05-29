@echo off
chcp 65001 >nul
cd /d "F:\claude\credit-scorecard"
echo ============================================
echo   Credit Scorecard API
echo   FastAPI on http://127.0.0.1:8000
echo   Swagger: http://127.0.0.1:8000/docs
echo ============================================
echo.
.\venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
pause
