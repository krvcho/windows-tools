"""
Utility functions and helpers for DISM operations
"""

import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class DismHealthStatus(Enum):
    """DISM health status enumeration"""
    HEALTHY = "healthy"
    CORRUPTED = "corrupted" 
    REPAIRABLE = "repairable"
    UNKNOWN = "unknown"
    ERROR = "error"

@dataclass
class DismResult:
    """Result of a DISM operation"""
    success: bool
    exit_code: int
    output: str
    error: str
    duration: float
    health_status: Optional[DismHealthStatus] = None

class DismProgressParser:
    """Parser for DISM progress output"""
    
    # Regex patterns for different DISM progress formats
    PROGRESS_PATTERNS = [
        r'\[([=\s]*)\]\s*(\d+\.?\d*)%',  # [========    ] 75.0%
        r'(\d+\.?\d*)%\s*complete',      # 75.0% complete
        r'Progress:\s*(\d+\.?\d*)%',     # Progress: 75.0%
    ]
    
    @classmethod
    def extract_progress(cls, line: str) -> Optional[int]:
        """Extract progress percentage from DISM output line"""
        for pattern in cls.PROGRESS_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:  # Pattern with progress bar
                        return int(float(match.group(2)))
                    else:  # Pattern with just percentage
                        return int(float(match.group(1)))
                except (ValueError, IndexError):
                    continue
        return None
    
    @classmethod
    def extract_operation_info(cls, line: str) -> Optional[str]:
        """Extract current operation information from DISM output"""
        operation_indicators = [
            "Scanning the image",
            "Restoring the image",
            "Downloading files",
            "Installing updates",
            "Verifying integrity",
            "Cleaning up",
            "Processing component"
        ]
        
        line_lower = line.lower()
        for indicator in operation_indicators:
            if indicator.lower() in line_lower:
                return indicator
        
        return None

class DismHealthAnalyzer:
    """Analyzer for DISM health check results"""
    
    @staticmethod
    def analyze_checkhealth_output(output: str) -> DismHealthStatus:
        """Analyze DISM checkhealth output to determine status"""
        output_lower = output.lower()
        
        if "no component store corruption detected" in output_lower:
            return DismHealthStatus.HEALTHY
        elif "component store corruption detected" in output_lower:
            return DismHealthStatus.CORRUPTED
        elif "the component store is repairable" in output_lower:
            return DismHealthStatus.REPAIRABLE
        elif "error" in output_lower or "failed" in output_lower:
            return DismHealthStatus.ERROR
        else:
            return DismHealthStatus.UNKNOWN
    
    @staticmethod
    def analyze_scanhealth_output(output: str) -> Dict[str, any]:
        """Analyze DISM scanhealth output for detailed information"""
        analysis = {
            'corruption_detected': False,
            'corruption_details': [],
            'recommendations': [],
            'estimated_repair_time': None
        }
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            if 'corruption' in line:
                analysis['corruption_detected'] = True
                analysis['corruption_details'].append(line)
            
            if 'recommend' in line:
                analysis['recommendations'].append(line)
        
        # Estimate repair time based on corruption level
        if analysis['corruption_detected']:
            corruption_count = len(analysis['corruption_details'])
            if corruption_count > 10:
                analysis['estimated_repair_time'] = "30-45 minutes"
            elif corruption_count > 5:
                analysis['estimated_repair_time'] = "20-30 minutes"
            else:
                analysis['estimated_repair_time'] = "15-20 minutes"
        
        return analysis
    
    @staticmethod
    def get_health_recommendations(status: DismHealthStatus) -> List[str]:
        """Get recommendations based on health status"""
        recommendations = []
        
        if status == DismHealthStatus.HEALTHY:
            recommendations.extend([
                "System image appears healthy",
                "Consider running SFC /scannow for additional verification",
                "Regular maintenance: Run DISM health checks monthly"
            ])
        elif status == DismHealthStatus.CORRUPTED:
            recommendations.extend([
                "System image corruption detected",
                "Run DISM /RestoreHealth immediately",
                "After DISM repair, run SFC /scannow",
                "Consider creating a system backup after repair"
            ])
        elif status == DismHealthStatus.REPAIRABLE:
            recommendations.extend([
                "System image has repairable corruption",
                "Run DISM /RestoreHealth to fix issues",
                "Monitor system performance after repair"
            ])
        elif status == DismHealthStatus.ERROR:
            recommendations.extend([
                "Error occurred during health check",
                "Try running as administrator",
                "Check Windows Update service status",
                "Consider running in Safe Mode if issues persist"
            ])
        else:
            recommendations.extend([
                "Unable to determine system health status",
                "Try running DISM /ScanHealth for detailed analysis",
                "Check system logs for additional information"
            ])
        
        return recommendations

class DismCommandBuilder:
    """Builder for DISM command arguments"""
    
    @staticmethod
    def build_checkhealth_command() -> List[str]:
        """Build command for DISM checkhealth"""
        return ['/online', '/cleanup-image', '/checkhealth']
    
    @staticmethod
    def build_scanhealth_command() -> List[str]:
        """Build command for DISM scanhealth"""
        return ['/online', '/cleanup-image', '/scanhealth']
    
    @staticmethod
    def build_restorehealth_command(source: Optional[str] = None, 
                                   limit_access: bool = False) -> List[str]:
        """Build command for DISM restorehealth"""
        cmd = ['/online', '/cleanup-image', '/restorehealth']
        
        if source:
            cmd.extend(['/source', source])
        
        if limit_access:
            cmd.append('/limitaccess')
        
        return cmd
    
    @staticmethod
    def build_component_cleanup_command(reset_base: bool = False) -> List[str]:
        """Build command for component store cleanup"""
        cmd = ['/online', '/cleanup-image', '/startcomponentcleanup']
        
        if reset_base:
            cmd.append('/resetbase')
        
        return cmd
    
    @staticmethod
    def build_analyze_component_store_command() -> List[str]:
        """Build command for analyzing component store"""
        return ['/online', '/cleanup-image', '/analyzecomponentstore']

class DismSystemInfo:
    """System information relevant to DISM operations"""
    
    @staticmethod
    def get_windows_version() -> Dict[str, str]:
        """Get Windows version information"""
        try:
            result = subprocess.run(
                ['dism', '/online', '/get-imageinfo'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return DismSystemInfo._parse_image_info(result.stdout)
            else:
                return {'error': 'Failed to get image info'}
                
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _parse_image_info(output: str) -> Dict[str, str]:
        """Parse DISM image info output"""
        info = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('DISM'):
                try:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
                except ValueError:
                    continue
        
        return info
    
    @staticmethod
    def check_internet_connectivity() -> bool:
        """Check if internet connection is available for DISM operations"""
        try:
            import urllib.request
            urllib.request.urlopen('http://www.microsoft.com', timeout=10)
            return True
        except:
            return False
    
    @staticmethod
    def get_available_disk_space() -> Optional[int]:
        """Get available disk space in GB for system drive"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("C:\\")
            return free // (1024**3)  # Convert to GB
        except:
            return None
    
    @staticmethod
    def estimate_dism_requirements() -> Dict[str, any]:
        """Estimate system requirements for DISM operations"""
        requirements = {
            'internet_required': True,
            'min_free_space_gb': 2,
            'estimated_time_minutes': 20,
            'admin_required': True,
            'recommendations': []
        }
        
        # Check available space
        free_space = DismSystemInfo.get_available_disk_space()
        if free_space and free_space < requirements['min_free_space_gb']:
            requirements['recommendations'].append(
                f"Low disk space: {free_space}GB available, {requirements['min_free_space_gb']}GB recommended"
            )
        
        # Check internet connectivity
        if not DismSystemInfo.check_internet_connectivity():
            requirements['recommendations'].append(
                "No internet connection detected - DISM may not be able to download repair files"
            )
        
        return requirements

# Utility functions for easy access
def quick_health_check() -> Tuple[DismHealthStatus, List[str]]:
    """Perform a quick health check and return status with recommendations"""
    try:
        result = subprocess.run(
            ['dism', '/online', '/cleanup-image', '/checkhealth'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            status = DismHealthAnalyzer.analyze_checkhealth_output(result.stdout)
            recommendations = DismHealthAnalyzer.get_health_recommendations(status)
            return status, recommendations
        else:
            return DismHealthStatus.ERROR, ["Failed to run health check"]
            
    except Exception as e:
        return DismHealthStatus.ERROR, [f"Error: {str(e)}"]

def get_system_readiness() -> Dict[str, any]:
    """Get system readiness for DISM operations"""
    readiness = {
        'dism_available': True,
        'admin_privileges': False,
        'internet_connection': False,
        'sufficient_space': False,
        'windows_version': 'Unknown',
        'recommendations': []
    }
    
    try:
        # Check DISM availability
        subprocess.run(['dism', '/?'], capture_output=True, timeout=5)
    except:
        readiness['dism_available'] = False
        readiness['recommendations'].append("DISM is not available on this system")
    
    # Check admin privileges
    try:
        import ctypes
        readiness['admin_privileges'] = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        pass
    
    if not readiness['admin_privileges']:
        readiness['recommendations'].append("Administrator privileges required")
    
    # Check internet connection
    readiness['internet_connection'] = DismSystemInfo.check_internet_connectivity()
    if not readiness['internet_connection']:
        readiness['recommendations'].append("Internet connection recommended for downloading repair files")
    
    # Check disk space
    free_space = DismSystemInfo.get_available_disk_space()
    readiness['sufficient_space'] = free_space and free_space >= 2
    if not readiness['sufficient_space']:
        readiness['recommendations'].append("At least 2GB free disk space recommended")
    
    return readiness
