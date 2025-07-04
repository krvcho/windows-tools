"""
Windows Firewall management and monitoring
Provides comprehensive firewall rule management and status monitoring
"""

import subprocess
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class FirewallProfile(Enum):
    """Firewall profile types"""
    DOMAIN = "domain"
    PRIVATE = "private"
    PUBLIC = "public"

class RuleAction(Enum):
    """Firewall rule actions"""
    ALLOW = "allow"
    BLOCK = "block"

class RuleDirection(Enum):
    """Firewall rule directions"""
    INBOUND = "in"
    OUTBOUND = "out"

class RuleProtocol(Enum):
    """Firewall rule protocols"""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ANY = "any"

@dataclass
class FirewallRule:
    """Firewall rule representation"""
    name: str
    enabled: bool
    direction: RuleDirection
    action: RuleAction
    protocol: RuleProtocol
    local_port: str
    remote_port: str
    local_address: str
    remote_address: str
    program: str
    service: str
    description: str
    profile: str
    group: str

@dataclass
class FirewallStatus:
    """Firewall status information"""
    domain_profile: bool
    private_profile: bool
    public_profile: bool
    domain_logging: bool
    private_logging: bool
    public_logging: bool
    domain_inbound: str
    private_inbound: str
    public_inbound: str
    domain_outbound: str
    private_outbound: str
    public_outbound: str

class WindowsFirewallManager:
    """Manager for Windows Firewall operations"""
    
    def __init__(self):
        self.netsh_cmd = "netsh"
        self.advfirewall_cmd = "advfirewall"
    
    def get_firewall_status(self) -> FirewallStatus:
        """Get current firewall status for all profiles"""
        try:
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "show", "allprofiles", "state"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_firewall_status(result.stdout)
            else:
                raise Exception(f"Failed to get firewall status: {result.stderr}")
                
        except Exception as e:
            raise Exception(f"Error getting firewall status: {str(e)}")
    
    def _parse_firewall_status(self, output: str) -> FirewallStatus:
        """Parse firewall status output"""
        lines = output.split('\n')
        status = {
            'domain_profile': False,
            'private_profile': False,
            'public_profile': False,
            'domain_logging': False,
            'private_logging': False,
            'public_logging': False,
            'domain_inbound': 'NotConfigured',
            'private_inbound': 'NotConfigured',
            'public_inbound': 'NotConfigured',
            'domain_outbound': 'NotConfigured',
            'private_outbound': 'NotConfigured',
            'public_outbound': 'NotConfigured'
        }
        
        current_profile = None
        
        for line in lines:
            line = line.strip()
            
            if 'Domain Profile Settings' in line:
                current_profile = 'domain'
            elif 'Private Profile Settings' in line:
                current_profile = 'private'
            elif 'Public Profile Settings' in line:
                current_profile = 'public'
            elif current_profile and 'State' in line and 'ON' in line:
                status[f'{current_profile}_profile'] = True
            elif current_profile and 'Logging' in line and 'Enabled' in line:
                status[f'{current_profile}_logging'] = True
            elif current_profile and 'Inbound connections' in line:
                if 'Allow' in line:
                    status[f'{current_profile}_inbound'] = 'Allow'
                elif 'Block' in line:
                    status[f'{current_profile}_inbound'] = 'Block'
            elif current_profile and 'Outbound connections' in line:
                if 'Allow' in line:
                    status[f'{current_profile}_outbound'] = 'Allow'
                elif 'Block' in line:
                    status[f'{current_profile}_outbound'] = 'Block'
        
        return FirewallStatus(**status)
    
    def set_firewall_state(self, profile: FirewallProfile, enabled: bool) -> bool:
        """Enable or disable firewall for a specific profile"""
        try:
            state = "on" if enabled else "off"
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "set", 
                   f"{profile.value}profile", "state", state]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def get_firewall_rules(self, direction: Optional[RuleDirection] = None) -> List[FirewallRule]:
        """Get all firewall rules or rules for specific direction"""
        try:
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "firewall", "show", "rule", "name=all"]
            if direction:
                cmd.extend(["dir=" + direction.value])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return self._parse_firewall_rules(result.stdout)
            else:
                return []
                
        except Exception:
            return []
    
    def _parse_firewall_rules(self, output: str) -> List[FirewallRule]:
        """Parse firewall rules output"""
        rules = []
        lines = output.split('\n')
        current_rule = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Rule Name:'):
                if current_rule:
                    rules.append(self._create_firewall_rule(current_rule))
                current_rule = {'name': line.split(':', 1)[1].strip()}
            elif ':' in line and current_rule:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                current_rule[key] = value
        
        # Add the last rule
        if current_rule:
            rules.append(self._create_firewall_rule(current_rule))
        
        return rules
    
    def _create_firewall_rule(self, rule_data: Dict[str, str]) -> FirewallRule:
        """Create FirewallRule object from parsed data"""
        return FirewallRule(
            name=rule_data.get('name', ''),
            enabled=rule_data.get('enabled', '').lower() == 'yes',
            direction=RuleDirection.INBOUND if rule_data.get('direction', '').lower() == 'in' else RuleDirection.OUTBOUND,
            action=RuleAction.ALLOW if rule_data.get('action', '').lower() == 'allow' else RuleAction.BLOCK,
            protocol=self._parse_protocol(rule_data.get('protocol', '')),
            local_port=rule_data.get('local_port', 'Any'),
            remote_port=rule_data.get('remote_port', 'Any'),
            local_address=rule_data.get('local_address', 'Any'),
            remote_address=rule_data.get('remote_address', 'Any'),
            program=rule_data.get('program', ''),
            service=rule_data.get('service', ''),
            description=rule_data.get('description', ''),
            profile=rule_data.get('profiles', 'Any'),
            group=rule_data.get('grouping', '')
        )
    
    def _parse_protocol(self, protocol_str: str) -> RuleProtocol:
        """Parse protocol string to enum"""
        protocol_lower = protocol_str.lower()
        if 'tcp' in protocol_lower:
            return RuleProtocol.TCP
        elif 'udp' in protocol_lower:
            return RuleProtocol.UDP
        elif 'icmp' in protocol_lower:
            return RuleProtocol.ICMP
        else:
            return RuleProtocol.ANY
    
    def add_firewall_rule(self, rule_name: str, direction: RuleDirection, 
                         action: RuleAction, protocol: RuleProtocol = RuleProtocol.ANY,
                         local_port: str = "any", remote_port: str = "any",
                         program: str = "", description: str = "",
                         profile: str = "any") -> bool:
        """Add a new firewall rule"""
        try:
            cmd = [
                self.netsh_cmd, self.advfirewall_cmd, "firewall", "add", "rule",
                f"name={rule_name}",
                f"dir={direction.value}",
                f"action={action.value}",
                f"protocol={protocol.value}",
                f"localport={local_port}",
                f"remoteport={remote_port}",
                f"profile={profile}"
            ]
            
            if program:
                cmd.append(f"program={program}")
            
            if description:
                cmd.append(f"description={description}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def delete_firewall_rule(self, rule_name: str) -> bool:
        """Delete a firewall rule by name"""
        try:
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "firewall", 
                   "delete", "rule", f"name={rule_name}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def enable_disable_rule(self, rule_name: str, enabled: bool) -> bool:
        """Enable or disable a firewall rule"""
        try:
            enable_state = "yes" if enabled else "no"
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "firewall", 
                   "set", "rule", f"name={rule_name}", f"new", f"enable={enable_state}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def reset_firewall(self) -> bool:
        """Reset firewall to default settings"""
        try:
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "reset"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def export_firewall_policy(self, file_path: str) -> bool:
        """Export firewall policy to file"""
        try:
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "export", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def import_firewall_policy(self, file_path: str) -> bool:
        """Import firewall policy from file"""
        try:
            cmd = [self.netsh_cmd, self.advfirewall_cmd, "import", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def get_blocked_connections(self) -> List[Dict[str, Any]]:
        """Get recently blocked connections from firewall logs"""
        try:
            # This would require parsing Windows Firewall logs
            # Location: %systemroot%\system32\LogFiles\Firewall\pfirewall.log
            log_path = r"C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
            
            blocked_connections = []
            
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Parse last 100 lines for recent activity
                    for line in lines[-100:]:
                        if 'DROP' in line:
                            parts = line.strip().split()
                            if len(parts) >= 10:
                                blocked_connections.append({
                                    'timestamp': f"{parts[0]} {parts[1]}",
                                    'action': parts[2],
                                    'protocol': parts[3],
                                    'src_ip': parts[4],
                                    'dst_ip': parts[5],
                                    'src_port': parts[6],
                                    'dst_port': parts[7],
                                    'size': parts[8] if len(parts) > 8 else '',
                                    'flags': parts[9] if len(parts) > 9 else ''
                                })
            except FileNotFoundError:
                pass  # Log file doesn't exist or logging is disabled
            
            return blocked_connections[-50:]  # Return last 50 blocked connections
            
        except Exception:
            return []
    
    def get_firewall_statistics(self) -> Dict[str, Any]:
        """Get firewall statistics and metrics"""
        try:
            rules = self.get_firewall_rules()
            status = self.get_firewall_status()
            blocked = self.get_blocked_connections()
            
            stats = {
                'total_rules': len(rules),
                'enabled_rules': len([r for r in rules if r.enabled]),
                'disabled_rules': len([r for r in rules if not r.enabled]),
                'inbound_rules': len([r for r in rules if r.direction == RuleDirection.INBOUND]),
                'outbound_rules': len([r for r in rules if r.direction == RuleDirection.OUTBOUND]),
                'allow_rules': len([r for r in rules if r.action == RuleAction.ALLOW]),
                'block_rules': len([r for r in rules if r.action == RuleAction.BLOCK]),
                'tcp_rules': len([r for r in rules if r.protocol == RuleProtocol.TCP]),
                'udp_rules': len([r for r in rules if r.protocol == RuleProtocol.UDP]),
                'recent_blocked_connections': len(blocked),
                'profiles_enabled': sum([
                    status.domain_profile,
                    status.private_profile,
                    status.public_profile
                ])
            }
            
            return stats
            
        except Exception:
            return {}

class FirewallRuleBuilder:
    """Builder for creating firewall rules"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset builder to default values"""
        self._name = ""
        self._direction = RuleDirection.INBOUND
        self._action = RuleAction.BLOCK
        self._protocol = RuleProtocol.ANY
        self._local_port = "any"
        self._remote_port = "any"
        self._program = ""
        self._description = ""
        self._profile = "any"
        return self
    
    def name(self, name: str):
        """Set rule name"""
        self._name = name
        return self
    
    def direction(self, direction: RuleDirection):
        """Set rule direction"""
        self._direction = direction
        return self
    
    def action(self, action: RuleAction):
        """Set rule action"""
        self._action = action
        return self
    
    def protocol(self, protocol: RuleProtocol):
        """Set rule protocol"""
        self._protocol = protocol
        return self
    
    def local_port(self, port: str):
        """Set local port"""
        self._local_port = port
        return self
    
    def remote_port(self, port: str):
        """Set remote port"""
        self._remote_port = port
        return self
    
    def program(self, program_path: str):
        """Set program path"""
        self._program = program_path
        return self
    
    def description(self, description: str):
        """Set rule description"""
        self._description = description
        return self
    
    def profile(self, profile: str):
        """Set firewall profile"""
        self._profile = profile
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build rule configuration"""
        return {
            'name': self._name,
            'direction': self._direction,
            'action': self._action,
            'protocol': self._protocol,
            'local_port': self._local_port,
            'remote_port': self._remote_port,
            'program': self._program,
            'description': self._description,
            'profile': self._profile
        }

class FirewallPresets:
    """Predefined firewall rule presets"""
    
    @staticmethod
    def get_common_presets() -> Dict[str, Dict[str, Any]]:
        """Get common firewall rule presets"""
        return {
            'Block All Inbound': {
                'name': 'Block All Inbound Traffic',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.BLOCK,
                'protocol': RuleProtocol.ANY,
                'description': 'Block all inbound traffic'
            },
            'Allow HTTP': {
                'name': 'Allow HTTP Traffic',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.ALLOW,
                'protocol': RuleProtocol.TCP,
                'local_port': '80',
                'description': 'Allow HTTP web traffic'
            },
            'Allow HTTPS': {
                'name': 'Allow HTTPS Traffic',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.ALLOW,
                'protocol': RuleProtocol.TCP,
                'local_port': '443',
                'description': 'Allow HTTPS secure web traffic'
            },
            'Allow SSH': {
                'name': 'Allow SSH Traffic',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.ALLOW,
                'protocol': RuleProtocol.TCP,
                'local_port': '22',
                'description': 'Allow SSH remote access'
            },
            'Allow RDP': {
                'name': 'Allow Remote Desktop',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.ALLOW,
                'protocol': RuleProtocol.TCP,
                'local_port': '3389',
                'description': 'Allow Remote Desktop connections'
            },
            'Block P2P': {
                'name': 'Block P2P Traffic',
                'direction': RuleDirection.OUTBOUND,
                'action': RuleAction.BLOCK,
                'protocol': RuleProtocol.TCP,
                'remote_port': '6881-6889',
                'description': 'Block BitTorrent and P2P traffic'
            },
            'Allow DNS': {
                'name': 'Allow DNS Traffic',
                'direction': RuleDirection.OUTBOUND,
                'action': RuleAction.ALLOW,
                'protocol': RuleProtocol.UDP,
                'remote_port': '53',
                'description': 'Allow DNS resolution'
            },
            'Block Telnet': {
                'name': 'Block Telnet',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.BLOCK,
                'protocol': RuleProtocol.TCP,
                'local_port': '23',
                'description': 'Block insecure Telnet connections'
            }
        }
    
    @staticmethod
    def get_security_presets() -> Dict[str, Dict[str, Any]]:
        """Get security-focused firewall presets"""
        return {
            'High Security Inbound': {
                'name': 'High Security - Block All Inbound',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.BLOCK,
                'protocol': RuleProtocol.ANY,
                'description': 'High security - block all inbound traffic'
            },
            'Block Suspicious Ports': {
                'name': 'Block Suspicious Ports',
                'direction': RuleDirection.INBOUND,
                'action': RuleAction.BLOCK,
                'protocol': RuleProtocol.TCP,
                'local_port': '135,139,445,1433,1434,3389',
                'description': 'Block commonly attacked ports'
            },
            'Allow Only Essential': {
                'name': 'Allow Only Essential Services',
                'direction': RuleDirection.OUTBOUND,
                'action': RuleAction.ALLOW,
                'protocol': RuleProtocol.TCP,
                'remote_port': '80,443,53',
                'description': 'Allow only HTTP, HTTPS, and DNS'
            }
        }

# Utility functions
def get_firewall_status() -> FirewallStatus:
    """Quick function to get firewall status"""
    manager = WindowsFirewallManager()
    return manager.get_firewall_status()

def get_firewall_rules() -> List[FirewallRule]:
    """Quick function to get all firewall rules"""
    manager = WindowsFirewallManager()
    return manager.get_firewall_rules()

def is_firewall_enabled() -> bool:
    """Check if Windows Firewall is enabled on any profile"""
    try:
        status = get_firewall_status()
        return status.domain_profile or status.private_profile or status.public_profile
    except:
        return False
