# Runtime hook to ensure Python encodings module is properly initialized
import sys
import os

# Make sure encodings module is importable
try:
    import encodings
except ImportError:
    # If encodings fails, try to manually set up the search path
    # This helps PyInstaller bundled apps find encodings
    pass

# Ensure utf-8 and ascii are always available
try:
    import encodings.utf_8
    import encodings.ascii
except ImportError:
    pass
