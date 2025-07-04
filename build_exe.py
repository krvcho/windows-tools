import sys
import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["PySide6", "winreg", "psutil", "ctypes"],
    "excludes": ["tkinter", "matplotlib"],
    "include_files": [],
    "optimize": 2,
}

# GUI applications require a different base on Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="SystemMaintenanceTools",
    version="1.0",
    description="Windows System Maintenance Tools",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="SystemMaintenanceTools.exe",
            icon=None,  # Add icon file path if you have one
            uac_admin=True  # Request admin privileges
        )
    ],
)
