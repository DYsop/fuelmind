@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "POWERSHELL_SCRIPT=%SCRIPT_DIR%fuelmind-nas.ps1"

if not exist "%POWERSHELL_SCRIPT%" (
  echo Fehler: fuelmind-nas.ps1 wurde nicht gefunden:
  echo %POWERSHELL_SCRIPT%
  pause
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%POWERSHELL_SCRIPT%" -Action "start" -OpenUrls
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
  echo.
  echo FuelMind konnte nicht erfolgreich gestartet werden.
  pause
  exit /b %EXITCODE%
)

echo.
echo FuelMind wurde gestartet.
pause
