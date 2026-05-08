@echo off
REM Windows Firewall Configuration for Biometric ADMS Listener
REM Run this script as Administrator to allow port 8000 for ADMS push protocol

echo ========================================
echo Biometric ADMS Firewall Configuration
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Configuring Windows Firewall for ADMS listener (port 8000)...
echo.

REM Remove existing rules (if any)
netsh advfirewall firewall delete rule name="Biometric ADMS Listener - TCP 8000" >nul 2>&1
netsh advfirewall firewall delete rule name="Biometric ADMS Listener - UDP 8000" >nul 2>&1

REM Add inbound rule for TCP port 8000
echo Adding TCP port 8000 inbound rule...
netsh advfirewall firewall add rule name="Biometric ADMS Listener - TCP 8000" dir=in action=allow protocol=TCP localport=8000 profile=any

REM Add inbound rule for UDP port 8000 (optional, for device discovery)
echo Adding UDP port 8000 inbound rule...
netsh advfirewall firewall add rule name="Biometric ADMS Listener - UDP 8000" dir=in action=allow protocol=UDP localport=8000 profile=any

echo.
echo ========================================
echo Firewall configuration completed!
echo ========================================
echo.
echo Port 8000 is now open for ADMS device connections.
echo.
echo Next steps:
echo 1. Make sure your device (192.168.1.119) can reach this server
echo 2. Configure device to push to: http://192.168.1.14:8000
echo 3. Start the biometric application
echo.

pause
