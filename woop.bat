@echo off
REM Double-click this file to launch woop on Windows.
REM It sets up the environment automatically on first run.
setlocal

cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo uv is required to run woop but was not found.
    echo.
    echo Install it once by running this in PowerShell, then double-click again:
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 ^| iex"
    echo.
    pause
    exit /b 1
)

REM "uv run" creates the environment, installs dependencies, and launches woop.
uv run python -m woop
if errorlevel 1 (
    echo.
    echo woop exited with an error.
    pause
)
