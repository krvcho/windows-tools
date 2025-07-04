import ctypes
import sys
import os
import subprocess

class AdminUtils:
    @staticmethod
    def is_admin():
        """Check if the current process is running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    @staticmethod
    def run_as_admin():
        """Restart the current script with administrator privileges"""
        if AdminUtils.is_admin():
            return True
        else:
            try:
                # Re-run the program with admin rights
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                return True
            except:
                return False
    
    @staticmethod
    def request_elevation():
        """Request UAC elevation for the current process"""
        if not AdminUtils.is_admin():
            try:
                # Show UAC prompt
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            except Exception as e:
                raise Exception(f"Failed to request elevation: {str(e)}")
    
    @staticmethod
    def get_user_info():
        """Get current user information"""
        try:
            import getpass
            import socket
            
            return {
                'username': getpass.getuser(),
                'computer_name': socket.gethostname(),
                'is_admin': AdminUtils.is_admin()
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def check_system_requirements():
        """Check if the system meets requirements for the application"""
        requirements = {
            'windows_version': True,
            'python_version': True,
            'admin_capable': True
        }
        
        try:
            # Check Windows version
            import platform
            if not platform.system().lower() == 'windows':
                requirements['windows_version'] = False
            
            # Check Python version (3.7+)
            if sys.version_info < (3, 7):
                requirements['python_version'] = False
            
            # Check if UAC elevation is possible
            try:
                ctypes.windll.shell32.IsUserAnAdmin()
            except:
                requirements['admin_capable'] = False
                
        except Exception:
            pass
        
        return requirements
    
    @staticmethod
    def create_elevated_process(command, arguments=""):
        """Create a new process with elevated privileges"""
        try:
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", command, arguments, None, 1
            )
            return result > 32  # Success if result > 32
        except Exception:
            return False
    
    @staticmethod
    def is_uac_enabled():
        """Check if UAC (User Account Control) is enabled"""
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "EnableLUA")
                return value == 1
        except:
            return True  # Assume enabled if can't determine
    
    @staticmethod
    def get_elevation_type():
        """Get the current process elevation type"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get current process token
            process = ctypes.windll.kernel32.GetCurrentProcess()
            token = wintypes.HANDLE()
            
            if not ctypes.windll.advapi32.OpenProcessToken(
                process, 0x0008, ctypes.byref(token)  # TOKEN_QUERY
            ):
                return "unknown"
            
            # Query token elevation
            elevation = wintypes.DWORD()
            size = wintypes.DWORD()
            
            if ctypes.windll.advapi32.GetTokenInformation(
                token, 20, ctypes.byref(elevation),  # TokenElevationType = 20
                ctypes.sizeof(elevation), ctypes.byref(size)
            ):
                ctypes.windll.kernel32.CloseHandle(token)
                
                if elevation.value == 1:
                    return "default"
                elif elevation.value == 2:
                    return "full"
                elif elevation.value == 3:
                    return "limited"
            
            ctypes.windll.kernel32.CloseHandle(token)
            return "unknown"
            
        except Exception:
            return "unknown"
