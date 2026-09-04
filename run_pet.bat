@echo off
rem 电脑管家桌宠启动器（用 pythonw 不弹控制台）
cd /d "%~dp0"
start "" "%~dp0venv\Scripts\pythonw.exe" -m pcpet.main
