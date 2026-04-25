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

set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=start"

set "OPEN_URLS_ARG="
if /I "%ACTION%"=="start" set "OPEN_URLS_ARG=-OpenUrls"
if /I "%ACTION%"=="restart" set "OPEN_URLS_ARG=-OpenUrls"
if /I "%ACTION%"=="rebuild" set "OPEN_URLS_ARG=-OpenUrls"

powershell -ExecutionPolicy Bypass -File "%POWERSHELL_SCRIPT%" -Action "%ACTION%" %OPEN_URLS_ARG%
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
  echo.
  echo FuelMind konnte nicht erfolgreich ausgefuehrt werden.
  pause
  exit /b %EXITCODE%
)

echo.
echo FuelMind-Aktion abgeschlossen: %ACTION%
pause
