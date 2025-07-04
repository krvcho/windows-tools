"""
Network diagnostic tools and utilities
Provides comprehensive network testing and analysis capabilities
"""

import subprocess
import socket
import time
import re
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from PySide6.QtCore import QThread, Signal

@dataclass
class PingResult:
    """Result of a ping operation"""
    host: str
    packets_sent: int
    packets_received: int
    packets_lost: int
    packet_loss_percent: float
    min_time: float
    max_time: float
    avg_time: float
    success: bool
    error: Optional[str] = None

@dataclass
class TracerouteHop:
    """Single hop in a traceroute"""
    hop_number: int
    ip_address: str
    hostname: Optional[str]
    response_times: List[float]
    timeout: bool = False

@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    description: str
    ip_address: str
    subnet_mask: str
    default_gateway: str
    dns_servers: List[str]
    mac_address: str
    status: str
    dhcp_enabled: bool

class NetworkToolsManager:
    """Manager for network diagnostic operations"""
    
    def __init__(self):
        self.active_processes = {}
    
    def ping_host(self, host: str, count: int = 4, timeout: int = 4000) -> PingResult:
        """Ping a host and return structured results"""
        try:
            cmd = ['ping', '-n', str(count), '-w', str(timeout), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_ping_output(host, result.stdout)
            else:
                return PingResult(
                    host=host, packets_sent=count, packets_received=0,
                    packets_lost=count, packet_loss_percent=100.0,
                    min_time=0, max_time=0, avg_time=0,
                    success=False, error=result.stderr
                )
                
        except Exception as e:
            return PingResult(
                host=host, packets_sent=count, packets_received=0,
                packets_lost=count, packet_loss_percent=100.0,
                min_time=0, max_time=0, avg_time=0,
                success=False, error=str(e)
            )
    
    def _parse_ping_output(self, host: str, output: str) -> PingResult:
        """Parse ping command output"""
        lines = output.split('\n')
        
        packets_sent = 0
        packets_received = 0
        packets_lost = 0
        packet_loss_percent = 0.0
        min_time = 0.0
        max_time = 0.0
        avg_time = 0.0
        
        # Parse statistics
        for line in lines:
            if 'Packets: Sent =' in line:
                # Extract packet statistics
                sent_match = re.search(r'Sent = (\d+)', line)
                received_match = re.search(r'Received = (\d+)', line)
                lost_match = re.search(r'Lost = (\d+)', line)
                loss_match = re.search(r'$$(\d+)% loss$$', line)
                
                if sent_match:
                    packets_sent = int(sent_match.group(1))
                if received_match:
                    packets_received = int(received_match.group(1))
                if lost_match:
                    packets_lost = int(lost_match.group(1))
                if loss_match:
                    packet_loss_percent = float(loss_match.group(1))
            
            elif 'Minimum =' in line:
                # Extract timing statistics
                min_match = re.search(r'Minimum = (\d+)ms', line)
                max_match = re.search(r'Maximum = (\d+)ms', line)
                avg_match = re.search(r'Average = (\d+)ms', line)
                
                if min_match:
                    min_time = float(min_match.group(1))
                if max_match:
                    max_time = float(max_match.group(1))
                if avg_match:
                    avg_time = float(avg_match.group(1))
        
        return PingResult(
            host=host,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packets_lost=packets_lost,
            packet_loss_percent=packet_loss_percent,
            min_time=min_time,
            max_time=max_time,
            avg_time=avg_time,
            success=packets_received > 0
        )
    
    def traceroute_host(self, host: str, max_hops: int = 30) -> List[TracerouteHop]:
        """Perform traceroute to a host"""
        try:
            cmd = ['tracert', '-h', str(max_hops), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return self._parse_traceroute_output(result.stdout)
            else:
                return []
                
        except Exception:
            return []
    
    def _parse_traceroute_output(self, output: str) -> List[TracerouteHop]:
        """Parse traceroute command output"""
        hops = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Tracing route' in line or 'over a maximum' in line:
                continue
            
            # Match traceroute line format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
            hop_match = re.match(r'\s*(\d+)\s+(.+)', line)
            if hop_match:
                hop_num = int(hop_match.group(1))
                hop_data = hop_match.group(2).strip()
                
                # Parse response times and IP/hostname
                times = []
                ip_address = ""
                hostname = None
                timeout = False
                
                if '*' in hop_data:
                    timeout = True
                else:
                    # Extract times
                    time_matches = re.findall(r'(\d+)\s*ms', hop_data)
                    times = [float(t) for t in time_matches]
                    
                    # Extract IP address
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', hop_data)
                    if ip_match:
                        ip_address = ip_match.group(1)
                    
                    # Extract hostname if present
                    hostname_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', hop_data)
                    if hostname_match and hostname_match.group(1) != ip_address:
                        hostname = hostname_match.group(1)
                
                hop = TracerouteHop(
                    hop_number=hop_num,
                    ip_address=ip_address,
                    hostname=hostname,
                    response_times=times,
                    timeout=timeout
                )
                hops.append(hop)
        
        return hops
    
    def get_network_interfaces(self) -> List[NetworkInterface]:
        """Get detailed network interface information"""
        try:
            cmd = ['ipconfig', '/all']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_ipconfig_output(result.stdout)
            else:
                return []
                
        except Exception:
            return []
    
    def _parse_ipconfig_output(self, output: str) -> List[NetworkInterface]:
        """Parse ipconfig /all output"""
        interfaces = []
        lines = output.split('\n')
        current_interface = None
        
        for line in lines:
            line = line.strip()
            
            if 'adapter' in line.lower() and ':' in line:
                # New interface
                if current_interface:
                    interfaces.append(current_interface)
                
                adapter_name = line.split(':')[0].strip()
                current_interface = {
                    'name': adapter_name,
                    'description': '',
                    'ip_address': '',
                    'subnet_mask': '',
                    'default_gateway': '',
                    'dns_servers': [],
                    'mac_address': '',
                    'status': '',
                    'dhcp_enabled': False
                }
            
            elif current_interface and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'description' in key:
                    current_interface['description'] = value
                elif 'physical address' in key:
                    current_interface['mac_address'] = value
                elif 'dhcp enabled' in key:
                    current_interface['dhcp_enabled'] = value.lower() == 'yes'
                elif 'ipv4 address' in key:
                    # Extract IP address (remove (Preferred) suffix)
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', value)
                    if ip_match:
                        current_interface['ip_address'] = ip_match.group(1)
                elif 'subnet mask' in key:
                    current_interface['subnet_mask'] = value
                elif 'default gateway' in key and value:
                    current_interface['default_gateway'] = value
                elif 'dns servers' in key:
                    current_interface['dns_servers'].append(value)
        
        # Add the last interface
        if current_interface:
            interfaces.append(current_interface)
        
        # Convert to NetworkInterface objects
        network_interfaces = []
        for iface in interfaces:
            if iface['ip_address']:  # Only include interfaces with IP addresses
                network_interfaces.append(NetworkInterface(
                    name=iface['name'],
                    description=iface['description'],
                    ip_address=iface['ip_address'],
                    subnet_mask=iface['subnet_mask'],
                    default_gateway=iface['default_gateway'],
                    dns_servers=iface['dns_servers'],
                    mac_address=iface['mac_address'],
                    status='Active' if iface['ip_address'] else 'Inactive',
                    dhcp_enabled=iface['dhcp_enabled']
                ))
        
        return network_interfaces
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network connection statistics"""
        try:
            cmd = ['netstat', '-e']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_netstat_output(result.stdout)
            else:
                return {}
                
        except Exception:
            return {}
    
    def _parse_netstat_output(self, output: str) -> Dict[str, Any]:
        """Parse netstat output for statistics"""
        stats = {}
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if 'Bytes' in line:
                # Next line should contain the values
                if i + 1 < len(lines):
                    values = lines[i + 1].split()
                    if len(values) >= 2:
                        stats['bytes_received'] = int(values[0])
                        stats['bytes_sent'] = int(values[1])
                break
        
        return stats
    
    def get_active_connections(self) -> List[Dict[str, str]]:
        """Get active network connections"""
        try:
            cmd = ['netstat', '-an']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_active_connections(result.stdout)
            else:
                return []
                
        except Exception:
            return []
    
    def _parse_active_connections(self, output: str) -> List[Dict[str, str]]:
        """Parse active connections from netstat output"""
        connections = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Proto' in line or 'Active' in line:
                continue
            
            parts = line.split()
            if len(parts) >= 4:
                connection = {
                    'protocol': parts[0],
                    'local_address': parts[1],
                    'foreign_address': parts[2],
                    'state': parts[3] if len(parts) > 3 else ''
                }
                connections.append(connection)
        
        return connections
    
    def test_dns_resolution(self, hostname: str) -> Dict[str, Any]:
        """Test DNS resolution for a hostname"""
        try:
            start_time = time.time()
            ip_address = socket.gethostbyname(hostname)
            resolution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'success': True,
                'hostname': hostname,
                'ip_address': ip_address,
                'resolution_time_ms': resolution_time
            }
        except Exception as e:
            return {
                'success': False,
                'hostname': hostname,
                'error': str(e)
            }
    
    def test_port_connectivity(self, host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
        """Test connectivity to a specific port"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            connection_time = (time.time() - start_time) * 1000
            
            return {
                'success': result == 0,
                'host': host,
                'port': port,
                'connection_time_ms': connection_time,
                'error': None if result == 0 else f"Connection failed (error {result})"
            }
        except Exception as e:
            return {
                'success': False,
                'host': host,
                'port': port,
                'error': str(e)
            }
    
    def get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        try:
            import urllib.request
            response = urllib.request.urlopen('https://api.ipify.org', timeout=10)
            return response.read().decode('utf-8').strip()
        except:
            try:
                # Fallback method
                response = urllib.request.urlopen('https://checkip.amazonaws.com', timeout=10)
                return response.read().decode('utf-8').strip()
            except:
                return None
    
    def flush_dns_cache(self) -> bool:
        """Flush DNS cache"""
        try:
            result = subprocess.run(['ipconfig', '/flushdns'], 
                                  capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def release_renew_ip(self) -> Tuple[bool, bool]:
        """Release and renew IP address"""
        try:
            # Release IP
            release_result = subprocess.run(['ipconfig', '/release'], 
                                          capture_output=True, text=True, timeout=30)
            
            # Renew IP
            renew_result = subprocess.run(['ipconfig', '/renew'], 
                                        capture_output=True, text=True, timeout=60)
            
            return (release_result.returncode == 0, renew_result.returncode == 0)
        except:
            return (False, False)
    
    def reset_winsock(self) -> bool:
        """Reset Winsock catalog"""
        try:
            result = subprocess.run(['netsh', 'winsock', 'reset'], 
                                  capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def reset_tcp_ip(self) -> bool:
        """Reset TCP/IP stack"""
        try:
            result = subprocess.run(['netsh', 'int', 'ip', 'reset'], 
                                  capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False

class NetworkDiagnostics:
    """Comprehensive network diagnostics"""
    
    def __init__(self):
        self.tools = NetworkToolsManager()
    
    def run_comprehensive_test(self, target_host: str = "google.com") -> Dict[str, Any]:
        """Run comprehensive network diagnostics"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'target_host': target_host,
            'tests': {}
        }
        
        # DNS Resolution Test
        results['tests']['dns_resolution'] = self.tools.test_dns_resolution(target_host)
        
        # Ping Test
        results['tests']['ping'] = self.tools.ping_host(target_host, count=4)
        
        # Port Connectivity Tests
        common_ports = [80, 443, 53, 22, 21, 25]
        port_tests = {}
        for port in common_ports:
            port_tests[f'port_{port}'] = self.tools.test_port_connectivity(target_host, port, timeout=3)
        results['tests']['port_connectivity'] = port_tests
        
        # Network Interface Information
        results['network_interfaces'] = self.tools.get_network_interfaces()
        
        # Public IP
        results['public_ip'] = self.tools.get_public_ip()
        
        # Network Statistics
        results['network_stats'] = self.tools.get_network_statistics()
        
        return results
    
    def diagnose_connectivity_issues(self) -> List[str]:
        """Diagnose common connectivity issues and provide recommendations"""
        recommendations = []
        
        # Test basic connectivity
        ping_result = self.tools.ping_host("8.8.8.8", count=2)
        if not ping_result.success:
            recommendations.append("No internet connectivity detected")
            recommendations.append("Check network cable/WiFi connection")
            recommendations.append("Verify network adapter is enabled")
        
        # Test DNS resolution
        dns_test = self.tools.test_dns_resolution("google.com")
        if not dns_test['success']:
            recommendations.append("DNS resolution issues detected")
            recommendations.append("Try flushing DNS cache")
            recommendations.append("Consider changing DNS servers to 8.8.8.8 and 8.8.4.4")
        
        # Check network interfaces
        interfaces = self.tools.get_network_interfaces()
        active_interfaces = [iface for iface in interfaces if iface.ip_address]
        
        if not active_interfaces:
            recommendations.append("No active network interfaces found")
            recommendations.append("Check network adapter drivers")
        elif len(active_interfaces) > 1:
            recommendations.append("Multiple active network interfaces detected")
            recommendations.append("This may cause routing conflicts")
        
        # Check for DHCP issues
        dhcp_interfaces = [iface for iface in active_interfaces if iface.dhcp_enabled]
        if dhcp_interfaces:
            for iface in dhcp_interfaces:
                if not iface.default_gateway:
                    recommendations.append(f"No default gateway for {iface.name}")
                    recommendations.append("Try releasing and renewing IP address")
        
        if not recommendations:
            recommendations.append("Network connectivity appears normal")
            recommendations.append("If experiencing issues, try running specific diagnostic tests")
        
        return recommendations

# Utility functions for easy access
def quick_ping(host: str, count: int = 4) -> PingResult:
    """Quick ping test"""
    manager = NetworkToolsManager()
    return manager.ping_host(host, count)

def quick_traceroute(host: str) -> List[TracerouteHop]:
    """Quick traceroute test"""
    manager = NetworkToolsManager()
    return manager.traceroute_host(host)

def get_network_info() -> List[NetworkInterface]:
    """Get network interface information"""
    manager = NetworkToolsManager()
    return manager.get_network_interfaces()

def diagnose_network() -> List[str]:
    """Quick network diagnosis"""
    diagnostics = NetworkDiagnostics()
    return diagnostics.diagnose_connectivity_issues()
