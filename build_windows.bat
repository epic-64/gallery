@echo off
REM Build script for Windows
REM Creates a standalone executable for Windows

echo ================================
echo Building Woop for Windows
echo ================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        exit /b 1
    )
)

echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building executable...
pyinstaller woop.spec

if errorlevel 1 (
    echo.
    echo ================================
    echo Build FAILED!
    echo ================================
    exit /b 1
)

echo.
echo ================================
echo Build Successful!
echo ================================
echo.
echo Executable location: dist\woop.exe
echo.
echo To distribute:
echo 1. The executable is standalone and can be copied anywhere
echo 2. Users can run it by double-clicking woop.exe
echo 3. No Python installation required on target machine
echo.

pause

