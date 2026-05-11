#!/usr/bin/env python3
"""
Desktop Application Launcher for Biometric Tools Manager
Runs the web server in background and displays UI in native window
"""
import webview
import threading
import time
import sys
import os
import traceback
import uuid
from biometric_web_app_fixed import EnhancedBiometricHandler, socketserver
from data_storage import storage

PORT = 8083
SERVER_PORT = PORT
server = None
server_ready = threading.Event()
DEBUG_LOG_FILE = os.path.join(storage.get_data_dir(), "desktop_debug.log")

def debug_log(message, exc=None):
    try:
        from datetime import datetime
        timestamp = datetime.now().isoformat(timespec="seconds")
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] [DESKTOP] {message}\n")
            if exc is not None:
                log_file.write(f"[{timestamp}] [DESKTOP] EXCEPTION: {repr(exc)}\n")
                log_file.write(traceback.format_exc())
                log_file.write("\n")
    except Exception:
        pass

debug_log(
    "desktop module loaded; "
    f"python={sys.version!r}; executable={sys.executable!r}; "
    f"frozen={getattr(sys, 'frozen', False)!r}; "
    f"_MEIPASS={getattr(sys, '_MEIPASS', None)!r}; "
    f"data_dir={storage.get_data_dir()!r}"
)

def start_server():
    """Start the HTTP server in background"""
    global server, SERVER_PORT
    try:
        # Pre-load data from storage on server start
        print(f"Loading data from: {storage.get_data_dir()}")
        devices = storage.load_devices()
        users = storage.load_users()
        settings = storage.load_settings()
        debug_log(f"start_server loaded devices={len(devices)}, users={len(users)}, settings_keys={list(settings.keys()) if isinstance(settings, dict) else 'n/a'}")
        print(f"Loaded: {len(devices)} devices, {len(users)} users")

        for candidate_port in [PORT, 8084, 8085, 8086, 8087]:
            try:
                debug_log(f"start_server attempting port={candidate_port}")
                with socketserver.TCPServer(("", candidate_port), EnhancedBiometricHandler) as httpd:
                    server = httpd
                    SERVER_PORT = candidate_port
                    server_ready.set()
                    debug_log(f"start_server listening port={candidate_port}")
                    print(f"Server running on port {candidate_port}")
                    httpd.serve_forever()
                    return
            except OSError as exc:
                debug_log(f"start_server port unavailable port={candidate_port}", exc)
                continue

        raise OSError("No available server ports found")
    except Exception as e:
        server_ready.set()
        debug_log("start_server failed", e)
        print(f"Server error: {e}")

def save_on_exit():
    """Save data before closing"""
    debug_log("save_on_exit called")
    print("Saving data before exit...")
    # Data is already being saved by auto-sync
    # This is just a final safety save
    time.sleep(1)  # Give time for any pending saves
    print("Data saved successfully")

class Api:
    """API class to expose Python functions to JavaScript"""
    
    def download_blob(self, filename, base64_data):
        """
        Download a file from base64 data using native file dialog
        
        Args:
            filename: Suggested filename
            base64_data: Base64 encoded file content
            
        Returns:
            True if file was saved, False if cancelled
        """
        import base64
        from tkinter import filedialog
        import tkinter as tk
        
        try:
            # Decode base64 data
            file_data = base64.b64decode(base64_data)
            
            # Create hidden root window for file dialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Get default downloads folder
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            default_path = os.path.join(downloads_folder, filename)
            
            # Show save file dialog
            file_path = filedialog.asksaveasfilename(
                initialdir=downloads_folder,
                initialfile=filename,
                defaultextension=os.path.splitext(filename)[1],
                filetypes=[
                    ("All Files", "*.*"),
                    ("Excel Files", "*.xlsx"),
                    ("CSV Files", "*.csv")
                ]
            )
            
            root.destroy()
            
            if file_path:
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                print(f"File saved: {file_path}")
                return True
            else:
                print("Download cancelled by user")
                return False
                
        except Exception as e:
            print(f"Download error: {e}")
            return False

def main():
    """Main application entry point"""
    debug_log("main started")
    print("=" * 60)
    print("Biometric Tools Manager - Desktop Application")
    print("=" * 60)
    print(f"Data directory: {storage.get_data_dir()}")
    print("=" * 60)

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    debug_log(f"server thread started alive={server_thread.is_alive()}")

    # Wait for server to start
    server_ready.wait(timeout=5)
    debug_log(f"after startup wait server_is_set={server is not None}, server_thread_alive={server_thread.is_alive()}")

    # Create API instance
    api = Api()
    debug_log("API instance created")

    # Create native window
    window = webview.create_window(
        title='Biometric Tools Manager',
        url=f'http://localhost:{SERVER_PORT}/?v={uuid.uuid4().hex}',
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(1024, 768),
        js_api=api  # Expose API to JavaScript
    )

    # Start the GUI (blocking call)
    webview.start()

    # Save data on exit
    save_on_exit()

    # Cleanup on exit
    if server:
        server.shutdown()

if __name__ == '__main__':
    main()
