# Scripts Directory

This directory contains all executable scripts for the Migration Analysis System.

## Main Scripts

### Setup Scripts
- **setup.bat** - Windows batch script for initial setup
- **setup.ps1** - PowerShell script for initial setup (recommended)
- **setup_wizard.py** - Interactive Python setup wizard

### Run Scripts
- **run.bat** - Windows batch script to run the analyzer
- **run.ps1** - PowerShell script to run the analyzer (recommended)

### Test Scripts (in tests/)
- **TEST_SETUP.bat** - Batch script to verify setup
- **TEST_SETUP.ps1** - PowerShell script to verify setup

## Usage

### From .agent root directory:
```powershell
# Setup
.\scripts\setup.ps1

# Run analysis
.\scripts\run.ps1 analyze warehouse/cycle-count --type route --smart
```

### Convenience wrappers in root:
For easier access, use the wrapper scripts in the .agent root directory:
```powershell
# Setup (calls scripts\setup.ps1)
.\setup.ps1

# Run (calls scripts\run.ps1)
.\run.ps1 analyze warehouse/cycle-count --type route --smart
```

## Notes

- All scripts automatically change directory to .agent root before execution
- Virtual environment and dependencies are managed in the parent directory
- PowerShell scripts (.ps1) are recommended over batch scripts (.bat) for better error handling
