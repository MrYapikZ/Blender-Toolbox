import os
from .constants import ADDON_DIR


# ------------------------------------------------------------------------
# File Manager
# ------------------------------------------------------------------------
class FileManager:
    @staticmethod
    def get_addon_directory():
        return ADDON_DIR

    @staticmethod
    def get_filepath(filename):
        addon_dir = FileManager.get_addon_directory()
        return os.path.join(addon_dir, filename)
