import os
import sys

# Test version detection logic
current_dir = os.getcwd()
print(f"Current directory: {current_dir}")
print(f"Contains 'src': {'src' in current_dir}")
print(f"Version file exists in current dir: {os.path.exists(os.path.join(current_dir, '.version'))}")

# Check the logic path
if hasattr(sys, '_MEIPASS'):
    print("Path: PyInstaller")
elif '__file__' in globals():
    print("Path: __file__ available")
else:
    print("Path: Command line mode")
    
    # Check if .version exists in current directory
    if os.path.exists(os.path.join(current_dir, '.version')):
        print("Found .version in current directory")
        root_dir = current_dir
    elif 'src' in current_dir:
        print("Found 'src' in path, searching up...")
    else:
        print("Using current directory as fallback")
        root_dir = current_dir

# Test reading the file
version_file = os.path.join(current_dir, '.version')
if os.path.exists(version_file):
    with open(version_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Raw content: {repr(content)}")
        print(f"Stripped content: {repr(content.strip())}")
