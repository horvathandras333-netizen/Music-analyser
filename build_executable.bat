@echo off
title Build LoopForge Executable
echo Building LoopForge portable standalone executable...
python "%~dp0build_portable.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)
echo.
echo Build complete! Executable is located in dist\LoopForge.exe
pause
