"""
Event Log GUI Components
Provides widgets for viewing, filtering, and exporting Windows event logs
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSpinBox, QPushButton, QTableWidget, 
                               QTableWidgetItem, QTextEdit, QSplitter, QGroupBox,
                               QCheckBox, QProgressBar, QFileDialog, QMessageBox,
                               QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor

from event_log_manager import (EventLogManager, EventLogEntry, EventLevel, 
                              EventLogThread, format_event_message, get_level_color)

class EventLogViewerWidget(QWidget):
    """Main widget for viewing and filtering event logs"""
    
    def __init__(self):
        super().__init__()
        self.event_log_manager = EventLogManager()
        self.current_events = []
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_events)
        self.setup_ui()
        
        # Connect signals
        self.event_log_manager.events_loaded.connect(self.display_events)
        self.event_log_manager.operation_completed.connect(self.handle_operation_completed)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control panel
        control_group = QGroupBox("Event Log Filters")
        control_layout = QVBoxLayout(control_group)
        
        # First row - Log selection and level filter
        filter_row1 = QHBoxLayout()
        
        filter_row1.addWidget(QLabel("Log:"))
        self.log_combo = QComboBox()
        self.log_combo.addItems(['System', 'Application', 'Security', 'Setup', 'Microsoft-Windows-PowerShell/Operational'])
        filter_row1.addWidget(self.log_combo)
        
        filter_row1.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(['All', 'Critical', 'Error', 'Warning', 'Information', 'Verbose'])
        filter_row1.addWidget(self.level_combo)
        
        filter_row1.addStretch()
        control_layout.addLayout(filter_row1)
        
        # Second row - Time range and max events
        filter_row2 = QHBoxLayout()
        
        filter_row2.addWidget(QLabel("Hours back:"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 168)  # 1 hour to 1 week
        self.hours_spin.setValue(24)
        filter_row2.addWidget(self.hours_spin)
        
        filter_row2.addWidget(QLabel("Max events:"))
        self.max_events_spin = QSpinBox()
        self.max_events_spin.setRange(10, 1000)
        self.max_events_spin.setValue(100)
        filter_row2.addWidget(self.max_events_spin)
        
        filter_row2.addStretch()
        control_layout.addLayout(filter_row2)
        
        # Third row - Action buttons
        action_row = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Events")
        self.load_btn.clicked.connect(self.load_events)
        action_row.addWidget(self.load_btn)
        
        self.export_btn = QPushButton("Export Events")
        self.export_btn.clicked.connect(self.export_events)
        self.export_btn.setEnabled(False)
        action_row.addWidget(self.export_btn)
        
        self.auto_refresh_checkbox = QCheckBox("Auto Refresh (30s)")
        self.auto_refresh_checkbox.toggled.connect(self.toggle_auto_refresh)
        action_row.addWidget(self.auto_refresh_checkbox)
        
        action_row.addStretch()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_events)
        action_row.addWidget(self.clear_btn)
        
        control_layout.addLayout(action_row)
        layout.addWidget(control_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(6)
        self.events_table.setHorizontalHeaderLabels([
            "Time", "Level", "Event ID", "Source", "Log", "Message"
        ])
        
        # Configure table
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Level
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Event ID
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)       # Source
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Log
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Message
        
        self.events_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.events_table.setAlternatingRowColors(True)
        self.events_table.setSortingEnabled(True)
        self.events_table.itemSelectionChanged.connect(self.show_event_details)
        
        content_splitter.addWidget(self.events_table)
        
        # Event details panel
        details_group = QGroupBox("Event Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)
        
        content_splitter.addWidget(details_group)
        
        # Set splitter proportions (70% table, 30% details)
        content_splitter.setSizes([700, 300])
        layout.addWidget(content_splitter)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.event_count_label = QLabel("Events: 0")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.event_count_label)
        
        layout.addLayout(status_layout)
    
    def load_events(self):
        """Load events based on current filter settings"""
        self.load_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Loading events...")
        
        # Get filter settings
        log_name = self.log_combo.currentText()
        level_text = self.level_combo.currentText()
        hours_back = self.hours_spin.value()
        max_events = self.max_events_spin.value()
        
        # Convert level filter
        level_filter = None
        if level_text != 'All':
            level_map = {
                'Critical': EventLevel.CRITICAL,
                'Error': EventLevel.ERROR,
                'Warning': EventLevel.WARNING,
                'Information': EventLevel.INFORMATION,
                'Verbose': EventLevel.VERBOSE
            }
            level_filter = level_map.get(level_text)
        
        # Load events in background thread
        self.load_thread = EventLogThread(
            self.event_log_manager,
            log_name,
            level_filter,
            hours_back,
            max_events
        )
        self.load_thread.events_loaded.connect(self.display_events)
        self.load_thread.error_occurred.connect(self.handle_load_error)
        self.load_thread.start()
    
    def display_events(self, events: List[EventLogEntry]):
        """Display events in the table"""
        self.current_events = events
        self.events_table.setRowCount(len(events))
        
        for i, event in enumerate(events):
            # Time
            time_item = QTableWidgetItem(event.time_created.strftime('%Y-%m-%d %H:%M:%S'))
            self.events_table.setItem(i, 0, time_item)
            
            # Level
            level_item = QTableWidgetItem(event.level_display_name)
            level_color = get_level_color(event.level)
            level_item.setForeground(QColor(level_color))
            self.events_table.setItem(i, 1, level_item)
            
            # Event ID
            id_item = QTableWidgetItem(str(event.event_id))
            self.events_table.setItem(i, 2, id_item)
            
            # Source
            source_item = QTableWidgetItem(event.source)
            self.events_table.setItem(i, 3, source_item)
            
            # Log
            log_item = QTableWidgetItem(event.log_name)
            self.events_table.setItem(i, 4, log_item)
            
            # Message (truncated)
            message_item = QTableWidgetItem(format_event_message(event.message, 100))
            message_item.setToolTip(event.message)  # Full message in tooltip
            self.events_table.setItem(i, 5, message_item)
        
        # Update UI
        self.load_btn.setEnabled(True)
        self.export_btn.setEnabled(len(events) > 0)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Events loaded successfully")
        self.event_count_label.setText(f"Events: {len(events)}")
        
        # Sort by time (newest first)
        self.events_table.sortItems(0, Qt.SortOrder.DescendingOrder)
    
    def handle_load_error(self, error_message: str):
        """Handle error during event loading"""
        self.load_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error_message}")
        
        QMessageBox.warning(self, "Error Loading Events", 
                           f"Failed to load events:\n{error_message}")
    
    def show_event_details(self):
        """Show detailed information for selected event"""
        current_row = self.events_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_events):
            event = self.current_events[current_row]
            
            details = f"""Event Details:

Event ID: {event.event_id}
Level: {event.level_display_name}
Source: {event.source}
Time Created: {event.time_created.strftime('%Y-%m-%d %H:%M:%S')}
Log Name: {event.log_name}
Task Category: {event.task_category}
Computer: {event.computer_name}
User: {event.user_id}

Message:
{event.message}
"""
            
            self.details_text.setPlainText(details)
    
    def export_events(self):
        """Export current events to file"""
        if not self.current_events:
            QMessageBox.information(self, "No Events", "No events to export.")
            return
        
        # Get export format
        format_dialog = QMessageBox()
        format_dialog.setWindowTitle("Export Format")
        format_dialog.setText("Choose export format:")
        
        detailed_btn = format_dialog.addButton("Detailed Text", QMessageBox.ButtonRole.ActionRole)
        simple_btn = format_dialog.addButton("Simple Text", QMessageBox.ButtonRole.ActionRole)
        csv_btn = format_dialog.addButton("CSV", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = format_dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        format_dialog.exec()
        clicked_button = format_dialog.clickedButton()
        
        if clicked_button == cancel_btn:
            return
        
        # Determine file extension and format
        if clicked_button == csv_btn:
            file_filter = "CSV Files (*.csv)"
            default_name = f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            export_format = "csv"
        else:
            file_filter = "Text Files (*.txt)"
            default_name = f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            export_format = "detailed" if clicked_button == detailed_btn else "simple"
        
        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Events", default_name, file_filter
        )
        
        if filename:
            try:
                if export_format == "csv":
                    success = self.event_log_manager.export_events_to_csv(self.current_events, filename)
                else:
                    success = self.event_log_manager.export_events_to_text(
                        self.current_events, filename, export_format
                    )
                
                if success:
                    QMessageBox.information(self, "Export Successful", 
                                          f"Events exported to:\n{filename}")
                else:
                    QMessageBox.warning(self, "Export Failed", 
                                      "Failed to export events. Check the file path and permissions.")
            
            except Exception as e:
                QMessageBox.critical(self, "Export Error", 
                                   f"Error exporting events:\n{str(e)}")
    
    def toggle_auto_refresh(self, enabled: bool):
        """Toggle auto-refresh functionality"""
        if enabled:
            self.auto_refresh_timer.start(30000)  # 30 seconds
            self.status_label.setText("Auto-refresh enabled")
        else:
            self.auto_refresh_timer.stop()
            self.status_label.setText("Auto-refresh disabled")
    
    def refresh_events(self):
        """Refresh events (called by auto-refresh timer)"""
        if self.load_btn.isEnabled():  # Only refresh if not currently loading
            self.load_events()
    
    def clear_events(self):
        """Clear the events table"""
        self.current_events = []
        self.events_table.setRowCount(0)
        self.details_text.clear()
        self.export_btn.setEnabled(False)
        self.event_count_label.setText("Events: 0")
        self.status_label.setText("Events cleared")
    
    def handle_operation_completed(self, operation: str, success: bool, message: str):
        """Handle completion of background operations"""
        if operation.startswith("export"):
            if success:
                self.status_label.setText("Export completed successfully")
            else:
                self.status_label.setText(f"Export failed: {message}")

class EventLogQuickActionsWidget(QWidget):
    """Widget for quick access to common event log queries"""
    
    def __init__(self):
        super().__init__()
        self.event_log_manager = EventLogManager()
        self.current_events = []
        self.setup_ui()
        
        # Connect signals
        self.event_log_manager.events_loaded.connect(self.display_results)
        self.event_log_manager.operation_completed.connect(self.handle_operation_completed)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Quick actions group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        self.system_errors_btn = QPushButton("Last 50 System Errors (24h)")
        self.system_errors_btn.clicked.connect(lambda: self.run_quick_query('system_errors'))
        button_layout.addWidget(self.system_errors_btn)
        
        self.app_errors_btn = QPushButton("Last 50 Application Errors (24h)")
        self.app_errors_btn.clicked.connect(lambda: self.run_quick_query('app_errors'))
        button_layout.addWidget(self.app_errors_btn)
        
        self.critical_events_btn = QPushButton("Critical Events (7 days)")
        self.critical_events_btn.clicked.connect(lambda: self.run_quick_query('critical'))
        button_layout.addWidget(self.critical_events_btn)
        
        self.warnings_btn = QPushButton("Recent Warnings (12h)")
        self.warnings_btn.clicked.connect(lambda: self.run_quick_query('warnings'))
        button_layout.addWidget(self.warnings_btn)
        
        self.security_events_btn = QPushButton("Security Events (24h)")
        self.security_events_btn.clicked.connect(lambda: self.run_quick_query('security'))
        button_layout.addWidget(self.security_events_btn)
        
        actions_layout.addLayout(button_layout)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self.quick_export_btn = QPushButton("Export Results")
        self.quick_export_btn.clicked.connect(self.export_results)
        self.quick_export_btn.setEnabled(False)
        export_layout.addWidget(self.quick_export_btn)
        
        actions_layout.addLayout(export_layout)
        layout.addWidget(actions_group)
        
        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        # Status and count
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready - Select a quick action above")
        self.count_label = QLabel("Results: 0")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.count_label)
        
        results_layout.addLayout(status_layout)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
    
    def run_quick_query(self, query_type: str):
        """Run a predefined quick query"""
        self.disable_buttons()
        self.status_label.setText("Loading...")
        
        if query_type == 'system_errors':
            self.current_events = self.event_log_manager.get_last_errors('System', 50, 24)
        elif query_type == 'app_errors':
            self.current_events = self.event_log_manager.get_last_errors('Application', 50, 24)
        elif query_type == 'critical':
            self.current_events = self.event_log_manager.get_critical_events(168)  # 7 days
        elif query_type == 'warnings':
            self.current_events = self.event_log_manager.get_events('System', EventLevel.WARNING, 12, 50)
        elif query_type == 'security':
            self.current_events = self.event_log_manager.get_events('Security', None, 24, 50)
        
        self.display_results(self.current_events)
    
    def display_results(self, events: List[EventLogEntry]):
        """Display query results"""
        self.current_events = events
        
        if not events:
            self.results_text.setPlainText("No events found matching the criteria.")
            self.status_label.setText("No events found")
            self.count_label.setText("Results: 0")
            self.quick_export_btn.setEnabled(False)
            self.enable_buttons()
            return
        
        # Format results for display
        results_text = f"Event Log Query Results\n"
        results_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        results_text += f"Total Events: {len(events)}\n"
        results_text += "=" * 80 + "\n\n"
        
        for i, event in enumerate(events, 1):
            results_text += f"{i:3d}. {event.time_created.strftime('%Y-%m-%d %H:%M:%S')} | "
            results_text += f"{event.level_display_name:11s} | "
            results_text += f"ID:{event.event_id:5d} | "
            results_text += f"{event.source[:30]:30s} | "
            results_text += f"{format_event_message(event.message, 80)}\n"
        
        self.results_text.setPlainText(results_text)
        self.status_label.setText("Query completed successfully")
        self.count_label.setText(f"Results: {len(events)}")
        self.quick_export_btn.setEnabled(True)
        self.enable_buttons()
    
    def export_results(self):
        """Export quick query results"""
        if not self.current_events:
            QMessageBox.information(self, "No Results", "No results to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Quick Query Results", 
            f"quick_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                success = self.event_log_manager.export_events_to_text(
                    self.current_events, filename, 'simple'
                )
                
                if success:
                    QMessageBox.information(self, "Export Successful", 
                                          f"Results exported to:\n{filename}")
                else:
                    QMessageBox.warning(self, "Export Failed", 
                                      "Failed to export results.")
            
            except Exception as e:
                QMessageBox.critical(self, "Export Error", 
                                   f"Error exporting results:\n{str(e)}")
    
    def disable_buttons(self):
        """Disable all action buttons"""
        self.system_errors_btn.setEnabled(False)
        self.app_errors_btn.setEnabled(False)
        self.critical_events_btn.setEnabled(False)
        self.warnings_btn.setEnabled(False)
        self.security_events_btn.setEnabled(False)
    
    def enable_buttons(self):
        """Enable all action buttons"""
        self.system_errors_btn.setEnabled(True)
        self.app_errors_btn.setEnabled(True)
        self.critical_events_btn.setEnabled(True)
        self.warnings_btn.setEnabled(True)
        self.security_events_btn.setEnabled(True)
    
    def handle_operation_completed(self, operation: str, success: bool, message: str):
        """Handle completion of background operations"""
        if operation.startswith("export"):
            if success:
                self.status_label.setText("Export completed successfully")
            else:
                self.status_label.setText(f"Export failed: {message}")
