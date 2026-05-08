#!/usr/bin/env python3
"""
Generate Windows Task Scheduler XML configuration file.
This provides more advanced scheduling options than the batch script.
"""

import os
from pathlib import Path
from datetime import datetime

def create_task_xml(interval_minutes=5, exe_path=None):
    """Create a Windows Task Scheduler XML file for the background sync service.
    
    Args:
        interval_minutes: Interval in minutes between task executions
        exe_path: Full path to the background_sync_service.exe
    """
    if exe_path is None:
        # Default to dist folder in current directory
        exe_path = Path(__file__).parent / "dist" / "background_sync_service.exe"
        exe_path = exe_path.resolve()
    
    # Get current user
    username = os.environ.get('USERNAME', 'SYSTEM')
    
    # Create XML content
    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().isoformat()}</Date>
    <Author>{username}</Author>
    <Description>Biometric Background Sync Service - Automatically syncs biometric data to ERP every {interval_minutes} minute(s)</Description>
    <URI>\\BiometricBackgroundSync</URI>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT{interval_minutes}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{username}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <Arguments>--force</Arguments>
      <WorkingDirectory>{exe_path.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
    
    # Save to file
    output_file = Path(__file__).parent / "BiometricBackgroundSync.xml"
    with open(output_file, 'w', encoding='utf-16') as f:
        f.write(xml_content)
    
    print(f"Task XML file created: {output_file}")
    print(f"Interval: Every {interval_minutes} minute(s)")
    print(f"Executable: {exe_path}")
    print()
    print("To import this task into Windows Task Scheduler:")
    print(f"1. Open Task Scheduler (Win+R, type 'taskschd.msc')")
    print(f"2. Click 'Import Task...' in the Actions panel")
    print(f"3. Select the file: {output_file}")
    print(f"4. Review settings and click OK")
    print()
    print("Or use command line:")
    print(f'schtasks /Create /TN "BiometricBackgroundSync" /XML "{output_file}" /F')
    
    return output_file

if __name__ == "__main__":
    import sys
    
    interval = 5  # Default 5 minutes
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"Invalid interval: {sys.argv[1]}")
            print("Usage: python create_task_xml.py [interval_in_minutes]")
            sys.exit(1)
    
    create_task_xml(interval)
