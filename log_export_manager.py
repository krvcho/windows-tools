"""
Log export manager for saving diagnostic outputs to files
Provides functionality to export logs from various system maintenance tools
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QPushButton, QMessageBox, QFileDialog, QTextEdit
from PySide6.QtCore import QObject, Signal, QThread
import platform

class LogExportManager(QObject):
    """Manager for exporting logs to files"""
    
    export_completed = Signal(str, bool)  # filepath, success
    
    def __init__(self):
        super().__init__()
        self.desktop_path = self._get_desktop_path()
    
    def _get_desktop_path(self) -> str:
        """Get the user's desktop path"""
        try:
            # Try to get desktop path
            if os.name == 'nt':  # Windows
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                if os.path.exists(desktop):
                    return desktop
            
            # Fallback to user home directory
            return os.path.expanduser('~')
        except Exception:
            # Final fallback to current directory
            return os.getcwd()
    
    def export_log(self, text_widget: QTextEdit, parent_widget, 
                   filename_prefix: str = "log") -> bool:
        """Export log content to a text file"""
        try:
            # Get content from text widget
            content = text_widget.toPlainText()
            
            if not content.strip():
                QMessageBox.information(
                    parent_widget, 
                    "No Content", 
                    "No log content to export."
                )
                return False
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.txt"
            
            # Default file path
            default_path = os.path.join(self.desktop_path, filename)
            
            # Show save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Save Log File",
                default_path,
                "Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return False  # User cancelled
            
            # Create log header
            header = self._create_log_header(filename_prefix)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(content)
            
            # Show success message
            QMessageBox.information(
                parent_widget,
                "Export Successful",
                f"Log exported successfully to:\n{file_path}"
            )
            
            self.export_completed.emit(file_path, True)
            return True
            
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Export Error",
                f"Failed to export log:\n{str(e)}"
            )
            self.export_completed.emit("", False)
            return False
    
    def _create_log_header(self, log_type: str) -> str:
        """Create a formatted header for the log file"""
        try:
            computer_name = os.environ.get('COMPUTERNAME', 'Unknown')
            username = os.environ.get('USERNAME', 'Unknown')
            os_info = platform.platform()
            
            header = f"""================================================================================
SYSTEM MAINTENANCE TOOLS - LOG EXPORT
================================================================================
Log Type: {log_type.replace('_', ' ').title()}
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Computer: {computer_name}
User: {username}
OS: {os_info}
Platform: {platform.system()} {platform.release()}
================================================================================

"""
            return header
            
        except Exception:
            # Fallback header if system info collection fails
            return f"""================================================================================
SYSTEM MAINTENANCE TOOLS - LOG EXPORT
================================================================================
Log Type: {log_type.replace('_', ' ').title()}
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

"""

class LogExportButton(QPushButton):
    """Custom button for log export functionality"""
    
    def __init__(self, text_widget: QTextEdit, parent_widget, 
                 export_manager: LogExportManager, filename_prefix: str):
        super().__init__("Save Log to File")
        self.text_widget = text_widget
        self.parent_widget = parent_widget
        self.export_manager = export_manager
        self.filename_prefix = filename_prefix
        
        # Set button style
        self.setObjectName("info-button")
        
        # Connect click event
        self.clicked.connect(self._export_log)
    
    def _export_log(self):
        """Handle export button click"""
        self.export_manager.export_log(
            self.text_widget, 
            self.parent_widget, 
            self.filename_prefix
        )

def add_export_button_to_layout(layout, text_widget: QTextEdit, parent_widget, 
                               export_manager: LogExportManager, filename_prefix: str):
    """Helper function to add export button to a layout"""
    export_button = LogExportButton(
        text_widget, parent_widget, export_manager, filename_prefix
    )
    layout.addWidget(export_button)
    return export_button

def create_export_manager() -> LogExportManager:
    """Factory function to create a log export manager"""
    return LogExportManager()
