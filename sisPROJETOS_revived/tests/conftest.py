"""
Pytest configuration file for sisPROJETOS tests.

This file sets up the Python path to allow proper imports of src modules.
"""

import sys
import os

# Add src directory to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(project_root, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
