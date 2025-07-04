import sys
import os
import subprocess
import threading
import time
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QTextEdit, QPushButton, 
                               QLabel, QComboBox, QMessageBox, QScrollArea, QGroupBox, QLineEdit)
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QFont, QPalette, QColor

from system_commands import SystemCommandRunner, SilentCommandRunner
from registry_manager import RegistryManager
from admin_utils import AdminUtils
from ui_styles import UIStyles
from network_tools import NetworkToolsManager
from firewall_gui import FirewallStatusWidget, FirewallRulesWidget, FirewallMonitorWidget
from cleanup_gui import CleanupLocationWidget, CleanupSchedulerWidget
from services_gui import ServicesStatusWidget, ServiceConfigWidget
from event_log_gui import EventLogViewerWidget, EventLogQuickActionsWidget
from system_info_gui import SystemInfoTabWidget
from log_export_manager import LogExportManager, add_export_button_to_layout

class SystemMaintenanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Maintenance Tools")
        self.setGeometry(100, 100, 1200, 900)  # Increased size for system info features
        
        # Initialize components
        self.admin_utils = AdminUtils()
        self.registry_manager = RegistryManager()
        self.command_runners = {}
        self.network_tools = NetworkToolsManager()
        self.log_export_manager = LogExportManager()
        self.silent_runner = SilentCommandRunner()
        
        # Check admin privileges
        self.check_admin_privileges()
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
    def check_admin_privileges(self):
        if not self.admin_utils.is_admin():
            reply = QMessageBox.warning(
                self, "Administrator Required",
                "This application requires administrator privileges to function properly.\n\n"
                "Please restart as administrator.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                sys.exit()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("System Maintenance Tools")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_sfc_tab()
        self.create_chkdsk_tab()
        self.create_dism_tab()
        self.create_registry_tab()
        self.create_network_tab()
        self.create_firewall_tab()
        self.create_cleanup_tab()
        self.create_services_tab()
        self.create_event_log_tab()
        self.create_system_info_tab()
    
    def create_sfc_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("System File Checker (SFC)")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Scans and repairs corrupted system files")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Output area
        self.sfc_output = QTextEdit()
        self.sfc_output.setObjectName("console")
        self.sfc_output.setReadOnly(True)
        self.sfc_output.setPlainText("Ready to run System File Checker...\n")
        layout.addWidget(self.sfc_output)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Add export button
        add_export_button_to_layout(button_layout, self.sfc_output, self, 
                                   self.log_export_manager, "sfc_log")
        
        self.sfc_run_btn = QPushButton("Run SFC /scannow")
        self.sfc_run_btn.setObjectName("primary-button")
        self.sfc_run_btn.clicked.connect(self.run_sfc)
        button_layout.addWidget(self.sfc_run_btn)
        
        self.sfc_stop_btn = QPushButton("Stop")
        self.sfc_stop_btn.setObjectName("danger-button")
        self.sfc_stop_btn.clicked.connect(self.stop_sfc)
        self.sfc_stop_btn.setEnabled(False)
        button_layout.addWidget(self.sfc_stop_btn)
        
        layout.addLayout(button_layout)
        self.tab_widget.addTab(tab, "System File Checker")
    
    def create_chkdsk_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("Disk Check (CHKDSK)")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Checks and repairs disk errors")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Drive selection
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Select Drive:"))
        
        self.drive_combo = QComboBox()
        self.populate_drives()
        drive_layout.addWidget(self.drive_combo)
        drive_layout.addStretch()
        
        layout.addLayout(drive_layout)
        
        # Output area
        self.chkdsk_output = QTextEdit()
        self.chkdsk_output.setObjectName("console")
        self.chkdsk_output.setReadOnly(True)
        self.chkdsk_output.setPlainText("Ready to run Disk Check...\n")
        layout.addWidget(self.chkdsk_output)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Add export button
        add_export_button_to_layout(button_layout, self.chkdsk_output, self, 
                                   self.log_export_manager, "chkdsk_log")
        
        self.chkdsk_run_btn = QPushButton("Run CHKDSK /f /r")
        self.chkdsk_run_btn.setObjectName("success-button")
        self.chkdsk_run_btn.clicked.connect(self.run_chkdsk)
        button_layout.addWidget(self.chkdsk_run_btn)
        
        self.chkdsk_stop_btn = QPushButton("Stop")
        self.chkdsk_stop_btn.setObjectName("danger-button")
        self.chkdsk_stop_btn.clicked.connect(self.stop_chkdsk)
        self.chkdsk_stop_btn.setEnabled(False)
        button_layout.addWidget(self.chkdsk_stop_btn)
        
        layout.addLayout(button_layout)
        self.tab_widget.addTab(tab, "Disk Check")
    
    def create_dism_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("DISM System Image Repair")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Repairs Windows system image corruption and prepares system for SFC scan")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # DISM options section
        options_layout = QHBoxLayout()
        
        # Checkhealth button
        self.dism_checkhealth_btn = QPushButton("Check Image Health")
        self.dism_checkhealth_btn.setObjectName("info-button")
        self.dism_checkhealth_btn.clicked.connect(self.run_dism_checkhealth)
        options_layout.addWidget(self.dism_checkhealth_btn)
        
        # Scanhealth button  
        self.dism_scanhealth_btn = QPushButton("Scan Image Health")
        self.dism_scanhealth_btn.setObjectName("warning-button")
        self.dism_scanhealth_btn.clicked.connect(self.run_dism_scanhealth)
        options_layout.addWidget(self.dism_scanhealth_btn)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Output area
        self.dism_output = QTextEdit()
        self.dism_output.setObjectName("console")
        self.dism_output.setReadOnly(True)
        self.dism_output.setPlainText("Ready to run DISM commands...\n")
        layout.addWidget(self.dism_output)
        
        # Main action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Add export button
        add_export_button_to_layout(button_layout, self.dism_output, self, 
                                   self.log_export_manager, "dism_log")
        
        self.dism_run_btn = QPushButton("Run DISM /RestoreHealth")
        self.dism_run_btn.setObjectName("success-button")
        self.dism_run_btn.clicked.connect(self.run_dism_restorehealth)
        button_layout.addWidget(self.dism_run_btn)
        
        self.dism_stop_btn = QPushButton("Stop")
        self.dism_stop_btn.setObjectName("danger-button")
        self.dism_stop_btn.clicked.connect(self.stop_dism)
        self.dism_stop_btn.setEnabled(False)
        button_layout.addWidget(self.dism_stop_btn)
        
        layout.addLayout(button_layout)
        self.tab_widget.addTab(tab, "DISM Repair")
    
    def create_registry_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("Windows Update Registry Tweaks")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Disable automatic Windows updates and related services")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Output area
        self.registry_output = QTextEdit()
        self.registry_output.setObjectName("console")
        self.registry_output.setReadOnly(True)
        self.registry_output.setPlainText("Ready to apply registry tweaks...\n")
        layout.addWidget(self.registry_output)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Add export button
        add_export_button_to_layout(button_layout, self.registry_output, self, 
                                   self.log_export_manager, "registry_log")
        
        self.disable_updates_btn = QPushButton("Disable Windows Updates")
        self.disable_updates_btn.setObjectName("warning-button")
        self.disable_updates_btn.clicked.connect(self.disable_updates)
        button_layout.addWidget(self.disable_updates_btn)
        
        self.enable_updates_btn = QPushButton("Enable Windows Updates")
        self.enable_updates_btn.setObjectName("info-button")
        self.enable_updates_btn.clicked.connect(self.enable_updates)
        button_layout.addWidget(self.enable_updates_btn)
        
        layout.addLayout(button_layout)
        self.tab_widget.addTab(tab, "Registry Tweaks")
    
    def create_network_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("Network Diagnostic Tools")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Network connectivity testing, routing analysis, and configuration tools")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Network tools section
        tools_layout = QHBoxLayout()
        
        # Ping section
        ping_group = QGroupBox("Ping Test")
        ping_layout = QVBoxLayout(ping_group)
        
        ping_input_layout = QHBoxLayout()
        ping_input_layout.addWidget(QLabel("Target:"))
        self.ping_target = QLineEdit()
        self.ping_target.setPlaceholderText("google.com or 8.8.8.8")
        self.ping_target.setText("google.com")
        ping_input_layout.addWidget(self.ping_target)
        
        ping_count_layout = QHBoxLayout()
        ping_count_layout.addWidget(QLabel("Count:"))
        self.ping_count = QComboBox()
        self.ping_count.addItems(["4", "10", "20", "Continuous"])
        ping_count_layout.addWidget(self.ping_count)
        ping_count_layout.addStretch()
        
        ping_layout.addLayout(ping_input_layout)
        ping_layout.addLayout(ping_count_layout)
        
        self.ping_btn = QPushButton("Start Ping")
        self.ping_btn.setObjectName("primary-button")
        self.ping_btn.clicked.connect(self.run_ping)
        ping_layout.addWidget(self.ping_btn)
        
        self.ping_stop_btn = QPushButton("Stop")
        self.ping_stop_btn.setObjectName("danger-button")
        self.ping_stop_btn.clicked.connect(self.stop_ping)
        self.ping_stop_btn.setEnabled(False)
        ping_layout.addWidget(self.ping_stop_btn)
        
        tools_layout.addWidget(ping_group)
        
        # Traceroute section
        tracert_group = QGroupBox("Traceroute")
        tracert_layout = QVBoxLayout(tracert_group)
        
        tracert_input_layout = QHBoxLayout()
        tracert_input_layout.addWidget(QLabel("Target:"))
        self.tracert_target = QLineEdit()
        self.tracert_target.setPlaceholderText("google.com")
        self.tracert_target.setText("google.com")
        tracert_input_layout.addWidget(self.tracert_target)
        
        tracert_layout.addLayout(tracert_input_layout)
        
        self.tracert_btn = QPushButton("Start Traceroute")
        self.tracert_btn.setObjectName("success-button")
        self.tracert_btn.clicked.connect(self.run_tracert)
        tracert_layout.addWidget(self.tracert_btn)
        
        self.tracert_stop_btn = QPushButton("Stop")
        self.tracert_stop_btn.setObjectName("danger-button")
        self.tracert_stop_btn.clicked.connect(self.stop_tracert)
        self.tracert_stop_btn.setEnabled(False)
        tracert_layout.addWidget(self.tracert_stop_btn)
        
        tools_layout.addWidget(tracert_group)
        
        # Quick tools section
        quick_tools_group = QGroupBox("Quick Tools")
        quick_tools_layout = QVBoxLayout(quick_tools_group)
        
        self.ipconfig_btn = QPushButton("IP Configuration")
        self.ipconfig_btn.setObjectName("info-button")
        self.ipconfig_btn.clicked.connect(self.run_ipconfig)
        quick_tools_layout.addWidget(self.ipconfig_btn)
        
        self.netstat_btn = QPushButton("Network Statistics")
        self.netstat_btn.setObjectName("warning-button")
        self.netstat_btn.clicked.connect(self.run_netstat)
        quick_tools_layout.addWidget(self.netstat_btn)
        
        self.dns_flush_btn = QPushButton("Flush DNS Cache")
        self.dns_flush_btn.setObjectName("info-button")
        self.dns_flush_btn.clicked.connect(self.flush_dns)
        quick_tools_layout.addWidget(self.dns_flush_btn)
        
        self.network_reset_btn = QPushButton("Reset Network")
        self.network_reset_btn.setObjectName("warning-button")
        self.network_reset_btn.clicked.connect(self.reset_network)
        quick_tools_layout.addWidget(self.network_reset_btn)
        
        tools_layout.addWidget(quick_tools_group)
        layout.addLayout(tools_layout)
        
        # Output area
        self.network_output = QTextEdit()
        self.network_output.setObjectName("console")
        self.network_output.setReadOnly(True)
        self.network_output.setPlainText("Ready to run network diagnostics...\n")
        layout.addWidget(self.network_output)
        
        # Clear output and export buttons
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        
        # Add export button
        add_export_button_to_layout(clear_layout, self.network_output, self, 
                                   self.log_export_manager, "network_log")
        
        self.clear_network_btn = QPushButton("Clear Output")
        self.clear_network_btn.clicked.connect(self.clear_network_output)
        clear_layout.addWidget(self.clear_network_btn)
        
        layout.addLayout(clear_layout)
        self.tab_widget.addTab(tab, "Network Tools")
    
    def create_firewall_tab(self):
        """Create the Windows Firewall management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("Windows Firewall Management")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Manage Windows Firewall settings, rules, and monitor network activity")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Create firewall sub-tabs
        firewall_tabs = QTabWidget()
        
        # Status tab
        self.firewall_status_widget = FirewallStatusWidget()
        firewall_tabs.addTab(self.firewall_status_widget, "Status & Control")
        
        # Rules management tab
        self.firewall_rules_widget = FirewallRulesWidget()
        firewall_tabs.addTab(self.firewall_rules_widget, "Rules Management")
        
        # Activity monitor tab
        self.firewall_monitor_widget = FirewallMonitorWidget()
        firewall_tabs.addTab(self.firewall_monitor_widget, "Activity Monitor")
        
        layout.addWidget(firewall_tabs)
        self.tab_widget.addTab(tab, "Firewall")
    
    def create_cleanup_tab(self):
        """Create the System Cleanup tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("System Cleanup")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Clean temporary files, cache, Recycle Bin, and free up disk space")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Create cleanup sub-tabs
        cleanup_tabs = QTabWidget()
        
        # Cleanup locations tab
        self.cleanup_locations_widget = CleanupLocationWidget()
        cleanup_tabs.addTab(self.cleanup_locations_widget, "Disk Cleanup")
        
        # Scheduler tab
        self.cleanup_scheduler_widget = CleanupSchedulerWidget()
        cleanup_tabs.addTab(self.cleanup_scheduler_widget, "Scheduler")
        
        layout.addWidget(cleanup_tabs)
        self.tab_widget.addTab(tab, "System Cleanup")

    def create_services_tab(self):
        """Create the Windows Services management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("Windows Services Management")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("Monitor and control Windows services including Windows Update, network, and system services")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Create services sub-tabs
        services_tabs = QTabWidget()
        
        # Services status and control tab
        self.services_status_widget = ServicesStatusWidget()
        services_tabs.addTab(self.services_status_widget, "Service Control")
        
        # Service configuration tab
        self.service_config_widget = ServiceConfigWidget()
        services_tabs.addTab(self.service_config_widget, "Startup Configuration")
        
        layout.addWidget(services_tabs)
        self.tab_widget.addTab(tab, "Services")
    
    def create_event_log_tab(self):
        """Create the Event Log Viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("Windows Event Log Viewer")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("View, filter, and export Windows event logs including System, Application, and Security logs")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Create event log sub-tabs
        event_log_tabs = QTabWidget()
        
        # Event log viewer tab
        self.event_log_viewer_widget = EventLogViewerWidget()
        event_log_tabs.addTab(self.event_log_viewer_widget, "Event Log Viewer")
        
        # Quick actions tab
        self.event_log_quick_actions_widget = EventLogQuickActionsWidget()
        event_log_tabs.addTab(self.event_log_quick_actions_widget, "Quick Actions")
        
        layout.addWidget(event_log_tabs)
        self.tab_widget.addTab(tab, "Event Logs")
    
    def create_system_info_tab(self):
        """Create the System Information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title and description
        title = QLabel("System Information & Monitoring")
        title.setObjectName("tab-title")
        layout.addWidget(title)
        
        desc = QLabel("View detailed system information and monitor real-time performance metrics")
        desc.setObjectName("description")
        layout.addWidget(desc)
        
        # Create system info widget
        self.system_info_widget = SystemInfoTabWidget()
        layout.addWidget(self.system_info_widget)
        
        self.tab_widget.addTab(tab, "System Info")
    
    def populate_drives(self):
        import psutil
        drives = []
        for partition in psutil.disk_partitions():
            if 'fixed' in partition.opts:
                drives.append(partition.device.replace('\\', ''))
        
        self.drive_combo.addItems(drives)
    
    def apply_styles(self):
        self.setStyleSheet(UIStyles.get_stylesheet())
    
    # SFC Commands
    def run_sfc(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to run SFC.")
            return
        
        self.sfc_run_btn.setEnabled(False)
        self.sfc_stop_btn.setEnabled(True)
        self.sfc_output.clear()
        self.sfc_output.append("Starting System File Checker...")
        
        self.command_runners['sfc'] = SystemCommandRunner(
            'sfc', '/scannow', self.sfc_output
        )
        self.command_runners['sfc'].finished.connect(self.sfc_finished)
        self.command_runners['sfc'].start()
    
    def stop_sfc(self):
        if 'sfc' in self.command_runners:
            self.command_runners['sfc'].stop()
            self.sfc_output.append("\nProcess terminated by user.")
    
    def sfc_finished(self):
        self.sfc_run_btn.setEnabled(True)
        self.sfc_stop_btn.setEnabled(False)
    
    # CHKDSK Commands
    def run_chkdsk(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to run CHKDSK.")
            return
        
        selected_drive = self.drive_combo.currentText()
        if not selected_drive:
            QMessageBox.warning(self, "Error", "Please select a drive to check.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm CHKDSK",
            f"CHKDSK will check drive {selected_drive} and may require a system restart.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.chkdsk_run_btn.setEnabled(False)
        self.chkdsk_stop_btn.setEnabled(True)
        self.chkdsk_output.clear()
        self.chkdsk_output.append(f"Starting Disk Check on drive {selected_drive}...")
        
        self.command_runners['chkdsk'] = SystemCommandRunner(
            'chkdsk', f'{selected_drive} /f /r', self.chkdsk_output
        )
        self.command_runners['chkdsk'].finished.connect(self.chkdsk_finished)
        self.command_runners['chkdsk'].start()
    
    def stop_chkdsk(self):
        if 'chkdsk' in self.command_runners:
            self.command_runners['chkdsk'].stop()
            self.chkdsk_output.append("\nProcess terminated by user.")
    
    def chkdsk_finished(self):
        self.chkdsk_run_btn.setEnabled(True)
        self.chkdsk_stop_btn.setEnabled(False)
    
    # DISM Commands
    def run_dism_checkhealth(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to run DISM.")
            return
        
        self.dism_checkhealth_btn.setEnabled(False)
        self.dism_output.clear()
        self.dism_output.append("Running DISM check health...")
        
        self.command_runners['dism_check'] = SystemCommandRunner(
            'dism', '/online /cleanup-image /checkhealth', self.dism_output
        )
        self.command_runners['dism_check'].finished.connect(self.dism_checkhealth_finished)
        self.command_runners['dism_check'].start()

    def run_dism_scanhealth(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to run DISM.")
            return
        
        self.dism_scanhealth_btn.setEnabled(False)
        self.dism_output.clear()
        self.dism_output.append("Running DISM scan health (this may take several minutes)...")
        
        self.command_runners['dism_scan'] = SystemCommandRunner(
            'dism', '/online /cleanup-image /scanhealth', self.dism_output
        )
        self.command_runners['dism_scan'].finished.connect(self.dism_scanhealth_finished)
        self.command_runners['dism_scan'].start()

    def run_dism_restorehealth(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to run DISM.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm DISM Restore Health",
            "DISM /RestoreHealth will attempt to repair Windows system image corruption.\n"
            "This process may take 15-30 minutes and requires internet connection.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.dism_run_btn.setEnabled(False)
        self.dism_stop_btn.setEnabled(True)
        self.dism_checkhealth_btn.setEnabled(False)
        self.dism_scanhealth_btn.setEnabled(False)
        self.dism_output.clear()
        self.dism_output.append("Starting DISM restore health (this may take 15-30 minutes)...")
        
        self.command_runners['dism'] = SystemCommandRunner(
            'dism', '/online /cleanup-image /restorehealth', self.dism_output
        )
        self.command_runners['dism'].finished.connect(self.dism_finished)
        self.command_runners['dism'].start()

    def stop_dism(self):
        if 'dism' in self.command_runners:
            self.command_runners['dism'].stop()
            self.dism_output.append("\nDISM process terminated by user.")

    def dism_checkhealth_finished(self):
        self.dism_checkhealth_btn.setEnabled(True)

    def dism_scanhealth_finished(self):
        self.dism_scanhealth_btn.setEnabled(True)

    def dism_finished(self):
        self.dism_run_btn.setEnabled(True)
        self.dism_stop_btn.setEnabled(False)
        self.dism_checkhealth_btn.setEnabled(True)
        self.dism_scanhealth_btn.setEnabled(True)
        
        # Suggest running SFC after DISM
        reply = QMessageBox.question(
            self, "DISM Completed",
            "DISM restore health has completed.\n\n"
            "It's recommended to run SFC /scannow after DISM to verify system file integrity.\n\n"
            "Would you like to switch to the SFC tab?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tab_widget.setCurrentIndex(0)  # Switch to SFC tab
    
    # Registry Commands
    def disable_updates(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to modify registry.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Registry Changes",
            "This will disable Windows automatic updates, Delivery Optimization, and Windows Store auto updates.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.registry_output.clear()
        self.registry_output.append("Disabling Windows Updates...")
        
        try:
            self.registry_manager.disable_windows_updates(self.registry_output)
            self.registry_output.append("✓ Windows Updates disabled successfully!")
            QMessageBox.information(self, "Success", "Windows Updates have been disabled successfully.")
        except Exception as e:
            self.registry_output.append(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error applying registry changes: {str(e)}")
    
    def enable_updates(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to modify registry.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Registry Changes",
            "This will re-enable Windows automatic updates and related services.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.registry_output.clear()
        self.registry_output.append("Enabling Windows Updates...")
        
        try:
            self.registry_manager.enable_windows_updates(self.registry_output)
            self.registry_output.append("✓ Windows Updates enabled successfully!")
            QMessageBox.information(self, "Success", "Windows Updates have been enabled successfully.")
        except Exception as e:
            self.registry_output.append(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error applying registry changes: {str(e)}")

    # Network Commands
    def run_ping(self):
        target = self.ping_target.text().strip()
        if not target:
            QMessageBox.warning(self, "Error", "Please enter a target to ping.")
            return
        
        count = self.ping_count.currentText()
        if count == "Continuous":
            args = f"-t {target}"
        else:
            args = f"-n {count} {target}"
        
        self.ping_btn.setEnabled(False)
        self.ping_stop_btn.setEnabled(True)
        self.network_output.append(f"\n=== Starting Ping to {target} ===")
        
        self.command_runners['ping'] = SystemCommandRunner(
            'ping', args, self.network_output
        )
        self.command_runners['ping'].finished.connect(self.ping_finished)
        self.command_runners['ping'].start()

    def stop_ping(self):
        if 'ping' in self.command_runners:
            self.command_runners['ping'].stop()
            self.network_output.append("\nPing terminated by user.")

    def ping_finished(self):
        self.ping_btn.setEnabled(True)
        self.ping_stop_btn.setEnabled(False)

    def run_tracert(self):
        target = self.tracert_target.text().strip()
        if not target:
            QMessageBox.warning(self, "Error", "Please enter a target for traceroute.")
            return
        
        self.tracert_btn.setEnabled(False)
        self.tracert_stop_btn.setEnabled(True)
        self.network_output.append(f"\n=== Starting Traceroute to {target} ===")
        
        self.command_runners['tracert'] = SystemCommandRunner(
            'tracert', target, self.network_output
        )
        self.command_runners['tracert'].finished.connect(self.tracert_finished)
        self.command_runners['tracert'].start()

    def stop_tracert(self):
        if 'tracert' in self.command_runners:
            self.command_runners['tracert'].stop()
            self.network_output.append("\nTraceroute terminated by user.")

    def tracert_finished(self):
        self.tracert_btn.setEnabled(True)
        self.tracert_stop_btn.setEnabled(False)

    def run_ipconfig(self):
        self.network_output.append("\n=== IP Configuration ===")
        
        self.command_runners['ipconfig'] = SystemCommandRunner(
            'ipconfig', '/all', self.network_output
        )
        self.command_runners['ipconfig'].start()

    def run_netstat(self):
        self.network_output.append("\n=== Network Statistics ===")
        
        self.command_runners['netstat'] = SystemCommandRunner(
            'netstat', '-an', self.network_output
        )
        self.command_runners['netstat'].start()

    def flush_dns(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to flush DNS cache.")
            return
        
        self.network_output.append("\n=== Flushing DNS Cache ===")
        
        # Use silent runner for DNS flush to avoid cmd window
        result = self.silent_runner.run_silent_command('ipconfig', '/flushdns')
        
        if result['success']:
            self.network_output.append("DNS cache flushed successfully.")
            self.network_output.append(result['stdout'])
        else:
            self.network_output.append(f"Error flushing DNS cache: {result['stderr']}")

    def reset_network(self):
        if not self.admin_utils.is_admin():
            QMessageBox.critical(self, "Error", "Administrator privileges required to reset network.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Network Reset",
            "This will reset network adapters and may temporarily disconnect your internet.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.network_output.append("\n=== Resetting Network Configuration ===")
        
        # Run multiple network reset commands using silent runner
        commands = [
            ('netsh', 'winsock reset'),
            ('netsh', 'int ip reset'),
            ('ipconfig', '/release'),
            ('ipconfig', '/renew'),
            ('ipconfig', '/flushdns')
        ]
        
        for cmd, args in commands:
            self.network_output.append(f"Running: {cmd} {args}")
            result = self.silent_runner.run_silent_command(cmd, args, timeout=60)
            
            if result['success']:
                self.network_output.append("✓ Command completed successfully")
                if result['stdout'].strip():
                    self.network_output.append(result['stdout'])
            else:
                self.network_output.append(f"✗ Command failed: {result['stderr']}")
        
        self.network_output.append("\nNetwork reset completed. You may need to restart your computer.")

    def clear_network_output(self):
        self.network_output.clear()
        self.network_output.append("Network diagnostics output cleared.\n")

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("System Maintenance Tools")
    app.setApplicationVersion("1.0")
    
    window = SystemMaintenanceApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
