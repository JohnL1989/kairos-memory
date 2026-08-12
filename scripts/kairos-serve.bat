@echo off
rem Kairos Memory Service autostart (Windows Startup folder)
rem SYSTEM-less: runs as current user; all path vars explicit (HOME differs per context)
cd /d D:\projects\kairos-memory
set KAIROS_DATA_DIR=C:\Users\54111\.kairos
set KAIROS_DB_URL=sqlite:///C:/Users/54111/.kairos/kairos.db
set PYTHONPATH=
set KAIROS_BASE_URL=http://127.0.0.1:8010
.venv\Scripts\kairos.exe serve
