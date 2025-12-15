#!/bin/bash
# Build script for Linux
# Creates a standalone executable for Linux

echo "================================"
echo "Building Woop for Linux"
echo "================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller"
        exit 1
    fi
fi

echo "Cleaning previous build artifacts..."
rm -rf build dist

echo ""
echo "Building executable..."
pyinstaller woop.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "================================"
    echo "Build FAILED!"
    echo "================================"
    exit 1
fi

# Make the executable... executable
chmod +x dist/woop

echo ""
echo "================================"
echo "Build Successful!"
echo "================================"
echo ""
echo "Executable location: dist/woop"
echo ""
echo "To distribute:"
echo "1. The executable is standalone and can be copied anywhere"
echo "2. Users can run it with: ./woop"
echo "3. No Python installation required on target machine"
echo ""
echo "Note: The executable only works on Linux systems with compatible glibc"
echo ""

