import sys
from typing import Dict, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLabel, QTextEdit,
                               QGroupBox, QComboBox, QMessageBox, QHeaderView,
                               QAbstractItemView, QSplitter, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from services_manager import ServicesManager, ServiceInfo, ServiceStatus, ServiceStartType, ServiceMonitorThread
from admin_utils import AdminUtils

class ServicesStatusWidget(QWidget):
    """Widget for displaying and managing Windows services"""
    
    def __init__(self):
        super().__init__()
        self.services_manager = ServicesManager()
        self.admin_utils = AdminUtils()
        self.monitor_thread = None
        self.current_services = {}
        
        self.setup_ui()
        self.setup_connections()
        self.start_monitoring()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Services table
        services_group = QGroupBox("Windows Services")
        services_layout = QVBoxLayout(services_group)
        
        self.services_table = QTableWidget()
        self.setup_services_table()
        services_layout.addWidget(self.services_table)
        
        # Service action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.start_btn = QPushButton("Start Service")
        self.start_btn.setObjectName("success-button")
        self.start_btn.clicked.connect(self.start_selected_service)
        self.start_btn.setEnabled(False)
        action_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Service")
        self.stop_btn.setObjectName("danger-button")
        self.stop_btn.clicked.connect(self.stop_selected_service)
        self.stop_btn.setEnabled(False)
        action_layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("Restart Service")
        self.restart_btn.setObjectName("warning-button")
        self.restart_btn.clicked.connect(self.restart_selected_service)
        self.restart_btn.setEnabled(False)
        action_layout.addWidget(self.restart_btn)
        
        services_layout.addLayout(action_layout)
        splitter.addWidget(services_group)
        
        # Output area
        output_group = QGroupBox("Service Operations Log")
        output_layout = QVBoxLayout(output_group)
        
        self.output_text = QTextEdit()
        self.output_text.setObjectName("console")
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        self.output_text.setPlainText("Service management ready...\n")
        output_layout.addWidget(self.output_text)
        
        # Clear log button
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        clear_layout.addWidget(self.clear_log_btn)
        output_layout.addLayout(clear_layout)
        
        splitter.addWidget(output_group)
        layout.addWidget(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
    
    def create_control_panel(self) -> QWidget:
        """Create the control panel with refresh and filter options"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Status indicator
        self.status_label = QLabel("Monitoring Services...")
        self.status_label.setObjectName("status-label")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Filter combo
        layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Services",
            "Running Only",
            "Stopped Only",
            "Windows Update Services",
            "Network Services",
            "Security Services"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        layout.addWidget(self.filter_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("primary-button")
        self.refresh_btn.clicked.connect(self.refresh_services)
        layout.addWidget(self.refresh_btn)
        
        # Auto-refresh toggle
        self.auto_refresh_btn = QPushButton("Auto-Refresh: ON")
        self.auto_refresh_btn.setObjectName("info-button")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_btn)
        
        return panel
    
    def setup_services_table(self):
        """Setup the services table widget"""
        headers = ["Service Name", "Display Name", "Status", "Startup Type", "PID", "Description"]
        self.services_table.setColumnCount(len(headers))
        self.services_table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.services_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Service Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Display Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Startup Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # PID
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Description
        
        # Connect selection change
        self.services_table.itemSelectionChanged.connect(self.on_service_selection_changed)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.services_manager.operation_completed.connect(self.on_operation_completed)
    
    def start_monitoring(self):
        """Start the service monitoring thread"""
        if self.monitor_thread is None or not self.monitor_thread.isRunning():
            self.monitor_thread = ServiceMonitorThread(self.services_manager)
            self.monitor_thread.services_updated.connect(self.update_services_display)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the service monitoring thread"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread = None
    
    def update_services_display(self, services: Dict[str, ServiceInfo]):
        """Update the services table with new data"""
        self.current_services = services
        
        # Clear existing rows
        self.services_table.setRowCount(0)
        
        # Apply current filter
        filtered_services = self.get_filtered_services(services)
        
        # Populate table
        self.services_table.setRowCount(len(filtered_services))
        
        for row, (service_name, service_info) in enumerate(filtered_services.items()):
            # Service Name
            name_item = QTableWidgetItem(service_name)
            name_item.setData(Qt.ItemDataRole.UserRole, service_name)
            self.services_table.setItem(row, 0, name_item)
            
            # Display Name
            display_item = QTableWidgetItem(service_info.display_name)
            self.services_table.setItem(row, 1, display_item)
            
            # Status
            status_item = QTableWidgetItem(service_info.status.value)
            status_item.setForeground(self.get_status_color(service_info.status))
            self.services_table.setItem(row, 2, status_item)
            
            # Startup Type
            startup_item = QTableWidgetItem(service_info.start_type.value)
            self.services_table.setItem(row, 3, startup_item)
            
            # PID
            pid_text = str(service_info.pid) if service_info.pid else "-"
            pid_item = QTableWidgetItem(pid_text)
            self.services_table.setItem(row, 4, pid_item)
            
            # Description
            desc_item = QTableWidgetItem(service_info.description)
            desc_item.setToolTip(service_info.description)
            self.services_table.setItem(row, 5, desc_item)
        
        # Update status
        running_count = sum(1 for s in services.values() if s.status == ServiceStatus.RUNNING)
        total_count = len(services)
        self.status_label.setText(f"Services: {running_count}/{total_count} running")
    
    def get_filtered_services(self, services: Dict[str, ServiceInfo]) -> Dict[str, ServiceInfo]:
        """Apply current filter to services"""
        filter_text = self.filter_combo.currentText()
        
        if filter_text == "All Services":
            return services
        elif filter_text == "Running Only":
            return {k: v for k, v in services.items() if v.status == ServiceStatus.RUNNING}
        elif filter_text == "Stopped Only":
            return {k: v for k, v in services.items() if v.status == ServiceStatus.STOPPED}
        elif filter_text == "Windows Update Services":
            update_services = ['wuauserv', 'bits', 'cryptsvc', 'msiserver', 'trustedinstaller']
            return {k: v for k, v in services.items() if k in update_services}
        elif filter_text == "Network Services":
            network_services = ['lanmanserver', 'lanmanworkstation', 'dnscache', 'dhcp', 'netlogon', 'netman', 'nsi']
            return {k: v for k, v in services.items() if k in network_services}
        elif filter_text == "Security Services":
            security_services = ['mpssvc', 'windefend', 'wscsvc', 'wersvc']
            return {k: v for k, v in services.items() if k in security_services}
        
        return services
    
    def get_status_color(self, status: ServiceStatus) -> QColor:
        """Get color for service status"""
        if status == ServiceStatus.RUNNING:
            return QColor(0, 150, 0)  # Green
        elif status == ServiceStatus.STOPPED:
            return QColor(200, 0, 0)  # Red
        elif status in [ServiceStatus.START_PENDING, ServiceStatus.STOP_PENDING]:
            return QColor(255, 165, 0)  # Orange
        else:
            return QColor(128, 128, 128)  # Gray
    
    def apply_filter(self):
        """Apply the selected filter"""
        if self.current_services:
            self.update_services_display(self.current_services)
    
    def refresh_services(self):
        """Manually refresh services"""
        self.output_text.append("Refreshing services...")
        if self.monitor_thread and self.monitor_thread.isRunning():
            # Force an immediate update
            services = self.services_manager.get_all_important_services()
            self.update_services_display(services)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh monitoring"""
        if self.auto_refresh_btn.isChecked():
            self.auto_refresh_btn.setText("Auto-Refresh: ON")
            self.start_monitoring()
        else:
            self.auto_refresh_btn.setText("Auto-Refresh: OFF")
            self.stop_monitoring()
    
    def on_service_selection_changed(self):
        """Handle service selection change"""
        selected_items = self.services_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            service_name = self.services_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            service_info = self.current_services.get(service_name)
            
            if service_info:
                # Enable/disable buttons based on service status
                is_running = service_info.status == ServiceStatus.RUNNING
                is_stopped = service_info.status == ServiceStatus.STOPPED
                
                self.start_btn.setEnabled(is_stopped)
                self.stop_btn.setEnabled(is_running and service_info.can_stop)
                self.restart_btn.setEnabled(is_running)
        else:
            # No selection
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
    
    def get_selected_service(self) -> Optional[str]:
        """Get the currently selected service name"""
        selected_items = self.services_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            return self.services_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None
    
    def start_selected_service(self):
        """Start the selected service"""
        service_name = self.get_selected_service()
        if not service_name:
            return
        
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to start services.")
            return
        
        service_info = self.current_services.get(service_name)
        if service_info:
            reply = QMessageBox.question(
                self, "Confirm Start Service",
                f"Start service '{service_info.display_name}' ({service_name})?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.services_manager.start_service(service_name, self.output_text)
    
    def stop_selected_service(self):
        """Stop the selected service"""
        service_name = self.get_selected_service()
        if not service_name:
            return
        
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to stop services.")
            return
        
        service_info = self.current_services.get(service_name)
        if service_info:
            reply = QMessageBox.question(
                self, "Confirm Stop Service",
                f"Stop service '{service_info.display_name}' ({service_name})?\n\n"
                f"Warning: Stopping this service may affect system functionality.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.services_manager.stop_service(service_name, self.output_text)
    
    def restart_selected_service(self):
        """Restart the selected service"""
        service_name = self.get_selected_service()
        if not service_name:
            return
        
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to restart services.")
            return
        
        service_info = self.current_services.get(service_name)
        if service_info:
            reply = QMessageBox.question(
                self, "Confirm Restart Service",
                f"Restart service '{service_info.display_name}' ({service_name})?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.services_manager.restart_service(service_name, self.output_text)
    
    def on_operation_completed(self, operation: str, success: bool, message: str):
        """Handle service operation completion"""
        if success:
            self.output_text.append(f"✓ {operation.capitalize()} operation completed successfully")
        else:
            self.output_text.append(f"✗ {operation.capitalize()} operation failed: {message}")
        
        # Refresh the display after a short delay
        QTimer.singleShot(2000, self.refresh_services)
    
    def clear_log(self):
        """Clear the output log"""
        self.output_text.clear()
        self.output_text.append("Service management log cleared.\n")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.stop_monitoring()
        event.accept()

class ServiceConfigWidget(QWidget):
    """Widget for configuring service startup types"""
    
    def __init__(self):
        super().__init__()
        self.services_manager = ServicesManager()
        self.admin_utils = AdminUtils()
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Service Startup Configuration")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Configure how services start with Windows")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Service selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Service:"))
        
        self.service_combo = QComboBox()
        self.populate_service_combo()
        selection_layout.addWidget(self.service_combo)
        
        selection_layout.addWidget(QLabel("Startup Type:"))
        
        self.startup_combo = QComboBox()
        self.startup_combo.addItems([
            "Automatic",
            "Manual", 
            "Disabled"
        ])
        selection_layout.addWidget(self.startup_combo)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("primary-button")
        self.apply_btn.clicked.connect(self.apply_startup_config)
        selection_layout.addWidget(self.apply_btn)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)
        
        # Output area
        self.config_output = QTextEdit()
        self.config_output.setObjectName("console")
        self.config_output.setReadOnly(True)
        self.config_output.setPlainText("Ready to configure service startup types...\n")
        layout.addWidget(self.config_output)
    
    def populate_service_combo(self):
        """Populate the service selection combo"""
        services = self.services_manager.get_all_important_services()
        for service_name, service_info in services.items():
            display_text = f"{service_info.display_name} ({service_name})"
            self.service_combo.addItem(display_text, service_name)
    
    def apply_startup_config(self):
        """Apply the selected startup configuration"""
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to configure services.")
            return
        
        service_name = self.service_combo.currentData()
        startup_text = self.startup_combo.currentText()
        
        if not service_name:
            return
        
        # Map UI text to enum
        startup_map = {
            "Automatic": ServiceStartType.AUTOMATIC,
            "Manual": ServiceStartType.MANUAL,
            "Disabled": ServiceStartType.DISABLED
        }
        
        startup_type = startup_map.get(startup_text)
        if not startup_type:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Configuration Change",
            f"Set startup type for '{self.service_combo.currentText()}' to '{startup_text}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.services_manager.set_service_startup_type(
                service_name, startup_type, self.config_output
            )
            
            if success:
                QMessageBox.information(self, "Success", "Service startup type updated successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to update service startup type.")
