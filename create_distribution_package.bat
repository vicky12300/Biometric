@echo off
REM ========================================================================
REM Create Production Distribution Package
REM ========================================================================
REM This script creates a ready-to-distribute package with everything needed
REM ========================================================================

echo ================================================
echo Creating Production Distribution Package
echo ================================================
echo.

REM Step 1: Build the executables
echo Step 1: Building standalone executables...
echo (This includes Python and all dependencies - no installation needed by users)
echo.
call build_windows.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to build executables!
    pause
    exit /b 1
)
echo.

REM Step 2: Create distribution folder
set "DIST_FOLDER=BiometricToolsManager_v1.0_Standalone"
echo Step 2: Creating distribution folder: %DIST_FOLDER%
if exist "%DIST_FOLDER%" rmdir /s /q "%DIST_FOLDER%"
mkdir "%DIST_FOLDER%"
echo.

REM Step 3: Copy executables
echo Step 3: Copying standalone executables...
copy "dist\Biometric.exe" "%DIST_FOLDER%\" >nul
copy "dist\background_sync_service.exe" "%DIST_FOLDER%\" >nul
echo   - Biometric.exe (includes Python + all libraries)
echo   - background_sync_service.exe (includes Python + all libraries)
echo.

REM Step 4: Copy resources
echo Step 4: Copying resources...
copy "auriga.png" "%DIST_FOLDER%\" >nul
copy "auriga1.png" "%DIST_FOLDER%\" >nul
copy "bio.ico" "%DIST_FOLDER%\" >nul
echo   - Images and icons
echo.

REM Step 5: Copy setup scripts
echo Step 5: Copying setup scripts...
copy "setup_windows_task.bat" "%DIST_FOLDER%\" >nul
copy "check_service_status.bat" "%DIST_FOLDER%\" >nul
echo   - Background service setup script
echo   - Status checker
echo.

REM Step 6: Copy documentation
echo Step 6: Copying documentation...
copy "README.md" "%DIST_FOLDER%\" >nul
copy "BACKGROUND_SERVICE_SETUP.md" "%DIST_FOLDER%\" >nul 2>nul
copy "PRODUCTION_READY.md" "%DIST_FOLDER%\" >nul 2>nul
echo   - User documentation
echo.

REM Step 7: Create quick start guide
echo Step 7: Creating Quick Start Guide for users...
(
echo ================================================
echo Biometric Tools Manager - Quick Start Guide
echo ================================================
echo.
echo IMPORTANT: This software is 100%% STANDALONE!
echo - NO Python installation required
echo - NO dependencies required
echo - NO manual configuration required
echo.
echo Just run Biometric.exe and you're ready to go!
echo.
echo ================================================
echo Installation Steps:
echo ================================================
echo.
echo 1. Extract this folder to any location on your computer
echo    Example: C:\Program Files\BiometricToolsManager
echo.
echo 2. Double-click "Biometric.exe" to launch the application
echo.
echo 3. ^(Optional^) Setup background sync service:
echo    - Right-click "setup_windows_task.bat"
echo    - Select "Run as administrator"
echo    - Choose your sync interval
echo.
echo That's it! No other installation needed.
echo.
echo ================================================
echo What's Included:
echo ================================================
echo.
echo - Biometric.exe: Main application
echo   ^(Includes Python interpreter and all libraries^)
echo.
echo - background_sync_service.exe: Background sync service
echo   ^(Runs automatically to sync data to ERP^)
echo.
echo - setup_windows_task.bat: Setup background service
echo   ^(Creates scheduled task for automatic syncing^)
echo.
echo - check_service_status.bat: Check if service is running
echo.
echo ================================================
echo System Requirements:
echo ================================================
echo.
echo - Windows 10 or Windows 11 ^(64-bit^)
echo - 100 MB free disk space
echo - Internet connection ^(for ERP sync^)
echo.
echo NO Python, NO pip, NO dependencies required!
echo.
echo ================================================
echo Support:
echo ================================================
echo.
echo For help, see README.md
echo.
) > "%DIST_FOLDER%\QUICK_START.txt"
echo   - Quick Start Guide created
echo.

REM Step 8: Create desktop shortcut helper
echo Step 8: Creating desktop shortcut helper...
(
echo @echo off
echo set SCRIPT=%%TEMP%%\CreateShortcut.vbs
echo echo Set oWS = WScript.CreateObject^("WScript.Shell"^) ^> %%SCRIPT%%
echo echo sLinkFile = oWS.SpecialFolders^("Desktop"^) ^& "\Biometric Tools Manager.lnk" ^>^> %%SCRIPT%%
echo echo Set oLink = oWS.CreateShortcut^(sLinkFile^) ^>^> %%SCRIPT%%
echo echo oLink.TargetPath = "%%~dp0Biometric.exe" ^>^> %%SCRIPT%%
echo echo oLink.WorkingDirectory = "%%~dp0" ^>^> %%SCRIPT%%
echo echo oLink.IconLocation = "%%~dp0bio.ico" ^>^> %%SCRIPT%%
echo echo oLink.Description = "Biometric Tools Manager" ^>^> %%SCRIPT%%
echo echo oLink.Save ^>^> %%SCRIPT%%
echo cscript //nologo %%SCRIPT%%
echo del %%SCRIPT%%
echo echo Desktop shortcut created successfully!
echo pause
) > "%DIST_FOLDER%\Create_Desktop_Shortcut.bat"
echo   - Desktop shortcut helper created
echo.

REM Step 9: Show summary
echo ================================================
echo SUCCESS! Distribution package created!
echo ================================================
echo.
echo Package location: %DIST_FOLDER%
echo.
echo Package contents:
echo   - Standalone executables (no Python needed!)
echo   - All resources and images
echo   - Setup scripts
echo   - Documentation
echo   - Quick Start Guide
echo.
echo File sizes:
dir "%DIST_FOLDER%\*.exe" | find "Biometric"
dir "%DIST_FOLDER%\*.exe" | find "background"
echo.
echo ================================================
echo Distribution Options:
echo ================================================
echo.
echo Option 1: ZIP File (Simplest)
echo   - Right-click "%DIST_FOLDER%" folder
echo   - Select "Send to" -^> "Compressed (zipped) folder"
echo   - Distribute the .zip file
echo.
echo Option 2: Professional Installer
echo   - Run "build_professional_installer.bat"
echo   - Creates single .exe installer
echo.
echo ================================================
echo What Users Need to Do:
echo ================================================
echo.
echo 1. Extract the ZIP file
echo 2. Double-click Biometric.exe
echo 3. Done!
echo.
echo NO Python installation required!
echo NO dependencies required!
echo 100%% standalone and ready to use!
echo.
pause
