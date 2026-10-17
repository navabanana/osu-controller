@echo off
chcp 65001 >nul
where python >nul 2>nul || (echo Installe Python 3 depuis python.org, en cochant "Add python.exe to PATH", puis relance. & pause & exit /b)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --onefile --noconsole --name DualSenseOsu dualsense_osu.py
echo.
echo Termine : ton programme est dans dist\DualSenseOsu.exe
pause
