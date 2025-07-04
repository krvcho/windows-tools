"""
System cleanup manager for temporary files, cache, and system clutter
Provides comprehensive cleanup of various Windows system locations
"""

import os
import shutil
import subprocess
import tempfile
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class CleanupLocation:
    """Represents a cleanup location with metadata"""
    name: str
    path: str
    description: str
    size_mb: float = 0.0
    file_count: int = 0
    enabled: bool = True
    requires_admin: bool = False
    safe_to_delete: bool = True
    category: str = "General"

@dataclass
class CleanupResult:
    """Result of a cleanup operation"""
    location: str
    success: bool
    files_deleted: int
    size_freed_mb: float
    error_message: str = ""
    duration_seconds: float = 0.0

class SystemCleanupManager:
    """Manager for system cleanup operations"""
    
    def __init__(self):
        self.cleanup_locations = {}
        self.total_size_mb = 0.0
        self.total_files = 0
        self._initialize_cleanup_locations()
    
    def _initialize_cleanup_locations(self):
        """Initialize all cleanup locations"""
        
        # User temporary files
        user_temp = os.environ.get('TEMP', '')
        if user_temp:
            self.cleanup_locations['user_temp'] = CleanupLocation(
                name="User Temporary Files",
                path=user_temp,
                description="Temporary files created by applications for current user",
                category="Temporary Files",
                safe_to_delete=True
            )
        
        # System temporary files
        system_temp = os.environ.get('TMP', 'C:\\Windows\\Temp')
        self.cleanup_locations['system_temp'] = CleanupLocation(
            name="System Temporary Files",
            path=system_temp,
            description="System-wide temporary files",
            category="Temporary Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Windows temporary directory
        windows_temp = "C:\\Windows\\Temp"
        self.cleanup_locations['windows_temp'] = CleanupLocation(
            name="Windows Temp Directory",
            path=windows_temp,
            description="Windows system temporary files",
            category="Temporary Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Recycle Bin
        self.cleanup_locations['recycle_bin'] = CleanupLocation(
            name="Recycle Bin",
            path="$Recycle.Bin",
            description="Files in Recycle Bin for all users",
            category="Recycle Bin",
            requires_admin=True,
            safe_to_delete=False  # User should confirm
        )
        
        # Windows Update Cache
        self.cleanup_locations['windows_update_cache'] = CleanupLocation(
            name="Windows Update Cache",
            path="C:\\Windows\\SoftwareDistribution\\Download",
            description="Downloaded Windows Update files",
            category="System Cache",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Windows Update Logs
        self.cleanup_locations['windows_update_logs'] = CleanupLocation(
            name="Windows Update Logs",
            path="C:\\Windows\\Logs\\WindowsUpdate",
            description="Windows Update log files",
            category="Log Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Browser caches
        self._add_browser_cache_locations()
        
        # System log files
        self._add_system_log_locations()
        
        # Application caches
        self._add_application_cache_locations()
        
        # Prefetch files
        self.cleanup_locations['prefetch'] = CleanupLocation(
            name="Prefetch Files",
            path="C:\\Windows\\Prefetch",
            description="Windows prefetch files (keeps recent 128)",
            category="System Cache",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Memory dumps
        self.cleanup_locations['memory_dumps'] = CleanupLocation(
            name="Memory Dump Files",
            path="C:\\Windows\\Minidump",
            description="System crash dump files",
            category="System Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Error reporting
        self.cleanup_locations['error_reports'] = CleanupLocation(
            name="Error Reports",
            path="C:\\ProgramData\\Microsoft\\Windows\\WER",
            description="Windows Error Reporting files",
            category="System Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Delivery Optimization
        self.cleanup_locations['delivery_optimization'] = CleanupLocation(
            name="Delivery Optimization",
            path="C:\\Windows\\ServiceProfiles\\NetworkService\\AppData\\Local\\Microsoft\\Windows\\DeliveryOptimization",
            description="Windows Update delivery optimization cache",
            category="System Cache",
            requires_admin=True,
            safe_to_delete=True
        )
    
    def _add_browser_cache_locations(self):
        """Add browser cache cleanup locations"""
        user_profile = os.environ.get('USERPROFILE', '')
        
        if user_profile:
            # Chrome cache
            chrome_cache = os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cache')
            if os.path.exists(chrome_cache):
                self.cleanup_locations['chrome_cache'] = CleanupLocation(
                    name="Chrome Cache",
                    path=chrome_cache,
                    description="Google Chrome browser cache",
                    category="Browser Cache",
                    safe_to_delete=True
                )
            
            # Firefox cache
            firefox_cache = os.path.join(user_profile, 'AppData', 'Local', 'Mozilla', 'Firefox', 'Profiles')
            if os.path.exists(firefox_cache):
                self.cleanup_locations['firefox_cache'] = CleanupLocation(
                    name="Firefox Cache",
                    path=firefox_cache,
                    description="Mozilla Firefox browser cache",
                    category="Browser Cache",
                    safe_to_delete=True
                )
            
            # Edge cache
            edge_cache = os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache')
            if os.path.exists(edge_cache):
                self.cleanup_locations['edge_cache'] = CleanupLocation(
                    name="Edge Cache",
                    path=edge_cache,
                    description="Microsoft Edge browser cache",
                    category="Browser Cache",
                    safe_to_delete=True
                )
    
    def _add_system_log_locations(self):
        """Add system log cleanup locations"""
        
        # CBS logs
        self.cleanup_locations['cbs_logs'] = CleanupLocation(
            name="CBS Log Files",
            path="C:\\Windows\\Logs\\CBS",
            description="Component-Based Servicing log files",
            category="Log Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # DISM logs
        self.cleanup_locations['dism_logs'] = CleanupLocation(
            name="DISM Log Files",
            path="C:\\Windows\\Logs\\DISM",
            description="DISM operation log files",
            category="Log Files",
            requires_admin=True,
            safe_to_delete=True
        )
        
        # Setup logs
        self.cleanup_locations['setup_logs'] = CleanupLocation(
            name="Setup Log Files",
            path="C:\\Windows\\Panther",
            description="Windows setup and upgrade logs",
            category="Log Files",
            requires_admin=True,
            safe_to_delete=True
        )
    
    def _add_application_cache_locations(self):
        """Add application cache cleanup locations"""
        user_profile = os.environ.get('USERPROFILE', '')
        
        if user_profile:
            # Windows Store cache
            store_cache = os.path.join(user_profile, 'AppData', 'Local', 'Packages')
            if os.path.exists(store_cache):
                self.cleanup_locations['store_cache'] = CleanupLocation(
                    name="Windows Store Cache",
                    path=store_cache,
                    description="Windows Store app cache files",
                    category="Application Cache",
                    safe_to_delete=True
                )
            
            # Thumbnail cache
            thumbnail_cache = os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Windows', 'Explorer')
            if os.path.exists(thumbnail_cache):
                self.cleanup_locations['thumbnail_cache'] = CleanupLocation(
                    name="Thumbnail Cache",
                    path=thumbnail_cache,
                    description="Windows thumbnail cache files",
                    category="Application Cache",
                    safe_to_delete=True
                )
    
    def scan_cleanup_locations(self, progress_callback=None) -> Dict[str, CleanupLocation]:
        """Scan all cleanup locations to calculate sizes"""
        total_locations = len(self.cleanup_locations)
        completed = 0
        
        def scan_location(location_key, location):
            try:
                if location.path == "$Recycle.Bin":
                    # Special handling for Recycle Bin
                    size_mb, file_count = self._scan_recycle_bin()
                else:
                    size_mb, file_count = self._calculate_directory_size(location.path)
                
                location.size_mb = size_mb
                location.file_count = file_count
                return location_key, location
            except Exception as e:
                location.size_mb = 0.0
                location.file_count = 0
                return location_key, location
        
        # Use ThreadPoolExecutor for parallel scanning
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_location = {
                executor.submit(scan_location, key, loc): key 
                for key, loc in self.cleanup_locations.items()
            }
            
            for future in as_completed(future_to_location):
                location_key, updated_location = future.result()
                self.cleanup_locations[location_key] = updated_location
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_locations)
        
        # Calculate totals
        self.total_size_mb = sum(loc.size_mb for loc in self.cleanup_locations.values())
        self.total_files = sum(loc.file_count for loc in self.cleanup_locations.values())
        
        return self.cleanup_locations
    
    def _calculate_directory_size(self, directory_path: str) -> Tuple[float, int]:
        """Calculate total size and file count for a directory"""
        if not os.path.exists(directory_path):
            return 0.0, 0
        
        total_size = 0
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        
        return total_size / (1024 * 1024), file_count  # Convert to MB
    
    def _scan_recycle_bin(self) -> Tuple[float, int]:
        """Scan Recycle Bin for all users"""
        total_size = 0
        file_count = 0
        
        # Check all drives for Recycle Bin
        for drive in ['C:', 'D:', 'E:', 'F:']:
            recycle_path = f"{drive}\\$Recycle.Bin"
            if os.path.exists(recycle_path):
                try:
                    for root, dirs, files in os.walk(recycle_path):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if os.path.exists(file_path):
                                    total_size += os.path.getsize(file_path)
                                    file_count += 1
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue
        
        return total_size / (1024 * 1024), file_count
    
    def cleanup_location(self, location_key: str, progress_callback=None) -> CleanupResult:
        """Clean up a specific location"""
        if location_key not in self.cleanup_locations:
            return CleanupResult(
                location=location_key,
                success=False,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message="Location not found"
            )
        
        location = self.cleanup_locations[location_key]
        start_time = datetime.now()
        
        try:
            if location_key == 'recycle_bin':
                return self._empty_recycle_bin()
            elif location_key == 'prefetch':
                return self._cleanup_prefetch_files()
            elif location_key == 'windows_update_cache':
                return self._cleanup_windows_update_cache()
            else:
                return self._cleanup_directory(location, progress_callback)
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CleanupResult(
                location=location.name,
                success=False,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message=str(e),
                duration_seconds=duration
            )
    
    def _cleanup_directory(self, location: CleanupLocation, progress_callback=None) -> CleanupResult:
        """Clean up a directory location"""
        start_time = datetime.now()
        files_deleted = 0
        size_freed = 0.0
        
        if not os.path.exists(location.path):
            return CleanupResult(
                location=location.name,
                success=True,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message="Directory does not exist"
            )
        
        try:
            total_files = location.file_count
            processed_files = 0
            
            for root, dirs, files in os.walk(location.path, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            files_deleted += 1
                            size_freed += file_size
                            
                            processed_files += 1
                            if progress_callback and total_files > 0:
                                progress_callback(processed_files, total_files)
                                
                    except (OSError, PermissionError):
                        continue
                
                # Remove empty directories
                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except (OSError, PermissionError):
                        continue
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return CleanupResult(
                location=location.name,
                success=True,
                files_deleted=files_deleted,
                size_freed_mb=size_freed / (1024 * 1024),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CleanupResult(
                location=location.name,
                success=False,
                files_deleted=files_deleted,
                size_freed_mb=size_freed / (1024 * 1024),
                error_message=str(e),
                duration_seconds=duration
            )
    
    def _empty_recycle_bin(self) -> CleanupResult:
        """Empty the Recycle Bin using Windows API"""
        start_time = datetime.now()
        
        try:
            # Get current Recycle Bin size
            original_size_mb, original_count = self._scan_recycle_bin()
            
            # Use PowerShell to empty Recycle Bin
            cmd = [
                'powershell', '-Command',
                'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                return CleanupResult(
                    location="Recycle Bin",
                    success=True,
                    files_deleted=original_count,
                    size_freed_mb=original_size_mb,
                    duration_seconds=duration
                )
            else:
                return CleanupResult(
                    location="Recycle Bin",
                    success=False,
                    files_deleted=0,
                    size_freed_mb=0.0,
                    error_message=result.stderr or "Failed to empty Recycle Bin",
                    duration_seconds=duration
                )
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CleanupResult(
                location="Recycle Bin",
                success=False,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message=str(e),
                duration_seconds=duration
            )
    
    def _cleanup_prefetch_files(self) -> CleanupResult:
        """Clean up prefetch files (keep recent 128)"""
        start_time = datetime.now()
        prefetch_path = "C:\\Windows\\Prefetch"
        
        if not os.path.exists(prefetch_path):
            return CleanupResult(
                location="Prefetch Files",
                success=True,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message="Prefetch directory does not exist"
            )
        
        try:
            # Get all prefetch files with their modification times
            prefetch_files = []
            for file in os.listdir(prefetch_path):
                if file.endswith('.pf'):
                    file_path = os.path.join(prefetch_path, file)
                    if os.path.isfile(file_path):
                        mtime = os.path.getmtime(file_path)
                        size = os.path.getsize(file_path)
                        prefetch_files.append((file_path, mtime, size))
            
            # Sort by modification time (newest first)
            prefetch_files.sort(key=lambda x: x[1], reverse=True)
            
            # Keep the 128 most recent files, delete the rest
            files_to_delete = prefetch_files[128:]
            files_deleted = 0
            size_freed = 0.0
            
            for file_path, _, file_size in files_to_delete:
                try:
                    os.remove(file_path)
                    files_deleted += 1
                    size_freed += file_size
                except (OSError, PermissionError):
                    continue
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return CleanupResult(
                location="Prefetch Files",
                success=True,
                files_deleted=files_deleted,
                size_freed_mb=size_freed / (1024 * 1024),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CleanupResult(
                location="Prefetch Files",
                success=False,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message=str(e),
                duration_seconds=duration
            )
    
    def _cleanup_windows_update_cache(self) -> CleanupResult:
        """Clean up Windows Update cache safely"""
        start_time = datetime.now()
        
        try:
            # Stop Windows Update service first
            stop_cmd = ['net', 'stop', 'wuauserv']
            subprocess.run(stop_cmd, capture_output=True, timeout=30)
            
            # Clean the download directory
            download_path = "C:\\Windows\\SoftwareDistribution\\Download"
            result = self._cleanup_directory(
                CleanupLocation(
                    name="Windows Update Cache",
                    path=download_path,
                    description="Windows Update downloads",
                    category="System Cache"
                )
            )
            
            # Restart Windows Update service
            start_cmd = ['net', 'start', 'wuauserv']
            subprocess.run(start_cmd, capture_output=True, timeout=30)
            
            return result
            
        except Exception as e:
            # Try to restart the service even if cleanup failed
            try:
                start_cmd = ['net', 'start', 'wuauserv']
                subprocess.run(start_cmd, capture_output=True, timeout=30)
            except:
                pass
            
            duration = (datetime.now() - start_time).total_seconds()
            return CleanupResult(
                location="Windows Update Cache",
                success=False,
                files_deleted=0,
                size_freed_mb=0.0,
                error_message=str(e),
                duration_seconds=duration
            )
    
    def cleanup_selected_locations(self, location_keys: List[str], 
                                 progress_callback=None) -> List[CleanupResult]:
        """Clean up multiple selected locations"""
        results = []
        total_locations = len(location_keys)
        
        for i, location_key in enumerate(location_keys):
            if progress_callback:
                progress_callback(i, total_locations, f"Cleaning {location_key}...")
            
            result = self.cleanup_location(location_key)
            results.append(result)
        
        if progress_callback:
            progress_callback(total_locations, total_locations, "Cleanup completed")
        
        return results
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get summary of cleanup locations by category"""
        categories = {}
        
        for location in self.cleanup_locations.values():
            category = location.category
            if category not in categories:
                categories[category] = {
                    'locations': [],
                    'total_size_mb': 0.0,
                    'total_files': 0,
                    'enabled_count': 0
                }
            
            categories[category]['locations'].append(location)
            categories[category]['total_size_mb'] += location.size_mb
            categories[category]['total_files'] += location.file_count
            if location.enabled:
                categories[category]['enabled_count'] += 1
        
        return {
            'categories': categories,
            'total_size_mb': self.total_size_mb,
            'total_files': self.total_files,
            'total_locations': len(self.cleanup_locations)
        }
    
    def get_disk_space_info(self) -> Dict[str, Any]:
        """Get disk space information for system drives"""
        disk_info = {}
        
        for drive in ['C:', 'D:', 'E:', 'F:']:
            try:
                if os.path.exists(drive + '\\'):
                    usage = shutil.disk_usage(drive + '\\')
                    disk_info[drive] = {
                        'total_gb': usage.total / (1024**3),
                        'used_gb': (usage.total - usage.free) / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'used_percent': ((usage.total - usage.free) / usage.total) * 100
                    }
            except:
                continue
        
        return disk_info

class CleanupScheduler:
    """Scheduler for automatic cleanup operations"""
    
    def __init__(self):
        self.scheduled_tasks = {}
    
    def schedule_cleanup(self, location_keys: List[str], 
                        schedule_type: str = "daily",
                        time_of_day: str = "02:00") -> bool:
        """Schedule automatic cleanup"""
        try:
            # This would integrate with Windows Task Scheduler
            # For now, we'll store the configuration
            task_name = f"SystemCleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.scheduled_tasks[task_name] = {
                'location_keys': location_keys,
                'schedule_type': schedule_type,
                'time_of_day': time_of_day,
                'created': datetime.now(),
                'enabled': True
            }
            
            return True
            
        except Exception:
            return False
    
    def create_windows_task(self, task_name: str, location_keys: List[str],
                           schedule_type: str = "daily", time_of_day: str = "02:00") -> bool:
        """Create a Windows scheduled task for cleanup"""
        try:
            # Create PowerShell script for cleanup
            script_content = f"""
# Automated System Cleanup Script
$locations = @({', '.join([f'"{key}"' for key in location_keys])})

# Add cleanup logic here
Write-Host "Running automated cleanup for locations: $($locations -join ', ')"
"""
            
            script_path = os.path.join(tempfile.gettempdir(), f"{task_name}.ps1")
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Create scheduled task using schtasks
            cmd = [
                'schtasks', '/create',
                '/tn', task_name,
                '/tr', f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
                '/sc', schedule_type,
                '/st', time_of_day,
                '/ru', 'SYSTEM'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False

# Utility functions
def get_system_cleanup_manager() -> SystemCleanupManager:
    """Get a configured system cleanup manager"""
    return SystemCleanupManager()

def quick_temp_cleanup() -> List[CleanupResult]:
    """Quick cleanup of temporary files only"""
    manager = SystemCleanupManager()
    temp_locations = ['user_temp', 'system_temp', 'windows_temp']
    return manager.cleanup_selected_locations(temp_locations)

def estimate_cleanup_time(total_files: int) -> str:
    """Estimate cleanup time based on file count"""
    if total_files < 1000:
        return "Less than 1 minute"
    elif total_files < 10000:
        return "1-3 minutes"
    elif total_files < 50000:
        return "3-10 minutes"
    else:
        return "10+ minutes"

def format_size(size_mb: float) -> str:
    """Format size in human-readable format"""
    if size_mb < 1:
        return f"{size_mb * 1024:.1f} KB"
    elif size_mb < 1024:
        return f"{size_mb:.1f} MB"
    else:
        return f"{size_mb / 1024:.1f} GB"
