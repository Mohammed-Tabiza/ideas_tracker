@echo off
setlocal
cd /d %~dp0

if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

start "ideas-tracker-backend" cmd /k "python -m uvicorn app.main:app --reload --port 8000"
start "ideas-tracker-frontend" cmd /k "npm run dev"
