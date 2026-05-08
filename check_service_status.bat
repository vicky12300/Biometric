@echo off
REM Quick script to check if background service is running

echo ================================================
echo Background Service Status Check
echo ================================================
echo.

REM Check if the process is running
echo Checking for background_sync_service.exe...
tasklist /FI "IMAGENAME eq background_sync_service.exe" 2>nul | find /I "background_sync_service.exe" >nul

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Background service is RUNNING!
    echo.
    tasklist /FI "IMAGENAME eq background_sync_service.exe" /FO TABLE
    echo.
) else (
    echo.
    echo [INFO] Background service is NOT currently running.
    echo.
    echo This is normal if:
    echo - The task runs periodically (not continuously)
    echo - The service just finished a sync cycle
    echo - The task hasn't triggered yet
    echo.
)

REM Check Task Scheduler status
echo Checking Task Scheduler...
schtasks /Query /TN "BiometricBackgroundSync" /FO LIST 2>nul | findstr /C:"Status:" /C:"Last Run Time:" /C:"Next Run Time:" /C:"Last Result:"

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Task "BiometricBackgroundSync" not found in Task Scheduler!
    echo Please run setup_windows_task.bat to create it.
    echo.
) else (
    echo.
)

REM Check if log file exists
set "LOG_FILE=%APPDATA%\BiometricToolsManager\auto_sync_service.log"
echo Checking log file...
if exist "%LOG_FILE%" (
    echo [SUCCESS] Log file found: %LOG_FILE%
    echo.
    echo Last 10 lines of log:
    echo ----------------------------------------
    powershell -Command "Get-Content '%LOG_FILE%' -Tail 10"
    echo ----------------------------------------
    echo.
) else (
    echo [WARNING] Log file not found: %LOG_FILE%
    echo The service may not have run yet.
    echo.
)

echo ================================================
echo Status check complete!
echo ================================================
echo.
pause
