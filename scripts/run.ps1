# PowerShell Run Script for PHP-to-Laravel Migration Analysis System
# Activates virtual environment and runs main.py with arguments

# Change to parent directory (.agent root)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptDir)

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run scripts\setup.ps1 first to create the virtual environment" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Run main.py with all arguments passed to this script
python main.py @args

# Capture the exit code
$exitCode = $LASTEXITCODE

# Exit with the same code as the Python script
exit $exitCode
