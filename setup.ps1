# Convenience wrapper for scripts\setup.ps1
# This allows running .\setup.ps1 from the root directory

& "$PSScriptRoot\scripts\setup.ps1" $args
exit $LASTEXITCODE
