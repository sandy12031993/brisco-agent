@echo off
REM Convenience wrapper for scripts\run.bat
REM This allows running run.bat from the root directory

call "%~dp0scripts\run.bat" %*
exit /b %errorlevel%
