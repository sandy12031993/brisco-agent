@echo off
REM Setup script for PHP-to-Laravel Migration Analysis System
REM Creates virtual environment and installs dependencies

echo.
echo ========================================
echo  Migration Analysis System - Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

REM Check if venv already exists
if exist "venv\" (
    echo.
    echo [WARNING] Virtual environment already exists at: venv\
    echo.
    set /p "RECREATE=Do you want to recreate it? This will delete existing venv (y/N): "
    if /i "%RECREATE%"=="y" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo [INFO] Keeping existing virtual environment
        goto :skip_venv_creation
    )
)

echo.
echo [2/4] Creating virtual environment...
python -m venv venv

if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    echo Try: python -m pip install --upgrade pip
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment created at: venv\

:skip_venv_creation

echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment activated

echo.
echo [4/4] Installing dependencies...
echo This may take a few minutes...
echo.

REM Upgrade pip first
python -m pip install --upgrade pip setuptools wheel

REM Install requirements
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install some dependencies
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Virtual environment created at: venv\
echo.
echo Next steps:
echo   1. Run: run.bat status
echo   2. Try: run.bat analyze --help
echo.
echo To manually activate the virtual environment:
echo   venv\Scripts\activate.bat
echo.
pause
