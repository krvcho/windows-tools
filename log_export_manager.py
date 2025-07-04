"""
Log Export Manager
Handles exporting logs from various text widgets to files
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QTextEdit, QFileDialog, QMessageBox, QWidget

class LogExportManager:
    """Manager for exporting logs to files"""
    
    def __init__(self):
        self.desktop_path = self.get_desktop_path()
    
    def get_desktop_path(self) -> str:
        """Get the user's desktop path"""
        try:
            # Try to get desktop path from environment
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(desktop):
                return desktop
            
            # Fallback to user home directory
            return os.path.expanduser("~")
        except Exception:
            # Ultimate fallback to current directory
            return os.getcwd()
    
    def generate_filename(self, prefix: str = "system_log") -> str:
        """Generate a unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.txt"
    
    def export_text_widget_content(self, text_widget: QTextEdit, parent: QWidget, 
                                 default_filename: str = None, title: str = "Save Log") -> bool:
        """
        Export content from a QTextEdit widget to a file
        
        Args:
            text_widget: The QTextEdit widget containing the log content
            parent: Parent widget for dialog
            default_filename: Default filename (will generate if None)
            title: Dialog title
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            # Get content from text widget
            content = text_widget.toPlainText()
            
            if not content.strip():
                QMessageBox.information(parent, "No Content", "No log content to export.")
                return False
            
            # Generate default filename if not provided
            if not default_filename:
                default_filename = self.generate_filename()
            
            # Ensure .txt extension
            if not default_filename.endswith('.txt'):
                default_filename += '.txt'
            
            # Create full path to desktop
            default_path = os.path.join(self.desktop_path, default_filename)
            
            # Show save dialog
            filename, _ = QFileDialog.getSaveFileName(
                parent,
                title,
                default_path,
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                return self.save_content_to_file(content, filename, parent)
            
            return False
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Error exporting log:\n{str(e)}")
            return False
    
    def save_content_to_file(self, content: str, filename: str, parent: QWidget = None) -> bool:
        """
        Save content to a file
        
        Args:
            content: Text content to save
            filename: Full path to save file
            parent: Parent widget for error dialogs
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Add header with timestamp and system info
            header = self.generate_log_header()
            full_content = header + "\n" + content
            
            # Write to file with UTF-8 encoding
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            if parent:
                QMessageBox.information(
                    parent, 
                    "Export Successful", 
                    f"Log saved successfully to:\n{filename}"
                )
            
            return True
            
        except Exception as e:
            if parent:
                QMessageBox.critical(
                    parent, 
                    "Save Error", 
                    f"Error saving log file:\n{str(e)}"
                )
            return False
    
    def generate_log_header(self) -> str:
        """Generate a header for log files with system information"""
        try:
            import platform
            import getpass
            
            header = "=" * 80 + "\n"
            header += "SYSTEM MAINTENANCE TOOLS - LOG EXPORT\n"
            header += "=" * 80 + "\n"
            header += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"Computer: {platform.node()}\n"
            header += f"User: {getpass.getuser()}\n"
            header += f"OS: {platform.system()} {platform.release()}\n"
            header += f"Platform: {platform.platform()}\n"
            header += "=" * 80 + "\n"
            
            return header
            
        except Exception:
            # Fallback header if system info fails
            return f"System Maintenance Tools Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "=" * 80 + "\n"
    
    def export_multiple_logs(self, log_data: dict, parent: QWidget, 
                           filename_prefix: str = "combined_logs") -> bool:
        """
        Export multiple logs to a single file
        
        Args:
            log_data: Dictionary with section names as keys and content as values
            parent: Parent widget for dialogs
            filename_prefix: Prefix for the filename
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            if not log_data:
                QMessageBox.information(parent, "No Content", "No log content to export.")
                return False
            
            # Generate filename
            filename = self.generate_filename(filename_prefix)
            default_path = os.path.join(self.desktop_path, filename)
            
            # Show save dialog
            save_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Save Combined Logs",
                default_path,
                "Text Files (*.txt);;All Files (*)"
            )
            
            if save_path:
                # Combine all log content
                combined_content = ""
                
                for section_name, content in log_data.items():
                    if content and content.strip():
                        combined_content += f"\n{'=' * 60}\n"
                        combined_content += f"{section_name.upper()}\n"
                        combined_content += f"{'=' * 60}\n"
                        combined_content += content + "\n"
                
                if combined_content:
                    return self.save_content_to_file(combined_content, save_path, parent)
                else:
                    QMessageBox.information(parent, "No Content", "No log content to export.")
                    return False
            
            return False
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Error exporting combined logs:\n{str(e)}")
            return False

class LogExportButton:
    """Helper class to create standardized log export buttons"""
    
    def __init__(self, export_manager: LogExportManager):
        self.export_manager = export_manager
    
    def create_export_button(self, parent, text_widget: QTextEdit, 
                           button_text: str = "Save Log to File",
                           filename_prefix: str = "log") -> 'QPushButton':
        """
        Create a standardized export button
        
        Args:
            parent: Parent widget
            text_widget: QTextEdit widget to export from
            button_text: Text for the button
            filename_prefix: Prefix for generated filename
            
        Returns:
            QPushButton: Configured export button
        """
        from PySide6.QtWidgets import QPushButton
        
        button = QPushButton(button_text)
        button.setObjectName("info-button")
        
        def export_log():
            filename = self.export_manager.generate_filename(filename_prefix)
            self.export_manager.export_text_widget_content(
                text_widget, parent, filename, f"Save {filename_prefix.title()} Log"
            )
        
        button.clicked.connect(export_log)
        return button

# Utility functions for easy integration
def create_log_export_manager() -> LogExportManager:
    """Create a new LogExportManager instance"""
    return LogExportManager()

def add_export_button_to_layout(layout, text_widget: QTextEdit, parent,
                               export_manager: LogExportManager = None,
                               filename_prefix: str = "log") -> 'QPushButton':
    """
    Add an export button to an existing layout
    
    Args:
        layout: Layout to add button to
        text_widget: QTextEdit widget to export from
        parent: Parent widget
        export_manager: LogExportManager instance (creates new if None)
        filename_prefix: Prefix for generated filename
        
    Returns:
        QPushButton: The created export button
    """
    if export_manager is None:
        export_manager = LogExportManager()
    
    button_helper = LogExportButton(export_manager)
    export_button = button_helper.create_export_button(parent, text_widget, "Save Log to File", filename_prefix)
    
    # Add button to layout
    from PySide6.QtWidgets import QHBoxLayout
    if isinstance(layout, QHBoxLayout):
        layout.addWidget(export_button)
    else:
        # Create horizontal layout for the button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(export_button)
        layout.addLayout(button_layout)
    
    return export_button
