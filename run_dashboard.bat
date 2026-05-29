@echo off
chcp 65001 >nul
cd /d "F:\claude\credit-scorecard"
echo ============================================
echo   Credit Scorecard Dashboard
echo   Streamlit on http://127.0.0.1:8501
echo ============================================
echo.
.\venv\Scripts\python.exe -m streamlit run dashboard/app.py --server.port 8501
pause
