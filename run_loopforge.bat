@echo off
title LoopForge Launcher
echo Launching LoopForge Application...
python "%~dp0main.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] LoopForge exited with an error code.
    pause
)
