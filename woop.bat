@echo off
setlocal

:: Activate the virtual environment
call .venv\Scripts\activate.bat

:: Run the script
python src\main.py