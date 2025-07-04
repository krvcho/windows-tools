import sys
from typing import Dict, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLabel, QTextEdit,
                               QGroupBox, QComboBox, QMessageBox, QHeaderView,
                               QAbstractItemView, QSplitter, QFrame, QScrollArea,
                               QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QSize
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Services table container
        services_container = self.create_services_container()
        splitter.addWidget(services_container)
        
        # Output area container
        output_container = self.create_output_container()
        splitter.addWidget(output_container)
        
        layout.addWidget(splitter)
        
        # Set splitter proportions (70% table, 30% output)
        splitter.setSizes([500, 200])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
    
    def create_control_panel(self) -> QWidget:
        """Create the control panel with refresh and filter options"""
        panel = QFrame()
        panel.setObjectName("control-panel")
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(60)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status indicator
        self.status_label = QLabel("Monitoring Services...")
        self.status_label.setObjectName("status-label")
        self.status_label.setMinimumWidth(200)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Filter section
        filter_label = QLabel("Filter:")
        filter_label.setMinimumWidth(40)
        layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(150)
        self.filter_combo.addItems([
            "All Services",
            "Running Only",
            "Stopped Only",
            "Windows Update",
            "Network Services",
            "Security Services"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        layout.addWidget(self.filter_combo)
        
        # Control buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("primary-button")
        self.refresh_btn.setMinimumWidth(80)
        self.refresh_btn.clicked.connect(self.refresh_services)
        layout.addWidget(self.refresh_btn)
        
        # Auto-refresh toggle
        self.auto_refresh_btn = QPushButton("Auto: ON")
        self.auto_refresh_btn.setObjectName("info-button")
        self.auto_refresh_btn.setMinimumWidth(80)
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_btn)
        
        return panel
    
    def create_services_container(self) -> QWidget:
        """Create the services table container"""
        container = QGroupBox("Windows Services")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Services table
        self.services_table = QTableWidget()
        self.setup_services_table()
        layout.addWidget(self.services_table)
        
        # Service action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        # Selection info
        self.selection_label = QLabel("Select a service to manage")
        self.selection_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        action_layout.addWidget(self.selection_label)
        
        action_layout.addStretch()
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("success-button")
        self.start_btn.setMinimumWidth(80)
        self.start_btn.clicked.connect(self.start_selected_service)
        self.start_btn.setEnabled(False)
        action_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger-button")
        self.stop_btn.setMinimumWidth(80)
        self.stop_btn.clicked.connect(self.stop_selected_service)
        self.stop_btn.setEnabled(False)
        action_layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.setObjectName("warning-button")
        self.restart_btn.setMinimumWidth(80)
        self.restart_btn.clicked.connect(self.restart_selected_service)
        self.restart_btn.setEnabled(False)
        action_layout.addWidget(self.restart_btn)
        
        layout.addLayout(action_layout)
        return container
    
    def create_output_container(self) -> QWidget:
        """Create the output log container"""
        container = QGroupBox("Service Operations Log")
        layout = QVBoxLayout(container)
        
        self.output_text = QTextEdit()
        self.output_text.setObjectName("console")
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        self.output_text.setMaximumHeight(250)
        self.output_text.setPlainText("Service management ready...\n")
        layout.addWidget(self.output_text)
        
        # Clear log button
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.setMinimumWidth(80)
        self.clear_log_btn.clicked.connect(self.clear_log)
        clear_layout.addWidget(self.clear_log_btn)
        layout.addLayout(clear_layout)
        
        return container
    
    def setup_services_table(self):
        """Setup the services table widget"""
        headers = ["Service Name", "Display Name", "Status", "Startup", "PID", "Description"]
        self.services_table.setColumnCount(len(headers))
        self.services_table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.services_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setSortingEnabled(True)
        self.services_table.setShowGrid(True)
        self.services_table.setWordWrap(False)
        
        # Set minimum table size
        self.services_table.setMinimumHeight(300)
        
        # Set column widths for better visibility
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)      # Service Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)    # Display Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)      # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)      # Startup Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)      # PID
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)    # Description
        
        # Set specific column widths
        self.services_table.setColumnWidth(0, 120)  # Service Name
        self.services_table.setColumnWidth(2, 80)   # Status
        self.services_table.setColumnWidth(3, 80)   # Startup Type
        self.services_table.setColumnWidth(4, 60)   # PID
        
        # Set row height
        self.services_table.verticalHeader().setDefaultSectionSize(25)
        self.services_table.verticalHeader().setVisible(False)
        
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
        
        # Store current selection
        current_selection = self.get_selected_service()
        
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
            name_item.setToolTip(f"Service Name: {service_name}")
            self.services_table.setItem(row, 0, name_item)
            
            # Display Name
            display_item = QTableWidgetItem(service_info.display_name or service_name)
            display_item.setToolTip(service_info.display_name or service_name)
            self.services_table.setItem(row, 1, display_item)
            
            # Status
            status_item = QTableWidgetItem(service_info.status.value)
            status_color = self.get_status_color(service_info.status)
            status_item.setForeground(status_color)
            status_item.setToolTip(f"Status: {service_info.status.value}")
            self.services_table.setItem(row, 2, status_item)
            
            # Startup Type
            startup_item = QTableWidgetItem(service_info.start_type.value)
            startup_item.setToolTip(f"Startup Type: {service_info.start_type.value}")
            self.services_table.setItem(row, 3, startup_item)
            
            # PID
            pid_text = str(service_info.pid) if service_info.pid else "-"
            pid_item = QTableWidgetItem(pid_text)
            pid_item.setToolTip(f"Process ID: {pid_text}")
            if service_info.pid:
                pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.services_table.setItem(row, 4, pid_item)
            
            # Description
            description = service_info.description or "No description available"
            desc_item = QTableWidgetItem(description)
            desc_item.setToolTip(description)
            self.services_table.setItem(row, 5, desc_item)
        
        # Restore selection if possible
        if current_selection:
            self.select_service_by_name(current_selection)
        
        # Update status
        running_count = sum(1 for s in services.values() if s.status == ServiceStatus.RUNNING)
        total_count = len(services)
        filtered_count = len(filtered_services)
        
        if filtered_count != total_count:
            self.status_label.setText(f"Services: {running_count}/{total_count} running | Showing: {filtered_count}")
        else:
            self.status_label.setText(f"Services: {running_count}/{total_count} running")
    
    def select_service_by_name(self, service_name: str):
        """Select a service by name in the table"""
        for row in range(self.services_table.rowCount()):
            item = self.services_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == service_name:
                self.services_table.selectRow(row)
                break
    
    def get_filtered_services(self, services: Dict[str, ServiceInfo]) -> Dict[str, ServiceInfo]:
        """Apply current filter to services"""
        filter_text = self.filter_combo.currentText()
        
        if filter_text == "All Services":
            return services
        elif filter_text == "Running Only":
            return {k: v for k, v in services.items() if v.status == ServiceStatus.RUNNING}
        elif filter_text == "Stopped Only":
            return {k: v for k, v in services.items() if v.status == ServiceStatus.STOPPED}
        elif filter_text == "Windows Update":
            update_services = ['wuauserv', 'bits', 'cryptsvc', 'msiserver', 'trustedinstaller']
            return {k: v for k, v in services.items() if k.lower() in update_services}
        elif filter_text == "Network Services":
            network_services = ['lanmanserver', 'lanmanworkstation', 'dnscache', 'dhcp', 'netlogon', 'netman', 'nsi']
            return {k: v for k, v in services.items() if k.lower() in network_services}
        elif filter_text == "Security Services":
            security_services = ['mpssvc', 'windefend', 'wscsvc', 'wersvc']
            return {k: v for k, v in services.items() if k.lower() in security_services}
        
        return services
    
    def get_status_color(self, status: ServiceStatus) -> QColor:
        """Get color for service status"""
        if status == ServiceStatus.RUNNING:
            return QColor(39, 174, 96)  # Green
        elif status == ServiceStatus.STOPPED:
            return QColor(231, 76, 60)  # Red
        elif status in [ServiceStatus.START_PENDING, ServiceStatus.STOP_PENDING]:
            return QColor(243, 156, 18)  # Orange
        else:
            return QColor(149, 165, 166)  # Gray
    
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
            self.auto_refresh_btn.setText("Auto: ON")
            self.start_monitoring()
        else:
            self.auto_refresh_btn.setText("Auto: OFF")
            self.stop_monitoring()
    
    def on_service_selection_changed(self):
        """Handle service selection change"""
        selected_items = self.services_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            service_name = self.services_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            service_info = self.current_services.get(service_name)
            
            if service_info:
                # Update selection label
                self.selection_label.setText(f"Selected: {service_info.display_name}")
                self.selection_label.setStyleSheet("color: #2C3E50; font-weight: bold;")
                
                # Enable/disable buttons based on service status
                is_running = service_info.status == ServiceStatus.RUNNING
                is_stopped = service_info.status == ServiceStatus.STOPPED
                
                self.start_btn.setEnabled(is_stopped)
                self.stop_btn.setEnabled(is_running and service_info.can_stop)
                self.restart_btn.setEnabled(is_running)
        else:
            # No selection
            self.selection_label.setText("Select a service to manage")
            self.selection_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Service Startup Configuration")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Configure how services start with Windows")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Configuration container
        config_container = QGroupBox("Service Configuration")
        config_layout = QVBoxLayout(config_container)
        config_layout.setSpacing(15)
        
        # Service selection
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(10)
        
        selection_layout.addWidget(QLabel("Service:"))
        
        self.service_combo = QComboBox()
        self.service_combo.setMinimumWidth(300)
        self.populate_service_combo()
        selection_layout.addWidget(self.service_combo)
        
        selection_layout.addStretch()
        config_layout.addLayout(selection_layout)
        
        # Startup type selection
        startup_layout = QHBoxLayout()
        startup_layout.setSpacing(10)
        
        startup_layout.addWidget(QLabel("Startup Type:"))
        
        self.startup_combo = QComboBox()
        self.startup_combo.setMinimumWidth(150)
        self.startup_combo.addItems([
            "Automatic",
            "Manual", 
            "Disabled"
        ])
        startup_layout.addWidget(self.startup_combo)
        
        self.apply_btn = QPushButton("Apply Configuration")
        self.apply_btn.setObjectName("primary-button")
        self.apply_btn.setMinimumWidth(150)
        self.apply_btn.clicked.connect(self.apply_startup_config)
        startup_layout.addWidget(self.apply_btn)
        
        startup_layout.addStretch()
        config_layout.addLayout(startup_layout)
        
        layout.addWidget(config_container)
        
        # Output area
        output_container = QGroupBox("Configuration Log")
        output_layout = QVBoxLayout(output_container)
        
        self.config_output = QTextEdit()
        self.config_output.setObjectName("console")
        self.config_output.setReadOnly(True)
        self.config_output.setMinimumHeight(200)
        self.config_output.setPlainText("Ready to configure service startup types...\n")
        output_layout.addWidget(self.config_output)
        
        layout.addWidget(output_container)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def populate_service_combo(self):
        """Populate the service selection combo"""
        try:
            services = self.services_manager.get_all_important_services()
            for service_name, service_info in sorted(services.items(), key=lambda x: x[1].display_name or x[0]):
                display_text = f"{service_info.display_name or service_name} ({service_name})"
                self.service_combo.addItem(display_text, service_name)
        except Exception as e:
            self.config_output.append(f"Error loading services: {str(e)}")
    
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
