@echo off
REM Run script for PHP-to-Laravel Migration Analysis System
REM Activates virtual environment and runs main.py with arguments

REM Change to parent directory (.agent root)
cd /d "%~dp0.."

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run scripts\setup.bat first to create the virtual environment
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment silently
call venv\Scripts\activate.bat

REM Run main.py with all arguments passed to this batch file
python main.py %*

REM Capture the exit code
set EXIT_CODE=%errorlevel%

REM Deactivate virtual environment (optional, as closing terminal does this)
REM call venv\Scripts\deactivate.bat

REM Exit with the same code as the Python script
exit /b %EXIT_CODE%
