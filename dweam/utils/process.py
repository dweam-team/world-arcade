import sys
import os
import subprocess
import asyncio

def is_debug_build() -> bool:
    """Detect if we're running the debug build based on executable name"""
    if getattr(sys, 'frozen', False):
        # We're running in a PyInstaller bundle
        executable_path = sys.executable
        return 'debug' in os.path.basename(executable_path).lower()
    return True  # In development environment, always use debug mode

def get_subprocess_flags() -> int:
    """Get the appropriate subprocess creation flags based on build type"""
    if sys.platform == "win32" and not is_debug_build():
        return subprocess.CREATE_NO_WINDOW
    return 0

def get_asyncio_subprocess_flags() -> int:
    """Get the appropriate asyncio subprocess creation flags based on build type"""
    if sys.platform == "win32" and not is_debug_build():
        return subprocess.CREATE_NO_WINDOW
    return 0

def patch_subprocess_popen():
    """
    Monkey patch subprocess.Popen to always use CREATE_NO_WINDOW in release mode.
    This ensures any subprocess created (even by third-party libraries) won't show windows.
    """
    if sys.platform != "win32" or is_debug_build():
        return

    original_Popen = subprocess.Popen
    def Popen_no_window(*args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        return original_Popen(*args, **kwargs)
    subprocess.Popen = Popen_no_window 