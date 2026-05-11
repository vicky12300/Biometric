#!/usr/bin/env python3
import http.server
import socketserver
import json
import html
import os
import webbrowser
import threading
import csv
import io
import time
import sys
import traceback
import builtins
if os.name == 'nt':
    import ctypes
    def hide_console_window():
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass
    hide_console_window()
from urllib.parse import parse_qs
from zk import ZK, const
from datetime import datetime, timedelta
from data_storage import storage

DEBUG_LOG_FILE = os.path.join(storage.get_data_dir(), "biometric_debug.log")

def debug_log(message, exc=None):
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] [WEB] {message}", flush=True)
    if exc is not None:
        print(f"[{timestamp}] [WEB] EXCEPTION: {repr(exc)}", flush=True)
        traceback.print_exc()
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] [WEB] {message}\n")
            if exc is not None:
                log_file.write(f"[{timestamp}] [WEB] EXCEPTION: {repr(exc)}\n")
                log_file.write(traceback.format_exc())
                log_file.write("\n")
    except Exception:
        pass

def safe_strptime(date_string, format_string):
    value = str(date_string).strip()
    debug_log(f"safe_strptime called value={value!r}, format={format_string!r}")

    if format_string == "%Y-%m-%d":
        try:
            year, month, day = map(int, value.split("-"))
            parsed = datetime(year, month, day)
            debug_log(f"safe_strptime parsed date value={value!r} -> {parsed.isoformat()}")
            return parsed
        except Exception as exc:
            debug_log(f"safe_strptime failed for date value={value!r}", exc)
            raise

    if format_string == "%Y-%m-%d %H:%M:%S":
        try:
            date_part, time_part = value.replace("T", " ", 1).split(" ", 1)
            year, month, day = map(int, date_part.split("-"))
            hour, minute, second = map(int, time_part.split(":"))
            parsed = datetime(year, month, day, hour, minute, second)
            debug_log(f"safe_strptime parsed datetime value={value!r} -> {parsed.isoformat()}")
            return parsed
        except Exception as exc:
            debug_log(f"safe_strptime failed for datetime value={value!r}", exc)
            raise

    debug_log(f"safe_strptime unsupported format={format_string!r}, value={value!r}")
    raise ValueError(f"Unsupported date format: {format_string}")

debug_log(
    "module loaded; "
    f"python={sys.version!r}; executable={sys.executable!r}; "
    f"frozen={getattr(sys, 'frozen', False)!r}; "
    f"_MEIPASS={getattr(sys, '_MEIPASS', None)!r}; "
    f"_strptime_loaded={'_strptime' in sys.modules}; "
    f"log_file={DEBUG_LOG_FILE!r}"
)

_original_import = builtins.__import__

def _debug_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "_strptime":
        debug_log("IMPORT ATTEMPT for _strptime\n" + "".join(traceback.format_stack(limit=20)))
    try:
        return _original_import(name, globals, locals, fromlist, level)
    except ModuleNotFoundError as exc:
        if name == "_strptime" or getattr(exc, "name", None) == "_strptime":
            debug_log(f"IMPORT FAILED for name={name!r}, exc_name={getattr(exc, 'name', None)!r}", exc)
        raise

builtins.__import__ = _debug_import

class EnhancedBiometricHandler(http.server.SimpleHTTPRequestHandler):
    # ... rest of the code remains the same
    def _write_response(self, payload):
        try:
            if isinstance(payload, str):
                payload = payload.encode()
            self.wfile.write(payload)
            return True
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError) as exc:
            debug_log(f"Client disconnected before response completed path={self.path!r}", exc)
            return False

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            # Add cache-busting headers to prevent browser caching
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Biometric Tools Manager - Enhanced</title>
    <meta charset="UTF-8">
    <style>
        :root {
            --primary: #0b74c4;
            --primary-dark: #075a99;
            --primary-light: #e7f3ff;
            --accent: #17a2b8;
            --success: #2e9f4b;
            --danger: #d83a4a;
            --warning: #ffc247;
            --surface: #ffffff;
            --surface-alt: #f4f7fb;
            --border: #d8e0eb;
            --text: #1f2d3d;
            --text-muted: #5f6b7a;
            --shadow-sm: 0 2px 6px rgba(15, 23, 42, 0.08);
            --shadow-md: 0 12px 30px rgba(15, 23, 42, 0.12);
            --radius-sm: 6px;
            --radius-md: 12px;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Segoe UI', sans-serif;
            margin: 0;
            background: linear-gradient(180deg, #f0f5fb 0%, #f8fbff 100%);
            color: var(--text);
        }

        h1, h2, h3, h4 {
            margin: 0 0 12px;
            font-weight: 600;
            color: var(--text);
        }

        p {
            margin: 0 0 16px;
            color: var(--text-muted);
        }

        a {
            color: var(--primary);
        }

        .header {
            background: var(--primary);
            color: white;
            padding: 14px 24px 16px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 12px;
        }

        .header-content {
            max-width: 1080px;
            margin: 0 auto;
            padding: 0 12px;
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 16px;
        }

        .brand {
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .brand-logo {
            height: 48px;
            width: auto;
            object-fit: contain;
            border-radius: 0;
            box-shadow: none;
        }

        .header-title {
            text-align: center;
            min-width: 0;
        }

        .page-title {
            font-size: 26px;
            letter-spacing: 0.4px;
            font-weight: 600;
            color: #ffffff;
            margin: 0;
        }

        .page-subtitle {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.75);
            margin: 6px 0 0;
        }

        .header-actions {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            background: rgba(255, 255, 255, 0.2);
            padding: 6px 13px;
            border-radius: 999px;
            color: #ffffff;
        }

        .header-actions span {
            color: #ffffff;
        }

        .header-actions .logout-btn {
            box-shadow: none;
        }

        .container {
            max-width: 1200px;
            margin: 8px auto 48px;
            padding: 0 24px 40px;
        }

        .tabs {
            display: flex;
            background: var(--surface);
            border-radius: var(--radius-md);
            margin-bottom: 24px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }

        .tab {
            flex: 1;
            padding: 16px 12px;
            text-align: center;
            cursor: pointer;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-weight: 500;
            transition: all 0.25s ease;
            border-bottom: 3px solid transparent;
        }

        .tab:hover {
            color: var(--primary);
            background: rgba(11, 116, 196, 0.12);
        }

        .tab.active {
            background: #ffffff;
            color: var(--primary);
            font-weight: 600;
            border-bottom: 3px solid var(--primary);
            box-shadow: inset 0 -2px 0 rgba(11, 116, 196, 0.2);
        }

        .tab-content {
            display: none;
            background: var(--surface);
            padding: 32px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
        }

        .tab-content.active {
            display: block;
        }

        .section-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .form-row {
            display: flex;
            gap: 20px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }

        .form-group {
            flex: 1;
            min-width: 220px;
        }

        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: var(--text);
        }

        input,
        select,
        textarea {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 14px;
            transition: border 0.2s ease, box-shadow 0.2s ease;
        }

        input:focus,
        select:focus,
        textarea:focus {
            border-color: var(--primary);
            outline: none;
            box-shadow: 0 0 0 3px rgba(11, 116, 196, 0.15);
        }

        button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 11px 20px;
            border: none;
            border-radius: var(--radius-sm);
            background: var(--primary);
            color: white;
            font-weight: 600;
            font-size: 14px;
            letter-spacing: 0.2px;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.2s ease, background 0.2s ease;
            box-shadow: 0 2px 4px rgba(11, 116, 196, 0.2);
        }

        button:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(11, 116, 196, 0.18);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }

        button.secondary {
            background: var(--success);
            box-shadow: 0 2px 4px rgba(46, 159, 75, 0.18);
        }

        button.secondary:hover {
            background: #24853c;
            box-shadow: 0 6px 14px rgba(46, 159, 75, 0.18);
        }

        button.danger {
            background: var(--danger);
            box-shadow: 0 2px 4px rgba(216, 58, 74, 0.18);
        }

        button.danger:hover {
            background: #c22f3f;
            box-shadow: 0 6px 14px rgba(216, 58, 74, 0.18);
        }

        button.link-btn {
            background: transparent;
            color: var(--primary);
            box-shadow: none;
            padding-left: 0;
            padding-right: 0;
        }

        button.link-btn:hover {
            background: transparent;
            color: var(--primary-dark);
            transform: none;
        }

        .action-bar,
        .quick-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 24px;
            align-items: center;
        }

        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }

        .log-feed {
            max-height: 300px;
            overflow-y: auto;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(15, 23, 42, 0.05);
        }

        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 24px 0;
        }

        .filters {
            background: var(--surface-alt);
            padding: 20px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
            margin-bottom: 24px;
        }

        .filters-row {
            display: flex;
            gap: 16px;
            align-items: flex-end;
            flex-wrap: wrap;
        }

        .filters h4 {
            margin-bottom: 16px;
            color: var(--text);
        }

        .settings-section,
        .card {
            background: var(--surface);
            padding: 24px;
            border-radius: var(--radius-md);
            border: 1px solid rgba(15, 23, 42, 0.05);
            box-shadow: var(--shadow-sm);
            margin-bottom: 24px;
        }

        .device-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .device-card {
            background: var(--surface);
            padding: 20px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            border: 1px solid rgba(15, 23, 42, 0.05);
        }

        .device-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }

        .status-online {
            background: #daf3e1;
            color: #1c7c37;
        }

        .status-offline {
            background: #fde2e6;
            color: #b62836;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }

        thead {
            background: var(--primary);
            color: white;
        }

        th,
        td {
            border: 1px solid rgba(15, 23, 42, 0.08);
            padding: 12px 14px;
            text-align: left;
            vertical-align: middle;
        }

        tbody tr:nth-child(every) {}

        tbody tr:nth-child(odd) {
            background: rgba(12, 116, 196, 0.02);
        }

        tbody tr:hover {
            background: rgba(11, 116, 196, 0.08);
            cursor: default;
        }

        thead th {
            font-weight: 600;
            letter-spacing: 0.4px;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        .export-options {
            display: flex;
            gap: 12px;
            margin: 24px 0;
            flex-wrap: wrap;
        }

        .result {
            margin: 20px 0;
            padding: 20px;
            background: var(--surface-alt);
            border-radius: var(--radius-md);
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }

        .success {
            color: var(--success);
        }

        .error {
            color: var(--danger);
        }

        .loader-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(9, 27, 45, 0.7);
            z-index: 9999;
        }

        .loader-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: white;
            padding: 32px;
            border-radius: var(--radius-md);
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(4px);
        }

        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.2);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loader-text {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 6px;
        }

        .loader-subtext {
            font-size: 14px;
            opacity: 0.85;
        }

        .overlay-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.55);
            z-index: 10001;
            padding: 24px;
            overflow-y: auto;
        }

        .overlay-modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-card {
            background: var(--surface);
            width: 100%;
            max-width: 520px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            overflow: hidden;
            border: 1px solid rgba(15, 23, 42, 0.08);
            animation: fadeInUp 0.24s ease;
        }

        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            background: var(--surface-alt);
            border-bottom: 1px solid rgba(15, 23, 42, 0.05);
        }

        .modal-header h3 {
            margin: 0;
            font-size: 20px;
            font-weight: 600;
            color: var(--primary);
        }

        .modal-close {
            background: transparent;
            border: none;
            font-size: 26px;
            line-height: 1;
            cursor: pointer;
            color: var(--text-muted);
            padding: 4px;
        }

        .modal-close:hover {
            color: var(--primary);
        }

        .modal-body {
            padding: 24px;
        }

        .modal-actions {
            display: flex;
            gap: 12px;
            padding: 20px 24px 24px;
            background: var(--surface-alt);
            border-top: 1px solid rgba(15, 23, 42, 0.05);
        }

        .modal-actions .primary {
            flex: 1;
        }

        .modal-actions .secondary {
            flex: 1;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translate3d(0, 12px, 0);
            }
            to {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        .logout-btn {
            background: #ffffff !important;
            color: var(--primary) !important;
            text-decoration: none !important;
            padding: 8px 16px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .logout-btn:hover {
            background: #f0f7ff !important;
            color: var(--primary-dark) !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(11, 116, 196, 0.18) !important;
        }

        .app-content {
            display: none;
        }

        /* Login Screen Styles */
        .login-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(11, 116, 196, 0.92), rgba(4, 48, 84, 0.92));
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .login-container {
            background: var(--surface);
            padding: 44px 40px 36px;
            border-radius: 18px;
            box-shadow: var(--shadow-md);
            max-width: 420px;
            width: 100%;
            text-align: center;
        }

        .login-title {
            color: var(--primary);
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .login-subtitle {
            color: var(--text-muted);
            margin-bottom: 32px;
        }

        .login-form {
            text-align: left;
        }

        .login-form input {
            margin-bottom: 20px;
            font-size: 16px;
        }

        .login-btn {
            width: 100%;
            font-size: 16px;
            font-weight: 700;
            padding: 12px 18px;
            box-shadow: 0 8px 20px rgba(11, 116, 196, 0.25);
        }

        .login-btn:hover {
            background: var(--primary-dark);
        }

        .login-error {
            color: var(--danger);
            margin-top: 15px;
            text-align: center;
            display: none;
        }

        @media (max-width: 768px) {
            .header {
                padding: 16px 16px 22px;
            }

            .header-content {
                grid-template-columns: 1fr;
                justify-items: center;
                gap: 12px;
                text-align: center;
            }

            .brand {
                justify-content: center;
            }

            .header-title {
                text-align: center;
            }

            .tabs {
                flex-direction: column;
            }

            .header-actions {
                position: static;
                justify-content: center;
                margin-bottom: 16px;
            }

            .container {
                margin: -60px 16px 24px;
                padding: 0 16px 24px;
            }

            .tab {
                font-size: 13px;
                padding: 14px 8px;
            }

            .tab-content {
                padding: 24px;
            }

            .form-group {
                min-width: 180px;
            }

            button {
                width: 100%;
            }

            .header {
                padding-bottom: 56px;
            }

            .modal-card {
                margin: auto 0;
            }

            .header-grid {
                flex-direction: column;
                align-items: center;
                gap: 16px;
            }

            .header-title {
                text-align: center;
            }

            .header-actions {
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <!-- Login Screen -->
    <div id="loginOverlay" class="login-overlay">
        <div class="login-container">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="/auriga1.png" alt="Auriga Logo" style="height: 60px; width: auto; margin: 0 auto;" onerror="if(this.src.includes('auriga1.png')){this.src='/Auriga - Original.jpg';}else{this.onerror=null;this.src='/auriga.png';}">
            </div>
            <div class="login-title">🔐 Biometric Tools</div>
            <div class="login-subtitle">Please login to access the system</div>
            <form class="login-form" onsubmit="handleLogin(event)">
                <input type="text" id="loginUsername" placeholder="Username" required>
                <input type="password" id="loginPassword" placeholder="Password" required>
                <button type="submit" class="login-btn">Login</button>
                <div id="loginError" class="login-error">Invalid username or password</div>
            </form>
            <div style="margin-top: 20px; font-size: 12px; color: #999;">
                Default: admin / admin123<br>
                Viewer: viewer / viewer123
            </div>
        </div>
    </div>
    
    <!-- Main Application -->
    <div id="appContent" class="app-content">
    <div class="header">
        <div class="header-content">
            <div class="brand">
                <img src="/Auriga - Original.jpg" alt="Auriga" class="brand-logo" onerror="this.onerror=null;this.src='/auriga.png';">
            </div>
            <div class="header-title">
                <h1 class="page-title">Biometric Tools Manager - Enhanced</h1>
                <p class="page-subtitle">Complete biometric device management with ERP integration</p>
            </div>
            <div class="header-actions">
                <span id="userInfo">Welcome, User</span>
                <a href="#" onclick="logout()" class="logout-btn">Logout</a>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('devices')">Devices</button>
            <button class="tab" onclick="showTab('data')">Data & Reports</button>
            <button class="tab" onclick="showTab('erp')">ERP Integration</button>
            <button class="tab" onclick="showTab('users')">User Management</button>
            <button class="tab" onclick="showTab('settings')">Settings</button>
        </div>

        <div id="devices" class="tab-content active">
            <h2>Device Management</h2>

            <!-- Device Action Buttons -->
            <div class="action-bar">
                <button onclick="openAddDeviceModal()" class="secondary">➕ Add Device</button>
                <button onclick="discoverDevices()" class="secondary">🔍 Auto Discover</button>
            </div>

            <!-- Device Filters -->
            <div class="filters">
                <h4>Device Filters</h4>
                <div class="filters-row">
                    <div class="form-group">
                        <label>Device Name:</label>
                        <input type="text" id="filterDeviceName" placeholder="Search device name...">
                    </div>
                    <div class="form-group">
                        <label>Device Type:</label>
                        <select id="filterDeviceType">
                            <option value="">All Types</option>
                            <option value="ZKTeco">ZKTeco</option>
                            <option value="ESSL">ESSL</option>
                            <option value="Hikvision">Hikvision</option>
                            <option value="Suprema">Suprema</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Status:</label>
                        <select id="filterDeviceStatus">
                            <option value="">All Status</option>
                            <option value="online">Online</option>
                            <option value="offline">Offline</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <button onclick="applyDeviceFilters()">Apply Filters</button>
                        <button onclick="clearDeviceFilters()" class="secondary">Clear</button>
                    </div>
                </div>
            </div>

            <!-- Devices Table -->
            <div class="settings-section">
                <h3>💻 All Devices</h3>
                <div class="table-wrapper">
                    <table id="devicesTable">
                        <thead>
                            <tr>
                                <th>Device Name</th>
                                <th>Type</th>
                                <th>IP Address</th>
                                <th>Port</th>
                                <th>Mode</th>
                                <th>Status</th>
                                <th>Last Sync</th>
                                <th style="text-align: center;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="devicesTableBody">
                            <!-- Devices will be populated here -->
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Device History Section -->
            <div class="settings-section">
                <h3>📋 Device Activity Log</h3>
                <div class="action-bar">
                    <button onclick="loadDeviceHistory()">🔄 Refresh</button>
                    <button onclick="clearDeviceHistory()" class="danger">🗑️ Clear History</button>
                    <span style="color: #666; font-size: 0.9em;">Shows device add/update/delete activities</span>
                </div>
                <div id="deviceHistory" class="log-feed">
                    <div style="color: #666; text-align: center;">No device activity yet</div>
                </div>
            </div>
        </div>

        <div id="data" class="tab-content">
            <h2>Data & Reports</h2>
            
            <div class="quick-actions">
                <button onclick="setToday()">Today</button>
                <button onclick="setYesterday()">Yesterday</button>
                <button onclick="setThisWeek()">This Week</button>
                <button onclick="setThisMonth()">This Month</button>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Start Date:</label>
                    <input type="date" id="startDate">
                </div>
                <div class="form-group">
                    <label>End Date:</label>
                    <input type="date" id="endDate">
                </div>
                <div class="form-group">
                    <label>Device:</label>
                    <select id="selectedDevice">
                        <option value="">All Devices</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="dummyMode"> Use Dummy Data (for testing)
                    </label>
                </div>
                <div class="form-group">
                    <button onclick="fetchAllData()">Fetch Data</button>
                </div>
            </div>
            
            <div class="filters">
                <h4>Advanced Filters</h4>
                <div class="filters-row">
                    <div class="form-group">
                        <label>Employee Name:</label>
                        <input type="text" id="filterEmployee" placeholder="Search employee...">
                    </div>
                    <div class="form-group">
                        <label>Employee ID:</label>
                        <input type="text" id="filterEmployeeId" placeholder="Employee ID...">
                    </div>
                    <div class="form-group">
                        <label>Punch Type:</label>
                        <select id="filterPunchType">
                            <option value="">All</option>
                            <option value="check-in">Check In</option>
                            <option value="check-out">Check Out</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <button onclick="applyFilters()">Apply Filters</button>
                        <button onclick="clearFilters()" class="secondary">Clear</button>
                    </div>
                </div>
            </div>
            
            <div id="dataStats" class="stats" style="display:none;">
                <!-- Stats will be shown here -->
            </div>
            
            <div class="export-options" style="display:none;" id="exportOptions">
                <button onclick="exportData('csv')">Export CSV</button>
                <button onclick="exportData('excel')">Export Excel</button>
                <button onclick="sendToERP()" class="secondary">Send to ERP</button>
            </div>
            
            <div id="dataResult" class="result" style="display:none;"></div>
            
            <div id="pagination" class="pagination" style="display:none;">
                <!-- Pagination will be shown here -->
            </div>
        </div>

        <div id="erp" class="tab-content">
            <h2>ERP Integration</h2>
            <div class="form-row">
                <div class="form-group">
                    <label>ERP System:</label>
                    <select id="erpSystem">
                        <option value="frappe">Frappe/ERPNext</option>
                        <option value="sap">SAP</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>API URL:</label>
                    <input type="text" id="erpUrl" placeholder="http://equiplus:8000">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>API Key/Token:</label>
                    <input type="text" id="erpApiKey" placeholder="0f786ec9036ffb3:dc8989f51e338c7">
                    <small style="color: #666; font-size: 0.9em;">Format: api_key:api_secret<br>Current: 90a91d938cde43d:6fb6e458971b73e</small>
                </div>
                <div class="form-group">
                    <button onclick="testERPConnection()">Test Connection</button>
                </div>
            </div>
            
            <div class="card" style="background: var(--primary-light); border: none;">
                <div style="font-size: 0.9em; color: #0066cc;">
                    <strong>ERPNext API Key Setup:</strong><br>
                    1. Login to ERPNext as Administrator<br>
                    2. Go to: User → [Your User] → API Access → Generate Keys<br>
                    3. Copy both API Key and API Secret<br>
                    4. Format: api_key:api_secret (no spaces)<br>
                    5. Enable "Employee Checkin" in DocType settings<br><br>
                    <strong>Employee Validation:</strong><br>
                    • Only employees existing in ERPNext will be synced<br>
                    • Non-existing employees will be skipped<br><br>
                    <strong>Common Issues:</strong><br>
                    • API key expired - Generate new one<br>
                    • User lacks "System Manager" role<br>
                    • API access disabled for user<br>
                    • Wrong ERPNext URL or port
                </div>
            </div>
            <div id="erpStatus" class="result" style="display:none;"></div>
        </div>

        <div id="users" class="tab-content">
            <h2>User Management</h2>
            
            <!-- Add User Button -->
            <div class="action-bar">
                <button onclick="openAddUserModal()" class="secondary">➕ Add New User</button>
            </div>

            <!-- Users List Table -->
            <div class="settings-section">
                <h3>📋 All Users</h3>
                <div class="table-wrapper">
                    <table id="usersTable">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Full Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Last Login</th>
                                <th style="text-align: center;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                            <!-- Users will be populated here -->
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- User History Section -->
            <div class="settings-section">
                <h3>📋 User Activity Log</h3>
                <div class="action-bar">
                    <button onclick="loadUserHistory()">🔄 Refresh</button>
                    <button onclick="clearUserHistory()" class="danger">🗑️ Clear History</button>
                    <span style="color: #666; font-size: 0.9em;">Shows user add/update/delete activities</span>
                </div>
                <div id="userHistory" class="log-feed">
                    <div style="color: #666; text-align: center;">No user activity yet</div>
                </div>
            </div>
            
            <!-- Add New User Modal -->
            <div id="addUserModal" class="overlay-modal">
                <div class="modal-card">
                    <div class="modal-header">
                        <h3>➕ Add New User</h3>
                        <button class="modal-close" onclick="closeAddUserModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="text" id="newUsername" placeholder="Enter username">
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="newPassword" placeholder="Enter password">
                        </div>
                        <div class="form-group">
                            <label>Full Name:</label>
                            <input type="text" id="newFullName" placeholder="Enter full name">
                        </div>
                        <div class="form-group">
                            <label>Email:</label>
                            <input type="email" id="newEmail" placeholder="Enter email">
                        </div>
                        <div class="form-group">
                            <label>Role:</label>
                            <select id="newUserRole">
                                <option value="Admin">Admin</option>
                                <option value="Viewer">Viewer</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button onclick="addNewUser()" class="primary">Add User</button>
                        <button onclick="closeAddUserModal()" class="secondary">Cancel</button>
                    </div>
                </div>
            </div>
            
            <!-- Change Password Modal -->
            <div id="changePasswordModal" class="overlay-modal">
                <div class="modal-card">
                    <div class="modal-header">
                        <h3>🔐 Change Password</h3>
                        <button class="modal-close" onclick="closeChangePasswordModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="text" id="changePasswordUsername" readonly>
                        </div>
                        <div class="form-group">
                            <label>New Password:</label>
                            <input type="password" id="changePasswordNew" placeholder="Enter new password">
                        </div>
                        <div class="form-group">
                            <label>Confirm Password:</label>
                            <input type="password" id="changePasswordConfirm" placeholder="Confirm new password">
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button onclick="savePasswordChange()" class="primary">Save Password</button>
                        <button onclick="closeChangePasswordModal()" class="secondary">Cancel</button>
                    </div>
                </div>
            </div>
            
            <!-- Edit User Modal -->
            <div id="editUserModal" class="overlay-modal">
                <div class="modal-card">
                    <div class="modal-header">
                        <h3>✏️ Edit User</h3>
                        <button class="modal-close" onclick="closeEditUserModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="text" id="editUsername" readonly>
                        </div>
                        <div class="form-group">
                            <label>Full Name:</label>
                            <input type="text" id="editFullName" placeholder="Enter full name">
                        </div>
                        <div class="form-group">
                            <label>Email:</label>
                            <input type="email" id="editEmail" placeholder="Enter email">
                        </div>
                        <div class="form-group">
                            <label>Role:</label>
                            <select id="editUserRole">
                                <option value="Admin">Admin</option>
                                <option value="Viewer">Viewer</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button onclick="saveUserEdit()" class="primary">Save Changes</button>
                        <button onclick="closeEditUserModal()" class="secondary">Cancel</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="settings" class="tab-content">
            <h2>Settings</h2>
            
            <div class="settings-section" style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>🔄 Auto-Sync to ERP</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="autoSyncEnabled"> Enable Auto-Sync
                        </label>
                        <small style="color: #666;">Automatically send new punches to ERP</small>
                    </div>
                    <div class="form-group">
                        <label>Sync Interval (minutes):</label>
                        <select id="syncInterval">
                            <option value="1">Every 1 minute</option>
                            <option value="5" selected>Every 5 minutes</option>
                            <option value="10">Every 10 minutes</option>
                            <option value="15">Every 15 minutes</option>
                            <option value="30">Every 30 minutes</option>
                            <option value="60">Every 1 hour</option>
                            <option value="180">Every 3 hours</option>
                            <option value="360">Every 6 hours</option>
                            <option value="540">Every 9 hours</option>
                            <option value="720">Every 12 hours</option>
                            <option value="1440">Daily at midnight</option>
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="testModeEnabled"> Test Mode (Use Dummy Data)
                        </label>
                        <small style="color: #666;">Generate test data for auto-sync testing</small>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Auto-Sync Status:</label>
                        <div id="autoSyncStatus" style="padding: 10px; background: #f8f9fa; border-radius: 5px; margin-top: 5px;">
                            <span id="syncStatusText">Disabled</span>
                            <div id="syncStats" style="font-size: 0.9em; color: #666; margin-top: 5px;"></div>
                        </div>
                    </div>
                    <div class="form-group">
                        <button onclick="toggleAutoSync()" id="autoSyncToggle">Start Auto-Sync</button>
                        <button onclick="syncNow()" class="secondary">Sync Now</button>
                        <button onclick="openCustomSyncModal()" style="background: #17a2b8; color: white; border: none; cursor: pointer;">Custom Sync</button>
                    </div>
                </div>
            </div>
            <div class="settings-section" style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>👥 Punch Deduplication</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="punchFilterEnabled"> Ignore rapid duplicate punches
                        </label>
                        <small style="color: #666;">Skip punches for the same employee within the selected time window</small>
                    </div>
                    <div class="form-group">
                        <label>Ignore Interval (seconds):</label>
                        <select id="punchFilterInterval">
                            <option value="1">1 second</option>
                            <option value="2">2 seconds</option>
                            <option value="3" selected>3 seconds</option>
                            <option value="4">4 seconds</option>
                            <option value="5">5 seconds</option>
                            <option value="6">6 seconds</option>
                            <option value="7">7 seconds</option>
                            <option value="8">8 seconds</option>
                            <option value="9">9 seconds</option>
                            <option value="10">10 seconds</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="settings-section" style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>📊 Sync History</h3>
                <div id="syncHistory" style="max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;">
                    <div style="color: #666; text-align: center;">No sync history yet</div>
                </div>
            </div>
            
            <div class="form-row">
                <button onclick="saveSettings()">Save Settings</button>
                <button onclick="clearSyncHistory()" class="danger">Clear History</button>
            </div>
        </div>
    </div>
    </div> <!-- End of appContent -->

    <!-- Custom Sync Modal -->
    <div id="customSyncModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10001;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 500px; width: 90%;">
            <h3 style="margin-top: 0; color: #007cba;">📅 Custom Sync from Date/Time</h3>
            <p style="color: #666; margin-bottom: 20px;">Sync data from all devices starting from the specified date and time</p>
            
            <div style="margin-bottom: 15px;">
                <label>Sync From Date:</label>
                <input type="date" id="customSyncDate" style="width: 100%;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label>Sync From Time:</label>
                <input type="time" id="customSyncTime" style="width: 100%;">
            </div>
            
            <div style="margin-bottom: 20px; padding: 10px; background: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;">
                <small style="color: #856404;">
                    <strong>Note:</strong> This will sync data from the specified date/time to now for ALL devices. 
                    Existing records will be skipped to prevent duplicates.
                </small>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button onclick="performCustomSync()" style="flex: 1; background: #17a2b8; color: white;">Start Custom Sync</button>
                <button onclick="closeCustomSyncModal()" class="secondary" style="flex: 1;">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Device Modals -->
    <div id="addDeviceModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10001;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 500px; width: 90%;">
            <h3 style="margin-top: 0; color: #007cba;">➕ Add New Device</h3>
            <div style="margin-bottom: 15px;">
                <label>Device Name:</label>
                <input type="text" id="deviceName" placeholder="Office Main Door">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Device Type:</label>
                <select id="deviceType">
                    <option value="ZKTeco">ZKTeco</option>
                    <option value="ESSL">ESSL</option>
                    <option value="Hikvision">Hikvision</option>
                    <option value="Suprema">Suprema</option>
                </select>
            </div>
            <div style="margin-bottom: 15px;">
                <label>IP Address:</label>
                <input type="text" id="deviceIP" placeholder="192.168.0.30">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Port:</label>
                <input type="number" id="devicePort" value="4370">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Latitude:</label>
                <input type="text" id="deviceLat" placeholder="e.g., 28.7041">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Longitude:</label>
                <input type="text" id="deviceLong" placeholder="e.g., 77.1025">
            </div>
            <div style="margin-bottom: 20px;">
                <label>Connection Mode:</label>
                <select id="deviceMode">
                    <option value="real">Real Device (ZK Pull)</option>
                    <option value="adms">ADMS Push (Face Device)</option>
                    <option value="dummy">Dummy Mode (Testing)</option>
                </select>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="addDevice()" style="flex: 1;">Add Device</button>
                <button onclick="closeAddDeviceModal()" class="secondary" style="flex: 1;">Cancel</button>
            </div>
        </div>
    </div>
    
    <div id="editDeviceModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10001;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 500px; width: 90%;">
            <h3 style="margin-top: 0; color: #007cba;">✏️ Edit Device</h3>
            <div style="margin-bottom: 15px;">
                <label>Device Name:</label>
                <input type="text" id="editDeviceName" placeholder="Office Main Door">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Device Type:</label>
                <select id="editDeviceType">
                    <option value="ZKTeco">ZKTeco</option>
                    <option value="ESSL">ESSL</option>
                    <option value="Hikvision">Hikvision</option>
                    <option value="Suprema">Suprema</option>
                </select>
            </div>
            <div style="margin-bottom: 15px;">
                <label>IP Address:</label>
                <input type="text" id="editDeviceIP" placeholder="192.168.0.30">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Port:</label>
                <input type="number" id="editDevicePort" value="4370">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Latitude:</label>
                <input type="text" id="editDeviceLat" placeholder="e.g., 28.7041">
            </div>
            <div style="margin-bottom: 15px;">
                <label>Longitude:</label>
                <input type="text" id="editDeviceLong" placeholder="e.g., 77.1025">
            </div>
            <div style="margin-bottom: 20px;">
                <label>Connection Mode:</label>
                <select id="editDeviceMode">
                    <option value="real">Real Device (ZK Pull)</option>
                    <option value="adms">ADMS Push (Face Device)</option>
                    <option value="dummy">Dummy Mode (Testing)</option>
                </select>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="saveDeviceEdit()" style="flex: 1;">Save Changes</button>
                <button onclick="closeEditDeviceModal()" class="secondary" style="flex: 1;">Cancel</button>
            </div>
        </div>
    </div>

    <div id="editLastSyncModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10001;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 500px; width: 90%;">
            <h3 style="margin-top: 0; color: #007cba;">⏰ Edit Last Sync Time</h3>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 20px;">
                Set the timestamp from which the next sync should start fetching data. Leave empty to sync last 7 days.
            </p>
            <div style="margin-bottom: 15px;">
                <label>Last Sync Time:</label>
                <input type="datetime-local" id="editLastSyncInput" class="form-control" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" step="1">
                <small style="display: block; color: #666; font-size: 12px; margin-top: 5px;">
                    Next sync will fetch data from this time onwards
                </small>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="saveLastSyncEdit()" style="flex: 1;">Save</button>
                <button onclick="setCurrentTime()" style="flex: 1; background: #28a745; color: white;">Current Time</button>
                <button onclick="closeEditLastSyncModal()" class="secondary" style="flex: 1;">Cancel</button>
            </div>
        </div>
    </div>

    <div id="loaderOverlay" class="loader-overlay">
        <div class="loader-content">
            <div class="spinner"></div>
            <div class="loader-text" id="loaderText">Processing...</div>
            <div class="loader-subtext" id="loaderSubtext">Please wait...</div>
        </div>
    </div>

    <script>
        // Initialize from server, not localStorage
        let devices = [];
        let users = [];
        let appSettings = {};
        let erpConfig = {};
        let allRecords = [];
        let dataLoaded = false;
        
        // Helper functions for server-side storage
        async function saveDevicesToServer() {
            try {
                await fetch('/api/devices', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(devices)
                });
                console.log('✓ Devices saved to server');
            } catch (error) {
                console.error('Error saving devices:', error);
            }
        }
        
        async function loadDevicesFromServer() {
            try {
                const response = await fetch('/api/devices');
                if (response.ok) {
                    devices = await response.json();
                    console.log(`✓ Loaded ${devices.length} devices from server`);
                    return true;
                }
            } catch (error) {
                console.error('Error loading devices:', error);
            }
            return false;
        }
        
        async function loadUsersFromServer() {
            try {
                const response = await fetch('/api/users');
                if (response.ok) {
                    users = await response.json();
                    
                    // Migrate old user data to ensure all fields exist
                    let needsSave = false;
                    users = users.map(user => {
                        if (!user.status || !user.lastLogin || !user.fullName || !user.email) {
                            needsSave = true;
                            return {
                                ...user,
                                status: user.status || 'Active',
                                lastLogin: user.lastLogin || 'Never',
                                fullName: user.fullName || user.username,
                                email: user.email || ''
                            };
                        }
                        return user;
                    });
                    
                    // Save migrated data back to server
                    if (needsSave) {
                        console.log('Migrating user data with missing fields...');
                        await saveUsersToServer();
                    }
                    
                    console.log(`✓ Loaded ${users.length} users from server`);
                    return true;
                }
            } catch (error) {
                console.error('Error loading users:', error);
            }
            return false;
        }
        
        async function saveUsersToServer() {
            try {
                await fetch('/api/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(users)
                });
                console.log('✓ Users saved to server');
            } catch (error) {
                console.error('Error saving users:', error);
            }
        }
        
        async function loadSettingsFromServer() {
            try {
                const response = await fetch('/api/settings');
                if (response.ok) {
                    appSettings = await response.json();
                    console.log('✓ Settings loaded from server');
                    return true;
                }
            } catch (error) {
                console.error('Error loading settings:', error);
            }
            return false;
        }
        
        async function saveSettingsToServer() {
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(appSettings)
                });
                console.log('✓ Settings saved to server');
            } catch (error) {
                console.error('Error saving settings:', error);
            }
        }
        
        async function loadErpConfigFromServer() {
            try {
                const response = await fetch('/api/erp-config');
                if (response.ok) {
                    erpConfig = await response.json();
                    console.log('✓ ERP config loaded from server');
                    return true;
                }
            } catch (error) {
                console.error('Error loading ERP config:', error);
            }
            return false;
        }
        
        async function saveErpConfigToServer() {
            try {
                await fetch('/api/erp-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(erpConfig)
                });
                console.log('✓ ERP config saved to server');
            } catch (error) {
                console.error('Error saving ERP config:', error);
            }
        }

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            if (tabName === 'devices') {
                loadDevices();
                loadDeviceHistory();
            } else if (tabName === 'users') {
                loadUsersTable();
                loadUserHistory();
            }
        }

        function showLoader(text = 'Processing...', subtext = 'Please wait...') {
            document.getElementById('loaderText').textContent = text;
            document.getElementById('loaderSubtext').textContent = subtext;
            document.getElementById('loaderOverlay').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        function hideLoader() {
            document.getElementById('loaderOverlay').style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        function openAddDeviceModal() {
            if (!isAdmin()) {
                alert('Admin access required to add devices');
                return;
            }
            
            // Clear form
            document.getElementById('deviceName').value = '';
            document.getElementById('deviceType').value = 'ZKTeco';
            document.getElementById('deviceIP').value = '';
            document.getElementById('devicePort').value = '4370';
            document.getElementById('deviceLat').value = '';
            document.getElementById('deviceLong').value = '';
            document.getElementById('deviceMode').value = 'real';
            
            document.getElementById('addDeviceModal').style.display = 'block';
        }
        
        function closeAddDeviceModal() {
            document.getElementById('addDeviceModal').style.display = 'none';
        }
        
        async function addDevice() {
            if (!isAdmin()) {
                alert('Admin access required to add devices');
                return;
            }
            
            const name = document.getElementById('deviceName').value.trim();
            const ip = document.getElementById('deviceIP').value.trim();
            
            if (!name || !ip) {
                alert('Device name and IP address are required!');
                return;
            }
            
            const device = {
                id: Date.now().toString(),
                name: name,
                type: document.getElementById('deviceType').value,
                ip: ip,
                port: document.getElementById('devicePort').value,
                latitude: document.getElementById('deviceLat').value.trim() || null,
                longitude: document.getElementById('deviceLong').value.trim() || null,
                mode: document.getElementById('deviceMode').value,
                status: 'offline',
                lastSync: null
            };
            
            devices.push(device);
            await saveDevicesToServer();
            
            // Log device addition
            logDeviceAction('add', device.name, `Added device: ${device.name} (${device.type}) at ${device.ip}:${device.port}`);
            
            loadDevices();
            updateDeviceDropdown();
            closeAddDeviceModal();
            
            alert('Device added successfully!');
        }
        
        function editDevice(deviceId) {
            if (!isAdmin()) {
                alert('Admin access required to edit devices');
                return;
            }
            
            const device = devices.find(d => d.id === deviceId);
            if (!device) return;
            
            document.getElementById('editDeviceName').value = device.name;
            document.getElementById('editDeviceType').value = device.type;
            document.getElementById('editDeviceIP').value = device.ip;
            document.getElementById('editDevicePort').value = device.port;
            document.getElementById('editDeviceLat').value = device.latitude || '';
            document.getElementById('editDeviceLong').value = device.longitude || '';
            document.getElementById('editDeviceMode').value = device.mode;
            
            document.getElementById('editDeviceModal').style.display = 'block';
            document.getElementById('editDeviceModal').dataset.deviceId = deviceId;
        }
        
        async function saveDeviceEdit() {
            const deviceId = document.getElementById('editDeviceModal').dataset.deviceId;
            const deviceIndex = devices.findIndex(d => d.id === deviceId);
            
            if (deviceIndex === -1) return;
            
            const oldDevice = {...devices[deviceIndex]};
            const name = document.getElementById('editDeviceName').value.trim();
            const ip = document.getElementById('editDeviceIP').value.trim();
            
            if (!name || !ip) {
                alert('Device name and IP address are required!');
                return;
            }
            
            devices[deviceIndex].name = name;
            devices[deviceIndex].type = document.getElementById('editDeviceType').value;
            devices[deviceIndex].ip = ip;
            devices[deviceIndex].port = document.getElementById('editDevicePort').value;
            devices[deviceIndex].latitude = document.getElementById('editDeviceLat').value.trim() || null;
            devices[deviceIndex].longitude = document.getElementById('editDeviceLong').value.trim() || null;
            devices[deviceIndex].mode = document.getElementById('editDeviceMode').value;
            
            await saveDevicesToServer();
            
            // Log device update with changes
            const changes = [];
            if (oldDevice.name !== name) changes.push(`name: ${oldDevice.name} → ${name}`);
            if (oldDevice.type !== devices[deviceIndex].type) changes.push(`type: ${oldDevice.type} → ${devices[deviceIndex].type}`);
            if (oldDevice.ip !== ip) changes.push(`IP: ${oldDevice.ip} → ${ip}`);
            if (oldDevice.port !== devices[deviceIndex].port) changes.push(`port: ${oldDevice.port} → ${devices[deviceIndex].port}`);
            if (oldDevice.latitude !== devices[deviceIndex].latitude) changes.push(`lat: ${oldDevice.latitude} → ${devices[deviceIndex].latitude}`);
            if (oldDevice.longitude !== devices[deviceIndex].longitude) changes.push(`long: ${oldDevice.longitude} → ${devices[deviceIndex].longitude}`);
            if (oldDevice.mode !== devices[deviceIndex].mode) changes.push(`mode: ${oldDevice.mode} → ${devices[deviceIndex].mode}`);
            
            const changeText = changes.length > 0 ? ` (${changes.join(', ')})` : '';
            logDeviceAction('update', name, `Updated device: ${name}${changeText}`);
            
            loadDevices();
            updateDeviceDropdown();
            closeEditDeviceModal();
            
            alert('Device updated successfully!');
        }
        
        function closeEditDeviceModal() {
            document.getElementById('editDeviceModal').style.display = 'none';
        }
        
        function editLastSync(deviceId) {
            if (!isAdmin()) {
                alert('Admin access required to edit last sync time');
                return;
            }
            
            const device = devices.find(d => d.id === deviceId);
            if (!device) return;
            
            const input = document.getElementById('editLastSyncInput');
            
            // Convert lastSync to datetime-local format if it exists
            if (device.lastSync && device.lastSync !== 'Never') {
                try {
                    const date = new Date(device.lastSync);
                    if (!isNaN(date.getTime())) {
                        // Format: YYYY-MM-DDTHH:mm:ss
                        const year = date.getFullYear();
                        const month = String(date.getMonth() + 1).padStart(2, '0');
                        const day = String(date.getDate()).padStart(2, '0');
                        const hours = String(date.getHours()).padStart(2, '0');
                        const minutes = String(date.getMinutes()).padStart(2, '0');
                        const seconds = String(date.getSeconds()).padStart(2, '0');
                        input.value = `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
                    } else {
                        input.value = '';
                    }
                } catch (e) {
                    input.value = '';
                }
            } else {
                input.value = '';
            }
            
            document.getElementById('editLastSyncModal').style.display = 'block';
            document.getElementById('editLastSyncModal').dataset.deviceId = deviceId;
        }
        
        async function saveLastSyncEdit() {
            const deviceId = document.getElementById('editLastSyncModal').dataset.deviceId;
            const input = document.getElementById('editLastSyncInput');
            const deviceIndex = devices.findIndex(d => d.id === deviceId);
            
            if (deviceIndex === -1) return;
            
            if (input.value) {
                const date = new Date(input.value);
                setDeviceLastSync(devices[deviceIndex], date);
            } else {
                devices[deviceIndex].lastSync = null;
                localStorage.removeItem(`lastSync_${deviceId}`);
            }
            
            await saveDevicesToServer();
            loadDevices();
            closeEditLastSyncModal();
            
            alert('Last sync time updated successfully!');
        }
        
        
        function setCurrentTime() {
            const input = document.getElementById('editLastSyncInput');
            const now = new Date();
            
            // Format: YYYY-MM-DDTHH:mm
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            
            input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
        }

        
        function closeEditLastSyncModal() {
            document.getElementById('editLastSyncModal').style.display = 'none';
        }
        
        function applyDeviceFilters() {
            const nameFilter = document.getElementById('filterDeviceName').value.toLowerCase();
            const typeFilter = document.getElementById('filterDeviceType').value;
            const statusFilter = document.getElementById('filterDeviceStatus').value;
            
            filteredDevices = devices.filter(device => {
                const matchesName = !nameFilter || device.name.toLowerCase().includes(nameFilter);
                const matchesType = !typeFilter || device.type === typeFilter;
                const matchesStatus = !statusFilter || device.status === statusFilter;
                
                return matchesName && matchesType && matchesStatus;
            });
            
            loadDevicesTable();
        }
        
        function clearDeviceFilters() {
            document.getElementById('filterDeviceName').value = '';
            document.getElementById('filterDeviceType').value = '';
            document.getElementById('filterDeviceStatus').value = '';
            
            filteredDevices = devices;
            loadDevicesTable();
        }

        let filteredDevices = [];
        
        function loadDevices() {
            filteredDevices = devices;
            loadDevicesTable();
        }
        
        function loadDevicesTable() {
            const tbody = document.getElementById('devicesTableBody');
            tbody.innerHTML = '';
            
            filteredDevices.forEach(device => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="padding: 10px; border: 1px solid #ddd;">${device.name}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${device.type}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${device.ip}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${device.port}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="color: ${device.mode === 'dummy' ? '#dc3545' : device.mode === 'adms' ? '#fd7e14' : '#28a745'}; font-weight: bold;">
                            ${device.mode === 'dummy' ? 'Dummy' : device.mode === 'adms' ? 'ADMS' : 'Real'}
                        </span>
                    </td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="background: ${device.status === 'online' ? '#28a745' : '#dc3545'}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">
                            ${device.status || 'offline'}
                        </span>
                    </td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span id="lastSync_${device.id}">${formatLastSync(device.lastSync)}</span>
                        ${isAdmin() ? `
                            <button onclick="editLastSync('${device.id}')" 
                                    style="background: none; border: none; color: #007cba; cursor: pointer; margin-left: 5px; font-size: 0.9em;" 
                                    title="Edit Last Sync Time">
                                ✏️
                            </button>
                        ` : ''}
                    </td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">
                        ${isAdmin() ? `
                            <button onclick="editDevice('${device.id}')" style="background: #007cba; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer;">Edit</button>
                            <button onclick="testDevice('${device.id}')" style="background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer;">Test</button>
                            <button onclick="syncDevice('${device.id}')" style="background: #ffc107; color: black; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer;">Sync</button>
                            <button onclick="deleteDevice('${device.id}')" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Delete</button>
                        ` : '<span style="color: #666; font-style: italic;">View Only</span>'}
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function updateDeviceDropdown() {
            const select = document.getElementById('selectedDevice');
            select.innerHTML = '<option value="">All Devices</option>';
            
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = device.name;
                select.appendChild(option);
            });
        }

        async function testDevice(deviceId) {
            if (!isAdmin()) {
                alert('Admin access required to test devices');
                return;
            }
            
            const device = devices.find(d => d.id === deviceId);
            if (!device) return;
            
            showLoader('Testing Device Connection...', `Connecting to ${device.ip}:${device.port}`);
            
            try {
                // If device is in dummy mode, simulate success
                if (device.mode === 'dummy') {
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
                    device.status = 'online';
                    await saveDevicesToServer();
                    loadDevices();
                    alert('Dummy device test successful!');
                    return;
                }
                
                const response = await fetch('/test-device', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip: device.ip, port: parseInt(device.port) })
                });
                
                const result = await response.json();
                device.status = result.success ? 'online' : 'offline';
                await saveDevicesToServer();
                loadDevices();
                
                const message = result.success ? 
                    'Device is online and responding!' : 
                    `Device connection failed: ${result.error || result.message || 'Unknown error'}`;
                    
                alert(message);
                
            } catch (error) {
                console.error('Test device error:', error);
                device.status = 'offline';
                await saveDevicesToServer();
                loadDevices();
                alert(`Test failed: ${error.message}`);
            } finally {
                hideLoader();
            }
        }

        async function discoverDevices() {
            if (!isAdmin()) {
                alert('Admin access required to discover devices');
                return;
            }
            
            showLoader('Discovering Devices...', 'Scanning network for biometric devices');
            
            try {
                // Simulate device discovery
                await new Promise(resolve => setTimeout(resolve, 3000));
                alert('Device discovery completed. No new devices found.');
            } catch (error) {
                alert('Discovery failed: ' + error.message);
            } finally {
                hideLoader();
            }
        }

        async function syncDevice(deviceId) {
            if (!isAdmin()) {
                alert('Admin access required to sync devices');
                return;
            }
            
            const device = devices.find(d => d.id === deviceId);
            if (!device) return;
            
            showLoader('Syncing Device to ERP...', `Fetching data from ${device.name} and sending to ERP`);
            
            try {
                // Get ERP config
                const erpConfig = {
                    system: document.getElementById('erpSystem').value,
                    url: document.getElementById('erpUrl').value,
                    apiKey: document.getElementById('erpApiKey').value
                };
                
                if (!erpConfig.url || !erpConfig.apiKey) {
                    alert('Please configure ERP settings first in the ERP Integration tab');
                    return;
                }
                
                
                // Determine start date based on lastSync
                const endDate = new Date();
                let startDate;
                
                // Check if device has a lastSync timestamp
                const lastSyncKey = `lastSync_${device.id}`;
                const lastSyncTime = localStorage.getItem(lastSyncKey);
                
                if (lastSyncTime) {
                    // Use lastSync as start date
                    startDate = parseSyncTime(lastSyncTime);
                    console.log(`Using lastSync as start date: ${startDate.toISOString()}`);
                } else if (device.lastSync && device.lastSync !== 'Never') {
                    // Fallback to device.lastSync if localStorage doesn't have it
                    try {
                        startDate = parseSyncTime(device.lastSync);
                        if (!startDate) throw new Error('Invalid lastSync');
                        console.log(`Using device.lastSync as start date: ${startDate.toISOString()}`);
                    } catch (e) {
                        // If parsing fails, default to 7 days
                        startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
                        console.log(`Failed to parse lastSync, using 7 days: ${startDate.toISOString()}`);
                    }
                } else {
                    // No lastSync, default to last 7 days
                    startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
                    console.log(`No lastSync found, using 7 days: ${startDate.toISOString()}`);
                }
                
                const useDummy = device.mode === 'dummy';
                const data = await fetchDeviceData(device, 
                    startDate.toISOString().split('T')[0], 
                    endDate.toISOString().split('T')[0], 
                    useDummy
                );
                
                
                if (!data.success || !data.punchRecords || data.punchRecords.length === 0) {
                    alert('No data found to sync from device');
                    return;
                }
                
                // Filter records to only include those AFTER lastSync
                let recordsToSync = data.punchRecords;
                if (startDate) {
                    recordsToSync = data.punchRecords.filter(record => {
                        const recordTime = new Date(record.timestamp);
                        return recordTime > startDate; // Only records AFTER lastSync
                    });
                    
                    if (recordsToSync.length === 0) {
                        alert(`No new records found after last sync (${startDate.toLocaleString()})`);
                        return;
                    }
                }
                
                // Send to ERP
                const response = await fetch('/send-to-erp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        data: recordsToSync.map(record => ({
                            ...record,
                            deviceName: device.name,
                            latitude: device.latitude,
                            longitude: device.longitude
                        })),
                        erpConfig: erpConfig
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    const successCount = result.details?.success || 0;
                    
                    console.log(`\n🔄 SYNC RESULT:`);
                    console.log(`  Success: ${result.success}`);
                    console.log(`  Success count: ${successCount}`);
                    console.log(`  Records sent: ${recordsToSync.length}`);
                    
                    // Only update lastSync if records were actually sent successfully to ERP
                    if (successCount > 0) {
                        console.log(`  ✅ Updating lastSync (successCount > 0)`);
                        
                        // Find the latest timestamp from the records that were synced
                        let latestRecordTime = null;
                        for (const record of recordsToSync) {
                            console.log(`    Checking record: ${record.timestamp}`);
                            const ts = new Date(record.timestamp);
                            console.log(`      Parsed as: ${ts.toISOString()} (valid: ${!isNaN(ts.getTime())})`);
                            if (!isNaN(ts.getTime())) {
                                if (!latestRecordTime || ts > latestRecordTime) {
                                    latestRecordTime = ts;
                                    console.log(`      ✅ New latest: ${latestRecordTime.toISOString()}`);
                                }
                            }
                        }

                        if (latestRecordTime) {
                            console.log(`  📅 Setting lastSync to: ${latestRecordTime.toISOString()} (${latestRecordTime.toLocaleString()})`);
                            setDeviceLastSync(device, latestRecordTime);
                        } else {
                            console.warn(`  ⚠️ No valid latestRecordTime found! lastSync NOT updated`);
                        }

                        await saveDevicesToServer();
                        loadDevices();
                    } else {
                        console.log(`  ❌ NOT updating lastSync (successCount = ${successCount})`);
                    }
                    console.log(`🔄 END SYNC RESULT\n`);
                    
                    const skippedCount = result.details?.skipped || 0;
                    const failedCount = result.details?.errors || 0;
                    
                    let message = `Device sync completed!\n\nResults:\n- ${successCount} records sent to ERP\n`;
                    if (skippedCount > 0) message += `- ${skippedCount} records skipped\n`;
                    if (failedCount > 0) message += `- ${failedCount} records failed\n`;
                    
                    alert(message);
                } else {
                    alert(`Sync failed: ${result.error}`);
                }
                
            } catch (error) {
                alert('Sync failed: ' + error.message);
            } finally {
                hideLoader();
            }
        }

        async function testAllDevices() {
            if (!isAdmin()) {
                alert('Admin access required to test devices');
                return;
            }
            
            if (devices.length === 0) {
                alert('No devices to test');
                return;
            }
            
            showLoader('Testing All Devices...', `Testing ${devices.length} device(s)`);
            
            try {
                let successCount = 0;
                for (const device of devices) {
                    try {
                        const response = await fetch('/test-device', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ ip: device.ip, port: parseInt(device.port) })
                        });
                        
                        const result = await response.json();
                        device.status = result.success ? 'online' : 'offline';
                        if (result.success) successCount++;
                    } catch (error) {
                        device.status = 'offline';
                    }
                }
                
                await saveDevicesToServer();
                loadDevices();
                alert(`Testing completed: ${successCount}/${devices.length} devices online`);
            } catch (error) {
                alert('Test all failed: ' + error.message);
            } finally {
                hideLoader();
            }
        }

        async function deleteDevice(deviceId) {
            if (!isAdmin()) {
                alert('Admin access required to delete devices');
                return;
            }
            
            const device = devices.find(d => d.id === deviceId);
            if (!device) return;
            
            if (confirm('Are you sure you want to delete this device?')) {
                devices = devices.filter(d => d.id !== deviceId);
                await saveDevicesToServer();
                
                // Log device deletion
                logDeviceAction('delete', device.name, `Deleted device: ${device.name} (${device.type}) at ${device.ip}:${device.port}`);
                
                loadDevices();
            }
        }

        let loaderSubtextLastUpdate = 0;
        const LOADER_SUBTEXT_INTERVAL = 800;

        function updateLoaderSubtext(text, force = false) {
            const now = Date.now();
            if (!force && now - loaderSubtextLastUpdate < LOADER_SUBTEXT_INTERVAL) {
                return;
            }
            const subtextEl = document.getElementById('loaderSubtext');
            if (subtextEl) {
                subtextEl.textContent = text;
                loaderSubtextLastUpdate = now;
            }
        }

        async function fetchAllData() {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const selectedDevice = document.getElementById('selectedDevice').value;
            const dummyMode = document.getElementById('dummyMode').checked;
            console.log('Report fetch started', { startDate, endDate, selectedDevice, dummyMode, devices: devices.map(d => ({ id: d.id, name: d.name, ip: d.ip, mode: d.mode })) });
            
            const deviceCount = selectedDevice ? 1 : devices.length;
            loaderSubtextLastUpdate = 0;
            showLoader('Fetching Attendance Data...', `Processing ${deviceCount} device(s) from ${startDate || 'all dates'} to ${endDate || 'today'}`);
            updateLoaderSubtext('Connecting to devices...', true);
            
            try {
                let allData = [];
                
                if (selectedDevice) {
                    const device = devices.find(d => d.id === selectedDevice);
                    if (device) {
                        const data = await fetchDeviceData(device, startDate, endDate, dummyMode);
                        console.log('Report selected device response', device.name, data);
                        if (data.success) {
                            // Enrich records with device name
                            allData = (data.punchRecords || []).map(record => ({
                                ...record,
                                deviceName: device.name || device.ip || 'Unknown Device',
                                latitude: device.latitude,
                                longitude: device.longitude
                            }));
                        }
                    }
                } else {
                    // Fetch from all devices
                    for (let i = 0; i < devices.length; i++) {
                        const device = devices[i];
                        updateLoaderSubtext(`Fetching device ${i + 1} of ${deviceCount}...`);
                        const data = await fetchDeviceData(device, startDate, endDate, dummyMode);
                        console.log('Report device response', device.name, data);
                        if (data.success) {
                            allData = allData.concat((data.punchRecords || []).map(record => ({
                                ...record,
                                deviceName: device.name || device.ip || 'Unknown Device',
                                latitude: device.latitude,
                                longitude: device.longitude
                            })));
                        }
                        updateLoaderSubtext(`Completed ${i + 1}/${deviceCount} device responses...`);
                    }
                }
                
                allRecords = allData;
                console.log('Report fetch completed records', allData.length);
                filteredRecords = allData;
                currentPage = 1;
                showDataStats();
                displayRecords();
                document.getElementById('exportOptions').style.display = 'flex';
                
            } catch (error) {
                document.getElementById('dataResult').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
            } finally {
                hideLoader();
            }
        }

        async function fetchDeviceData(device, startDate, endDate, dummyMode) {
            // Use device's mode if global dummy mode is not set
            const useDummy = dummyMode || device.mode === 'dummy';
            
            const params = new URLSearchParams({
                ip: device.ip,
                port: device.port,
                startDate: startDate,
                endDate: endDate,
                dummy: useDummy,
                mode: device.mode || 'real'
            });
            
            const response = await fetch('/fetch?' + params);
            const result = await response.json();
            console.log('fetchDeviceData result', device.name || device.ip, result.success, result.message || result.error, (result.punchRecords || []).length);
            return result;
        }

        function showDataStats() {
            const stats = calculateStats(allRecords);
            const statsContainer = document.getElementById('dataStats');
            
            statsContainer.innerHTML = `
                <div class="stat-card" style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #007cba;">${stats.totalRecords}</div>
                    <div>Total Records</div>
                </div>
                <div class="stat-card" style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #007cba;">${stats.uniqueEmployees}</div>
                    <div>Employees</div>
                </div>
                <div class="stat-card" style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #007cba;">${stats.checkIns}</div>
                    <div>Check Ins</div>
                </div>
                <div class="stat-card" style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #007cba;">${stats.checkOuts}</div>
                    <div>Check Outs</div>
                </div>
            `;
            
            statsContainer.style.display = 'flex';
        }

        function calculateStats(records) {
            return {
                totalRecords: filteredRecords.length,
                uniqueEmployees: new Set(filteredRecords.map(r => r.employeeId)).size,
                checkIns: filteredRecords.filter(r => r.punchType === 'check-in').length,
                checkOuts: filteredRecords.filter(r => r.punchType === 'check-out').length
            };
        }

        function displayRecords() {
            const start = (currentPage - 1) * recordsPerPage;
            const end = start + recordsPerPage;
            const pageRecords = filteredRecords.slice(start, end);
            
            let html = '<table><tr><th>Employee Name</th><th>Employee ID</th><th>Date & Time</th><th>Type</th>';
            if (devices.length > 1) html += '<th>Device</th>';
            html += '</tr>';
            
            pageRecords.forEach(record => {
                const date = new Date(record.timestamp);
                html += '<tr>';
                html += '<td><strong>' + record.employeeName + '</strong></td>';
                html += '<td>' + record.employeeId + '</td>';
                html += '<td>' + date.toLocaleString() + '</td>';
                html += '<td><span style="color: ' + (record.punchType === 'check-in' ? '#28a745' : '#dc3545') + '; font-weight: bold;">' + (record.punchType === 'check-in' ? 'IN' : 'OUT') + '</span></td>';
                if (devices.length > 1) html += '<td>' + (record.deviceName || 'Unknown') + '</td>';
                html += '</tr>';
            });
            
            html += '</table>';
            
            document.getElementById('dataResult').innerHTML = html;
            document.getElementById('dataResult').style.display = 'block';
            showPagination();
        }

        function showPagination() {
            const totalPages = Math.ceil(filteredRecords.length / recordsPerPage);
            const paginationContainer = document.getElementById('pagination');
            
            let html = '';
            
            if (currentPage > 1) {
                html += '<button onclick="changePage(' + (currentPage - 1) + ')" style="width: auto; padding: 8px 12px;">Previous</button>';
            }
            
            for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
                html += '<button onclick="changePage(' + i + ')" ' + (i === currentPage ? 'style="background: #005a8b; width: auto; padding: 8px 12px;"' : 'style="width: auto; padding: 8px 12px;"') + '>' + i + '</button>';
            }
            
            if (currentPage < totalPages) {
                html += '<button onclick="changePage(' + (currentPage + 1) + ')" style="width: auto; padding: 8px 12px;">Next</button>';
            }
            
            paginationContainer.innerHTML = html;
            paginationContainer.style.display = totalPages > 1 ? 'flex' : 'none';
        }

        function changePage(page) {
            currentPage = page;
            displayRecords();
        }

        async function exportData(format) {
            showLoader('Exporting Data...', `Preparing ${allRecords.length} records`);
            
            try {
                const response = await fetch('/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        format: format,
                        data: allRecords
                    })
                });
                
                
                if (response.ok) {
                    const blob = await response.blob();
                    const arrayBuffer = await blob.arrayBuffer();
                    // Use proper file extensions
                    const extension = format === 'excel' ? 'xlsx' : format;
                    const fileName = `attendance_${new Date().toISOString().split('T')[0]}.${extension}`;

                    const toBase64 = buffer => new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result.split(',')[1]);
                        reader.onerror = reject;
                        reader.readAsDataURL(new Blob([buffer]));
                    });

                    const fileBase64 = await toBase64(arrayBuffer);

                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.download_blob === 'function') {
                        const saved = await window.pywebview.api.download_blob(fileName, fileBase64);
                        if (!saved) {
                            alert('Download cancelled.');
                        }
                    } else {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = fileName;
                        a.click();
                        window.URL.revokeObjectURL(url);
                    }
                } else {
                    alert('Export failed');
                }
            } catch (error) {
                alert('Export error: ' + error.message);
            } finally {
                hideLoader();
            }
        }

        async function testERPConnection() {
            if (!isAdmin()) {
                alert('Admin access required to test ERP connection');
                return;
            }
            
            const erpSystem = document.getElementById('erpSystem').value;
            const erpUrl = document.getElementById('erpUrl').value;
            const erpApiKey = document.getElementById('erpApiKey').value;
            
            showLoader('Testing ERP...', `Connecting to ${erpSystem}`);
            
            try {
                const response = await fetch('/test-erp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        system: erpSystem,
                        url: erpUrl,
                        apiKey: erpApiKey
                    })
                });
                
                const result = await response.json();
                document.getElementById('erpStatus').innerHTML = result.success ? 
                    '<div class="success">ERP connection successful!</div>' : 
                    '<div class="error">ERP connection failed: ' + result.error + '</div>';
                document.getElementById('erpStatus').style.display = 'block';
            } catch (error) {
                document.getElementById('erpStatus').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                document.getElementById('erpStatus').style.display = 'block';
            } finally {
                hideLoader();
            }
        }

        async function sendToERP() {
            if (!isAdmin()) {
                alert('Admin access required to send data to ERP');
                return;
            }
            
            if (allRecords.length === 0) {
                alert('No data to send to ERP');
                return;
            }
            
            const erpConfig = {
                system: document.getElementById('erpSystem').value,
                url: document.getElementById('erpUrl').value,
                apiKey: document.getElementById('erpApiKey').value
            };
            
            if (!erpConfig.url || !erpConfig.apiKey) {
                alert('Please configure ERP settings first');
                return;
            }
            
            showLoader('Sending to ERP...', `Uploading ${allRecords.length} records`);
            
            try {
                const response = await fetch('/send-to-erp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        data: allRecords,
                        erpConfig: erpConfig
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                
                const result = await response.json();
                alert(result.success ? result.message : 'Failed: ' + result.error);
            } catch (error) {
                console.error('ERP sync error:', error);
                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    alert('Network Error: Unable to connect to server. Please check your internet connection.');
                } else {
                    alert('Error: ' + error.message);
                }
            } finally {
                hideLoader();
            }
        }

        // Auto-sync variables
        let autoSyncInterval = null;
        let lastSyncTime = null;
        let syncStats = { total: 0, success: 0, failed: 0 };
        
        async function saveSettings() {
            if (!isAdmin()) {
                alert('Admin access required to save settings');
                return;
            }
            
            // Wait for both saves to complete
            await Promise.all([
                saveERPConfig(),
                saveAutoSyncSettings()
            ]);
            
            alert('Settings saved!');
        }
        
        async function saveAutoSyncSettings() {
            const autoSyncSettings = {
                enabled: document.getElementById('autoSyncEnabled').checked,
                interval: parseInt(document.getElementById('syncInterval').value),
                testMode: document.getElementById('testModeEnabled').checked
            };

            const punchFilterSettings = {
                enabled: document.getElementById('punchFilterEnabled').checked,
                intervalSeconds: parseInt(document.getElementById('punchFilterInterval').value)
            };

            // Save to localStorage for immediate use
            localStorage.setItem('autoSyncSettings', JSON.stringify(autoSyncSettings));
            localStorage.setItem('punchFilterSettings', JSON.stringify(punchFilterSettings));

            if (!appSettings || typeof appSettings !== 'object') {
                appSettings = {};
            }
            appSettings.autoSync = autoSyncSettings;
            appSettings.punchFilter = punchFilterSettings;

            // Save to server for persistence across EXE restarts
            try {
                await saveSettingsToServer();
                console.log('✓ Auto-sync settings saved to server and localStorage');
            } catch (error) {
                console.error('Error saving auto-sync settings to server:', error);
            }

            try {
                await loadSettingsFromServer();
                applyLoadedSettings();
            } catch (error) {
                console.error('Error refreshing settings after save:', error);
            }
        }
        
        async function loadAutoSyncSettings() {
            // Try to load from server first (persists across EXE restarts)
            try {
                const response = await fetch('/api/settings');
                if (response.ok) {
                    const data = await response.json();
                    if (data && data.autoSync) {
                        const settings = data.autoSync;
                        document.getElementById('autoSyncEnabled').checked = settings.enabled || false;
                        document.getElementById('syncInterval').value = settings.interval || 5;
                        document.getElementById('testModeEnabled').checked = settings.testMode || false;
                        
                        // Also save to localStorage for quick access
                        localStorage.setItem('autoSyncSettings', JSON.stringify(settings));
                        
                        console.log('✓ Auto-sync settings loaded from server');
                    }
                    if (data && data.punchFilter) {
                        const pf = data.punchFilter;
                        document.getElementById('punchFilterEnabled').checked = pf.enabled || false;
                        document.getElementById('punchFilterInterval').value = pf.intervalSeconds || 3;
                        localStorage.setItem('punchFilterSettings', JSON.stringify(pf));
                    }
                    applyLoadedSettings();
                    return;
                }
            } catch (error) {
                console.error('Error loading auto-sync settings from server:', error);
            }

            // Fallback to localStorage if server load fails
            const saved = localStorage.getItem('autoSyncSettings');
            if (saved) {
                const settings = JSON.parse(saved);
                document.getElementById('autoSyncEnabled').checked = settings.enabled || false;
                document.getElementById('syncInterval').value = settings.interval || 5;
                document.getElementById('testModeEnabled').checked = settings.testMode || false;

                console.log('✓ Auto-sync settings loaded from localStorage (fallback)');
            }

            const savedPunchFilter = localStorage.getItem('punchFilterSettings');
            if (savedPunchFilter) {
                const pf = JSON.parse(savedPunchFilter);
                document.getElementById('punchFilterEnabled').checked = pf.enabled || false;
                document.getElementById('punchFilterInterval').value = pf.intervalSeconds || 3;
                console.log('✓ Punch filter settings loaded from localStorage (fallback)');
            }

            // Don't auto-start sync on load - let user manually start it
            // This prevents errors when devices/ERP not yet loaded
        }

        function applyLoadedSettings() {
            appSettings.punchFilter = appSettings.punchFilter || {
                enabled: document.getElementById('punchFilterEnabled').checked,
                intervalSeconds: parseInt(document.getElementById('punchFilterInterval').value) || 3
            };
        }

        function parseSyncTime(value) {
            if (!value || value === 'Never') return null;
            const parsed = new Date(value);
            return Number.isNaN(parsed.getTime()) ? null : parsed;
        }

        function setDeviceLastSync(device, latestTime) {
            if (!device || !latestTime || Number.isNaN(latestTime.getTime())) return;
            const syncTimeISO = latestTime.toISOString();
            device.lastSync = syncTimeISO;
            localStorage.setItem(`lastSync_${device.id}`, syncTimeISO);
        }

        function formatLastSync(value) {
            const parsed = parseSyncTime(value);
            return parsed ? parsed.toLocaleString() : (value || 'Never');
        }
        
        function toggleAutoSync() {
            if (!isAdmin()) {
                alert('Admin access required to control auto-sync');
                return;
            }
            
            const enabled = document.getElementById('autoSyncEnabled').checked;
            if (enabled) {
                startAutoSync();
            } else {
                stopAutoSync();
            }
        }
        
        function startAutoSync() {
            if (autoSyncInterval) {
                clearInterval(autoSyncInterval);
            }
            
            const intervalMinutes = parseInt(document.getElementById('syncInterval').value);
            const intervalMs = intervalMinutes * 60 * 1000;
            
            document.getElementById('autoSyncEnabled').checked = true;
            document.getElementById('autoSyncToggle').textContent = 'Stop Auto-Sync';
            document.getElementById('syncStatusText').textContent = `Running (every ${intervalMinutes} min)`;
            document.getElementById('autoSyncStatus').style.background = '#d4edda';
            
            // Start the interval
            autoSyncInterval = setInterval(performAutoSync, intervalMs);
            
            // Don't perform initial sync to avoid startup errors
            // Initial sync will happen after the first interval
            
            addSyncLog('Auto-sync started', 'info');
            saveAutoSyncSettings();
        }
        
        function stopAutoSync() {
            if (autoSyncInterval) {
                clearInterval(autoSyncInterval);
                autoSyncInterval = null;
            }
            
            document.getElementById('autoSyncEnabled').checked = false;
            document.getElementById('autoSyncToggle').textContent = 'Start Auto-Sync';
            document.getElementById('syncStatusText').textContent = 'Disabled';
            document.getElementById('autoSyncStatus').style.background = '#f8f9fa';
            
            addSyncLog('Auto-sync stopped', 'info');
            saveAutoSyncSettings();
        }
        
        async function performAutoSync() {
            try {
                // Check if devices are loaded and available
                if (!devices || !Array.isArray(devices) || devices.length === 0) {
                    console.log('Auto-sync skipped: No devices configured');
                    return;
                }
                
                // Get ERP config
                const erpConfig = {
                    system: document.getElementById('erpSystem')?.value,
                    url: document.getElementById('erpUrl')?.value,
                    apiKey: document.getElementById('erpApiKey')?.value
                };
                
                if (!erpConfig.url || !erpConfig.apiKey) {
                    console.log('Auto-sync skipped: ERP not configured');
                    return;
                }
                
                // Check if test mode is enabled
                const testMode = document.getElementById('testModeEnabled')?.checked || false;
                
                // Get new punches from all devices
                let allNewRecords = [];
                const deviceLatestTimes = {}; // Track latest time per device
                const now = new Date();
                
                if (testMode) {
                    const since = lastSyncTime || new Date(now.getTime() - 24 * 60 * 60 * 1000);
                    allNewRecords = generateTestSyncData(since, now);
                    addSyncLog(`Generated ${allNewRecords.length} test records`, 'info');
                } else {
                    // Get real data from devices - use per-device lastSync
                    for (const device of devices) {
                        try {
                            // Get device-specific lastSync
                            let deviceLastSync = null;
                            const lastSyncKey = `lastSync_${device.id}`;
                            const storedLastSync = localStorage.getItem(lastSyncKey);
                            
                            if (storedLastSync) {
                                deviceLastSync = parseSyncTime(storedLastSync);
                            } else if (device.lastSync && device.lastSync !== 'Never') {
                                try {
                                    deviceLastSync = parseSyncTime(device.lastSync);
                                } catch (e) {
                                    // Parsing failed, use 7 days
                                }
                            }
                            
                            // Default to 7 days if no lastSync
                            const since = deviceLastSync || new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                            
                            // Use dummy mode if device is set to dummy
                            const useDummy = device.mode === 'dummy';
                            const data = await fetchDeviceData(device, 
                                since.toISOString().split('T')[0], 
                                now.toISOString().split('T')[0], 
                                useDummy
                            );
                        
                        if (data.success && data.punchRecords) {
                            // Filter records newer than device's last sync
                            const newRecords = data.punchRecords.filter(record => {
                                const recordTime = new Date(record.timestamp);
                                return !deviceLastSync || recordTime > deviceLastSync;
                            });
                            addSyncLog(`${device.name}: fetched ${data.punchRecords.length}, new ${newRecords.length}`, newRecords.length > 0 ? 'info' : 'info');

                            if (newRecords.length > 0) {
                                // Track latest time for this device
                                let deviceLatest = deviceLastSync;
                                newRecords.forEach(record => {
                                    const recordTime = new Date(record.timestamp);
                                    if (!deviceLatest || recordTime > deviceLatest) {
                                        deviceLatest = recordTime;
                                    }
                                });
                                deviceLatestTimes[device.id] = deviceLatest;


                                allNewRecords = allNewRecords.concat(newRecords.map(record => ({
                                    ...record,
                                    deviceName: device.name || device.ip || 'Unknown Device',
                                    latitude: device.latitude,
                                    longitude: device.longitude
                                })));
                            }
                        }
                    } catch (error) {
                        console.error(`Error fetching from device ${device.name}:`, error);
                        addSyncLog(`${device.name}: Fetch error - ${error.message}`, 'error');
                    }
                }
                }
                
                if (allNewRecords.length === 0) {
                    console.log('Auto-sync: No new punches found');
                    addSyncLog('No new punches found', 'info');
                    return;
                }
                
                // Send to ERP
                const response = await fetch('/send-to-erp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        data: allNewRecords,
                        erpConfig: erpConfig
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    syncStats.total += allNewRecords.length;
                    syncStats.success += result.details?.success || 0;
                    syncStats.failed += result.details?.errors || 0;
                    
                    const successCount = result.details?.success || 0;
                    const skippedCount = result.details?.skipped || 0;
                    const failedCount = result.details?.errors || 0;
                    
                    let message = `Synced: ${successCount} sent`;
                    if (skippedCount > 0) message += `, ${skippedCount} skipped`;
                    if (failedCount > 0) message += `, ${failedCount} failed`;
                    
                    addSyncLog(message, 'success');
                    
                    // Show detailed sync results
                    if (result.details?.success_list) {
                        result.details.success_list.forEach(success => {
                            addSyncLog(`✅ Success: ${success}`, 'success');
                        });
                    }
                    
                    if (result.details?.skipped_list) {
                        result.details.skipped_list.forEach(skipped => {
                            addSyncLog(`⏩ Skipped: ${skipped}`, 'info');
                        });
                    }
                    
                    if (result.details?.error_list) {
                        result.details.error_list.forEach(error => {
                            addSyncLog(`❌ Failed: ${error}`, 'error');
                        });
                    }
                    
                    
                    lastSyncTime = lastSyncTime || now;

                    // Update last sync time for devices that had successful syncs
                    if (successCount > 0 && Object.keys(deviceLatestTimes).length > 0) {
                        // Update each device's lastSync individually
                        for (const [deviceId, latestTime] of Object.entries(deviceLatestTimes)) {
                            const device = devices.find(d => d.id === deviceId);
                            if (device) {
                                setDeviceLastSync(device, latestTime);
                            }
                        }
                        await saveDevicesToServer();
                        loadDevices(); // Refresh device display
                    }
                } else {
                    syncStats.failed += allNewRecords.length;
                    
                    // Get error message from result.error or result.message or default
                    const errorMsg = result.error || result.message || 'Unknown sync error';
                    addSyncLog(`Sync failed: ${errorMsg}`, 'error');
                    
                    // Show detailed error info
                    if (result.details?.error_list && result.details.error_list.length > 0) {
                        result.details.error_list.forEach(error => {
                            addSyncLog(`Detail: ${error}`, 'error');
                        });
                    }
                }
                
                updateSyncStats();
                
            } catch (error) {
                console.error('Auto-sync error:', error);
                // Only log critical errors to sync history
                if (error.message && !error.message.includes('devices') && !error.message.includes('undefined')) {
                    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                        addSyncLog('Network error: Unable to connect. Check internet connection.', 'error');
                    } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                        addSyncLog('Connection error: Server unreachable', 'error');
                    } else {
                        addSyncLog(`Auto-sync error: ${error.message}`, 'error');
                    }
                }
                // Don't stop auto-sync on error, just log it
            }
        }
        
        function syncNow() {
            if (!isAdmin()) {
                alert('Admin access required to sync now');
                return;
            }
            
            addSyncLog('Manual sync triggered', 'info');
            performAutoSync();
        }
        
        function openCustomSyncModal() {
            if (!isAdmin()) {
                alert('Admin access required for custom sync');
                return;
            }
            
            // Set default to yesterday
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            document.getElementById('customSyncDate').value = yesterday.toISOString().split('T')[0];
            document.getElementById('customSyncTime').value = '00:00';
            
            document.getElementById('customSyncModal').style.display = 'block';
        }
        
        function closeCustomSyncModal() {
            document.getElementById('customSyncModal').style.display = 'none';
        }
        
        async function performCustomSync() {
            const syncDate = document.getElementById('customSyncDate').value;
            const syncTime = document.getElementById('customSyncTime').value;
            
            if (!syncDate || !syncTime) {
                alert('Please select both date and time');
                return;
            }
            
            const customStartTime = new Date(`${syncDate}T${syncTime}`);
            const now = new Date();
            
            if (customStartTime >= now) {
                alert('Sync date/time must be in the past');
                return;
            }
            
            closeCustomSyncModal();
            
            try {
                // Get ERP config
                const erpConfig = {
                    system: document.getElementById('erpSystem').value,
                    url: document.getElementById('erpUrl').value,
                    apiKey: document.getElementById('erpApiKey').value
                };
                
                if (!erpConfig.url || !erpConfig.apiKey) {
                    alert('Please configure ERP settings first');
                    return;
                }
                
                addSyncLog(`Custom sync started from ${customStartTime.toLocaleString()}`, 'info');
                
                let totalSynced = 0;
                let latestRecordTime = null;        
                
                for (const device of devices) {
                    try {
                        addSyncLog(`Syncing ${device.name} from ${customStartTime.toLocaleString()}`, 'info');
                        
                        // Fetch data from custom start time
                        const useDummy = device.mode === 'dummy';
                        const data = await fetchDeviceData(device, 
                            customStartTime.toISOString().split('T')[0], 
                            now.toISOString().split('T')[0], 
                            useDummy
                        );
                        
                        if (data.success && data.punchRecords && data.punchRecords.length > 0) {
                            // Filter records newer than custom start time
                            const newRecords = data.punchRecords.filter(record => {
                                const recordTime = new Date(record.timestamp);
                                return recordTime >= customStartTime;
                            });

                            if (newRecords.length > 0) {
                                newRecords.forEach(record => {
                                    const recordTime = new Date(record.timestamp);
                                    if (!latestRecordTime || recordTime > latestRecordTime) {
                                        latestRecordTime = recordTime;
                                    }
                                });

                                // Send to ERP
                                const response = await fetch('/send-to-erp', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        data: newRecords.map(record => ({
                                            ...record,
                                            deviceName: device.name || device.ip || 'Unknown Device',
                                            latitude: device.latitude,
                                            longitude: device.longitude
                                        })),
                                        erpConfig: erpConfig
                                    })
                                });
                                
                                const result = await response.json();
                                
                                if (result.success) {
                                    const successCount = result.details?.success || 0;
                                    totalSynced += successCount;

                                    // Update last sync time only if records were successfully sent
                                    if (successCount > 0) {
                                        const latestTime = latestRecordTime || now;
                                        setDeviceLastSync(device, latestTime);
                                    }
                                    
                                    addSyncLog(`${device.name}: ${successCount} records synced`, 'success');
                                } else {
                                    addSyncLog(`${device.name}: Sync failed - ${result.error}`, 'error');
                                }
                            } else {
                                addSyncLog(`${device.name}: No new records found`, 'info');
                            }
                        } else {
                            addSyncLog(`${device.name}: No data available`, 'info');
                        }
                        
                    } catch (error) {
                        addSyncLog(`${device.name}: Error - ${error.message}`, 'error');
                    }
                }
                
                // Update devices and show summary
                await saveDevicesToServer();
                loadDevices();
                
                addSyncLog(`Custom sync completed: ${totalSynced} total records synced from ${customStartTime.toLocaleString()}`, 'success');
                
                if (totalSynced > 0) {
                    alert(`Custom sync completed successfully!\n\n${totalSynced} records synced from ${customStartTime.toLocaleString()}`);
                } else {
                    alert('Custom sync completed - No new records found to sync');
                }
                
            } catch (error) {
                addSyncLog(`Custom sync failed: ${error.message}`, 'error');
                alert('Custom sync failed: ' + error.message);
            }
        }
        
        function updateSyncStats() {
            const statsDiv = document.getElementById('syncStats');
            statsDiv.innerHTML = `Total: ${syncStats.total} | Success: ${syncStats.success} | Failed: ${syncStats.failed}`;
        }
        
        function addSyncLog(message, type = 'info') {
            const historyDiv = document.getElementById('syncHistory');
            if (!historyDiv) return; // Safety check
            
            const timestamp = new Date().toLocaleString();
            
            const logEntry = document.createElement('div');
            logEntry.style.marginBottom = '5px';
            logEntry.style.padding = '5px';
            logEntry.style.borderRadius = '3px';
            
            const colors = {
                'info': '#d1ecf1',
                'success': '#d4edda', 
                'warning': '#fff3cd',
                'error': '#f8d7da'
            };
            
            logEntry.style.background = colors[type] || colors.info;
            logEntry.innerHTML = `<small>${timestamp}</small><br>${message}`;
            
            // Remove "No sync history" message
            if (historyDiv.children.length === 1 && historyDiv.children[0].textContent.includes('No sync history')) {
                historyDiv.innerHTML = '';
            }
            
            historyDiv.insertBefore(logEntry, historyDiv.firstChild);
            
            // Keep only last 20 entries
            while (historyDiv.children.length > 20) {
                historyDiv.removeChild(historyDiv.lastChild);
            }
            
            // Save sync history to localStorage
            saveSyncHistory();
        }
        
        async function saveSyncHistory() {
            try {
                const historyDiv = document.getElementById('syncHistory');
                if (!historyDiv) return;
                
                const logs = [];
                for (let i = 0; i < Math.min(historyDiv.children.length, 20); i++) {
                    const child = historyDiv.children[i];
                    logs.push({
                        html: child.innerHTML,
                        background: child.style.background
                    });
                }
                
                // Save to localStorage for immediate use
                localStorage.setItem('syncHistory', JSON.stringify(logs));
                
                // Save to server for persistence across EXE restarts
                try {
                    await fetch('/api/sync-history', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(logs)
                    });
                } catch (error) {
                    console.error('Error saving sync history to server:', error);
                }
            } catch (error) {
                console.error('Error saving sync history:', error);
            }
        }
        
        async function loadSyncHistory() {
            try {
                const historyDiv = document.getElementById('syncHistory');
                if (!historyDiv) return;
                
                // Try to load from server first (persists across EXE restarts)
                try {
                    const response = await fetch('/api/sync-history');
                    if (response.ok) {
                        const logs = await response.json();
                        if (logs && logs.length > 0) {
                            historyDiv.innerHTML = '';
                            logs.forEach(log => {
                                const logEntry = document.createElement('div');
                                logEntry.style.marginBottom = '5px';
                                logEntry.style.padding = '5px';
                                logEntry.style.borderRadius = '3px';
                                logEntry.style.background = log.background;
                                logEntry.innerHTML = log.html;
                                historyDiv.appendChild(logEntry);
                            });
                            
                            // Also save to localStorage for quick access
                            localStorage.setItem('syncHistory', JSON.stringify(logs));
                            
                            console.log('✓ Sync history loaded from server (' + logs.length + ' entries)');
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Error loading sync history from server:', error);
                }
                
                // Fallback to localStorage if server load fails
                const saved = localStorage.getItem('syncHistory');
                if (saved) {
                    const logs = JSON.parse(saved);
                    historyDiv.innerHTML = '';
                    logs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.style.marginBottom = '5px';
                        logEntry.style.padding = '5px';
                        logEntry.style.borderRadius = '3px';
                        logEntry.style.background = log.background;
                        logEntry.innerHTML = log.html;
                        historyDiv.appendChild(logEntry);
                    });
                    
                    console.log('✓ Sync history loaded from localStorage (fallback)');
                }
            } catch (error) {
                console.error('Error loading sync history:', error);
            }
        }
        
        function generateTestSyncData(since, now) {
            // Generate 1-3 random test records
            const recordCount = Math.floor(Math.random() * 3) + 1;
            const testRecords = [];
            
            const testEmployees = ['101', '102', '103', '132', '110', '133'];
            const testNames = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown', 'Mike Davis', 'Sarah Johnson'];
            
            for (let i = 0; i < recordCount; i++) {
                const employeeIndex = Math.floor(Math.random() * testEmployees.length);
                const randomTime = new Date(since.getTime() + Math.random() * (now.getTime() - since.getTime()));
                
                testRecords.push({
                    employeeId: testEmployees[employeeIndex],
                    employeeName: testNames[employeeIndex],
                    timestamp: randomTime.toISOString(),
                    punchType: Math.random() > 0.5 ? 'check-in' : 'check-out',
                    deviceName: 'Test Device'
                });
            }
            
            return testRecords;
        }
        
        function clearSyncHistory() {
            if (!isAdmin()) {
                alert('Admin access required to clear sync history');
                return;
            }
            
            if (confirm('Clear sync history?')) {
                document.getElementById('syncHistory').innerHTML = '<div style="color: #666; text-align: center;">No sync history yet</div>';
                syncStats = { total: 0, success: 0, failed: 0 };
                updateSyncStats();
                lastSyncTime = null;
                
                // Clear from localStorage
                localStorage.removeItem('syncHistory');
                
                // Clear from server
                try {
                    fetch('/api/sync-history', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify([])
                    });
                } catch (error) {
                    console.error('Error clearing sync history from server:', error);
                }
                
                console.log('✓ Sync history cleared');
            }
        }

        async function saveERPConfig() {
            const erpConfig = {
                system: document.getElementById('erpSystem').value,
                url: document.getElementById('erpUrl').value,
                apiKey: document.getElementById('erpApiKey').value
            };
            
            // Save to localStorage for immediate use
            localStorage.setItem('erpConfig', JSON.stringify(erpConfig));
            
            // Save to server for persistence across EXE restarts
            try {
                await fetch('/api/erp-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(erpConfig)
                });
                console.log('✓ ERP config saved to server and localStorage:', erpConfig);
            } catch (error) {
                console.error('Error saving ERP config to server:', error);
            }
        }

        async function loadERPConfig() {
            // Try to load from server first (persists across EXE restarts)
            try {
                const response = await fetch('/api/erp-config');
                if (response.ok) {
                    const config = await response.json();
                    if (config && Object.keys(config).length > 0) {
                        const systemEl = document.getElementById('erpSystem');
                        const urlEl = document.getElementById('erpUrl');
                        const apiKeyEl = document.getElementById('erpApiKey');
                        
                        if (systemEl) systemEl.value = config.system || 'frappe';
                        if (urlEl) urlEl.value = config.url || '';
                        if (apiKeyEl) apiKeyEl.value = config.apiKey || '';
                        
                        // Also save to localStorage for quick access
                        localStorage.setItem('erpConfig', JSON.stringify(config));
                        
                        console.log('✓ ERP config loaded from server:', config);
                        console.log('  - System:', systemEl?.value);
                        console.log('  - URL:', urlEl?.value);
                        console.log('  - API Key:', apiKeyEl?.value ? '***' + apiKeyEl.value.slice(-10) : 'empty');
                        return;
                    }
                }
            } catch (error) {
                console.error('Error loading ERP config from server:', error);
            }
            
            // Fallback to localStorage if server load fails
            const saved = localStorage.getItem('erpConfig');
            if (saved) {
                try {
                    const config = JSON.parse(saved);
                    const systemEl = document.getElementById('erpSystem');
                    const urlEl = document.getElementById('erpUrl');
                    const apiKeyEl = document.getElementById('erpApiKey');
                    
                    if (systemEl) systemEl.value = config.system || 'frappe';
                    if (urlEl) urlEl.value = config.url || '';
                    if (apiKeyEl) apiKeyEl.value = config.apiKey || '';
                    
                    console.log('✓ ERP config loaded from localStorage (fallback):', config);
                } catch (error) {
                    console.error('Error loading ERP config:', error);
                }
            } else {
                console.log('⚠ No saved ERP config found');
            }
        }

        // Date Management
        function setToday() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('startDate').value = today;
            document.getElementById('endDate').value = today;
        }

        function setYesterday() {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const dateStr = yesterday.toISOString().split('T')[0];
            document.getElementById('startDate').value = dateStr;
            document.getElementById('endDate').value = dateStr;
        }

        function setThisWeek() {
            const today = new Date();
            const firstDay = new Date(today.setDate(today.getDate() - today.getDay()));
            const lastDay = new Date(today.setDate(today.getDate() - today.getDay() + 6));
            
            document.getElementById('startDate').value = firstDay.toISOString().split('T')[0];
            document.getElementById('endDate').value = lastDay.toISOString().split('T')[0];
        }

        function setThisMonth() {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            
            document.getElementById('startDate').value = firstDay.toISOString().split('T')[0];
            document.getElementById('endDate').value = lastDay.toISOString().split('T')[0];
        }

        let filteredRecords = [];
        let currentPage = 1;
        let recordsPerPage = 20;

        // Filtering Functions
        function applyFilters() {
            const employeeFilter = document.getElementById('filterEmployee').value.toLowerCase();
            const employeeIdFilter = document.getElementById('filterEmployeeId').value.toLowerCase();
            const punchTypeFilter = document.getElementById('filterPunchType').value;
            
            filteredRecords = allRecords.filter(record => {
                const matchesEmployee = !employeeFilter || record.employeeName.toLowerCase().includes(employeeFilter);
                const matchesEmployeeId = !employeeIdFilter || record.employeeId.toLowerCase().includes(employeeIdFilter);
                const matchesPunchType = !punchTypeFilter || record.punchType === punchTypeFilter;
                
                return matchesEmployee && matchesEmployeeId && matchesPunchType;
            });
            
            currentPage = 1;
            showDataStats();
            displayRecords();
        }

        function clearFilters() {
            document.getElementById('filterEmployee').value = '';
            document.getElementById('filterEmployeeId').value = '';
            document.getElementById('filterPunchType').value = '';
            
            filteredRecords = allRecords;
            currentPage = 1;
            showDataStats();
            displayRecords();
        }

        // Auto-save ERP config when fields change
        function setupERPAutoSave() {
            ['erpSystem', 'erpUrl', 'erpApiKey'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('change', saveERPConfig);
                    element.addEventListener('input', saveERPConfig);
                }
            });
        }

        // Login functionality
        async function handleLogin(event) {
            event.preventDefault();
            
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            // Get users from localStorage or use defaults
            const users = getUsers();
            const validCredentials = users;
            
            const isValid = validCredentials.some(cred => 
                cred.username === username && cred.password === password
            );
            
            if (isValid) {
                // Update last login time and get user role
                const users = getUsers();
                const userIndex = users.findIndex(u => u.username === username);
                let userRole = 'Viewer';
                
                if (userIndex !== -1) {
                    users[userIndex].lastLogin = new Date().toLocaleString();
                    userRole = users[userIndex].role;
                    await saveUsers(users);
                }
                
                // Store login status with role
                localStorage.setItem('isLoggedIn', 'true');
                localStorage.setItem('currentUser', username);
                localStorage.setItem('currentUserRole', userRole);
                
                console.log(`✓ Logged in as ${username} (${userRole})`);
                
                // Hide login screen and show app
                document.getElementById('loginOverlay').style.display = 'none';
                document.getElementById('appContent').style.display = 'block';
                
                // Apply role permissions
                applyRolePermissions();
                
                // Initialize app
                initializeApp();
            } else {
                // Show error
                document.getElementById('loginError').style.display = 'block';
                setTimeout(() => {
                    document.getElementById('loginError').style.display = 'none';
                }, 3000);
            }
        }
        
        function logout() {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('currentUser');
            localStorage.removeItem('currentUserRole');
            location.reload();
        }
        
        function checkLoginStatus() {
            const isLoggedIn = localStorage.getItem('isLoggedIn');
            const currentUser = localStorage.getItem('currentUser');
            
            if (isLoggedIn === 'true' && currentUser) {
                // User is logged in, show app
                document.getElementById('loginOverlay').style.display = 'none';
                document.getElementById('appContent').style.display = 'block';
                
                // Get user role (from localStorage or users array)
                const userRole = getCurrentUserRole();
                document.getElementById('userInfo').textContent = `Welcome, ${currentUser} (${userRole})`;
                
                console.log(`✓ User ${currentUser} logged in with role: ${userRole}`);
                
                // Apply role-based permissions
                applyRolePermissions();
                
                initializeApp();
            } else {
                // Show login screen
                document.getElementById('loginOverlay').style.display = 'flex';
                document.getElementById('appContent').style.display = 'none';
            }
        }
        
        async function initializeApp() {
            setToday();
            loadDevices();
            updateDeviceDropdown();
            await loadERPConfig();
            await loadSyncHistory();
            setupERPAutoSave();
            await loadAutoSyncSettings();
            applyRolePermissions();
            
            // Crash recovery: disabled to prevent startup errors
            // performCrashRecovery();
            
            // Setup auto-sync toggle listener
            document.getElementById('autoSyncEnabled').addEventListener('change', function() {
                if (this.checked) {
                    startAutoSync();
                } else {
                    stopAutoSync();
                }
            });
        }
        
        // Role-based Access Control
        function getCurrentUserRole() {
            // First check if role is stored in localStorage (from login)
            const storedRole = localStorage.getItem('currentUserRole');
            if (storedRole) {
                return storedRole;
            }
            
            // Fallback: check from users array
            const currentUser = localStorage.getItem('currentUser');
            if (!currentUser) return 'Viewer';
            
            const users = getUsers();
            const user = users.find(u => u.username === currentUser);
            return user ? user.role : 'Viewer';
        }
        
        function isAdmin() {
            const role = getCurrentUserRole();
            // Case-insensitive check for safety
            const result = role && role.toLowerCase() === 'admin';
            console.log(`isAdmin() check: role="${role}", isAdmin=${result}`);
            return result;
        }
        
        function applyRolePermissions() {
            if (!isAdmin()) {
                disableViewerElements();
            }
        }
        
        function disableViewerElements() {
            // Disable device management buttons
            const deviceButtons = ['openAddDeviceModal', 'discoverDevices', 'testAllDevices'];
            deviceButtons.forEach(funcName => {
                const btn = document.querySelector(`button[onclick="${funcName}()"]`);
                if (btn) {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                    btn.title = 'Admin access required';
                }
            });
            
            // Disable ERP settings
            ['erpSystem', 'erpUrl', 'erpApiKey'].forEach(id => {
                const elem = document.getElementById(id);
                if (elem) {
                    elem.disabled = true;
                    elem.style.opacity = '0.5';
                }
            });
            
            // Disable ERP buttons
            const erpBtn = document.querySelector('button[onclick="testERPConnection()"]');
            if (erpBtn) {
                erpBtn.disabled = true;
                erpBtn.style.opacity = '0.5';
                erpBtn.title = 'Admin access required';
            }
            
            // Disable auto-sync settings
            ['autoSyncEnabled', 'syncInterval', 'testModeEnabled'].forEach(id => {
                const elem = document.getElementById(id);
                if (elem) {
                    elem.disabled = true;
                    elem.style.opacity = '0.5';
                }
            });
            
            // Disable settings buttons
            const settingsButtons = ['toggleAutoSync', 'syncNow', 'saveSettings', 'clearSyncHistory'];
            settingsButtons.forEach(funcName => {
                const btn = document.querySelector(`button[onclick="${funcName}()"]`);
                if (btn) {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                    btn.title = 'Admin access required';
                }
            });
            
            // Hide user management add button
            const addUserBtn = document.querySelector('button[onclick="openAddUserModal()"]');
            if (addUserBtn) {
                addUserBtn.style.display = 'none';
            }
            
            // Hide device add button
            const addDeviceBtn = document.querySelector('button[onclick="openAddDeviceModal()"]');
            if (addDeviceBtn) {
                addDeviceBtn.style.display = 'none';
            }
            
            // Disable send to ERP button
            const sendErpBtn = document.querySelector('button[onclick="sendToERP()"]');
            if (sendErpBtn) {
                sendErpBtn.disabled = true;
                sendErpBtn.style.opacity = '0.5';
                sendErpBtn.title = 'Admin access required';
            }
        }
        
        // User Management Functions
        function getUsers() {
            // Return from global users variable (loaded from server)
            if (users.length === 0) {
                // Return defaults if not loaded yet
                return [
                    { username: 'admin', password: 'admin123', role: 'Admin', fullName: 'Administrator', email: 'admin@company.com', status: 'Active', lastLogin: 'Never' },
                    { username: 'viewer', password: 'viewer123', role: 'Viewer', fullName: 'Viewer User', email: 'viewer@company.com', status: 'Active', lastLogin: 'Never' }
                ];
            }
            return users;
        }
        
        async function saveUsers(updatedUsers) {
            users = updatedUsers;
            await saveUsersToServer();
        }
        
        function loadUsersTable() {
            console.log('loadUsersTable() called');
            const currentRole = getCurrentUserRole();
            const adminStatus = isAdmin();
            console.log(`Loading users table - Current role: ${currentRole}, Is Admin: ${adminStatus}`);
            
            const users = getUsers();
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = '';
            
            users.forEach((user, index) => {
                // Ensure user has all required fields with defaults
                const userStatus = user.status || 'Active';
                const userLastLogin = user.lastLogin || 'Never';
                const userFullName = user.fullName || 'N/A';
                const userEmail = user.email || 'N/A';
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="padding: 10px; border: 1px solid #ddd;">${user.username}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${userFullName}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${userEmail}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="background: ${user.role === 'Admin' ? '#28a745' : '#007cba'}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">
                            ${user.role}
                        </span>
                    </td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="background: ${userStatus === 'Active' ? '#28a745' : '#dc3545'}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">
                            ${userStatus}
                        </span>
                    </td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${userLastLogin}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">
                        ${isAdmin() ? `<button onclick="editUser('${user.username}')" style="background: #007cba; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer;">Edit</button>` : ''}
                        ${isAdmin() ? `<button onclick="changeUserPassword('${user.username}')" style="background: #ffc107; color: black; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer;">Password</button>` : ''}
                        ${isAdmin() && user.username !== 'admin' ? `<button onclick="deleteUser('${user.username}')" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Delete</button>` : ''}
                        ${!isAdmin() ? '<span style="color: #666; font-style: italic;">View Only</span>' : ''}
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function openAddUserModal() {
            if (!isAdmin()) {
                alert('Admin access required to add users');
                return;
            }
            
            // Clear form
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('newUserRole').value = 'Admin';
            document.getElementById('newFullName').value = '';
            document.getElementById('newEmail').value = '';
            
            document.getElementById('addUserModal').classList.add('active');
        }
        
        function closeAddUserModal() {
            document.getElementById('addUserModal').classList.remove('active');
        }
        
        async function addNewUser() {
            if (!isAdmin()) {
                alert('Admin access required');
                return;
            }
            
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newPassword').value;
            const role = document.getElementById('newUserRole').value;
            const fullName = document.getElementById('newFullName').value.trim();
            const email = document.getElementById('newEmail').value.trim();
            
            if (!username || !password) {
                alert('Username and password are required!');
                return;
            }
            
            const users = getUsers();
            
            // Check if username already exists
            if (users.find(u => u.username === username)) {
                alert('Username already exists!');
                return;
            }
            
            const newUser = {
                username: username,
                password: password,
                role: role,
                fullName: fullName || username,
                email: email,
                status: 'Active',
                lastLogin: 'Never'
            };
            
            users.push(newUser);
            await saveUsers(users);
            
            // Log user addition
            logUserAction('add', username, `Added user: ${username} (${role}) - ${fullName || username}`);
            
            loadUsersTable();
            closeAddUserModal();
            
            alert('User added successfully!');
        }
        
        function editUser(username) {
            if (!isAdmin()) {
                alert('Admin access required to edit users');
                return;
            }
            
            const users = getUsers();
            const user = users.find(u => u.username === username);
            
            if (!user) return;
            
            document.getElementById('editUsername').value = user.username;
            document.getElementById('editFullName').value = user.fullName || '';
            document.getElementById('editEmail').value = user.email || '';
            document.getElementById('editUserRole').value = user.role;
            
            document.getElementById('editUserModal').classList.add('active');
        }
        
        async function saveUserEdit() {
            const username = document.getElementById('editUsername').value;
            const fullName = document.getElementById('editFullName').value.trim();
            const email = document.getElementById('editEmail').value.trim();
            const role = document.getElementById('editUserRole').value;
            
            const users = getUsers();
            const userIndex = users.findIndex(u => u.username === username);
            
            if (userIndex === -1) return;
            
            const oldUser = {...users[userIndex]};
            
            users[userIndex].fullName = fullName;
            users[userIndex].email = email;
            users[userIndex].role = role;
            
            await saveUsers(users);
            
            // Log user update with changes
            const changes = [];
            if (oldUser.fullName !== fullName) changes.push(`name: ${oldUser.fullName} → ${fullName}`);
            if (oldUser.email !== email) changes.push(`email: ${oldUser.email} → ${email}`);
            if (oldUser.role !== role) changes.push(`role: ${oldUser.role} → ${role}`);
            
            const changeText = changes.length > 0 ? ` (${changes.join(', ')})` : '';
            logUserAction('update', username, `Updated user: ${username}${changeText}`);
            
            loadUsersTable();
            closeEditUserModal();
            
            alert('User updated successfully!');
        }
        
        function closeEditUserModal() {
            document.getElementById('editUserModal').classList.remove('active');
        }
        
        async function changeUserPassword(username) {
            if (!isAdmin()) {
                alert('Admin access required to change passwords');
                return;
            }
            
            document.getElementById('changePasswordUsername').value = username;
            document.getElementById('changePasswordNew').value = '';
            document.getElementById('changePasswordConfirm').value = '';
            document.getElementById('changePasswordModal').classList.add('active');
        }
        
        async function savePasswordChange() {
            const username = document.getElementById('changePasswordUsername').value;
            const newPassword = document.getElementById('changePasswordNew').value;
            const confirmPassword = document.getElementById('changePasswordConfirm').value;
            
            if (!newPassword || !confirmPassword) {
                alert('Please enter both password fields!');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }
            
            if (newPassword.length < 6) {
                alert('Password must be at least 6 characters long!');
                return;
            }
            
            const users = getUsers();
            const userIndex = users.findIndex(u => u.username === username);
            
            if (userIndex === -1) return;
            
            users[userIndex].password = newPassword;
            await saveUsers(users);
            
            // Log password change
            logUserAction('password', username, `Changed password for user: ${username}`);
            
            closeChangePasswordModal();
            
            alert('Password changed successfully!');
        }
        
        function closeChangePasswordModal() {
            document.getElementById('changePasswordModal').classList.remove('active');
        }
        
        async function deleteUser(username) {
            if (!isAdmin()) {
                alert('Admin access required to delete users');
                return;
            }
            
            if (username === 'admin') {
                alert('Cannot delete admin user!');
                return;
            }
            
            if (!confirm(`Are you sure you want to delete user '${username}'?`)) {
                return;
            }
            
            const users = getUsers();
            const user = users.find(u => u.username === username);
            const filteredUsers = users.filter(u => u.username !== username);
            await saveUsers(filteredUsers);
            
            // Log user deletion
            if (user) {
                logUserAction('delete', username, `Deleted user: ${username} (${user.role}) - ${user.fullName || username}`);
            }
            
            loadUsersTable();
            
            alert('User deleted successfully!');
        }

        // Device History/Logging Functions
        async function logDeviceAction(action, deviceName, description) {
            const currentUser = localStorage.getItem('currentUser') || 'Unknown';
            const timestamp = new Date().toLocaleString();
            
            const logEntry = {
                timestamp: timestamp,
                user: currentUser,
                action: action,
                deviceName: deviceName,
                description: description
            };
            
            // Add to beginning of history
            deviceHistory.unshift(logEntry);
            
            // Keep only last 100 entries
            if (deviceHistory.length > 100) {
                deviceHistory.splice(100);
            }
            
            // Save to server
            await saveDeviceHistoryToServer();
            
            // Real-time update: refresh history if on devices tab
            if (document.getElementById('devices').classList.contains('active')) {
                loadDeviceHistory();
            }
        }
        
        let deviceHistory = [];
        
        async function loadDeviceHistoryFromServer() {
            try {
                const response = await fetch('/api/device-history');
                if (response.ok) {
                    deviceHistory = await response.json();
                    console.log(`✓ Loaded ${deviceHistory.length} device history entries from server`);
                    return true;
                }
            } catch (error) {
                console.error('Error loading device history:', error);
            }
            return false;
        }
        
        async function saveDeviceHistoryToServer() {
            try {
                await fetch('/api/device-history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(deviceHistory)
                });
                console.log('✓ Device history saved to server');
            } catch (error) {
                console.error('Error saving device history:', error);
            }
        }
        
        function getDeviceHistory() {
            return deviceHistory;
        }
        
        function loadDeviceHistory() {
            const history = getDeviceHistory();
            const historyDiv = document.getElementById('deviceHistory');
            
            if (history.length === 0) {
                historyDiv.innerHTML = '<div style="color: #666; text-align: center;">No device activity yet</div>';
                return;
            }
            
            let html = '';
            history.forEach(entry => {
                const actionColors = {
                    'add': '#28a745',
                    'update': '#ffc107',
                    'delete': '#dc3545'
                };
                
                const actionColor = actionColors[entry.action] || '#007cba';
                
                html += `
                    <div style="margin-bottom: 10px; padding: 10px; border-left: 4px solid ${actionColor}; background: white; border-radius: 3px;">
                        <div style="display: flex; justify-content: space-between; align-items: start; gap: 15px;">
                            <div style="flex: 1;">
                                <div style="font-weight: bold; color: ${actionColor}; text-transform: uppercase; font-size: 0.8em;">
                                    ${entry.action} DEVICE
                                </div>
                                <div style="margin: 5px 0; font-weight: 500;">${entry.description}</div>
                                <div style="font-size: 0.85em; color: #666;">
                                    <span style="font-weight: 500;">By:</span> ${entry.user} | 
                                    <span style="font-weight: 500;">When:</span> ${entry.timestamp}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            historyDiv.innerHTML = html;
        }
        
        async function clearDeviceHistory() {
            if (!isAdmin()) {
                alert('Admin access required to clear device history');
                return;
            }
            
            if (confirm('Are you sure you want to clear all device activity history?')) {
                deviceHistory = [];
                await saveDeviceHistoryToServer();
                loadDeviceHistory();
                alert('Device history cleared successfully!');
            }
        }
        
        // User History/Logging Functions
        async function logUserAction(action, username, description) {
            const currentUser = localStorage.getItem('currentUser') || 'Unknown';
            const timestamp = new Date().toLocaleString();
            
            const logEntry = {
                timestamp: timestamp,
                user: currentUser,
                action: action,
                username: username,
                description: description
            };
            
            // Add to beginning of history
            userHistory.unshift(logEntry);
            
            // Keep only last 100 entries
            if (userHistory.length > 100) {
                userHistory.splice(100);
            }
            
            // Save to server
            await saveUserHistoryToServer();
            
            // Real-time update: refresh history if on users tab
            if (document.getElementById('users').classList.contains('active')) {
                loadUserHistory();
            }
        }
        
        let userHistory = [];
        
        async function loadUserHistoryFromServer() {
            try {
                const response = await fetch('/api/user-history');
                if (response.ok) {
                    userHistory = await response.json();
                    console.log(`✓ Loaded ${userHistory.length} user history entries from server`);
                    return true;
                }
            } catch (error) {
                console.error('Error loading user history:', error);
            }
            return false;
        }
        
        async function saveUserHistoryToServer() {
            try {
                await fetch('/api/user-history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userHistory)
                });
                console.log('✓ User history saved to server');
            } catch (error) {
                console.error('Error saving user history:', error);
            }
        }
        
        function getUserHistory() {
            return userHistory;
        }
        
        function loadUserHistory() {
            const history = getUserHistory();
            const historyDiv = document.getElementById('userHistory');
            
            if (history.length === 0) {
                historyDiv.innerHTML = '<div style="color: #666; text-align: center;">No user activity yet</div>';
                return;
            }
            
            let html = '';
            history.forEach(entry => {
                const actionColors = {
                    'add': '#28a745',
                    'update': '#ffc107',
                    'delete': '#dc3545',
                    'password': '#17a2b8'
                };
                
                const actionColor = actionColors[entry.action] || '#007cba';
                
                html += `
                    <div style="margin-bottom: 10px; padding: 10px; border-left: 4px solid ${actionColor}; background: white; border-radius: 3px;">
                        <div style="display: flex; justify-content: space-between; align-items: start; gap: 15px;">
                            <div style="flex: 1;">
                                <div style="font-weight: bold; color: ${actionColor}; text-transform: uppercase; font-size: 0.8em;">
                                    ${entry.action} USER
                                </div>
                                <div style="margin: 5px 0; font-weight: 500;">${entry.description}</div>
                                <div style="font-size: 0.85em; color: #666;">
                                    <span style="font-weight: 500;">By:</span> ${entry.user} | 
                                    <span style="font-weight: 500;">When:</span> ${entry.timestamp}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            historyDiv.innerHTML = html;
        }
        
        async function clearUserHistory() {
            if (!isAdmin()) {
                alert('Admin access required to clear user history');
                return;
            }
            
            if (confirm('Are you sure you want to clear all user activity history?')) {
                userHistory = [];
                await saveUserHistoryToServer();
                loadUserHistory();
                alert('User history cleared successfully!');
            }
        }

        // Crash Recovery Functions
        async function performCrashRecovery() {
            try {
                // Check if auto-sync is enabled first
                const autoSyncSettings = localStorage.getItem('autoSyncSettings');
                if (!autoSyncSettings) {
                    console.log('Auto-sync not configured, skipping crash recovery');
                    return;
                }
                
                const settings = JSON.parse(autoSyncSettings);
                if (!settings.enabled) {
                    console.log('Auto-sync disabled, skipping crash recovery');
                    return;
                }
                
                // Check if crash recovery is needed
                const lastAppStart = localStorage.getItem('lastAppStart');
                const currentStart = new Date().toISOString();
                
                // Store current app start time
                localStorage.setItem('lastAppStart', currentStart);
                
                if (!lastAppStart) {
                    // First time running, no recovery needed
                    console.log('First app start - No crash recovery needed');
                    return;
                }
                
                const timeSinceLastStart = new Date() - new Date(lastAppStart);
                const hoursDown = Math.floor(timeSinceLastStart / (1000 * 60 * 60));
                
                // If app was down for more than 1 hour, perform recovery
                if (hoursDown >= 1) {
                    console.log(`System was down for ${hoursDown} hours - Starting crash recovery`);
                    await performRecoverySync();
                } else {
                    console.log('Application restarted - No recovery needed');
                }
                
            } catch (error) {
                console.error('Crash recovery error:', error);
                // Don't show error to user on startup
            }
        }
        
        async function performRecoverySync() {
            try {
                // Check if devices are loaded
                if (!devices || devices.length === 0) {
                    console.log('No devices configured, skipping recovery');
                    return;
                }
                
                // Get ERP config
                const erpConfig = {
                    system: document.getElementById('erpSystem')?.value,
                    url: document.getElementById('erpUrl')?.value,
                    apiKey: document.getElementById('erpApiKey')?.value
                };
                
                if (!erpConfig.url || !erpConfig.apiKey) {
                    console.log('ERP not configured, skipping recovery');
                    return;
                }
                
                let totalRecovered = 0;
                
                for (const device of devices) {
                    try {
                        // Get last sync time for this device
                        const lastSyncKey = `lastSync_${device.id}`;
                        const lastSyncTime = localStorage.getItem(lastSyncKey);
                        
                        let startDate;
                        if (lastSyncTime) {
                            startDate = parseSyncTime(lastSyncTime);
                        } else {
                            // If no last sync, get last 24 hours
                            startDate = new Date(Date.now() - 24 * 60 * 60 * 1000);
                        }
                        
                        const endDate = new Date();
                        
                        console.log(`Recovering data from ${device.name} since ${startDate.toLocaleString()}`);
                        
                        // Fetch missed data
                        const useDummy = device.mode === 'dummy';
                        
                        // Check if fetchDeviceData function exists
                        if (typeof fetchDeviceData !== 'function') {
                            console.error('fetchDeviceData function not available');
                            continue;
                        }
                        
                        const data = await fetchDeviceData(device, 
                            startDate.toISOString().split('T')[0], 
                            endDate.toISOString().split('T')[0], 
                            useDummy
                        );
                        
                        if (data.success && data.punchRecords && data.punchRecords.length > 0) {
                            // Filter records newer than last sync
                            const newRecords = data.punchRecords.filter(record => {
                                const recordTime = new Date(record.timestamp);
                                return !lastSyncTime || recordTime > parseSyncTime(lastSyncTime);
                            });
                            
                            if (newRecords.length > 0) {
                                // Send to ERP
                                const response = await fetch('/send-to-erp', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        data: newRecords.map(record => ({
                                            ...record,
                                            deviceName: device.name
                                        })),
                                        erpConfig: erpConfig
                                    })
                                });
                                
                                if (!response.ok) {
                                    throw new Error(`Server error: ${response.status}`);
                                }
                                
                                
                                const result = await response.json();
                                
                                if (result.success) {
                                    const successCount = result.details?.success || 0;
                                    totalRecovered += successCount;
                                    
                                    // Update last sync time to latest record timestamp (NOT current time!)
                                    if (successCount > 0) {
                                        // Find the latest timestamp from the recovered records
                                        let latestRecordTime = null;
                                        for (const record of newRecords) {
                                            const ts = new Date(record.timestamp);
                                            if (!isNaN(ts.getTime())) {
                                                if (!latestRecordTime || ts > latestRecordTime) {
                                                    latestRecordTime = ts;
                                                }
                                            }
                                        }
                                        
                                        if (latestRecordTime) {
                                            setDeviceLastSync(device, latestRecordTime);
                                            console.log(`Recovered ${successCount} records from ${device.name}, lastSync set to ${latestRecordTime.toISOString()}`);
                                        }
                                    }
                                } else {
                                    console.error(`Recovery failed for ${device.name}: ${result.error}`);
                                }
                            } else {
                                console.log(`No new records found for ${device.name}`);
                            }
                        } else {
                            console.log(`No data available for recovery from ${device.name}`);
                        }
                        
                    } catch (error) {
                        console.error(`Recovery error for ${device.name}:`, error);
                        // Don't show errors to user during recovery
                    }
                }
                
                // Update devices and show summary
                if (totalRecovered > 0) {
                    await saveDevicesToServer();
                    loadDevices();
                    console.log(`Crash recovery completed: ${totalRecovered} records recovered`);
                }
                
            } catch (error) {
                console.error('Recovery sync failed:', error);
                // Don't show errors to user during recovery
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', async function() {
            // Load ERP config and sync history immediately (before login check)
            await loadERPConfig();
            await loadSyncHistory();
            
            checkLoginStatus();
            
            // Load all data from server on startup
            console.log('Loading data from server...');
            await Promise.all([
                loadDevicesFromServer(),
                loadUsersFromServer(),
                loadSettingsFromServer(),
                loadErpConfigFromServer(),
                loadDeviceHistoryFromServer(),
                loadUserHistoryFromServer()
            ]);
            
            // Load devices table and history if on devices tab
            if (document.getElementById('devices').classList.contains('active')) {
                loadDevices();
                loadDeviceHistory();
            }
            
            console.log('✓ Application initialized with all server data');
        });
        
        // Persistent Storage Integration
        function initPersistentStorage() {
            // Load data from server on startup
            loadFromServer();
            
            // Auto-save every 5 seconds
            setInterval(syncToServer, 5000);
            
            // Save before closing
            window.addEventListener('beforeunload', syncToServer);
        }
        
        async function loadFromServer() {
            try {
                const [devicesResp, usersResp, settingsResp, erpResp] = await Promise.all([
                    fetch('/api/devices'),
                    fetch('/api/users'),
                    fetch('/api/settings'),
                    fetch('/api/erp-config')
                ]);
                
                if (devicesResp.ok) {
                    const devices = await devicesResp.json();
                    await saveDevicesToServer();
                }
                if (usersResp.ok) {
                    const users = await usersResp.json();
                    localStorage.setItem('users', JSON.stringify(users));
                }
                if (settingsResp.ok) {
                    const settings = await settingsResp.json();
                    localStorage.setItem('appSettings', JSON.stringify(settings));
                }
                if (erpResp.ok) {
                    const config = await erpResp.json();
                    localStorage.setItem('erpConfig', JSON.stringify(config));
                }
                
                console.log('✓ Data loaded from persistent storage');
            } catch (error) {
                console.error('Error loading from server:', error);
            }
        }
        
        async function syncToServer() {
            try {
                const devices = JSON.parse(localStorage.getItem('devices') || '[]');
                const users = JSON.parse(localStorage.getItem('users') || '[]');
                const settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
                const erpConfig = JSON.parse(localStorage.getItem('erpConfig') || '{}');
                
                await Promise.all([
                    fetch('/api/devices', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(devices)
                    }),
                    fetch('/api/users', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(users)
                    }),
                    fetch('/api/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(settings)
                    }),
                    fetch('/api/erp-config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(erpConfig)
                    })
                ]);
                
                console.log('✓ Data synced to persistent storage');
            } catch (error) {
                console.error('Error syncing to server:', error);
            }
        }
    </script>
</body>
</html>'''
            
            self.wfile.write(html_content.encode())
            
        elif self.path.startswith('/fetch'):
            query = self.path.split('?')[1] if '?' in self.path else ''
            params = parse_qs(query)
            debug_log(f"GET /fetch raw_path={self.path!r}, params={params!r}")
            
            ip = params.get('ip', [''])[0]
            port = int(params.get('port', ['4370'])[0])
            start_date = params.get('startDate', [''])[0] or None
            end_date = params.get('endDate', [''])[0] or None
            dummy_mode = params.get('dummy', ['false'])[0].lower() == 'true'
            device_mode = params.get('mode', ['real'])[0]
            debug_log(f"GET /fetch resolved ip={ip!r}, port={port!r}, start_date={start_date!r}, end_date={end_date!r}, dummy_mode={dummy_mode!r}, device_mode={device_mode!r}")
            
            if dummy_mode:
                debug_log("GET /fetch using dummy data path")
                result = self.generate_dummy_data(start_date, end_date)
            elif device_mode == 'adms':
                debug_log("GET /fetch using ADMS data path")
                result = self.fetch_adms_data(ip, start_date, end_date)
            else:
                debug_log("GET /fetch using ZK device data path")
                result = self.fetch_device_data(ip, port, start_date, end_date)
            debug_log(f"GET /fetch result success={result.get('success')!r}, error={result.get('error')!r}, message={result.get('message')!r}, records={len(result.get('punchRecords', [])) if isinstance(result, dict) else 'n/a'}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self._write_response(json.dumps(result).encode())
            
        elif self.path in ('/Auriga - Original.jpg', '/Auriga%20-%20Original.jpg'):
            try:
                image_path = os.path.join(os.path.dirname(__file__), 'Auriga - Original.jpg')
                with open(image_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()

        elif self.path == '/auriga1.png':
            # Serve the primary login logo
            try:
                image_path = os.path.join(os.path.dirname(__file__), 'auriga1.png')
                with open(image_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()

        elif self.path == '/auriga.png':
            # Serve the legacy logo image as fallback
            try:
                image_path = os.path.join(os.path.dirname(__file__), 'auriga.png')
                with open(image_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
        
        elif self.path == '/api/devices':
            # Load devices from storage
            devices = storage.load_devices()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(devices).encode())
        
        elif self.path == '/api/users':
            # Load users from storage
            users = storage.load_users()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(users).encode())
        
        elif self.path == '/api/settings':
            # Load settings from storage
            settings = storage.load_settings()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(settings).encode())
        
        elif self.path == '/api/erp-config':
            # Load ERP config from storage
            config = storage.load_erp_config()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(config).encode())
        
        elif self.path == '/api/device-history':
            # Load device history from storage
            history = storage.load_device_history()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(history).encode())
        
        elif self.path == '/api/user-history':
            # Load user history from storage
            history = storage.load_user_history()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(history).encode())
        
        elif self.path == '/api/sync-history':
            # Load sync history from storage
            try:
                history = storage.load_sync_history()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(history).encode())
            except:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps([]).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        debug_log(f"do_POST path={self.path!r} from={self.client_address!r}")
        if self.path == '/export':
            self.handle_export()
        elif self.path == '/test-device':
            self.handle_test_device()
        elif self.path == '/test-erp':
            self.handle_test_erp()
        elif self.path == '/send-to-erp':
            self.handle_send_to_erp()
        elif self.path == '/api/devices':
            # Save devices to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            devices = json.loads(post_data.decode('utf-8'))
            storage.save_devices(devices)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        elif self.path == '/api/users':
            # Save users to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            users = json.loads(post_data.decode('utf-8'))
            storage.save_users(users)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        elif self.path == '/api/settings':
            # Save settings to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            settings = json.loads(post_data.decode('utf-8'))
            storage.save_settings(settings)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        elif self.path == '/api/erp-config':
            # Save ERP config to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data.decode('utf-8'))
            storage.save_erp_config(config)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        elif self.path == '/api/device-history':
            # Save device history to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            history = json.loads(post_data.decode('utf-8'))
            storage.save_device_history(history)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        elif self.path == '/api/user-history':
            # Save user history to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            history = json.loads(post_data.decode('utf-8'))
            storage.save_user_history(history)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        elif self.path == '/api/sync-history':
            # Save sync history to storage
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            history = json.loads(post_data.decode('utf-8'))
            storage.save_sync_history(history)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_export(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception as exc:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'Invalid export payload: {exc}'
            }).encode('utf-8'))
            return

        format_type = (data.get('format') or 'csv').lower()
        records = data.get('data', []) or []

        try:
            if format_type == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)

                writer.writerow(['Employee Name', 'Employee ID', 'Date & Time', 'Punch Type', 'Device'])

                for record in records:
                    writer.writerow([
                        record.get('employeeName', ''),
                        record.get('employeeId', ''),
                        record.get('timestamp', ''),
                        record.get('punchType', ''),
                        record.get('deviceName', '')
                    ])

                csv_payload = ('\ufeff' + output.getvalue()).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="attendance.csv"')
                self.send_header('Content-Length', str(len(csv_payload)))
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.end_headers()
                self.wfile.write(csv_payload)
                self.wfile.flush()
                return

            if format_type == 'excel':
                output = io.StringIO()
                output.write('<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>')
                output.write('<table border="1">')
                output.write('<tr><th>Employee Name</th><th>Employee ID</th><th>Date &amp; Time</th><th>Punch Type</th><th>Device</th></tr>')

                for record in records:
                    output.write('<tr>')
                    output.write(f"<td>{html.escape(str(record.get('employeeName', '')))}</td>")
                    output.write(f"<td>{html.escape(str(record.get('employeeId', '')))}</td>")
                    output.write(f"<td>{html.escape(str(record.get('timestamp', '')))}</td>")
                    output.write(f"<td>{html.escape(str(record.get('punchType', '')))}</td>")
                    output.write(f"<td>{html.escape(str(record.get('deviceName', '')))}</td>")
                    output.write('</tr>')

                output.write('</table></body></html>')

                excel_payload = output.getvalue().encode('utf-8')

                self.send_response(200)
                self.send_header('Content-type', 'application/vnd.ms-excel; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="attendance.xls"')
                self.send_header('Content-Length', str(len(excel_payload)))
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.end_headers()
                self.wfile.write(excel_payload)
                self.wfile.flush()
                return

            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'Unsupported export format: {format_type}'
            }).encode('utf-8'))

        except Exception as exc:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'Failed to generate export: {exc}'
            }).encode('utf-8'))
    
    def handle_test_device(self):
        debug_log("handle_test_device started")
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        ip = data.get('ip')
        port = int(data.get('port', 4370))
        debug_log(f"handle_test_device payload ip={ip!r}, port={port!r}")
        
        result = self.test_device_connection(ip, port)
        debug_log(f"handle_test_device result={result!r}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def handle_test_erp(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        system = data.get('system')
        url = data.get('url')
        api_key = data.get('apiKey')
        
        if system == 'frappe':
            result = self.test_frappe_connection(url, api_key)
        else:
            result = {'success': True, 'message': f'{system} connection test successful'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def handle_send_to_erp(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        records = data.get('data', [])
        erp_config = data.get('erpConfig', {})
        debug_log(f"handle_send_to_erp started records={len(records)}, system={erp_config.get('system')!r}, url_present={bool(erp_config.get('url'))}, api_key_present={bool(erp_config.get('apiKey'))}")
        
        if erp_config.get('system') == 'frappe':
            result = self.send_to_frappe(records, erp_config)
        else:
            result = {'success': True, 'message': f'Successfully sent {len(records)} records to ERP'}
        debug_log(f"handle_send_to_erp result success={result.get('success')!r}, message={result.get('message')!r}, error={result.get('error')!r}, details={result.get('details')!r}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def test_device_connection(self, ip, port):
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return {'success': True, 'message': f'Device at {ip}:{port} is reachable'}
            else:
                return {'success': False, 'error': f'Connection failed with error code {result}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_adms_data(self, ip, start_date=None, end_date=None):
        """Return punch records pushed by an ADMS device (e.g. ESSL AIFace Orcus)."""
        debug_log(f"fetch_adms_data started ip={ip!r}, start_date={start_date!r}, end_date={end_date!r}")
        try:
            from adms_listener import get_buffered_records
            all_records = storage.load_adms_punches()
            debug_log(f"fetch_adms_data loaded stored ADMS records count={len(all_records)}")
            for r in get_buffered_records():
                if r not in all_records:
                    all_records.append(r)
            debug_log(f"fetch_adms_data after buffer merge count={len(all_records)}")

            # Filter by device IP or serial number
            # ADMS records have deviceId which could be serial number or IP
            device_records = []
            for r in all_records:
                device_id = r.get('deviceId', '')
                # Match by IP or if deviceId contains the IP
                if device_id == ip or ip in device_id or device_id == 'unknown':
                    device_records.append(r)
            
            # If no records matched by IP, try to get device serial number from config
            if not device_records:
                devices = storage.load_devices() or []
                device_config = next((d for d in devices if d.get('ip') == ip), None)
                if device_config:
                    device_sn = device_config.get('serialNumber') or device_config.get('name')
                    if device_sn:
                        device_records = [r for r in all_records if r.get('deviceId') == device_sn]
            
            # If still no records, show all (backward compatibility)
            if not device_records:
                device_records = all_records
            debug_log(f"fetch_adms_data matched device_records count={len(device_records)}")

            if start_date or end_date:
                debug_log("fetch_adms_data applying date filter")
                start_dt = safe_strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_dt   = safe_strptime(end_date,   "%Y-%m-%d").date() if end_date   else None
                device_records = [
                    r for r in device_records
                    if (start_dt is None or datetime.fromisoformat(r['timestamp']).date() >= start_dt)
                    and (end_dt   is None or datetime.fromisoformat(r['timestamp']).date() <= end_dt)
                ]
            else:
                # If no date filter, show last 7 days instead of just 50 records
                seven_days_ago = (datetime.now() - timedelta(days=7)).date()
                device_records = [
                    r for r in device_records
                    if datetime.fromisoformat(r['timestamp']).date() >= seven_days_ago
                ]
            
            # Sort by timestamp descending (newest first)
            device_records = sorted(device_records, key=lambda x: x['timestamp'], reverse=True)
            latest_timestamp = device_records[0].get('timestamp') if device_records else None
            debug_log(f"fetch_adms_data success final_count={len(device_records)}, latest_timestamp={latest_timestamp!r}")

            return {
                'success': True,
                'punchRecords': device_records,
                'message': f'ADMS: {len(device_records)} records'
            }
        except Exception as e:
            debug_log("fetch_adms_data failed", e)
            return {'success': False, 'error': str(e)}

    def fetch_device_data(self, ip, port=4370, start_date=None, end_date=None):
        debug_log(f"fetch_device_data started ip={ip!r}, port={port!r}, start_date={start_date!r}, end_date={end_date!r}")
        """
        Fetch attendance from ESSL AirFace Orcus with multiple connection fallbacks.
        Tries TCP/UDP × ommit_ping × password combinations to maximise compatibility.
        """
        PUNCH_TYPE_MAP = {0: 'check-in', 1: 'check-out', 2: 'break-out',
                          3: 'break-in', 4: 'overtime-in', 5: 'overtime-out'}

        def _punch_label(rec):
            punch  = getattr(rec, 'punch',  None)
            status = getattr(rec, 'status', None)
            if punch  is not None and punch  in PUNCH_TYPE_MAP:
                return PUNCH_TYPE_MAP[punch]
            if status is not None and status in PUNCH_TYPE_MAP:
                return PUNCH_TYPE_MAP[status]
            return 'check-in' if (status or 0) == 0 else 'check-out'

        # Try multiple strategies for AirFace Orcus compatibility
        strategies = [
            dict(password=0,    force_udp=False, ommit_ping=True),   # most common success
            dict(password=0,    force_udp=False, ommit_ping=False),
            dict(password=0,    force_udp=True,  ommit_ping=True),
            dict(password=0,    force_udp=True,  ommit_ping=False),
            dict(password=1234, force_udp=False, ommit_ping=True),
            dict(password=1234, force_udp=True,  ommit_ping=True),
        ]

        conn = None
        last_exc = None
        for strat in strategies:
            try:
                debug_log(f"fetch_device_data trying strategy={strat!r}")
                zk = ZK(ip, port=port, timeout=30, **strat)
                conn = zk.connect()
                debug_log(f"fetch_device_data connected strategy={strat!r}")
                break
            except Exception as exc:
                last_exc = exc
                conn = None
                debug_log(f"fetch_device_data strategy failed strategy={strat!r}", exc)

        if conn is None:
            debug_log(f"fetch_device_data all strategies failed last_exc={last_exc!r}")
            return {'success': False, 'error': str(last_exc),
                    'message': f'All connection strategies failed: {last_exc}'}

        try:
            try:
                conn.disable_device()
                debug_log("fetch_device_data device disabled for read")
            except Exception:
                debug_log("fetch_device_data disable_device failed but continuing")
                pass

            # Build user lookup
            user_dict = {}
            try:
                users = conn.get_users() or []
                debug_log(f"fetch_device_data users count={len(users)}")
                for user in users:
                    clean_name = html.unescape(user.name) if user.name else f'Employee {user.uid}'
                    user_dict[user.uid] = clean_name
                    # Also index by user_id string (some devices use string IDs)
                    if hasattr(user, 'user_id') and user.user_id:
                        user_dict[user.user_id] = clean_name
            except Exception:
                debug_log("fetch_device_data get_users failed but continuing")
                pass

            attendance = conn.get_attendance()
            debug_log(f"fetch_device_data raw attendance count={len(attendance) if attendance else 0}")
            records = []

            if attendance:
                filtered_records = []
                for record in attendance:
                    record_date = record.timestamp.date()
                    if start_date:
                        start_dt = safe_strptime(start_date, "%Y-%m-%d").date()
                        if record_date < start_dt:
                            continue
                    if end_date:
                        end_dt = safe_strptime(end_date, "%Y-%m-%d").date()
                        if record_date > end_dt:
                            continue
                    filtered_records.append(record)

                if not start_date and not end_date:
                    filtered_records = sorted(attendance, key=lambda x: x.timestamp, reverse=True)[:200]
                debug_log(f"fetch_device_data filtered records count={len(filtered_records)}")

                for record in filtered_records:
                    uid = getattr(record, 'uid', record.user_id)
                    employee_name = (user_dict.get(record.user_id)
                                     or user_dict.get(uid)
                                     or f'Employee {record.user_id}')
                    records.append({
                        'employeeId':   str(record.user_id),
                        'employeeName': employee_name,
                        'timestamp':    record.timestamp.isoformat(),
                        'punchType':    _punch_label(record),
                        'rawData': {
                            'uid':    uid,
                            'status': getattr(record, 'status', None),
                            'punch':  getattr(record, 'punch',  None),
                        },
                    })

            try:
                conn.enable_device()
                debug_log("fetch_device_data device enabled after read")
            except Exception:
                debug_log("fetch_device_data enable_device failed but continuing")
                pass

            debug_log(f"fetch_device_data success final_count={len(records)}")
            return {
                'success':      True,
                'punchRecords': records,
                'message':      f'Successfully fetched {len(records)} records',
            }

        except Exception as e:
            debug_log("fetch_device_data failed", e)
            return {'success': False, 'error': str(e)}
        finally:
            try:
                conn.disconnect()
                debug_log("fetch_device_data disconnected")
            except Exception:
                debug_log("fetch_device_data disconnect failed")
                pass
    
    def generate_dummy_data(self, start_date=None, end_date=None):
        import random
        from datetime import datetime, timedelta
        
        employees = [
            {'id': '101', 'name': 'John Smith', 'dept': 'IT'},
            {'id': '102', 'name': 'Sarah Johnson', 'dept': 'HR'},
            {'id': '103', 'name': 'Mike Wilson', 'dept': 'Finance'},
            {'id': '104', 'name': 'Lisa Brown', 'dept': 'Marketing'},
            {'id': '105', 'name': 'David Lee', 'dept': 'IT'},
            {'id': '106', 'name': 'Emma Davis', 'dept': 'Operations'},
            {'id': '107', 'name': 'James Miller', 'dept': 'Sales'},
            {'id': '108', 'name': 'Anna Garcia', 'dept': 'HR'}
        ]
        
        records = []
        
        # Generate date range
        if start_date:
            start_dt = safe_strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = datetime.now() - timedelta(days=7)
            
        if end_date:
            end_dt = safe_strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
        
        # Generate records for each day
        current_date = start_dt
        while current_date <= end_dt:
            # Skip weekends for more realistic data
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                for employee in employees:
                    # 80% chance employee comes to work
                    if random.random() < 0.8:
                        # Check-in time (8:00-9:30 AM)
                        checkin_hour = random.randint(8, 9)
                        checkin_minute = random.randint(0, 59) if checkin_hour == 8 else random.randint(0, 30)
                        checkin_time = current_date.replace(hour=checkin_hour, minute=checkin_minute, second=random.randint(0, 59))
                        
                        records.append({
                            'employeeId': employee['id'],
                            'employeeName': employee['name'],
                            'timestamp': checkin_time.isoformat(),
                            'punchType': 'check-in',
                            'department': employee['dept']
                        })
                        
                        # Check-out time (5:00-7:00 PM)
                        checkout_hour = random.randint(17, 19)
                        checkout_minute = random.randint(0, 59)
                        checkout_time = current_date.replace(hour=checkout_hour, minute=checkout_minute, second=random.randint(0, 59))
                        
                        records.append({
                            'employeeId': employee['id'],
                            'employeeName': employee['name'],
                            'timestamp': checkout_time.isoformat(),
                            'punchType': 'check-out',
                            'department': employee['dept']
                        })
            
            current_date += timedelta(days=1)
        
        # Sort by timestamp
        records.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'success': True,
            'punchRecords': records,
            'message': f'Generated {len(records)} dummy records for testing'
        }

    def test_frappe_connection(self, url, api_key):
        try:
            import urllib.request
            import urllib.error
            import base64
            
            # Validate API key format
            if not api_key or ':' not in api_key:
                return {'success': False, 'error': 'API key must be in format: api_key:api_secret'}
            
            # Clean and format URL
            if not url.startswith('http'):
                url = 'http://' + url
            if url.endswith('/'):
                url = url[:-1]
            
            # Method 1: Try token authentication with a basic endpoint
            test_url = f"{url}/api/resource/User"
            req = urllib.request.Request(test_url)
            req.add_header('Authorization', f'token {api_key}')
            req.add_header('Content-Type', 'application/json')
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    return {'success': True, 'message': f'Frappe connection successful with token auth (HTTP {response.status})'}
            except urllib.error.HTTPError as e:
                # Method 2: Try basic authentication as fallback
                try:
                    credentials = base64.b64encode(api_key.encode()).decode('ascii')
                    req2 = urllib.request.Request(test_url)
                    req2.add_header('Authorization', f'Basic {credentials}')
                    req2.add_header('Content-Type', 'application/json')
                    
                    with urllib.request.urlopen(req2, timeout=10) as response:
                        return {'success': True, 'message': f'Frappe connection successful with basic auth (HTTP {response.status})'}
                except:
                    pass
                
                # Method 3: Try without authentication to test connectivity
                try:
                    req3 = urllib.request.Request(test_url)
                    with urllib.request.urlopen(req3, timeout=10) as response:
                        return {'success': False, 'error': f'Server reachable but authentication failed. Check API key validity in ERPNext.'}
                except:
                    pass
                
                # Read original error response
                error_body = ''
                try:
                    error_body = e.read().decode('utf-8')
                except:
                    pass
                
                if e.code == 401:
                    return {'success': False, 'error': f'Authentication failed - API key may be invalid or expired. Generate new API key in ERPNext User settings.'}
                elif e.code == 403:
                    return {'success': False, 'error': f'Access forbidden - User may not have System Manager role or API access disabled.'}
                else:
                    return {'success': False, 'error': f'HTTP {e.code}: {e.reason}. Response: {error_body[:100]}'}
                    
        except Exception as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def send_to_frappe(self, records, config):
        try:
            import urllib.request
            import urllib.error
            
            url = config.get('url', '')
            api_key = config.get('apiKey', '')
            
            # Clean and format URL
            if not url.startswith('http'):
                url = 'http://' + url
            if url.endswith('/'):
                url = url[:-1]
            
            settings = storage.load_settings() or {}
            punch_filter_cfg = settings.get('punchFilter') or {}
            dedup_enabled = bool(punch_filter_cfg.get('enabled', False))
            dedup_interval_seconds = int(punch_filter_cfg.get('intervalSeconds', 0) or 0)
            dedup_skipped = 0

            if dedup_enabled and dedup_interval_seconds > 0:
                dedup_window = timedelta(seconds=dedup_interval_seconds)
                accepted_times = {}
                filtered_records = []

                def parse_timestamp(value):
                    if not value:
                        return None
                    cleaned = value.strip().replace('Z', '')
                    try:
                        return datetime.fromisoformat(cleaned)
                    except ValueError:
                        try:
                            return safe_strptime(cleaned, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            return None

                for record in records:
                    employee_key = str(record.get('employeeId') or '').strip()
                    record_ts = parse_timestamp(record.get('timestamp'))

                    if employee_key and record_ts:
                        seen_times = accepted_times.setdefault(employee_key, [])
                        is_duplicate = False

                        for candidate in seen_times:
                            if abs((record_ts - candidate).total_seconds()) <= dedup_interval_seconds:
                                is_duplicate = True
                                break

                        if is_duplicate:
                            dedup_skipped += 1
                            print(
                                f"DEBUG: Deduplicated punch for employee {employee_key} at {record.get('timestamp')} "
                                f"within {dedup_interval_seconds} second window"
                            )
                            continue

                        seen_times.append(record_ts)

                    filtered_records.append(record)

                if dedup_skipped:
                    print(
                        f"DEBUG: Punch deduplication enabled - filtered {dedup_skipped} duplicate record(s) "
                        f"using {dedup_interval_seconds}s window"
                    )

                records = filtered_records
            else:
                dedup_skipped = 0

            # Get list of existing employees from ERPNext for validation
            existing_employees = self.get_existing_employees(url, api_key)
            if existing_employees is None:
                print("WARNING: Could not fetch employee list from ERPNext. Proceeding without validation.")
            
            success_count = 0
            error_count = 0
            skipped_count = 0
            errors = []
            success_records = []
            
            print(f"DEBUG: Starting to process {len(records)} records for ERP sync")
            
            for record in records:
                employee_id = record.get('employeeId')
                
                if not employee_id or employee_id == 'undefined' or employee_id == 'null':
                    skipped_count += 1
                    errors.append(f'Invalid employee ID: {employee_id} (skipped)')
                    print(f"DEBUG: Skipping record with invalid employee ID: {employee_id}")
                    continue
                
                erp_employee_id = None
                device_id = str(employee_id).strip()
                
                # If we have a mapping from ERP, validate via attendance_device_id
                if existing_employees is not None:
                    print(f"\nDEBUG: Looking up ERP employee for device ID '{device_id}'")
                    if device_id in existing_employees:
                        employee_record = existing_employees[device_id]
                        erp_employee_id = employee_record['erp_id']
                        print(f"DEBUG: Device ID '{device_id}' mapped to ERP employee {erp_employee_id} ({employee_record['name']})")
                    else:
                        skipped_count += 1
                        errors.append(f'Device ID {device_id}: Not found in ERPNext (skipped)')
                        print(f"DEBUG: Device ID '{device_id}' not found in ERP mapping.")
                        
                        sample_ids = list(existing_employees.items())
                        if sample_ids:
                            print("  Available device ID mappings (first 20):")
                            for idx, (dev_id, emp_rec) in enumerate(sample_ids[:20]):
                                print(f"    {idx + 1}. Device ID '{dev_id}' -> Employee {emp_rec['erp_id']} ({emp_rec['name']})")
                            if len(sample_ids) > 20:
                                print(f"    ...and {len(sample_ids) - 20} more")
                        else:
                            print("  ERP mapping is empty after filtering attendance_device_id values.")
                        continue
                else:
                    print(f"\nDEBUG: ERP employee mapping unavailable; skipping record for device ID '{device_id}'")
                    skipped_count += 1
                    errors.append('Employee mapping unavailable: verify ERP connection/credentials')
                    continue
                
                if not erp_employee_id:
                    # Should not reach here, but guard to avoid sending invalid payloads
                    skipped_count += 1
                    errors.append(f'Device ID {device_id}: No ERP employee resolved (skipped)')
                    print(f"DEBUG: No ERP employee resolved for device ID '{device_id}', skipping record")
                    continue
                
                try:
                    # Convert timestamp to MySQL-compatible format
                    timestamp = record.get('timestamp')
                    
                    # Validate timestamp exists
                    if not timestamp or timestamp == 'undefined' or timestamp == 'null':
                        error_count += 1
                        errors.append(f'Employee {employee_id}: Invalid timestamp (skipped)')
                        print(f"DEBUG: Skipping record with invalid timestamp for employee {employee_id}")
                        continue
                    
                    try:
                        # Parse the timestamp and convert to MySQL format
                        if 'T' in timestamp:
                            # Remove timezone info and milliseconds for MySQL compatibility
                            timestamp = timestamp.replace('Z', '').split('.')[0]
                            # Convert to MySQL datetime format: YYYY-MM-DD HH:MM:SS
                            dt = datetime.fromisoformat(timestamp)
                            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        print(f"DEBUG: Error parsing timestamp {timestamp}: {e}")
                        # Fallback to current time if parsing fails
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    device_name = record.get('deviceName') or 'Unknown Device'
                    latitude = record.get('latitude')
                    longitude = record.get('longitude')
                    
                    frappe_record = {
                        'doctype': 'Employee Checkin',
                        'employee': erp_employee_id,  # Use the mapped employee ID
                        'time': timestamp,
                        'device_id': device_name
                    }
                    
                    if latitude:
                        frappe_record['latitude'] = str(latitude)
                    if longitude:
                        frappe_record['longitude'] = str(longitude)
                    
                    print(f"DEBUG: Sending record for employee {employee_id} from device '{device_name}': {frappe_record}")
                    
                    api_url = f"{url}/api/resource/Employee%20Checkin"
                    data = json.dumps(frappe_record).encode('utf-8')
                    req = urllib.request.Request(api_url, data=data, method='POST')
                    req.add_header('Authorization', f'token {api_key}')
                    req.add_header('Content-Type', 'application/json')
                    
                    with urllib.request.urlopen(req, timeout=30) as response:
                        response_data = response.read().decode('utf-8')
                        print(f"DEBUG: Response for employee {employee_id}: Status {response.status}, Data: {response_data[:200]}")
                        
                        if response.status in [200, 201]:
                            success_count += 1
                            success_records.append({
                                'device_key': record.get('_syncDeviceId'),
                                'timestamp': record.get('timestamp'),
                                'employeeId': employee_id
                            })
                            print(f"DEBUG: Successfully created checkin for employee {employee_id}")
                        else:
                            error_count += 1
                            errors.append(f'Employee {employee_id}: HTTP {response.status} - {response_data[:100]}')
                            print(f"DEBUG: Failed to create checkin for employee {employee_id}: {response.status}")
                            
                except urllib.error.HTTPError as e:
                    error_count += 1
                    error_body = ''
                    try:
                        error_body = e.read().decode('utf-8')
                    except:
                        pass
                    
                    print(f"DEBUG: HTTP Error for employee {employee_id}: {e.code} - {error_body[:200]}")
                    
                    if e.code == 401:
                        errors.append(f'Employee {employee_id}: Invalid API Key')
                    elif e.code == 403:
                        errors.append(f'Employee {employee_id}: Access Forbidden')
                    else:
                        errors.append(f'Employee {employee_id}: HTTP {e.code} - {error_body[:50]}')
                except urllib.error.URLError as e:
                    error_count += 1
                    print(f"DEBUG: URL Error for employee {employee_id}: {str(e)}")
                    if 'timed out' in str(e).lower():
                        errors.append(f'Employee {employee_id}: Connection timeout - Check network/ERP server')
                    elif 'connection refused' in str(e).lower():
                        errors.append(f'Employee {employee_id}: Connection refused - ERP server may be down')
                    else:
                        errors.append(f'Employee {employee_id}: Network error - {str(e)[:50]}')
                except ConnectionError as e:
                    error_count += 1
                    print(f"DEBUG: Connection Error for employee {employee_id}: {str(e)}")
                    errors.append(f'Employee {employee_id}: Connection failed - Check internet connection')
                except TimeoutError as e:
                    error_count += 1
                    print(f"DEBUG: Timeout Error for employee {employee_id}: {str(e)}")
                    errors.append(f'Employee {employee_id}: Request timeout - Server not responding')
                except Exception as e:
                    error_count += 1
                    print(f"DEBUG: Exception for employee {employee_id}: {str(e)}")
                    errors.append(f'Employee {employee_id}: {str(e)[:50]}')
            
            message = f'Processed {len(records)} records: {success_count} sent'
            if skipped_count > 0:
                message += f', {skipped_count} skipped (not in ERPNext)'
            if error_count > 0:
                message += f', {error_count} failed'
            if dedup_skipped > 0:
                message += f', {dedup_skipped} deduplicated'
            
            print(f"DEBUG: Final result - Success: {success_count}, Skipped: {skipped_count}, Failed: {error_count}")
            
            # Determine if operation was successful
            is_success = success_count > 0 or skipped_count > 0
            
            result = {
                'success': is_success,
                'message': message,
                'details': {
                    'success': success_count,
                    'skipped': skipped_count,
                    'errors': error_count,
                    'deduplicated': dedup_skipped,
                    'success_records': success_records,
                    'error_list': errors[:5]
                }
            }
            
            # If all records failed, add error field for better frontend handling
            if not is_success and error_count > 0:
                result['error'] = message
            
            return result
                
        except urllib.error.URLError as e:
            error_msg = str(e)
            if 'timed out' in error_msg.lower():
                return {'success': False, 'error': 'Connection timeout - Check network connection and ERP server status'}
            elif 'connection refused' in error_msg.lower():
                return {'success': False, 'error': 'Connection refused - ERP server may be down or unreachable'}
            elif 'nodename nor servname provided' in error_msg.lower() or 'name or service not known' in error_msg.lower():
                return {'success': False, 'error': 'Invalid ERP URL - Cannot resolve hostname'}
            else:
                return {'success': False, 'error': f'Network error: {error_msg[:100]}'}
        except ConnectionError as e:
            return {'success': False, 'error': f'Connection failed - Check internet connection: {str(e)[:100]}'}
        except TimeoutError as e:
            return {'success': False, 'error': f'Request timeout - ERP server not responding: {str(e)[:100]}'}
        except Exception as e:
            return {'success': False, 'error': f'Frappe integration error: {str(e)[:100]}'}
    
    def get_existing_employees(self, url, api_key):
        try:
            import urllib.request
            import urllib.error
            
            # Fetch employees in pages to cover installations with thousands of records
            fields = "%22name%22,%22employee%22,%22employee_name%22,%22attendance_device_id%22"
            page_size = 200
            offset = 0
            total_records = 0
            device_id_mapping = {}
            skipped_missing_device_id = 0
            pages_fetched = 0
            
            while True:
                api_url = (
                    f"{url}/api/resource/Employee?fields=[{fields}]&limit_page_length={page_size}&limit_start={offset}"
                )
                print(f"DEBUG: Fetching employees from: {api_url}")
                req = urllib.request.Request(api_url)
                req.add_header('Authorization', f'token {api_key}')
                req.add_header('Content-Type', 'application/json')
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status != 200:
                        print(f"DEBUG: Failed to fetch employees, status: {response.status}")
                        return None
                    data = json.loads(response.read().decode('utf-8'))
                    employees = data.get('data', [])
                    pages_fetched += 1
                    total_records += len(employees)
                    print(f"DEBUG: Retrieved {len(employees)} employees in page {pages_fetched} (offset {offset})")
                    
                    if not employees:
                        break
                    
                    for emp in employees:
                        emp_id = emp.get('employee')
                        if not emp_id:
                            continue
                            
                        raw_device_id = emp.get('attendance_device_id')
                        if raw_device_id is None:
                            skipped_missing_device_id += 1
                            continue
                        
                        # Get and clean the attendance_device_id
                        device_id = str(raw_device_id).strip()
                        if not device_id or device_id.lower() in {"none", "null"}:
                            skipped_missing_device_id += 1
                            continue
                            
                        # Create employee record
                        emp_record = {
                            'erp_id': str(emp_id).strip(),
                            'name': str(emp.get('employee_name', '')).strip(),
                            'attendance_device_id': device_id
                        }
                        
                        # Map by attendance device ID
                        device_id_mapping[device_id] = emp_record
                        print(f"DEBUG: Mapped device ID '{device_id}' to employee {emp_record['erp_id']} ({emp_record['name']})")
                
                if len(employees) < page_size:
                    break
                offset += page_size
            
            print(f"\nDEBUG: Employee Device ID Mapping Summary:")
            print(f"- Pages fetched: {pages_fetched}")
            print(f"- Total employee records processed: {total_records}")
            print(f"- Total employees with device IDs: {len(device_id_mapping)}")
            if skipped_missing_device_id:
                print(f"- Skipped employees without usable attendance_device_id: {skipped_missing_device_id}")
            
            if not device_id_mapping:
                print("DEBUG: No employees with attendance_device_id were found. Ensure ERPNext records are configured.")
            else:
                print("\nDEBUG: First 10 device ID mappings:")
                for i, (device_id, emp) in enumerate(list(device_id_mapping.items())[:10]):
                    print(f"  {i+1}. Device ID: '{device_id}' -> Employee: {emp['erp_id']} ({emp['name']})")
            
            return device_id_mapping if device_id_mapping else {}
                    
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("DEBUG: API key invalid or expired - skipping employee validation")
            else:
                print(f"DEBUG: HTTP Error fetching employees: {e.code} {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"DEBUG: Network error fetching employees: {str(e)}")
            return None
        except ConnectionError as e:
            print(f"DEBUG: Connection error fetching employees: {str(e)}")
            return None
        except TimeoutError as e:
            print(f"DEBUG: Timeout fetching employees: {str(e)}")
            return None
        except Exception as e:
            print(f"DEBUG: Error fetching employees: {str(e)}")
            return None

def perform_first_run_setup():
    """On first run of a new system/EXE, reset persisted data and optionally seed defaults."""
    try:
        # Get the data directory path from storage
        data_dir = storage.data_dir
        marker_file = os.path.join(data_dir, ".first_run_completed")
        
        print(f"Checking first-run status in: {data_dir}")
        print(f"Marker file exists: {os.path.exists(marker_file)}")

        # Only run once per system install (per data directory)
        if not os.path.exists(marker_file):
            print("First run detected: resetting stored data to factory defaults...")
            
            # Clear all data files
            data_files = [
                storage.devices_file,
                storage.users_file,
                storage.settings_file,
                storage.erp_config_file,
                storage.device_history_file,
                storage.user_history_file,
                storage.sync_history_file
            ]
            
            for data_file in data_files:
                try:
                    if data_file.exists():
                        data_file.unlink()
                        print(f"Removed existing data file: {data_file}")
                except Exception as e:
                    print(f"Warning: Could not remove {data_file}: {e}")
            
            # Reinitialize storage to create fresh default files
            storage._initialize_defaults()
            print("✓ Reset all data to factory defaults")

            # Default settings for a fresh system
            default_settings = {
                "dateFormat": "YYYY-MM-DD",
                "recordsPerPage": 50,
                "autoSync": False,
                "syncInterval": 60
            }
            storage.save_settings(default_settings)
            print("✓ Applied default settings")

            # If a bootstrap_config.json is packaged beside this script/EXE, apply it
            try:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                bootstrap_path = os.path.join(app_dir, "bootstrap_config.json")
                if os.path.exists(bootstrap_path):
                    print(f"Found bootstrap config at: {bootstrap_path}")
                    with open(bootstrap_path, "r") as f:
                        boot = json.load(f)
                    if isinstance(boot, dict):
                        if "devices" in boot:
                            storage.save_devices(boot.get("devices") or [])
                            print("✓ Applied bootstrap devices")
                        if "erp_config" in boot:
                            storage.save_erp_config(boot.get("erp_config") or {})
                            print("✓ Applied bootstrap ERP config")
                        if "settings" in boot:
                            storage.save_settings(boot.get("settings") or default_settings)
                            print("✓ Applied bootstrap settings")
                        if "users" in boot and isinstance(boot["users"], list):
                            storage.save_users(boot["users"])
                            print("✓ Applied bootstrap users")
                        print("✓ Bootstrap configuration applied successfully")
            except Exception as e:
                print(f"WARNING: Could not apply bootstrap_config.json: {e}")

            # Create data directory if it doesn't exist
            os.makedirs(data_dir, exist_ok=True)
            
            # Write marker file
            try:
                with open(marker_file, "w") as f:
                    f.write("This file indicates the first run setup is complete.")
                print(f"✓ Created first-run marker at: {marker_file}")
            except Exception as e:
                print(f"WARNING: Could not write first-run marker: {e}")

            print("✓ First-run setup completed successfully")
        else:
            print("First-run already completed, skipping initialization")
            
    except Exception as e:
        print(f"ERROR: First-run setup failed: {e}")
        import traceback
        traceback.print_exc()

def start_server():
    # Perform automatic fresh-setup on first run of a new install
    perform_first_run_setup()

    # Start ADMS push listener for face devices (port 8000, background thread)
    try:
        from adms_listener import start as start_adms
        start_adms(8000)
    except Exception as e:
        print(f"[ADMS] Could not start listener: {e}")

    PORT = 8083
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), EnhancedBiometricHandler) as httpd:
            print(f"Enhanced Biometric Tool Server running at http://localhost:{PORT}")
            webbrowser.open(f'http://localhost:{PORT}')
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98 or "Address already in use" in str(e):
            for alt_port in [8084, 8085, 8086, 8087]:
                try:
                    with socketserver.TCPServer(("", alt_port), EnhancedBiometricHandler) as httpd:
                        print(f"Server running at http://localhost:{alt_port}")
                        webbrowser.open(f'http://localhost:{alt_port}')
                        httpd.serve_forever()
                        break
                except OSError:
                    continue
            else:
                print("ERROR: No available ports found. Please restart your computer.")
                input("Press Enter to exit...")
        else:
            print(f"Server error: {e}")
            input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Server error: {e}")
        input("Press Enter to exit...")
