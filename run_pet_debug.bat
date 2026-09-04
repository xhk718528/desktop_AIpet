@echo off
rem 带控制台运行桌宠，用于排查问题：报错会直接显示在窗口里
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" -m pcpet.main
pause
