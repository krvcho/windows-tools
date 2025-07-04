import os
import sys
import subprocess
import winreg
from pathlib import Path

class SystemToolsInstaller:
    def __init__(self):
        self.app_name = "System Maintenance Tools"
        self.app_version = "1.0.0"
        self.install_dir = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "SystemMaintenanceTools"
    
    def install(self):
        """Install the application"""
        print(f"Installing {self.app_name} v{self.app_version}...")
        
        try:
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created installation directory: {self.install_dir}")
            
            # Copy application files
            self.copy_files()
            
            # Create desktop shortcut
            self.create_desktop_shortcut()
            
            # Add to Windows registry (for uninstall)
            self.add_to_registry()
            
            print("Installation completed successfully!")
            
        except Exception as e:
            print(f"Installation failed: {str(e)}")
            return False
        
        return True
    
    def copy_files(self):
        """Copy application files to installation directory"""
        import shutil
        
        current_dir = Path(__file__).parent
        files_to_copy = [
            "main.py",
            "system_commands.py",
            "registry_manager.py",
            "admin_utils.py",
            "ui_styles.py",
            "requirements.txt"
        ]
        
        for file_name in files_to_copy:
            src = current_dir / file_name
            dst = self.install_dir / file_name
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Copied {file_name}")
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        try:
            import win32com.client
            
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / f"{self.app_name}.lnk"
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_dir / "main.py"}"'
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print(f"Created desktop shortcut: {shortcut_path}")
            
        except Exception as e:
            print(f"Failed to create desktop shortcut: {str(e)}")
    
    def add_to_registry(self):
        """Add application to Windows registry for uninstall"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\SystemMaintenanceTools"
            
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, self.app_name)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, self.app_version)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "System Administrator")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, 
                                f'python "{self.install_dir / "installer.py"}" --uninstall')
                
            print("Added to Windows registry")
            
        except Exception as e:
            print(f"Failed to add to registry: {str(e)}")
    
    def uninstall(self):
        """Uninstall the application"""
        print(f"Uninstalling {self.app_name}...")
        
        try:
            # Remove installation directory
            import shutil
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                print(f"Removed installation directory: {self.install_dir}")
            
            # Remove desktop shortcut
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / f"{self.app_name}.lnk"
            if shortcut_path.exists():
                shortcut_path.unlink()
                print(f"Removed desktop shortcut: {shortcut_path}")
            
            # Remove from registry
            try:
                winreg.DeleteKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\SystemMaintenanceTools"
                )
                print("Removed from Windows registry")
            except FileNotFoundError:
                pass
            
            print("Uninstallation completed successfully!")
            
        except Exception as e:
            print(f"Uninstallation failed: {str(e)}")
            return False
        
        return True

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        installer = SystemToolsInstaller()
        installer.uninstall()
    else:
        installer = SystemToolsInstaller()
        installer.install()

if __name__ == "__main__":
    main()
