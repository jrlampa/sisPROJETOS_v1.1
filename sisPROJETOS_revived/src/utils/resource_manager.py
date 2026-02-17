"""
Resource Manager - Handles resource file locations for both development and production builds
"""

import os
import sys


class ResourceManager:
    """Manages resource file paths for both development and PyInstaller bundled environments"""

    def __init__(self):
        self._setup_paths()

    def _setup_paths(self):
        """Setup resource paths based on execution environment"""
        if getattr(sys, "frozen", False):
            # Running as PyInstaller executable
            self.base_path = sys._MEIPASS
            # Templates are in the root _MEIPASS directory (where sisPROJETOS.exe is located)
            self.templates_dir = os.path.join(self.base_path, "resources", "templates")
        else:
            # Running in development
            current_file = os.path.abspath(__file__)  # /path/to/src/utils/resource_manager.py
            src_dir = os.path.dirname(os.path.dirname(current_file))  # /path/to/src/
            self.base_path = os.path.dirname(src_dir)  # /path/to/ (project root)
            self.templates_dir = os.path.join(src_dir, "resources", "templates")

    def get_template(self, filename):
        """
        Get the full path to a template file

        Args:
            filename (str): Template filename (e.g., 'prancha.dwg')

        Returns:
            str: Full path to the template file
        """
        return os.path.join(self.templates_dir, filename)

    def template_exists(self, filename):
        """
        Check if a template file exists

        Args:
            filename (str): Template filename

        Returns:
            bool: True if template exists
        """
        return os.path.exists(self.get_template(filename))

    def get_all_templates(self):
        """
        Get list of all available templates

        Returns:
            list: List of template filenames
        """
        if os.path.exists(self.templates_dir):
            return os.listdir(self.templates_dir)
        return []


# Global instance
_resource_manager = None


def get_resource_manager():
    """Get or create the global ResourceManager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
