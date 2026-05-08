import sys
print(f"Python version: {sys.version}")
print(f"Major: {sys.version_info.major}, Minor: {sys.version_info.minor}")

if sys.version_info < (3, 9):
    print("\n⚠️  WARNING: Python 3.9+ recommended for type hints")
    print("   Your version may have issues with Optional[] syntax")
