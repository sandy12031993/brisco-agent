@echo off
REM Quick test script to verify setup is working

echo.
echo ========================================
echo  Testing Migration Analysis System
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking virtual environment...
if exist "venv\" (
    echo [PASS] Virtual environment exists
) else (
    echo [FAIL] Virtual environment not found
    exit /b 1
)

echo.
echo [2/5] Testing Python in venv...
call venv\Scripts\activate.bat
python --version
if errorlevel 1 (
    echo [FAIL] Python not working in venv
    exit /b 1
) else (
    echo [PASS] Python working
)

echo.
echo [3/5] Checking installed packages...
pip show rich >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Package 'rich' not installed
    exit /b 1
) else (
    echo [PASS] Package 'rich' installed
)

pip show click >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Package 'click' not installed
    exit /b 1
) else (
    echo [PASS] Package 'click' installed
)

pip show pyyaml >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Package 'pyyaml' not installed
    exit /b 1
) else (
    echo [PASS] Package 'pyyaml' installed
)

echo.
echo [4/5] Testing import of custom modules...
python -c "from utils.pattern_learner import PatternLearner; print('[PASS] PatternLearner import')" 2>nul
if errorlevel 1 (
    echo [FAIL] Custom modules not importable
    exit /b 1
)

python -c "from analyzers.relationship_mapper import RelationshipMapper; print('[PASS] RelationshipMapper import')" 2>nul
if errorlevel 1 (
    echo [FAIL] RelationshipMapper import failed
    exit /b 1
)

echo.
echo [5/5] Testing main.py execution...
python main.py --version >nul 2>&1
if errorlevel 1 (
    REM --version might not exist, try --help instead
    python main.py --help >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] main.py not executing
        exit /b 1
    ) else (
        echo [PASS] main.py executable
    )
) else (
    echo [PASS] main.py executable
)

echo.
echo ========================================
echo  ALL TESTS PASSED!
echo ========================================
echo.
echo Your setup is working correctly.
echo.
echo Next steps:
echo   run.bat status
echo   run.bat analyze --help
echo   run.bat show-insights
echo.
pause
