"""
System Information Manager
Handles collection of comprehensive system information and real-time monitoring
"""

import os
import platform
import subprocess
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PySide6.QtCore import QThread, Signal, QObject

@dataclass
class SystemInfo:
    """Data class for static system information"""
    # Windows Information
    windows_version: str = "Unknown"
    windows_build: str = "Unknown"
    windows_edition: str = "Unknown"
    last_update_date: str = "Unknown"
    last_update_package: str = "Unknown"
    
    # System Information
    computer_name: str = "Unknown"
    user_name: str = "Unknown"
    system_uptime: str = "Unknown"
    motherboard: str = "Unknown"
    bios_version: str = "Unknown"
    
    # Hardware Information
    cpu_model: str = "Unknown"
    cpu_cores: int = 0
    cpu_threads: int = 0
    total_ram_gb: float = 0.0
    gpu_info: List[str] = None
    nvidia_driver_version: str = "Not Available"
    
    # Disk Information
    disk_info: List[Dict] = None
    
    def __post_init__(self):
        if self.gpu_info is None:
            self.gpu_info = []
        if self.disk_info is None:
            self.disk_info = []

@dataclass
class SystemMetrics:
    """Data class for real-time system metrics"""
    timestamp: datetime
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    ram_used_gb: float = 0.0
    ram_available_gb: float = 0.0
    gpu_usage: float = 0.0
    gpu_memory_usage: float = 0.0
    disk_usage: Dict[str, float] = None
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    temperature_cpu: Optional[float] = None
    
    def __post_init__(self):
        if self.disk_usage is None:
            self.disk_usage = {}

class SystemInfoManager(QObject):
    """Manager for collecting system information and metrics"""
    
    # Signals for async operations
    info_collected = Signal(SystemInfo)
    metrics_collected = Signal(SystemMetrics)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.last_network_stats = None
        self.last_network_time = None
    
    def get_complete_system_info(self) -> SystemInfo:
        """Collect complete static system information"""
        try:
            info = SystemInfo()
            
            # Windows Information
            info.windows_version = self.get_windows_version()
            info.windows_build = self.get_windows_build()
            info.windows_edition = self.get_windows_edition()
            info.last_update_date, info.last_update_package = self.get_last_windows_update()
            
            # System Information
            info.computer_name = platform.node()
            info.user_name = os.getenv('USERNAME', 'Unknown')
            info.system_uptime = self.get_system_uptime()
            info.motherboard = self.get_motherboard_info()
            info.bios_version = self.get_bios_info()
            
            # Hardware Information
            info.cpu_model = self.get_cpu_model()
            info.cpu_cores = psutil.cpu_count(logical=False) or 0
            info.cpu_threads = psutil.cpu_count(logical=True) or 0
            info.total_ram_gb = psutil.virtual_memory().total / (1024**3)
            info.gpu_info = self.get_gpu_info()
            info.nvidia_driver_version = self.get_nvidia_driver_version()
            
            # Disk Information
            info.disk_info = self.get_disk_info()
            
            return info
            
        except Exception as e:
            self.error_occurred.emit(f"Error collecting system info: {str(e)}")
            return SystemInfo()
    
    def get_real_time_metrics(self) -> SystemMetrics:
        """Collect real-time system metrics"""
        try:
            metrics = SystemMetrics(timestamp=datetime.now())
            
            # CPU Usage
            metrics.cpu_usage = psutil.cpu_percent(interval=1)
            
            # RAM Usage
            ram = psutil.virtual_memory()
            metrics.ram_usage = ram.percent
            metrics.ram_used_gb = ram.used / (1024**3)
            metrics.ram_available_gb = ram.available / (1024**3)
            
            # GPU Usage (NVIDIA only)
            gpu_usage, gpu_memory = self.get_gpu_usage()
            metrics.gpu_usage = gpu_usage
            metrics.gpu_memory_usage = gpu_memory
            
            # Disk Usage
            metrics.disk_usage = self.get_disk_usage()
            
            # Network Activity
            net_sent, net_recv = self.get_network_activity()
            metrics.network_sent_mb = net_sent
            metrics.network_recv_mb = net_recv
            
            # Temperature
            metrics.temperature_cpu = self.get_cpu_temperature()
            
            return metrics
            
        except Exception as e:
            self.error_occurred.emit(f"Error collecting metrics: {str(e)}")
            return SystemMetrics(timestamp=datetime.now())
    
    def get_windows_version(self) -> str:
        """Get Windows version information"""
        try:
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'Caption=' in line:
                    return line.split('=', 1)[1].strip()
            
            return platform.system() + " " + platform.release()
            
        except Exception:
            return platform.system() + " " + platform.release()
    
    def get_windows_build(self) -> str:
        """Get Windows build number"""
        try:
            result = subprocess.run(
                ['wmic', 'os', 'get', 'BuildNumber', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'BuildNumber=' in line:
                    return line.split('=', 1)[1].strip()
            
            return platform.version()
            
        except Exception:
            return platform.version()
    
    def get_windows_edition(self) -> str:
        """Get Windows edition"""
        try:
            result = subprocess.run(
                ['wmic', 'os', 'get', 'OperatingSystemSKU', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            # Map SKU numbers to edition names
            sku_map = {
                '1': 'Ultimate', '2': 'Home Basic', '3': 'Home Premium',
                '4': 'Enterprise', '6': 'Business', '7': 'Server Standard',
                '48': 'Professional', '49': 'Enterprise N', '50': 'Enterprise KN',
                '101': 'Home', '100': 'Home N', '103': 'Professional N'
            }
            
            for line in result.stdout.split('\n'):
                if 'OperatingSystemSKU=' in line:
                    sku = line.split('=', 1)[1].strip()
                    return sku_map.get(sku, f"Edition {sku}")
            
            return "Unknown Edition"
            
        except Exception:
            return "Unknown Edition"
    
    def get_last_windows_update(self) -> Tuple[str, str]:
        """Get information about the last Windows update"""
        try:
            # Use PowerShell to get Windows Update history
            ps_command = """
            Get-WinEvent -FilterHashtable @{LogName='System'; ID=43} -MaxEvents 1 | 
            Select-Object TimeCreated, Message | 
            ConvertTo-Json
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list) and data:
                        data = data[0]
                    
                    time_created = data.get('TimeCreated', 'Unknown')
                    message = data.get('Message', 'Unknown')
                    
                    # Extract KB number from message if available
                    import re
                    kb_match = re.search(r'KB\d+', message)
                    kb_number = kb_match.group() if kb_match else "Unknown Package"
                    
                    return time_created, kb_number
                except json.JSONDecodeError:
                    pass
            
            # Fallback method using wmic
            result = subprocess.run(
                ['wmic', 'qfe', 'get', 'InstalledOn,HotFixID', '/format:csv'],
                capture_output=True, text=True, timeout=20
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 2:  # Skip header lines
                    last_line = lines[-1]
                    parts = last_line.split(',')
                    if len(parts) >= 3:
                        return parts[1], parts[2]
            
            return "Unknown", "Unknown"
            
        except Exception as e:
            return f"Error: {str(e)}", "Unknown"
    
    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            return format_uptime(uptime_seconds)
        except Exception:
            return "Unknown"
    
    def get_motherboard_info(self) -> str:
        """Get motherboard information"""
        try:
            result = subprocess.run(
                ['wmic', 'baseboard', 'get', 'Manufacturer,Product', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            manufacturer = ""
            product = ""
            
            for line in result.stdout.split('\n'):
                if 'Manufacturer=' in line:
                    manufacturer = line.split('=', 1)[1].strip()
                elif 'Product=' in line:
                    product = line.split('=', 1)[1].strip()
            
            if manufacturer and product:
                return f"{manufacturer} {product}"
            elif manufacturer:
                return manufacturer
            elif product:
                return product
            else:
                return "Unknown"
                
        except Exception:
            return "Unknown"
    
    def get_bios_info(self) -> str:
        """Get BIOS information"""
        try:
            result = subprocess.run(
                ['wmic', 'bios', 'get', 'Manufacturer,SMBIOSBIOSVersion', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            manufacturer = ""
            version = ""
            
            for line in result.stdout.split('\n'):
                if 'Manufacturer=' in line:
                    manufacturer = line.split('=', 1)[1].strip()
                elif 'SMBIOSBIOSVersion=' in line:
                    version = line.split('=', 1)[1].strip()
            
            if manufacturer and version:
                return f"{manufacturer} {version}"
            elif version:
                return version
            else:
                return "Unknown"
                
        except Exception:
            return "Unknown"
    
    def get_cpu_model(self) -> str:
        """Get CPU model information"""
        try:
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'Name', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'Name=' in line:
                    return line.split('=', 1)[1].strip()
            
            return "Unknown CPU"
            
        except Exception:
            return "Unknown CPU"
    
    def get_gpu_info(self) -> List[str]:
        """Get graphics card information"""
        try:
            result = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'Name', '/value'],
                capture_output=True, text=True, timeout=15
            )
            
            gpu_list = []
            for line in result.stdout.split('\n'):
                if 'Name=' in line:
                    gpu_name = line.split('=', 1)[1].strip()
                    if gpu_name and gpu_name not in gpu_list:
                        gpu_list.append(gpu_name)
            
            return gpu_list if gpu_list else ["Unknown GPU"]
            
        except Exception:
            return ["Unknown GPU"]
    
    def get_nvidia_driver_version(self) -> str:
        """Get NVIDIA driver version"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return version if version else "Not Available"
            
            return "Not Available"
            
        except Exception:
            return "Not Available"
    
    def get_disk_info(self) -> List[Dict]:
        """Get disk information for all drives"""
        try:
            disk_info = []
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_info.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': usage.total / (1024**3),
                        'used_gb': usage.used / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'percent_used': (usage.used / usage.total) * 100
                    })
                    
                except (PermissionError, OSError):
                    # Skip drives that can't be accessed
                    continue
            
            return disk_info
            
        except Exception:
            return []
    
    def get_gpu_usage(self) -> Tuple[float, float]:
        """Get GPU usage and memory usage (NVIDIA only)"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory', 
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                values = result.stdout.strip().split(', ')
                if len(values) >= 2:
                    gpu_usage = float(values[0])
                    memory_usage = float(values[1])
                    return gpu_usage, memory_usage
            
            return 0.0, 0.0
            
        except Exception:
            return 0.0, 0.0
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Get current disk usage for all drives"""
        try:
            disk_usage = {}
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drive_letter = partition.device.replace('\\', '')
                    disk_usage[drive_letter] = (usage.used / usage.total) * 100
                    
                except (PermissionError, OSError):
                    continue
            
            return disk_usage
            
        except Exception:
            return {}
    
    def get_network_activity(self) -> Tuple[float, float]:
        """Get network send/receive rates in MB/s"""
        try:
            current_stats = psutil.net_io_counters()
            current_time = time.time()
            
            if self.last_network_stats and self.last_network_time:
                time_delta = current_time - self.last_network_time
                
                if time_delta > 0:
                    sent_delta = current_stats.bytes_sent - self.last_network_stats.bytes_sent
                    recv_delta = current_stats.bytes_recv - self.last_network_stats.bytes_recv
                    
                    sent_rate = (sent_delta / time_delta) / (1024 * 1024)  # MB/s
                    recv_rate = (recv_delta / time_delta) / (1024 * 1024)  # MB/s
                    
                    self.last_network_stats = current_stats
                    self.last_network_time = current_time
                    
                    return max(0, sent_rate), max(0, recv_rate)
            
            # First call or error - store current stats
            self.last_network_stats = current_stats
            self.last_network_time = current_time
            
            return 0.0, 0.0
            
        except Exception:
            return 0.0, 0.0
    
    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature (if available)"""
        try:
            # Try to get temperature from psutil (Linux/some Windows systems)
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                
                # Look for CPU temperature
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        for entry in entries:
                            if entry.current:
                                return entry.current
            
            # Windows-specific temperature reading (requires admin rights)
            try:
                result = subprocess.run(
                    ['wmic', '/namespace:\\\\root\\wmi', 'PATH', 'MSAcpi_ThermalZoneTemperature', 
                     'get', 'CurrentTemperature', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                
                for line in result.stdout.split('\n'):
                    if 'CurrentTemperature=' in line:
                        temp_kelvin = int(line.split('=')[1].strip())
                        temp_celsius = (temp_kelvin / 10) - 273.15
                        return temp_celsius
                        
            except Exception:
                pass
            
            return None
            
        except Exception:
            return None

class SystemMonitorThread(QThread):
    """Thread for continuous system monitoring"""
    
    metrics_updated = Signal(SystemMetrics)
    error_occurred = Signal(str)
    
    def __init__(self, system_info_manager: SystemInfoManager):
        super().__init__()
        self.system_info_manager = system_info_manager
        self.running = True
        self.update_interval = 2  # seconds
    
    def run(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = self.system_info_manager.get_real_time_metrics()
                self.metrics_updated.emit(metrics)
                
                # Sleep for update interval
                for _ in range(self.update_interval * 10):  # Check every 0.1 seconds
                    if not self.running:
                        break
                    self.msleep(100)
                    
            except Exception as e:
                self.error_occurred.emit(f"Monitoring error: {str(e)}")
                self.msleep(1000)  # Wait 1 second before retrying
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        self.wait(3000)  # Wait up to 3 seconds for thread to finish

# Utility functions
def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_uptime(seconds: float) -> str:
    """Format uptime seconds into human readable format"""
    try:
        uptime_delta = timedelta(seconds=int(seconds))
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
            
    except Exception:
        return "Unknown"
