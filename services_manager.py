import subprocess
import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QTextEdit

class ServiceStatus(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    START_PENDING = "START_PENDING"
    STOP_PENDING = "STOP_PENDING"
    CONTINUE_PENDING = "CONTINUE_PENDING"
    PAUSE_PENDING = "PAUSE_PENDING"
    UNKNOWN = "UNKNOWN"

class ServiceStartType(Enum):
    AUTOMATIC = "AUTO"
    AUTOMATIC_DELAYED = "AUTO_DELAYED"
    MANUAL = "MANUAL"
    DISABLED = "DISABLED"
    UNKNOWN = "UNKNOWN"

@dataclass
class ServiceInfo:
    name: str
    display_name: str
    status: ServiceStatus
    start_type: ServiceStartType
    description: str
    pid: Optional[int] = None
    can_stop: bool = True
    can_pause: bool = False

class ServicesManager(QObject):
    service_updated = Signal(str, ServiceInfo)  # service_name, service_info
    operation_completed = Signal(str, bool, str)  # operation, success, message
    
    def __init__(self):
        super().__init__()
        self.important_services = {
            # Windows Update Services
            'wuauserv': 'Windows Update',
            'bits': 'Background Intelligent Transfer Service',
            'cryptsvc': 'Cryptographic Services',
            'msiserver': 'Windows Installer',
            'trustedinstaller': 'Windows Modules Installer',
            
            # System Services
            'eventlog': 'Windows Event Log',
            'winmgmt': 'Windows Management Instrumentation',
            'rpcss': 'Remote Procedure Call (RPC)',
            'dcomlaunch': 'DCOM Server Process Launcher',
            'plugplay': 'Plug and Play',
            'power': 'Power',
            'themes': 'Themes',
            'audiosrv': 'Windows Audio',
            'audioendpointbuilder': 'Windows Audio Endpoint Builder',
            
            # Network Services
            'lanmanserver': 'Server',
            'lanmanworkstation': 'Workstation',
            'dnscache': 'DNS Client',
            'dhcp': 'DHCP Client',
            'netlogon': 'Netlogon',
            'netman': 'Network Connections',
            'nsi': 'Network Store Interface Service',
            
            # Security Services
            'mpssvc': 'Windows Defender Firewall',
            'windefend': 'Windows Defender Antivirus Service',
            'wscsvc': 'Security Center',
            'wersvc': 'Windows Error Reporting Service',
            
            # Print and Fax Services
            'spooler': 'Print Spooler',
            'fax': 'Fax',
            
            # Remote Services
            'termservice': 'Remote Desktop Services',
            'remoteregistry': 'Remote Registry',
            'remoteaccess': 'Routing and Remote Access',
            
            # Storage Services
            'vss': 'Volume Shadow Copy',
            'swprv': 'Microsoft Software Shadow Copy Provider',
            'vds': 'Virtual Disk',
            
            # Task Scheduler
            'schedule': 'Task Scheduler',
            
            # Windows Search
            'wsearch': 'Windows Search',
            
            # Windows Time
            'w32time': 'Windows Time',
            
            # User Profile Service
            'profSvc': 'User Profile Service',
            
            # Windows License Manager
            'licensingservice': 'Windows License Manager Service',
        }
        
        self.service_descriptions = {
            'wuauserv': 'Enables the detection, download, and installation of updates for Windows and other programs.',
            'bits': 'Transfers files in the background using idle network bandwidth.',
            'cryptsvc': 'Provides three management services: Catalog Database Service, Protected Root Service, and Automatic Root Certificate Update Service.',
            'msiserver': 'Installs, modifies, and removes applications provided as Windows Installer packages.',
            'trustedinstaller': 'Enables installation, modification, and removal of Windows updates and optional components.',
            'eventlog': 'Enables event log messages issued by Windows-based programs and components to be viewed in Event Viewer.',
            'winmgmt': 'Provides a common interface and object model to access management information about operating system, devices, applications and services.',
            'rpcss': 'Serves as the endpoint mapper and COM Service Control Manager.',
            'dcomlaunch': 'Provides launch functionality for DCOM services.',
            'plugplay': 'Enables a computer to recognize and adapt to hardware changes with little or no user input.',
            'power': 'Manages power policy and power policy notification delivery.',
            'themes': 'Provides user experience theme management.',
            'audiosrv': 'Manages audio for Windows-based programs.',
            'audioendpointbuilder': 'Manages audio devices for the Windows Audio service.',
            'lanmanserver': 'Supports file, print, and named-pipe sharing over the network.',
            'lanmanworkstation': 'Creates and maintains client network connections to remote servers.',
            'dnscache': 'Caches Domain Name System (DNS) names and registers the full computer name.',
            'dhcp': 'Registers and updates IP addresses and DNS records for this computer.',
            'netlogon': 'Maintains a secure channel between this computer and the domain controller.',
            'netman': 'Manages objects in the Network and Dial-Up Connections folder.',
            'nsi': 'Collects and stores network configuration and location information.',
            'mpssvc': 'Provides host-based firewall enforcement for the operating system.',
            'windefend': 'Helps protect users from malware and other potentially unwanted software.',
            'wscsvc': 'Monitors and reports security health settings on the computer.',
            'wersvc': 'Allows errors to be reported when programs stop working or responding.',
            'spooler': 'Loads files to memory for later printing.',
            'fax': 'Enables you to send and receive faxes.',
            'termservice': 'Allows users to connect interactively to a remote computer.',
            'remoteregistry': 'Enables remote users to modify registry settings on this computer.',
            'remoteaccess': 'Offers routing services to businesses in local area and wide area network environments.',
            'vss': 'Manages and implements Volume Shadow Copies used for backup and other purposes.',
            'swprv': 'Manages software-based volume shadow copies taken by the Volume Shadow Copy service.',
            'vds': 'Provides management services for disks, volumes, file systems, and storage arrays.',
            'schedule': 'Enables a user to configure and schedule automated tasks on this computer.',
            'wsearch': 'Provides content indexing, property caching, and search results for files, e-mail, and other content.',
            'w32time': 'Maintains date and time synchronization on all clients and servers in the network.',
            'profSvc': 'Responsible for loading and unloading user profiles.',
            'licensingservice': 'Provides infrastructure support for the Microsoft Store.',
        }
    
    def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Get detailed information about a specific service"""
        try:
            # Get service status using sc query
            result = subprocess.run(
                ['sc', 'query', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Parse sc query output
            lines = result.stdout.strip().split('\n')
            status_info = {}
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    status_info[key.strip()] = value.strip()
            
            # Get service configuration
            config_result = subprocess.run(
                ['sc', 'qc', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            config_info = {}
            if config_result.returncode == 0:
                config_lines = config_result.stdout.strip().split('\n')
                for line in config_lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        config_info[key.strip()] = value.strip()
            
            # Parse status
            state_str = status_info.get('STATE', '').upper()
            if 'RUNNING' in state_str:
                status = ServiceStatus.RUNNING
            elif 'STOPPED' in state_str:
                status = ServiceStatus.STOPPED
            elif 'PAUSED' in state_str:
                status = ServiceStatus.PAUSED
            elif 'START_PENDING' in state_str:
                status = ServiceStatus.START_PENDING
            elif 'STOP_PENDING' in state_str:
                status = ServiceStatus.STOP_PENDING
            elif 'CONTINUE_PENDING' in state_str:
                status = ServiceStatus.CONTINUE_PENDING
            elif 'PAUSE_PENDING' in state_str:
                status = ServiceStatus.PAUSE_PENDING
            else:
                status = ServiceStatus.UNKNOWN
            
            # Parse start type
            start_type_str = config_info.get('START_TYPE', '').upper()
            if 'AUTO_START' in start_type_str or start_type_str == '2':
                start_type = ServiceStartType.AUTOMATIC
            elif 'DEMAND_START' in start_type_str or start_type_str == '3':
                start_type = ServiceStartType.MANUAL
            elif 'DISABLED' in start_type_str or start_type_str == '4':
                start_type = ServiceStartType.DISABLED
            else:
                start_type = ServiceStartType.UNKNOWN
            
            # Extract PID if running
            pid = None
            if 'PID' in status_info:
                try:
                    pid = int(status_info['PID'])
                except ValueError:
                    pass
            
            # Get display name and description
            display_name = self.important_services.get(service_name, service_name)
            description = self.service_descriptions.get(service_name, "No description available")
            
            # Determine capabilities
            can_stop = status == ServiceStatus.RUNNING
            can_pause = False  # Most services don't support pause
            
            return ServiceInfo(
                name=service_name,
                display_name=display_name,
                status=status,
                start_type=start_type,
                description=description,
                pid=pid,
                can_stop=can_stop,
                can_pause=can_pause
            )
            
        except Exception as e:
            print(f"Error getting service info for {service_name}: {e}")
            return None
    
    def get_all_important_services(self) -> Dict[str, ServiceInfo]:
        """Get information for all important services"""
        services = {}
        for service_name in self.important_services.keys():
            service_info = self.get_service_info(service_name)
            if service_info:
                services[service_name] = service_info
        return services
    
    def start_service(self, service_name: str, output_widget: Optional[QTextEdit] = None) -> bool:
        """Start a Windows service"""
        try:
            if output_widget:
                output_widget.append(f"Starting service: {service_name}")
            
            result = subprocess.run(
                ['sc', 'start', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            message = result.stdout if success else result.stderr
            
            if output_widget:
                if success:
                    output_widget.append(f"✓ Service {service_name} started successfully")
                else:
                    output_widget.append(f"✗ Failed to start service {service_name}: {message}")
            
            self.operation_completed.emit("start", success, message)
            return success
            
        except Exception as e:
            error_msg = f"Error starting service {service_name}: {str(e)}"
            if output_widget:
                output_widget.append(f"✗ {error_msg}")
            self.operation_completed.emit("start", False, error_msg)
            return False
    
    def stop_service(self, service_name: str, output_widget: Optional[QTextEdit] = None) -> bool:
        """Stop a Windows service"""
        try:
            if output_widget:
                output_widget.append(f"Stopping service: {service_name}")
            
            result = subprocess.run(
                ['sc', 'stop', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            message = result.stdout if success else result.stderr
            
            if output_widget:
                if success:
                    output_widget.append(f"✓ Service {service_name} stopped successfully")
                else:
                    output_widget.append(f"✗ Failed to stop service {service_name}: {message}")
            
            self.operation_completed.emit("stop", success, message)
            return success
            
        except Exception as e:
            error_msg = f"Error stopping service {service_name}: {str(e)}"
            if output_widget:
                output_widget.append(f"✗ {error_msg}")
            self.operation_completed.emit("stop", False, error_msg)
            return False
    
    def restart_service(self, service_name: str, output_widget: Optional[QTextEdit] = None) -> bool:
        """Restart a Windows service"""
        try:
            if output_widget:
                output_widget.append(f"Restarting service: {service_name}")
            
            # First stop the service
            stop_success = self.stop_service(service_name, output_widget)
            if not stop_success:
                return False
            
            # Wait a moment for the service to fully stop
            time.sleep(2)
            
            # Then start the service
            start_success = self.start_service(service_name, output_widget)
            
            if start_success and output_widget:
                output_widget.append(f"✓ Service {service_name} restarted successfully")
            
            return start_success
            
        except Exception as e:
            error_msg = f"Error restarting service {service_name}: {str(e)}"
            if output_widget:
                output_widget.append(f"✗ {error_msg}")
            self.operation_completed.emit("restart", False, error_msg)
            return False
    
    def set_service_startup_type(self, service_name: str, start_type: ServiceStartType, output_widget: Optional[QTextEdit] = None) -> bool:
        """Set the startup type for a service"""
        try:
            if output_widget:
                output_widget.append(f"Setting startup type for {service_name} to {start_type.value}")
            
            # Map enum to sc config values
            type_map = {
                ServiceStartType.AUTOMATIC: 'auto',
                ServiceStartType.MANUAL: 'demand',
                ServiceStartType.DISABLED: 'disabled'
            }
            
            if start_type not in type_map:
                raise ValueError(f"Unsupported start type: {start_type}")
            
            result = subprocess.run(
                ['sc', 'config', service_name, 'start=', type_map[start_type]],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            success = result.returncode == 0
            message = result.stdout if success else result.stderr
            
            if output_widget:
                if success:
                    output_widget.append(f"✓ Startup type for {service_name} set to {start_type.value}")
                else:
                    output_widget.append(f"✗ Failed to set startup type: {message}")
            
            return success
            
        except Exception as e:
            error_msg = f"Error setting startup type for {service_name}: {str(e)}"
            if output_widget:
                output_widget.append(f"✗ {error_msg}")
            return False

class ServiceMonitorThread(QThread):
    """Thread for monitoring service status changes"""
    services_updated = Signal(dict)  # Dict[str, ServiceInfo]
    
    def __init__(self, services_manager: ServicesManager):
        super().__init__()
        self.services_manager = services_manager
        self.running = False
        self.update_interval = 5  # seconds
    
    def run(self):
        self.running = True
        while self.running:
            try:
                services = self.services_manager.get_all_important_services()
                self.services_updated.emit(services)
                
                # Sleep in small intervals to allow for quick shutdown
                for _ in range(self.update_interval * 10):
                    if not self.running:
                        break
                    self.msleep(100)
                    
            except Exception as e:
                print(f"Error in service monitor thread: {e}")
                self.msleep(1000)
    
    def stop(self):
        self.running = False
        self.wait(3000)  # Wait up to 3 seconds for thread to finish
