"""
Pytest configuration file for sisPROJETOS tests.

This file sets up the Python path to allow proper imports of src modules.
"""

import os
import sys

# Add both project root and src directory to Python path
# - project_root allows 'from src.modules...' (used in tests)
# - src_dir allows 'from database...' and 'from utils...' (used internally)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(project_root, "src")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
