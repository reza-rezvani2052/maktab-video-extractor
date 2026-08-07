@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Virtual environment not found: %PYTHON%
    echo.
    echo Run the following commands first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

"%PYTHON%" main.py %*
if errorlevel 1 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
)
pause
endlocal

