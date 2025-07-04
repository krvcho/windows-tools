"""
Event Log Manager for Windows Event Viewer functionality
Provides comprehensive event log viewing, filtering, and export capabilities
"""

import subprocess
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QTextEdit, QFileDialog, QMessageBox

class EventLevel(Enum):
    """Event log levels"""
    CRITICAL = 1
    ERROR = 2
    WARNING = 3
    INFORMATION = 4
    VERBOSE = 5

@dataclass
class EventLogEntry:
    """Single event log entry"""
    event_id: int
    level: EventLevel
    level_display_name: str
    log_name: str
    source: str
    time_created: datetime
    task_category: str
    computer_name: str
    user_id: str
    message: str
    
class EventLogManager(QObject):
    """Manager for Windows Event Log operations"""
    
    events_loaded = Signal(list)  # List[EventLogEntry]
    operation_completed = Signal(str, bool, str)  # operation, success, message
    
    def __init__(self):
        super().__init__()
        self.available_logs = [
            'System',
            'Application', 
            'Security',
            'Setup',
            'Microsoft-Windows-PowerShell/Operational'
        ]
        
        self.level_names = {
            1: 'Critical',
            2: 'Error', 
            3: 'Warning',
            4: 'Information',
            5: 'Verbose'
        }
    
    def get_events(self, log_name: str = 'System', 
                   level_filter: Optional[EventLevel] = None,
                   hours_back: int = 24,
                   max_events: int = 100) -> List[EventLogEntry]:
        """Get events from specified log with filtering"""
        try:
            # Calculate start time
            start_time = datetime.now() - timedelta(hours=hours_back)
            start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Build PowerShell command
            filter_hashtable = f"@{{'LogName'='{log_name}'; 'StartTime'='{start_time_str}'}}"
            
            if level_filter:
                filter_hashtable = filter_hashtable[:-1] + f"; 'Level'={level_filter.value}}}"
            
            ps_command = f"""
            try {{
                $events = Get-WinEvent -FilterHashtable {filter_hashtable} -MaxEvents {max_events} -ErrorAction Stop
                $events | ForEach-Object {{
                    [PSCustomObject]@{{
                        'EventId' = $_.Id
                        'Level' = $_.Level
                        'LevelDisplayName' = $_.LevelDisplayName
                        'LogName' = $_.LogName
                        'ProviderName' = $_.ProviderName
                        'TimeCreated' = $_.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
                        'TaskDisplayName' = $_.TaskDisplayName
                        'MachineName' = $_.MachineName
                        'UserId' = if ($_.UserId) {{ $_.UserId.ToString() }} else {{ 'N/A' }}
                        'Message' = $_.Message
                    }}
                }} | ConvertTo-Json -Depth 2
            }} catch {{
                Write-Output "ERROR: $($_.Exception.Message)"
            }}
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"PowerShell command failed: {result.stderr}")
            
            output = result.stdout.strip()
            if not output or output.startswith("ERROR:"):
                error_msg = output.replace("ERROR: ", "") if output.startswith("ERROR:") else "No events found"
                raise Exception(error_msg)
            
            # Parse JSON output
            events_data = json.loads(output)
            
            # Handle single event (not in array)
            if isinstance(events_data, dict):
                events_data = [events_data]
            
            # Convert to EventLogEntry objects
            events = []
            for event_data in events_data:
                try:
                    # Parse timestamp
                    time_created = datetime.fromisoformat(
                        event_data['TimeCreated'].replace('Z', '+00:00')
                    )
                    
                    # Map level to enum
                    level_value = event_data.get('Level', 4)
                    try:
                        level = EventLevel(level_value)
                    except ValueError:
                        level = EventLevel.INFORMATION
                    
                    event_entry = EventLogEntry(
                        event_id=event_data.get('EventId', 0),
                        level=level,
                        level_display_name=event_data.get('LevelDisplayName', 'Information'),
                        log_name=event_data.get('LogName', log_name),
                        source=event_data.get('ProviderName', 'Unknown'),
                        time_created=time_created,
                        task_category=event_data.get('TaskDisplayName', 'None'),
                        computer_name=event_data.get('MachineName', 'Unknown'),
                        user_id=event_data.get('UserId', 'N/A'),
                        message=event_data.get('Message', 'No message available')
                    )
                    
                    events.append(event_entry)
                    
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    continue
            
            self.events_loaded.emit(events)
            return events
            
        except Exception as e:
            error_msg = f"Error retrieving events: {str(e)}"
            self.operation_completed.emit("get_events", False, error_msg)
            return []
    
    def get_last_errors(self, log_name: str = 'System', 
                       count: int = 50, 
                       hours_back: int = 24) -> List[EventLogEntry]:
        """Get the last N error events from specified log"""
        return self.get_events(
            log_name=log_name,
            level_filter=EventLevel.ERROR,
            hours_back=hours_back,
            max_events=count
        )
    
    def get_critical_events(self, hours_back: int = 168) -> List[EventLogEntry]:  # 7 days
        """Get critical events from all logs"""
        all_events = []
        
        for log_name in ['System', 'Application']:
            try:
                events = self.get_events(
                    log_name=log_name,
                    level_filter=EventLevel.CRITICAL,
                    hours_back=hours_back,
                    max_events=50
                )
                all_events.extend(events)
            except Exception as e:
                print(f"Error getting critical events from {log_name}: {e}")
                continue
        
        # Sort by time (newest first)
        all_events.sort(key=lambda x: x.time_created, reverse=True)
        return all_events[:50]  # Return top 50
    
    def export_events_to_text(self, events: List[EventLogEntry], 
                             filename: str, 
                             format_type: str = 'detailed') -> bool:
        """Export events to text file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Windows Event Log Export\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Events: {len(events)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, event in enumerate(events, 1):
                    if format_type == 'detailed':
                        f.write(f"Event #{i}\n")
                        f.write(f"Event ID: {event.event_id}\n")
                        f.write(f"Level: {event.level_display_name}\n")
                        f.write(f"Source: {event.source}\n")
                        f.write(f"Time: {event.time_created.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Log: {event.log_name}\n")
                        f.write(f"Category: {event.task_category}\n")
                        f.write(f"Computer: {event.computer_name}\n")
                        f.write(f"User: {event.user_id}\n")
                        f.write(f"Message: {event.message}\n")
                        f.write("-" * 80 + "\n\n")
                    
                    elif format_type == 'simple':
                        f.write(f"{event.time_created.strftime('%Y-%m-%d %H:%M:%S')} | "
                               f"{event.level_display_name} | "
                               f"ID:{event.event_id} | "
                               f"{event.source} | "
                               f"{event.message[:100]}...\n")
                    
                    elif format_type == 'csv':
                        # This will be handled by export_events_to_csv
                        pass
            
            self.operation_completed.emit("export_text", True, f"Events exported to {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Error exporting events: {str(e)}"
            self.operation_completed.emit("export_text", False, error_msg)
            return False
    
    def export_events_to_csv(self, events: List[EventLogEntry], filename: str) -> bool:
        """Export events to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Event ID', 'Level', 'Source', 'Time Created', 
                    'Log Name', 'Category', 'Computer', 'User', 'Message'
                ])
                
                # Write events
                for event in events:
                    writer.writerow([
                        event.event_id,
                        event.level_display_name,
                        event.source,
                        event.time_created.strftime('%Y-%m-%d %H:%M:%S'),
                        event.log_name,
                        event.task_category,
                        event.computer_name,
                        event.user_id,
                        event.message.replace('\n', ' ').replace('\r', '')
                    ])
            
            self.operation_completed.emit("export_csv", True, f"Events exported to {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Error exporting events to CSV: {str(e)}"
            self.operation_completed.emit("export_csv", False, error_msg)
            return False
    
    def get_event_statistics(self, events: List[EventLogEntry]) -> Dict[str, Any]:
        """Get statistics about the events"""
        if not events:
            return {}
        
        stats = {
            'total_count': len(events),
            'level_breakdown': {},
            'source_breakdown': {},
            'time_range': {
                'start': min(event.time_created for event in events),
                'end': max(event.time_created for event in events)
            }
        }
        
        # Count by level
        for event in events:
            level_name = event.level_display_name
            stats['level_breakdown'][level_name] = stats['level_breakdown'].get(level_name, 0) + 1
        
        # Count by source (top 10)
        source_counts = {}
        for event in events:
            source_counts[event.source] = source_counts.get(event.source, 0) + 1
        
        # Get top 10 sources
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        stats['source_breakdown'] = dict(top_sources)
        
        return stats

class EventLogThread(QThread):
    """Thread for loading event logs without blocking UI"""
    
    events_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, event_log_manager: EventLogManager, 
                 log_name: str, level_filter: Optional[EventLevel],
                 hours_back: int, max_events: int):
        super().__init__()
        self.event_log_manager = event_log_manager
        self.log_name = log_name
        self.level_filter = level_filter
        self.hours_back = hours_back
        self.max_events = max_events
    
    def run(self):
        try:
            events = self.event_log_manager.get_events(
                self.log_name, 
                self.level_filter,
                self.hours_back,
                self.max_events
            )
            self.events_loaded.emit(events)
        except Exception as e:
            self.error_occurred.emit(str(e))

# Utility functions
def format_event_message(message: str, max_length: int = 100) -> str:
    """Format event message for display"""
    if not message:
        return "No message available"
    
    # Remove extra whitespace and newlines
    formatted = ' '.join(message.split())
    
    # Truncate if too long
    if len(formatted) > max_length:
        return formatted[:max_length] + "..."
    
    return formatted

def get_level_color(level: EventLevel) -> str:
    """Get color for event level"""
    color_map = {
        EventLevel.CRITICAL: '#8B0000',  # Dark red
        EventLevel.ERROR: '#FF0000',     # Red
        EventLevel.WARNING: '#FFA500',   # Orange
        EventLevel.INFORMATION: '#008000', # Green
        EventLevel.VERBOSE: '#808080'    # Gray
    }
    return color_map.get(level, '#000000')  # Default black
