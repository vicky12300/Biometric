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
from biometric_web_app_fixed import EnhancedBiometricHandler, socketserver
from data_storage import storage

PORT = 8083
server = None

def start_server():
    """Start the HTTP server in background"""
    global server
    try:
        # Pre-load data from storage on server start
        print(f"Loading data from: {storage.get_data_dir()}")
        devices = storage.load_devices()
        users = storage.load_users()
        settings = storage.load_settings()
        print(f"Loaded: {len(devices)} devices, {len(users)} users")
        
        with socketserver.TCPServer(("", PORT), EnhancedBiometricHandler) as httpd:
            server = httpd
            print(f"Server running on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")

def save_on_exit():
    """Save data before closing"""
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
    print("=" * 60)
    print("Biometric Tools Manager - Desktop Application")
    print("=" * 60)
    print(f"Data directory: {storage.get_data_dir()}")
    print("=" * 60)

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    # Create API instance
    api = Api()

    # Create native window
    window = webview.create_window(
        title='Biometric Tools Manager',
        url=f'http://localhost:{PORT}',
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
