"""
Version utility for the receipts application.
Provides version information throughout the application.
"""

import os
import sys

def get_version():
    """
    Get the current version from the .version file.
    
    Returns:
        str: Version string (e.g., "1.0.2")
    """
    try:
        # Get the root directory (where .version file is located)
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable
            root_dir = os.path.dirname(sys.executable)
            # DEBUG: print(f"DEBUG: PyInstaller mode, root_dir = {root_dir}")
        elif '__file__' in globals():
            # Running as script with __file__ available
            # Go up 3 levels: version.py -> utils -> src -> project_root
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        else:
            # Running from command line or interactive mode
            # Try to find project root by looking for .version file
            current_dir = os.getcwd()
            
            # Check if .version exists in current directory
            if os.path.exists(os.path.join(current_dir, '.version')):
                root_dir = current_dir
                # DEBUG: print(f"DEBUG: Command line mode, found .version in {current_dir}")
            # If we're in src or src/utils, go up to find project root
            elif 'src' in current_dir:
                # Go up directories until we find .version or reach filesystem root
                check_dir = current_dir
                while check_dir and check_dir != os.path.dirname(check_dir):
                    if os.path.exists(os.path.join(check_dir, '.version')):
                        root_dir = check_dir
                        break
                    check_dir = os.path.dirname(check_dir)
                else:
                    # Fallback to current directory
                    root_dir = current_dir
                # DEBUG: print(f"DEBUG: Command line mode with src, root_dir = {root_dir}")
            else:
                root_dir = current_dir
                # DEBUG: print(f"DEBUG: Command line mode fallback, root_dir = {root_dir}")
        
        version_file = os.path.join(root_dir, '.version')
        
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
                # DEBUG: print(f"DEBUG: Read version: {repr(version)}")
                return version
        else:
            # Fallback version if file doesn't exist
            # DEBUG: print("DEBUG: Version file not found, using fallback")
            return "1.0.0"
            
    except Exception as e:
        # Fallback version if any error occurs
        # DEBUG: print(f"DEBUG: Exception occurred: {e}")
        return "1.0.0"

def get_version_info():
    """
    Get detailed version information.
    
    Returns:
        dict: Dictionary with version details
    """
    version = get_version()
    return {
        'version': version,
        'name': 'Portal das Finanças Receipts',
        'description': 'Automated receipt generation for Portuguese tax authority',
        'author': 'Portal Receipts Team',
        'year': '2025'
    }

def format_version_string():
    """
    Format a user-friendly version string for display.
    
    Returns:
        str: Formatted version string
    """
    info = get_version_info()
    return f"{info['name']} v{info['version']} - {info['year']}"

# For convenience, make version available at module level
__version__ = get_version()
