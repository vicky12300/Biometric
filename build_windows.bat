@echo off
echo ================================================
echo Building Biometric Tools Manager for Windows...
echo ================================================
echo.

REM --- Clean old build files ---
echo Cleaning old build files...
if exist dist (
    rmdir /s /q dist
)
if exist build (
    rmdir /s /q build
)
if exist BiometricToolsManager.spec (
    del /f /q BiometricToolsManager.spec
)
if exist Biometric.spec (
    del /f /q Biometric.spec
)
echo Cleanup complete.
echo.

REM --- Install dependencies ---
echo Installing dependencies...
python -m pip install pywebview pyinstaller pyzk pillow
echo.

REM --- Build executable ---
echo Building executable...
python -m PyInstaller --onefile ^
    --windowed ^
    --name "Biometric" ^
    --icon bio.ico ^
    --add-data "auriga.png;." ^
    --add-data "auriga1.png;." ^
    --add-data "biometric_web_app_fixed.py;." ^
    --add-data "data_storage.py;." ^
    --add-data "adms_listener.py;." ^
    --hidden-import=webview ^
    --hidden-import=zk ^
    --hidden-import=data_storage ^
    --hidden-import=adms_listener ^
    --hidden-import=_strptime ^
    desktop_app.py
echo.

REM --- Build background executable ---
echo Building background service executable...
python -m PyInstaller background_sync_service.py ^
    --onefile ^
    --noconsole ^
    --name "background_sync_service" ^
    --add-data "data_storage.py;." ^
    --add-data "adms_listener.py;." ^
    --hidden-import=data_storage ^
    --hidden-import=adms_listener ^
    --hidden-import=_strptime 


echo.
echo Creating desktop shortcut...

REM Get the current directory (where the script is located)
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%dist\Biometric.exe"
set "ICON_PATH=%SCRIPT_DIR%bio.ico"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT_PATH=%DESKTOP%\Biometric Tools Manager.lnk"

REM Create a VBScript to generate the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%EXE_PATH%" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_DIR%dist" >> CreateShortcut.vbs
echo oLink.Description = "Biometric Tools Manager - Manage biometric devices and sync attendance data" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ICON_PATH%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

REM Run the VBScript
cscript //nologo CreateShortcut.vbs

REM Clean up the VBScript
del CreateShortcut.vbs

echo Desktop shortcut created: %SHORTCUT_PATH%
echo.

echo ================================================
echo Build complete! Check the 'dist' folder for Biometric.exe
echo Desktop shortcut created on your Desktop!
echo ================================================
pause
