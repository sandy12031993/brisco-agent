# Convenience wrapper for scripts\run.ps1
# This allows running .\run.ps1 from the root directory

& "$PSScriptRoot\scripts\run.ps1" @args
exit $LASTEXITCODE
