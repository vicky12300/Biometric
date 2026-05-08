@echo off
REM Windows Python Cache Cleanup Script
REM This removes all .pyc files that may contain old cached code

echo ========================================
echo Python Cache Cleanup for Windows
echo ========================================
echo.

echo [1] Checking Python version...
python --version
echo.

echo [2] Stopping any running Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak >nul
echo.

echo [3] Removing Python cache files...
if exist __pycache__ (
    rmdir /S /Q __pycache__
    echo    Removed __pycache__ directory
)

if exist *.pyc (
    del /F /Q *.pyc
    echo    Removed .pyc files
)

if exist adms_listener.pyc (
    del /F /Q adms_listener.pyc
    echo    Removed adms_listener.pyc
)

echo.
echo [4] Verifying adms_listener.py has no type hints...
findstr /C:"Optional" adms_listener.py >nul
if %errorlevel% equ 0 (
    echo    ❌ ERROR: adms_listener.py still contains "Optional"
    echo    The file was not properly updated!
    echo.
    echo    Please copy the updated adms_listener.py from Linux
    pause
    exit /b 1
) else (
    echo    ✅ OK: No "Optional" found in adms_listener.py
)

findstr /C:"dict | None" adms_listener.py >nul
if %errorlevel% equ 0 (
    echo    ❌ ERROR: adms_listener.py still contains "dict | None"
    echo    The file was not properly updated!
    echo.
    echo    Please copy the updated adms_listener.py from Linux
    pause
    exit /b 1
) else (
    echo    ✅ OK: No "dict | None" found in adms_listener.py
)

echo.
echo [5] Testing import...
python -c "import adms_listener; print('✅ Import successful')" 2>error.txt
if %errorlevel% neq 0 (
    echo    ❌ Import failed! Error:
    type error.txt
    del error.txt
    echo.
    pause
    exit /b 1
) else (
    echo    ✅ Import successful
    del error.txt 2>nul
)

echo.
echo ========================================
echo ✅ Cleanup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Start the biometric application
echo 2. Test ADMS fetch from browser
echo.
pause
