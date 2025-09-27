import os
import sys

# Add src to path
sys.path.append('src')

# Import and test
from utils.version import get_version

print("Testing get_version():")
print("Result:", repr(get_version()))
