import winreg
from typing import Dict, Any

class RegistryManager:
    def __init__(self):
        self.registry_changes = {
            # Windows Update Service
            r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU": {
                "NoAutoUpdate": {"disable": 1, "enable": 0},
                "AUOptions": {"disable": 1, "enable": 4}
            },
            # Delivery Optimization
            r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization": {
                "DODownloadMode": {"disable": 0, "enable": 1}
            },
            # Windows Store Auto Updates
            r"SOFTWARE\Policies\Microsoft\WindowsStore": {
                "AutoDownload": {"disable": 2, "enable": 4}
            }
        }
    
    def disable_windows_updates(self, output_widget):
        """Disable Windows automatic updates"""
        self._apply_registry_changes("disable", output_widget)
    
    def enable_windows_updates(self, output_widget):
        """Enable Windows automatic updates"""
        self._apply_registry_changes("enable", output_widget)
    
    def _apply_registry_changes(self, action: str, output_widget):
        """Apply registry changes based on action (enable/disable)"""
        for key_path, values in self.registry_changes.items():
            try:
                # Create or open the registry key
                with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    for value_name, actions in values.items():
                        if action in actions:
                            value_data = actions[action]
                            winreg.SetValueEx(
                                key, value_name, 0, winreg.REG_DWORD, value_data
                            )
                            output_widget.append(
                                f"Set HKLM\\{key_path}\\{value_name} = {value_data}"
                            )
                        
            except Exception as e:
                error_msg = f"Failed to modify HKLM\\{key_path}: {str(e)}"
                output_widget.append(error_msg)
                raise Exception(error_msg)
    
    def get_registry_value(self, key_path: str, value_name: str, default_value=None):
        """Get a registry value"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except FileNotFoundError:
            return default_value
        except Exception:
            return default_value
    
    def set_registry_value(self, key_path: str, value_name: str, value_data: Any, value_type=winreg.REG_DWORD):
        """Set a registry value"""
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, value_name, 0, value_type, value_data)
                return True
        except Exception as e:
            raise Exception(f"Failed to set registry value: {str(e)}")
    
    def delete_registry_value(self, key_path: str, value_name: str):
        """Delete a registry value"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, value_name)
                return True
        except FileNotFoundError:
            return True  # Value doesn't exist, consider it deleted
        except Exception as e:
            raise Exception(f"Failed to delete registry value: {str(e)}")
    
    def key_exists(self, key_path: str) -> bool:
        """Check if a registry key exists"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path):
                return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def backup_registry_key(self, key_path: str, backup_file: str):
        """Backup a registry key to a file"""
        try:
            import subprocess
            command = f'reg export "HKLM\\{key_path}" "{backup_file}" /y'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def restore_registry_key(self, backup_file: str):
        """Restore a registry key from a backup file"""
        try:
            import subprocess
            command = f'reg import "{backup_file}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
