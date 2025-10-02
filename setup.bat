@echo off
REM Convenience wrapper for scripts\setup.bat
REM This allows running setup.bat from the root directory

call "%~dp0scripts\setup.bat" %*
exit /b %errorlevel%
