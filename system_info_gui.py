"""
System Information GUI Components
Provides widgets for displaying system information and real-time monitoring
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QProgressBar, QTableWidget, QTableWidgetItem,
                               QGroupBox, QGridLayout, QPushButton, QTextEdit,
                               QSplitter, QFrame, QScrollArea, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPalette, QColor

from system_info_manager import (SystemInfoManager, SystemInfo, SystemMetrics, 
                                SystemMonitorThread, format_bytes, format_uptime)

class SystemInfoWidget(QWidget):
    """Widget for displaying static system information"""
    
    def __init__(self):
        super().__init__()
        self.system_info_manager = SystemInfoManager()
        self.setup_ui()
        self.load_system_info()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create scroll area for system info
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Windows Information Group
        windows_group = QGroupBox("Windows Information")
        windows_layout = QGridLayout(windows_group)
        
        self.windows_version_label = QLabel("Loading...")
        self.windows_build_label = QLabel("Loading...")
        self.windows_edition_label = QLabel("Loading...")
        self.last_update_date_label = QLabel("Loading...")
        self.last_update_package_label = QLabel("Loading...")
        
        windows_layout.addWidget(QLabel("Version:"), 0, 0)
        windows_layout.addWidget(self.windows_version_label, 0, 1)
        windows_layout.addWidget(QLabel("Build:"), 1, 0)
        windows_layout.addWidget(self.windows_build_label, 1, 1)
        windows_layout.addWidget(QLabel("Edition:"), 2, 0)
        windows_layout.addWidget(self.windows_edition_label, 2, 1)
        windows_layout.addWidget(QLabel("Last Update:"), 3, 0)
        windows_layout.addWidget(self.last_update_date_label, 3, 1)
        windows_layout.addWidget(QLabel("Update Package:"), 4, 0)
        windows_layout.addWidget(self.last_update_package_label, 4, 1)
        
        scroll_layout.addWidget(windows_group)
        
        # System Information Group
        system_group = QGroupBox("System Information")
        system_layout = QGridLayout(system_group)
        
        self.computer_name_label = QLabel("Loading...")
        self.user_name_label = QLabel("Loading...")
        self.uptime_label = QLabel("Loading...")
        self.motherboard_label = QLabel("Loading...")
        self.bios_label = QLabel("Loading...")
        
        system_layout.addWidget(QLabel("Computer Name:"), 0, 0)
        system_layout.addWidget(self.computer_name_label, 0, 1)
        system_layout.addWidget(QLabel("User Name:"), 1, 0)
        system_layout.addWidget(self.user_name_label, 1, 1)
        system_layout.addWidget(QLabel("System Uptime:"), 2, 0)
        system_layout.addWidget(self.uptime_label, 2, 1)
        system_layout.addWidget(QLabel("Motherboard:"), 3, 0)
        system_layout.addWidget(self.motherboard_label, 3, 1)
        system_layout.addWidget(QLabel("BIOS:"), 4, 0)
        system_layout.addWidget(self.bios_label, 4, 1)
        
        scroll_layout.addWidget(system_group)
        
        # Hardware Information Group
        hardware_group = QGroupBox("Hardware Information")
        hardware_layout = QGridLayout(hardware_group)
        
        self.cpu_model_label = QLabel("Loading...")
        self.cpu_cores_label = QLabel("Loading...")
        self.total_ram_label = QLabel("Loading...")
        self.gpu_info_label = QLabel("Loading...")
        self.nvidia_driver_label = QLabel("Loading...")
        
        hardware_layout.addWidget(QLabel("CPU Model:"), 0, 0)
        hardware_layout.addWidget(self.cpu_model_label, 0, 1)
        hardware_layout.addWidget(QLabel("CPU Cores/Threads:"), 1, 0)
        hardware_layout.addWidget(self.cpu_cores_label, 1, 1)
        hardware_layout.addWidget(QLabel("Total RAM:"), 2, 0)
        hardware_layout.addWidget(self.total_ram_label, 2, 1)
        hardware_layout.addWidget(QLabel("Graphics Cards:"), 3, 0)
        hardware_layout.addWidget(self.gpu_info_label, 3, 1)
        hardware_layout.addWidget(QLabel("NVIDIA Driver:"), 4, 0)
        hardware_layout.addWidget(self.nvidia_driver_label, 4, 1)
        
        scroll_layout.addWidget(hardware_group)
        
        # Disk Information Group
        disk_group = QGroupBox("Disk Information")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(5)
        self.disk_table.setHorizontalHeaderLabels([
            "Drive", "File System", "Total Size", "Used Space", "Free Space"
        ])
        self.disk_table.horizontalHeader().setStretchLastSection(True)
        
        disk_layout.addWidget(self.disk_table)
        scroll_layout.addWidget(disk_group)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh System Information")
        self.refresh_btn.clicked.connect(self.load_system_info)
        refresh_layout.addWidget(self.refresh_btn)
        
        scroll_layout.addLayout(refresh_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
    
    def load_system_info(self):
        """Load and display system information"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Loading...")
        
        try:
            system_info = self.system_info_manager.get_complete_system_info()
            self.update_display(system_info)
        except Exception as e:
            print(f"Error loading system info: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("Refresh System Information")
    
    def update_display(self, system_info: SystemInfo):
        """Update the display with system information"""
        # Windows Information
        self.windows_version_label.setText(system_info.windows_version)
        self.windows_build_label.setText(system_info.windows_build)
        self.windows_edition_label.setText(system_info.windows_edition)
        self.last_update_date_label.setText(system_info.last_update_date)
        self.last_update_package_label.setText(system_info.last_update_package)
        
        # System Information
        self.computer_name_label.setText(system_info.computer_name)
        self.user_name_label.setText(system_info.user_name)
        self.uptime_label.setText(system_info.system_uptime)
        self.motherboard_label.setText(system_info.motherboard)
        self.bios_label.setText(system_info.bios_version)
        
        # Hardware Information
        self.cpu_model_label.setText(system_info.cpu_model)
        self.cpu_cores_label.setText(f"{system_info.cpu_cores} cores / {system_info.cpu_threads} threads")
        self.total_ram_label.setText(f"{system_info.total_ram_gb:.1f} GB")
        
        # GPU Information
        gpu_text = "\n".join(system_info.gpu_info)
        self.gpu_info_label.setText(gpu_text)
        self.nvidia_driver_label.setText(system_info.nvidia_driver_version)
        
        # Disk Information
        self.disk_table.setRowCount(len(system_info.disk_info))
        for i, disk in enumerate(system_info.disk_info):
            self.disk_table.setItem(i, 0, QTableWidgetItem(disk['device']))
            self.disk_table.setItem(i, 1, QTableWidgetItem(disk['fstype']))
            self.disk_table.setItem(i, 2, QTableWidgetItem(f"{disk['total_gb']:.1f} GB"))
            self.disk_table.setItem(i, 3, QTableWidgetItem(f"{disk['used_gb']:.1f} GB ({disk['percent_used']:.1f}%)"))
            self.disk_table.setItem(i, 4, QTableWidgetItem(f"{disk['free_gb']:.1f} GB"))

class RealTimeMonitorWidget(QWidget):
    """Widget for real-time system monitoring"""
    
    def __init__(self):
        super().__init__()
        self.system_info_manager = SystemInfoManager()
        self.monitor_thread = None
        self.monitoring_active = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.auto_refresh_checkbox = QCheckBox("Auto Refresh (2 seconds)")
        self.auto_refresh_checkbox.toggled.connect(self.toggle_monitoring)
        control_layout.addWidget(self.auto_refresh_checkbox)
        
        control_layout.addStretch()
        
        self.manual_refresh_btn = QPushButton("Manual Refresh")
        self.manual_refresh_btn.clicked.connect(self.manual_refresh)
        control_layout.addWidget(self.manual_refresh_btn)
        
        layout.addLayout(control_layout)
        
        # Metrics display
        metrics_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Usage meters
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # CPU Usage
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout(cpu_group)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        cpu_layout.addWidget(self.cpu_progress)
        cpu_layout.addWidget(self.cpu_label)
        left_layout.addWidget(cpu_group)
        
        # RAM Usage
        ram_group = QGroupBox("RAM Usage")
        ram_layout = QVBoxLayout(ram_group)
        
        self.ram_progress = QProgressBar()
        self.ram_progress.setRange(0, 100)
        self.ram_label = QLabel("0%")
        self.ram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ram_details_label = QLabel("0 GB / 0 GB")
        self.ram_details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ram_layout.addWidget(self.ram_progress)
        ram_layout.addWidget(self.ram_label)
        ram_layout.addWidget(self.ram_details_label)
        left_layout.addWidget(ram_group)
        
        # GPU Usage (NVIDIA only)
        gpu_group = QGroupBox("GPU Usage (NVIDIA)")
        gpu_layout = QVBoxLayout(gpu_group)
        
        self.gpu_progress = QProgressBar()
        self.gpu_progress.setRange(0, 100)
        self.gpu_label = QLabel("0%")
        self.gpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gpu_memory_label = QLabel("Memory: 0%")
        self.gpu_memory_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        gpu_layout.addWidget(self.gpu_progress)
        gpu_layout.addWidget(self.gpu_label)
        gpu_layout.addWidget(self.gpu_memory_label)
        left_layout.addWidget(gpu_group)
        
        left_layout.addStretch()
        metrics_splitter.addWidget(left_panel)
        
        # Right panel - Detailed information
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Disk Usage
        disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(2)
        self.disk_table.setHorizontalHeaderLabels(["Drive", "Usage %"])
        self.disk_table.horizontalHeader().setStretchLastSection(True)
        
        disk_layout.addWidget(self.disk_table)
        right_layout.addWidget(disk_group)
        
        # Network Activity
        network_group = QGroupBox("Network Activity")
        network_layout = QVBoxLayout(network_group)
        
        self.network_sent_label = QLabel("Sent: 0 MB/s")
        self.network_recv_label = QLabel("Received: 0 MB/s")
        
        network_layout.addWidget(self.network_sent_label)
        network_layout.addWidget(self.network_recv_label)
        right_layout.addWidget(network_group)
        
        # Temperature (if available)
        temp_group = QGroupBox("Temperature")
        temp_layout = QVBoxLayout(temp_group)
        
        self.cpu_temp_label = QLabel("CPU: Not available")
        
        temp_layout.addWidget(self.cpu_temp_label)
        right_layout.addWidget(temp_group)
        
        # System Status
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        
        self.last_update_label = QLabel("Last Update: Never")
        self.monitoring_status_label = QLabel("Monitoring: Stopped")
        
        status_layout.addWidget(self.last_update_label)
        status_layout.addWidget(self.monitoring_status_label)
        right_layout.addWidget(status_group)
        
        right_layout.addStretch()
        metrics_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        metrics_splitter.setSizes([300, 400])
        layout.addWidget(metrics_splitter)
        
        # Initial refresh
        self.manual_refresh()
    
    def toggle_monitoring(self, enabled: bool):
        """Toggle real-time monitoring"""
        if enabled:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = SystemMonitorThread(self.system_info_manager)
            self.monitor_thread.metrics_updated.connect(self.update_metrics)
            self.monitor_thread.start()
            self.monitoring_status_label.setText("Monitoring: Active")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread = None
            self.monitoring_status_label.setText("Monitoring: Stopped")
    
    def manual_refresh(self):
        """Manually refresh metrics"""
        try:
            metrics = self.system_info_manager.get_real_time_metrics()
            self.update_metrics(metrics)
        except Exception as e:
            print(f"Error during manual refresh: {e}")
    
    def update_metrics(self, metrics: SystemMetrics):
        """Update the display with new metrics"""
        try:
            # CPU Usage
            self.cpu_progress.setValue(int(metrics.cpu_usage))
            self.cpu_label.setText(f"{metrics.cpu_usage:.1f}%")
            
            # RAM Usage
            self.ram_progress.setValue(int(metrics.ram_usage))
            self.ram_label.setText(f"{metrics.ram_usage:.1f}%")
            self.ram_details_label.setText(f"{metrics.ram_used_gb:.1f} GB / {metrics.ram_used_gb + metrics.ram_available_gb:.1f} GB")
            
            # GPU Usage
            self.gpu_progress.setValue(int(metrics.gpu_usage))
            self.gpu_label.setText(f"{metrics.gpu_usage:.1f}%")
            self.gpu_memory_label.setText(f"Memory: {metrics.gpu_memory_usage:.1f}%")
            
            # Disk Usage
            self.disk_table.setRowCount(len(metrics.disk_usage))
            for i, (drive, usage) in enumerate(metrics.disk_usage.items()):
                self.disk_table.setItem(i, 0, QTableWidgetItem(drive))
                
                # Create progress bar for disk usage
                usage_item = QTableWidgetItem(f"{usage:.1f}%")
                if usage > 90:
                    usage_item.setBackground(QColor(255, 200, 200))  # Light red
                elif usage > 80:
                    usage_item.setBackground(QColor(255, 255, 200))  # Light yellow
                
                self.disk_table.setItem(i, 1, usage_item)
            
            # Network Activity
            self.network_sent_label.setText(f"Sent: {metrics.network_sent_mb:.2f} MB/s")
            self.network_recv_label.setText(f"Received: {metrics.network_recv_mb:.2f} MB/s")
            
            # Temperature
            if metrics.temperature_cpu is not None:
                self.cpu_temp_label.setText(f"CPU: {metrics.temperature_cpu:.1f}°C")
            else:
                self.cpu_temp_label.setText("CPU: Not available")
            
            # Last update time
            self.last_update_label.setText(f"Last Update: {metrics.timestamp.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error updating metrics display: {e}")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.stop_monitoring()
        super().closeEvent(event)

class SystemInfoTabWidget(QWidget):
    """Main widget containing both system info and real-time monitoring"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create splitter for two panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # System Information Panel
        info_widget = SystemInfoWidget()
        splitter.addWidget(info_widget)
        
        # Real-time Monitoring Panel
        monitor_widget = RealTimeMonitorWidget()
        splitter.addWidget(monitor_widget)
        
        # Set initial sizes (60% for info, 40% for monitoring)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
