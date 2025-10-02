# PowerShell Setup Script for PHP-to-Laravel Migration Analysis System
# Creates virtual environment and installs dependencies

# Change to parent directory (.agent root)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptDir)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Migration Analysis System - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/4] Checking Python version..." -ForegroundColor Yellow
    Write-Host $pythonVersion -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if venv already exists
if (Test-Path "venv") {
    Write-Host ""
    Write-Host "[WARNING] Virtual environment already exists at: venv\" -ForegroundColor Yellow
    Write-Host ""
    $recreate = Read-Host "Do you want to recreate it? This will delete existing venv (y/N)"
    if ($recreate -eq "y" -or $recreate -eq "Y") {
        Write-Host "[INFO] Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    } else {
        Write-Host "[INFO] Keeping existing virtual environment" -ForegroundColor Green
        $skipVenvCreation = $true
    }
}

if (-not $skipVenvCreation) {
    Write-Host ""
    Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Try: python -m pip install --upgrade pip" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }

    Write-Host "[SUCCESS] Virtual environment created at: venv\" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/4] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to allow script execution:" -ForegroundColor Yellow
    Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[SUCCESS] Virtual environment activated" -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

# Upgrade pip first
python -m pip install --upgrade pip setuptools wheel --quiet

# Install requirements
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to install some dependencies" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Virtual environment created at: venv\" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\run.ps1 status" -ForegroundColor White
Write-Host "  2. Try: .\run.ps1 analyze --help" -ForegroundColor White
Write-Host ""
Write-Host "To manually activate the virtual environment:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"
