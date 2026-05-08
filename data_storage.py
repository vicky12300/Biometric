#!/usr/bin/env python3
"""
Persistent Data Storage for Biometric Tools Manager
Saves all application data to JSON files
"""
import json
import os
from pathlib import Path
from datetime import datetime

class DataStorage:
    """Handles persistent storage of application data"""
    
    @property
    def data_dir(self):
        """Get the data directory path"""
        return self._data_dir
        
    def __init__(self, data_dir=None):
        """Initialize storage with data directory"""
        if data_dir is None:
            # Use user's AppData folder on Windows, home on Linux/Mac
            if os.name == 'nt':  # Windows
                data_dir = os.path.join(os.getenv('APPDATA'), 'BiometricToolsManager')
            else:  # Linux/Mac
                data_dir = os.path.join(os.path.expanduser('~'), '.biometric_tools')
        
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.devices_file = self.data_dir / 'devices.json'
        self.users_file = self.data_dir / 'users.json'
        self.settings_file = self.data_dir / 'settings.json'
        self.erp_config_file = self.data_dir / 'erp_config.json'
        self.device_history_file = self.data_dir / 'device_history.json'
        self.user_history_file = self.data_dir / 'user_history.json'
        self.sync_history_file  = self.data_dir / 'sync_history.json'
        self.adms_punches_file   = self.data_dir / 'adms_punches.json'
        
        # Initialize default data if files don't exist
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Create default data files if they don't exist"""
        # Default users
        if not self.users_file.exists():
            default_users = [
                {
                    "username": "admin",
                    "password": "admin123",
                    "role": "Admin",
                    "fullName": "Administrator",
                    "email": "admin@company.com",
                    "status": "Active",
                    "lastLogin": "Never"
                },
                {
                    "username": "viewer",
                    "password": "viewer123",
                    "role": "Viewer",
                    "fullName": "Viewer User",
                    "email": "viewer@company.com",
                    "status": "Active",
                    "lastLogin": "Never"
                }
            ]
            self.save_users(default_users)
        
        # Default settings
        if not self.settings_file.exists():
            default_settings = {
                "dateFormat": "YYYY-MM-DD",
                "recordsPerPage": 50,
                "autoSync": False,
                "syncInterval": 60,
                "punchFilter": {
                    "enabled": False,
                    "intervalSeconds": 3
                }
            }
            self.save_settings(default_settings)
        
        # Empty devices list
        if not self.devices_file.exists():
            self.save_devices([])
        
        # Empty ERP config
        if not self.erp_config_file.exists():
            self.save_erp_config({})
    
    def save_devices(self, devices):
        """Save devices list to file"""
        with open(self.devices_file, 'w') as f:
            json.dump(devices, f, indent=2)
    
    def load_devices(self):
        """Load devices list from file"""
        try:
            with open(self.devices_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def update_device_last_sync(self, device_id, sync_time=None):
        """Update the lastSync timestamp for a specific device
        
        Args:
            device_id: The device ID to update
            sync_time: ISO format timestamp string, or None to use current time
        
        Returns:
            bool: True if device was found and updated, False otherwise
        """
        if sync_time is None:
            sync_time = datetime.now()
        elif isinstance(sync_time, str):
            # Convert ISO string to datetime object
            try:
                sync_time = datetime.fromisoformat(sync_time.replace('Z', '+00:00'))
            except:
                sync_time = datetime.now()
        
        # Convert to locale format: 1/30/2026, 10:38:11 (cross-platform)
        if hasattr(sync_time, 'strftime'):
            # Format as M/D/YYYY, HH:MM:SS (no leading zeros for month/day)
            month = sync_time.month
            day = sync_time.day
            year = sync_time.year
            hour = sync_time.hour
            minute = sync_time.minute
            second = sync_time.second
            locale_format = f"{month}/{day}/{year}, {hour:02d}:{minute:02d}:{second:02d}"
        else:
            locale_format = str(sync_time)
        
        devices = self.load_devices()
        updated = False
        
        for device in devices:
            if str(device.get('id')) == str(device_id) or str(device.get('ip')) == str(device_id):
                device['lastSync'] = locale_format
                updated = True
                break
        
        if updated:
            self.save_devices(devices)
        
        return updated

    def update_device_status(self, device_id, status, last_seen=None):
        """Update device online/offline status
        
        Args:
            device_id: Device ID or IP
            status: 'online' or 'offline'
            last_seen: Optional timestamp of last successful connection
        """
        devices = self.load_devices()
        updated = False
        
        for device in devices:
            if str(device.get('id')) == str(device_id) or str(device.get('ip')) == str(device_id):
                device['status'] = status
                if last_seen:
                    device['lastSeen'] = last_seen
                updated = True
                break
        
        if updated:
            self.save_devices(devices)
        
        return updated

    
    def save_users(self, users):
        """Save users list to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def load_users(self):
        """Load users list from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_settings(self, settings):
        """Save application settings to file"""
        # Ensure punch filter structure exists for backward compatibility
        if isinstance(settings, dict):
            punch_filter = settings.get("punchFilter")
            if not isinstance(punch_filter, dict):
                punch_filter = {}
            punch_filter.setdefault("enabled", False)
            punch_filter.setdefault("intervalSeconds", 3)
            settings["punchFilter"] = punch_filter

        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def load_settings(self):
        """Load application settings from file"""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_erp_config(self, config):
        """Save ERP configuration to file"""
        with open(self.erp_config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_erp_config(self):
        """Load ERP configuration from file"""
        try:
            with open(self.erp_config_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_device_history(self, history):
        """Save device history to file"""
        with open(self.device_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_device_history(self):
        """Load device history from file"""
        try:
            with open(self.device_history_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_user_history(self, history):
        """Save user history to file"""
        with open(self.user_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_user_history(self):
        """Load user history from file"""
        try:
            with open(self.user_history_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_sync_history(self, history):
        """Save sync history to file"""
        with open(self.sync_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_sync_history(self):
        """Load sync history from file"""
        try:
            with open(self.sync_history_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_adms_punches(self, records):
        """Persist ADMS push records received from face devices."""
        with open(self.adms_punches_file, 'w') as f:
            json.dump(records, f, indent=2)

    def load_adms_punches(self):
        """Load previously received ADMS push records."""
        try:
            with open(self.adms_punches_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def get_data_dir(self):
        """Get the data directory path"""
        return str(self.data_dir)
    
    def export_all_data(self, export_path):
        """Export all data to a single JSON file"""
        all_data = {
            'devices': self.load_devices(),
            'users': self.load_users(),
            'settings': self.load_settings(),
            'erp_config': self.load_erp_config(),
            'exported_at': datetime.now().isoformat()
        }
        with open(export_path, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    def import_all_data(self, import_path):
        """Import all data from a JSON file"""
        with open(import_path, 'r') as f:
            all_data = json.load(f)
        
        if 'devices' in all_data:
            self.save_devices(all_data['devices'])
        if 'users' in all_data:
            self.save_users(all_data['users'])
        if 'settings' in all_data:
            self.save_settings(all_data['settings'])
        if 'erp_config' in all_data:
            self.save_erp_config(all_data['erp_config'])

# Global storage instance
storage = DataStorage()
