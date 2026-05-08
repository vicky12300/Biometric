@echo off
REM ========================================================================
REM Windows Task Scheduler Setup for Biometric Background Sync Service
REM ========================================================================
REM This script creates a Windows scheduled task to run the background
REM sync service at a configurable interval.
REM ========================================================================

echo ================================================
echo Setting up Windows Task Scheduler
echo ================================================
echo.

REM Get the current directory where the EXE is located
set "EXE_PATH=%~dp0dist\background_sync_service.exe"
set "TASK_NAME=BiometricBackgroundSync"

REM Check if the EXE exists
if not exist "%EXE_PATH%" (
    echo ERROR: background_sync_service.exe not found in dist folder!
    echo Please run build_windows.bat first to create the executable.
    echo.
    pause
    exit /b 1
)

echo Found executable at: %EXE_PATH%
echo.

REM Display menu for interval selection
echo Select the sync interval:
echo.
echo === Minute-based Intervals ===
echo 1. Every 1 minute
echo 2. Every 5 minutes (Recommended)
echo 3. Every 10 minutes
echo 4. Every 15 minutes
echo 5. Every 30 minutes
echo.
echo === Hour-based Intervals ===
echo 6. Every 1 hour
echo 7. Every 3 hours
echo 8. Every 6 hours
echo 9. Every 12 hours
echo 10. Daily at midnight
echo.
echo === Other Options ===
echo 11. Custom interval
echo 12. Remove existing task
echo.

set /p choice="Enter your choice (1-12): "

if "%choice%"=="1" set INTERVAL=1
if "%choice%"=="2" set INTERVAL=5
if "%choice%"=="3" set INTERVAL=10
if "%choice%"=="4" set INTERVAL=15
if "%choice%"=="5" set INTERVAL=30
if "%choice%"=="6" set INTERVAL=60
if "%choice%"=="7" set INTERVAL=180
if "%choice%"=="8" set INTERVAL=360
if "%choice%"=="9" set INTERVAL=720
if "%choice%"=="10" set INTERVAL=1440
if "%choice%"=="11" (
    set /p INTERVAL="Enter custom interval in minutes: "
)
if "%choice%"=="12" (
    echo.
    echo Removing existing task and stopping any running processes...
    echo.
    
    REM Kill any running background_sync_service.exe processes
    echo Stopping background sync service processes...
    taskkill /F /IM background_sync_service.exe >nul 2>&1
    if %errorlevel% equ 0 (
        echo Background service processes stopped.
    ) else (
        echo No running background service processes found.
    )
    echo.
    
    REM Delete the scheduled task
    echo Removing scheduled task...
    schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
    if %errorlevel% equ 0 (
        echo Task removed successfully!
    ) else (
        echo No existing task found to remove.
    )
    echo.
    pause
    exit /b 0
)

echo.
echo Creating scheduled task to run every %INTERVAL% minute(s)...
echo.

REM Check if task already exists and remove it automatically
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found existing task "%TASK_NAME%"
    
    REM Kill any running background_sync_service.exe processes
    echo Stopping any running background service processes...
    taskkill /F /IM background_sync_service.exe >nul 2>&1
    
    REM Wait for processes to fully terminate
    timeout /t 2 /nobreak >nul
    
    echo Removing existing task before creating new one...
    schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
    echo Existing task removed.
    echo.
)

REM Create a temporary XML file with boot trigger and interval trigger
set "TEMP_XML=%TEMP%\BiometricBackgroundSync.xml"

echo Creating task configuration with boot trigger...
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>Biometric Background Sync Service - Runs every %INTERVAL% minute^(s^) and on system startup^</Description^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<TimeTrigger^>
echo       ^<Repetition^>
echo         ^<Interval^>PT%INTERVAL%M^</Interval^>
echo         ^<StopAtDurationEnd^>false^</StopAtDurationEnd^>
echo       ^</Repetition^>
echo       ^<StartBoundary^>2026-01-01T00:00:00^</StartBoundary^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</TimeTrigger^>
echo     ^<BootTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</BootTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal^>
echo       ^<LogonType^>InteractiveToken^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<RunOnlyIfNetworkAvailable^>false^</RunOnlyIfNetworkAvailable^>
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo   ^</Settings^>
echo   ^<Actions^>
echo     ^<Exec^>
echo       ^<Command^>%EXE_PATH%^</Command^>
echo       ^<Arguments^>--force^</Arguments^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%TEMP_XML%"

REM Import the XML to create the task
schtasks /Create /TN "%TASK_NAME%" /XML "%TEMP_XML%" /F

REM Capture the error level immediately after task creation
set TASK_RESULT=%errorlevel%

REM Clean up temp file
del "%TEMP_XML%" >nul 2>&1

echo.
if %TASK_RESULT% equ 0 (
    echo ================================================
    echo SUCCESS! Task created successfully!
    echo ================================================
    echo.
    echo Task Name: %TASK_NAME%
    echo Interval: Every %INTERVAL% minute(s)
    echo Executable: %EXE_PATH%
    echo.
    
    REM Start the background service directly (not through Task Scheduler)
    REM This ensures it starts running immediately, not in Queued state
    echo Starting the background service now...
    echo.
    
    REM Execute the service directly in the background
    start "" /B "%EXE_PATH%" --force
    
    REM Wait 2 seconds for the process to start
    timeout /t 2 /nobreak >nul
    
    REM Check if the process is actually running
    tasklist /FI "IMAGENAME eq background_sync_service.exe" 2>nul | find /I "background_sync_service.exe" >nul
    if %errorlevel% equ 0 (
        echo ================================================
        echo Background service is now RUNNING!
        echo ================================================
        echo.
        echo You can see it in Task Manager under "Background processes"
        echo The service is running NOW and will continue via Task Scheduler.
    ) else (
        echo Note: Service may not have started. Check Task Manager.
        echo The Task Scheduler will start it automatically at the scheduled time.
    )
    echo.
    
    echo The background sync service will now run automatically:
    echo - Every %INTERVAL% minute(s) in the background
    echo - On system startup/boot
    echo.
    echo To manage this task:
    echo - Open Task Scheduler (taskschd.msc)
    echo - Look for "%TASK_NAME%" in the Task Scheduler Library
    echo.
    echo To stop and remove this task, run this script again and select option 12.
    echo.
) else (
    echo ================================================
    echo ERROR: Failed to create scheduled task!
    echo ================================================
    echo.
    echo Error Code: %TASK_RESULT%
    echo.
    echo Please run this script as Administrator:
    echo 1. Right-click on this file
    echo 2. Select "Run as administrator"
    echo 3. Click "Yes" when prompted
    echo.
    echo If already running as Administrator, check:
    echo - Task Scheduler service is running
    echo - No permission issues with the executable path
    echo - XML file was created correctly
    echo.
)

pause
