@echo off
REM ========================================================================
REM Quick Start - Biometric Background Service
REM ========================================================================
REM This script provides a quick menu to build and setup the background
REM sync service with Windows Task Scheduler.
REM ========================================================================

:MENU
cls
echo ================================================
echo Biometric Background Sync Service - Quick Start
echo ================================================
echo.
echo What would you like to do?
echo.
echo 1. Build executables (first time setup)
echo 2. Setup Windows Task Scheduler (auto-start service)
echo 3. Test background service manually
echo 4. View service logs
echo 5. Remove scheduled task
echo 6. Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto BUILD
if "%choice%"=="2" goto SETUP_TASK
if "%choice%"=="3" goto TEST_SERVICE
if "%choice%"=="4" goto VIEW_LOGS
if "%choice%"=="5" goto REMOVE_TASK
if "%choice%"=="6" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:BUILD
echo.
echo ================================================
echo Building Executables...
echo ================================================
echo.
call build_windows.bat
echo.
echo Build complete!
echo.
pause
goto MENU

:SETUP_TASK
echo.
echo ================================================
echo Setting up Windows Task Scheduler...
echo ================================================
echo.

REM Check if executable exists
if not exist "dist\background_sync_service.exe" (
    echo ERROR: background_sync_service.exe not found!
    echo Please build the executables first (Option 1).
    echo.
    pause
    goto MENU
)

call setup_windows_task.bat
goto MENU

:TEST_SERVICE
echo.
echo ================================================
echo Testing Background Service...
echo ================================================
echo.

if not exist "dist\background_sync_service.exe" (
    echo ERROR: background_sync_service.exe not found!
    echo Please build the executables first (Option 1).
    echo.
    pause
    goto MENU
)

echo Starting background service manually...
echo Press Ctrl+C to stop the service.
echo.
echo Logs will be saved to:
echo %APPDATA%\BiometricToolsManager\auto_sync_service.log
echo.
echo Running with --force flag (same as Task Scheduler)
echo.

cd dist
start background_sync_service.exe --force
cd ..

echo.
echo Service started! Check the log file for output.
echo.
pause
goto MENU

:VIEW_LOGS
echo.
echo ================================================
echo Viewing Service Logs...
echo ================================================
echo.

set "LOG_FILE=%APPDATA%\BiometricToolsManager\auto_sync_service.log"

if exist "%LOG_FILE%" (
    notepad "%LOG_FILE%"
) else (
    echo Log file not found: %LOG_FILE%
    echo.
    echo The service may not have run yet, or the log directory
    echo doesn't exist. Try running the service first (Option 3).
    echo.
    pause
)

goto MENU

:REMOVE_TASK
echo.
echo ================================================
echo Removing Scheduled Task...
echo ================================================
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

REM Remove the scheduled task
schtasks /Query /TN "BiometricBackgroundSync" >nul 2>&1
if %errorlevel% neq 0 (
    echo Task "BiometricBackgroundSync" not found.
    echo Nothing to remove.
) else (
    schtasks /Delete /TN "BiometricBackgroundSync" /F
    if %errorlevel% equ 0 (
        echo Task removed successfully!
    ) else (
        echo Failed to remove task. Please run as Administrator.
    )
)

echo.
pause
goto MENU

:EXIT
echo.
echo Goodbye!
timeout /t 1 >nul
exit /b 0
