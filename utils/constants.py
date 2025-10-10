import os

try:
    # Prefer the constant from the root package if you defined it there
    from .. import ADDON_ID  # in __init__.py set: ADDON_ID = __name__
except Exception:
    # Fallback to the top-level package name
    ADDON_ID = (__package__.split('.', 1)[0] if __package__
                else __name__.split('.', 1)[0])

try:
    # Prefer the constant from the root package if defined there
    from .. import ADDON_DIR  # in __init__.py set: ADDON_DIR = os.path.dirname(__file__)
except Exception:
    # Fallback: determine the top-level add-on directory manually
    if __package__:
        # Get the top-level package name
        top_package = __package__.split('.', 1)[0]
        # Import it and get its file path
        pkg = __import__(top_package)
        ADDON_DIR = os.path.dirname(os.path.abspath(pkg.__file__))
    else:
        # If all else fails, just use this file’s directory
        ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
