@echo off
chcp 65001 >nul
echo ============================================
echo   Starting Credit Scorecard System...
echo ============================================
echo.
echo Starting API server on http://127.0.0.1:8000 ...
start "CreditScorecard-API" cmd /k "cd /d F:\claude\credit-scorecard && .\venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"
echo.
echo Starting Dashboard on http://127.0.0.1:8501 ...
start "CreditScorecard-Dashboard" cmd /k "cd /d F:\claude\credit-scorecard && .\venv\Scripts\python.exe -m streamlit run dashboard/app.py --server.port 8501"
echo.
echo Both services are starting in separate windows.
echo API Docs:  http://127.0.0.1:8000/docs
echo Dashboard: http://127.0.0.1:8501
echo.
pause
