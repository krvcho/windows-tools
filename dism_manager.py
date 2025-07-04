"""
DISM (Deployment Image Servicing and Management) operations manager
Handles Windows system image repair and maintenance
"""

import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from PySide6.QtCore import QThread, Signal

class DismManager:
    """Manager for DISM operations"""
    
    def __init__(self):
        self.current_process = None
        self.is_running = False
    
    def check_dism_availability(self) -> bool:
        """Check if DISM is available on the system"""
        try:
            result = subprocess.run(
                ['dism', '/?'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_image_info(self) -> dict:
        """Get Windows image information"""
        try:
            result = subprocess.run(
                ['dism', '/online', '/get-imageinfo'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return self._parse_image_info(result.stdout)
            else:
                return {'error': result.stderr}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _parse_image_info(self, output: str) -> dict:
        """Parse DISM image info output"""
        info = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
    
    def check_health_status(self) -> str:
        """Get current image health status"""
        try:
            result = subprocess.run(
                ['dism', '/online', '/cleanup-image', '/checkhealth'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'no component store corruption detected' in output:
                    return 'healthy'
                elif 'component store corruption detected' in output:
                    return 'corrupted'
                else:
                    return 'unknown'
            else:
                return 'error'
                
        except Exception:
            return 'error'
    
    def estimate_repair_time(self) -> str:
        """Estimate repair time based on system specs"""
        try:
            import psutil
            
            # Get system specs
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # Rough estimation based on typical performance
            if cpu_count >= 8 and memory_gb >= 16:
                return "15-20 minutes"
            elif cpu_count >= 4 and memory_gb >= 8:
                return "20-30 minutes"
            else:
                return "30-45 minutes"
                
        except Exception:
            return "20-30 minutes"

class DismCommandRunner(QThread):
    """Thread for running DISM commands with real-time output"""
    
    output_received = Signal(str)
    progress_update = Signal(int)  # Progress percentage
    finished = Signal(int)  # Exit code
    
    def __init__(self, command_args: list, output_widget=None):
        super().__init__()
        self.command_args = command_args
        self.output_widget = output_widget
        self.process = None
        self.should_stop = False
        
        # Connect signals
        if output_widget:
            self.output_received.connect(self.append_output)
    
    def run(self):
        """Execute DISM command"""
        try:
            # Prepare command
            full_command = ['dism'] + self.command_args
            
            # Start process
            self.process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Read output line by line
            while True:
                if self.should_stop:
                    self.process.terminate()
                    break
                
                output = self.process.stdout.readline()
                if output:
                    line = output.strip()
                    self.output_received.emit(line)
                    
                    # Extract progress if available
                    progress = self._extract_progress(line)
                    if progress is not None:
                        self.progress_update.emit(progress)
                        
                elif self.process.poll() is not None:
                    break
            
            # Get final exit code
            exit_code = self.process.returncode
            self.finished.emit(exit_code)
            
        except Exception as e:
            self.output_received.emit(f"Error: {str(e)}")
            self.finished.emit(1)
    
    def stop(self):
        """Stop the running DISM process"""
        self.should_stop = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def _extract_progress(self, line: str) -> Optional[int]:
        """Extract progress percentage from DISM output"""
        try:
            # DISM typically shows progress like "[===========     ] 55.0%"
            if '%' in line and '[' in line:
                # Find percentage
                percent_pos = line.find('%')
                if percent_pos > 0:
                    # Look backwards for the number
                    start = percent_pos - 1
                    while start >= 0 and (line[start].isdigit() or line[start] == '.'):
                        start -= 1
                    
                    if start < percent_pos - 1:
                        percent_str = line[start + 1:percent_pos]
                        return int(float(percent_str))
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def append_output(self, text: str):
        """Append text to output widget"""
        if self.output_widget and text.strip():
            self.output_widget.append(text)
            # Auto-scroll to bottom
            cursor = self.output_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.output_widget.setTextCursor(cursor)

class DismHealthChecker:
    """Utility class for checking system health with DISM"""
    
    @staticmethod
    def get_component_store_info() -> dict:
        """Get detailed component store information"""
        try:
            result = subprocess.run(
                ['dism', '/online', '/cleanup-image', '/analyzecomponentstore'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return DismHealthChecker._parse_component_store(result.stdout)
            else:
                return {'error': result.stderr}
                
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _parse_component_store(output: str) -> dict:
        """Parse component store analysis output"""
        info = {
            'size_of_component_store': 'Unknown',
            'shared_with_windows': 'Unknown',
            'backups_and_disabled_features': 'Unknown',
            'cache_and_temporary_data': 'Unknown',
            'date_of_last_cleanup': 'Unknown',
            'reclaimable_packages': 0,
            'component_store_cleanup_recommended': False
        }
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            if 'Windows Explorer Reported Size of Component Store' in line:
                info['size_of_component_store'] = line.split(':')[-1].strip()
            elif 'Shared with Windows' in line:
                info['shared_with_windows'] = line.split(':')[-1].strip()
            elif 'Backups and Disabled Features' in line:
                info['backups_and_disabled_features'] = line.split(':')[-1].strip()
            elif 'Cache and Temporary Data' in line:
                info['cache_and_temporary_data'] = line.split(':')[-1].strip()
            elif 'Date of Last Cleanup' in line:
                info['date_of_last_cleanup'] = line.split(':')[-1].strip()
            elif 'Component Store Cleanup Recommended' in line:
                recommended = line.split(':')[-1].strip().lower()
                info['component_store_cleanup_recommended'] = recommended == 'yes'
        
        return info
    
    @staticmethod
    def cleanup_component_store() -> bool:
        """Perform component store cleanup"""
        try:
            result = subprocess.run(
                ['dism', '/online', '/cleanup-image', '/startcomponentcleanup'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    @staticmethod
    def reset_base() -> bool:
        """Reset the base of superseded components (irreversible)"""
        try:
            result = subprocess.run(
                ['dism', '/online', '/cleanup-image', '/startcomponentcleanup', '/resetbase'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            return result.returncode == 0
            
        except Exception:
            return False

# Utility functions for DISM operations
def is_dism_available() -> bool:
    """Check if DISM is available on the system"""
    manager = DismManager()
    return manager.check_dism_availability()

def get_system_health_summary() -> dict:
    """Get a summary of system health status"""
    manager = DismManager()
    checker = DismHealthChecker()
    
    summary = {
        'dism_available': manager.check_dism_availability(),
        'image_health': manager.check_health_status(),
        'estimated_repair_time': manager.estimate_repair_time(),
        'component_store_info': checker.get_component_store_info()
    }
    
    return summary

def recommend_maintenance_actions() -> list:
    """Recommend maintenance actions based on system state"""
    recommendations = []
    
    try:
        health_summary = get_system_health_summary()
        
        if not health_summary['dism_available']:
            recommendations.append("DISM is not available on this system")
            return recommendations
        
        health_status = health_summary['image_health']
        
        if health_status == 'corrupted':
            recommendations.append("Run DISM /RestoreHealth to repair image corruption")
            recommendations.append("After DISM repair, run SFC /scannow to verify system files")
        elif health_status == 'healthy':
            recommendations.append("System image appears healthy")
            recommendations.append("Consider running SFC /scannow for additional verification")
        else:
            recommendations.append("Run DISM /ScanHealth for detailed health analysis")
        
        # Component store recommendations
        component_info = health_summary.get('component_store_info', {})
        if component_info.get('component_store_cleanup_recommended', False):
            recommendations.append("Component store cleanup is recommended to free disk space")
        
    except Exception as e:
        recommendations.append(f"Error analyzing system: {str(e)}")
    
    return recommendations
