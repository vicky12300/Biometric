#!/usr/bin/env python3
"""Convert PNG to ICO for Windows executable"""
from PIL import Image

def create_icon():
    """Convert auriga.png to auriga.ico"""
    try:
        img = Image.open('auriga.png')
        # Resize to common icon sizes
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save('auriga.ico', format='ICO', sizes=icon_sizes)
        print("✓ Icon created: auriga.ico")
    except Exception as e:
        print(f"Error creating icon: {e}")
        print("Install Pillow: pip install Pillow")

if __name__ == '__main__':
    create_icon()
