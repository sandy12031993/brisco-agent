# PowerShell Test Script to verify setup is working

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Testing Migration Analysis System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Check if venv exists
Write-Host "[1/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "[PASS] Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Virtual environment not found" -ForegroundColor Red
    Write-Host "Please run .\setup.ps1 first" -ForegroundColor Yellow
    $allPassed = $false
}

Write-Host ""
Write-Host "[2/5] Testing Python in venv..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Python working: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Python not working in venv" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""
Write-Host "[3/5] Checking installed packages..." -ForegroundColor Yellow

$packages = @('rich', 'click', 'pyyaml')
foreach ($package in $packages) {
    pip show $package > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Package '$package' installed" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Package '$package' not installed" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""
Write-Host "[4/5] Testing import of custom modules..." -ForegroundColor Yellow

try {
    python -c "from utils.pattern_learner import PatternLearner; print('[PASS] PatternLearner import')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] PatternLearner import" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host "[FAIL] Custom modules not importable" -ForegroundColor Red
    $allPassed = $false
}

try {
    python -c "from analyzers.relationship_mapper import RelationshipMapper; print('[PASS] RelationshipMapper import')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] RelationshipMapper import" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host "[FAIL] RelationshipMapper import failed" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""
Write-Host "[5/5] Testing main.py execution..." -ForegroundColor Yellow
python main.py --help > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] main.py executable" -ForegroundColor Green
} else {
    Write-Host "[FAIL] main.py not executing" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""
if ($allPassed) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your setup is working correctly." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1 status" -ForegroundColor White
    Write-Host "  .\run.ps1 analyze --help" -ForegroundColor White
    Write-Host "  .\run.ps1 show-insights" -ForegroundColor White
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " SOME TESTS FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the errors above and try running .\setup.ps1 again" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue"
