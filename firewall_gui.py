"""
GUI components for Windows Firewall management
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QLineEdit, QPushButton, QComboBox, 
                               QTextEdit, QTableWidget, QTableWidgetItem,
                               QTabWidget, QCheckBox, QSpinBox, QMessageBox,
                               QHeaderView, QAbstractItemView, QFileDialog,
                               QProgressBar, QSplitter)
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QFont, QColor, QIcon

from firewall_manager import (WindowsFirewallManager, FirewallProfile, RuleAction, 
                             RuleDirection, RuleProtocol, FirewallPresets, 
                             FirewallRuleBuilder)

class FirewallStatusWidget(QWidget):
    """Widget for displaying firewall status"""
    
    def __init__(self):
        super().__init__()
        self.firewall_manager = WindowsFirewallManager()
        self.setup_ui()
        self.refresh_status()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status overview
        status_group = QGroupBox("Firewall Status")
        status_layout = QVBoxLayout(status_group)
        
        # Profile status
        profiles_layout = QHBoxLayout()
        
        # Domain profile
        domain_group = QGroupBox("Domain Profile")
        domain_layout = QVBoxLayout(domain_group)
        self.domain_status = QLabel("Unknown")
        self.domain_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        domain_layout.addWidget(self.domain_status)
        
        self.domain_toggle = QPushButton("Toggle")
        self.domain_toggle.clicked.connect(lambda: self.toggle_profile(FirewallProfile.DOMAIN))
        domain_layout.addWidget(self.domain_toggle)
        
        profiles_layout.addWidget(domain_group)
        
        # Private profile
        private_group = QGroupBox("Private Profile")
        private_layout = QVBoxLayout(private_group)
        self.private_status = QLabel("Unknown")
        self.private_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        private_layout.addWidget(self.private_status)
        
        self.private_toggle = QPushButton("Toggle")
        self.private_toggle.clicked.connect(lambda: self.toggle_profile(FirewallProfile.PRIVATE))
        private_layout.addWidget(self.private_toggle)
        
        profiles_layout.addWidget(private_group)
        
        # Public profile
        public_group = QGroupBox("Public Profile")
        public_layout = QVBoxLayout(public_group)
        self.public_status = QLabel("Unknown")
        self.public_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        public_layout.addWidget(self.public_status)
        
        self.public_toggle = QPushButton("Toggle")
        self.public_toggle.clicked.connect(lambda: self.toggle_profile(FirewallProfile.PUBLIC))
        public_layout.addWidget(self.public_toggle)
        
        profiles_layout.addWidget(public_group)
        
        status_layout.addLayout(profiles_layout)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("Loading statistics...")
        stats_layout.addWidget(self.stats_label)
        
        status_layout.addWidget(stats_group)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh_status)
        controls_layout.addWidget(self.refresh_btn)
        
        self.reset_btn = QPushButton("Reset Firewall")
        self.reset_btn.clicked.connect(self.reset_firewall)
        controls_layout.addWidget(self.reset_btn)
        
        controls_layout.addStretch()
        status_layout.addLayout(controls_layout)
        
        layout.addWidget(status_group)
    
    def refresh_status(self):
        """Refresh firewall status display"""
        try:
            status = self.firewall_manager.get_firewall_status()
            stats = self.firewall_manager.get_firewall_statistics()
            
            # Update profile status
            self.domain_status.setText("ON" if status.domain_profile else "OFF")
            self.domain_status.setStyleSheet(
                "color: green;" if status.domain_profile else "color: red;"
            )
            
            self.private_status.setText("ON" if status.private_profile else "OFF")
            self.private_status.setStyleSheet(
                "color: green;" if status.private_profile else "color: red;"
            )
            
            self.public_status.setText("ON" if status.public_profile else "OFF")
            self.public_status.setStyleSheet(
                "color: green;" if status.public_profile else "color: red;"
            )
            
            # Update statistics
            stats_text = f"""
Total Rules: {stats.get('total_rules', 0)}
Enabled Rules: {stats.get('enabled_rules', 0)}
Inbound Rules: {stats.get('inbound_rules', 0)}
Outbound Rules: {stats.get('outbound_rules', 0)}
Recent Blocked: {stats.get('recent_blocked_connections', 0)}
            """.strip()
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            self.stats_label.setText(f"Error loading status: {str(e)}")
    
    def toggle_profile(self, profile: FirewallProfile):
        """Toggle firewall profile on/off"""
        try:
            current_status = self.firewall_manager.get_firewall_status()
            
            if profile == FirewallProfile.DOMAIN:
                new_state = not current_status.domain_profile
            elif profile == FirewallProfile.PRIVATE:
                new_state = not current_status.private_profile
            else:  # PUBLIC
                new_state = not current_status.public_profile
            
            success = self.firewall_manager.set_firewall_state(profile, new_state)
            
            if success:
                self.refresh_status()
                QMessageBox.information(
                    self, "Success", 
                    f"{profile.value.title()} profile {'enabled' if new_state else 'disabled'}"
                )
            else:
                QMessageBox.critical(
                    self, "Error", 
                    f"Failed to toggle {profile.value} profile"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error toggling profile: {str(e)}")
    
    def reset_firewall(self):
        """Reset firewall to default settings"""
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "This will reset Windows Firewall to default settings.\n"
            "All custom rules will be removed.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.firewall_manager.reset_firewall()
                if success:
                    self.refresh_status()
                    QMessageBox.information(self, "Success", "Firewall reset to defaults")
                else:
                    QMessageBox.critical(self, "Error", "Failed to reset firewall")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error resetting firewall: {str(e)}")

class FirewallRulesWidget(QWidget):
    """Widget for managing firewall rules"""
    
    def __init__(self):
        super().__init__()
        self.firewall_manager = WindowsFirewallManager()
        self.setup_ui()
        self.refresh_rules()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Rules")
        self.refresh_btn.clicked.connect(self.refresh_rules)
        controls_layout.addWidget(self.refresh_btn)
        
        self.add_rule_btn = QPushButton("Add Rule")
        self.add_rule_btn.clicked.connect(self.show_add_rule_dialog)
        controls_layout.addWidget(self.add_rule_btn)
        
        self.delete_rule_btn = QPushButton("Delete Selected")
        self.delete_rule_btn.clicked.connect(self.delete_selected_rule)
        controls_layout.addWidget(self.delete_rule_btn)
        
        # Filter controls
        controls_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Rules", "Inbound", "Outbound", "Enabled", "Disabled"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        controls_layout.addWidget(self.filter_combo)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(8)
        self.rules_table.setHorizontalHeaderLabels([
            "Name", "Enabled", "Direction", "Action", "Protocol", 
            "Local Port", "Remote Port", "Program"
        ])
        
        # Configure table
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.rules_table.setAlternatingRowColors(True)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rules_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.rules_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def refresh_rules(self):
        """Refresh firewall rules display"""
        try:
            self.status_label.setText("Loading rules...")
            rules = self.firewall_manager.get_firewall_rules()
            
            self.rules_table.setRowCount(len(rules))
            
            for row, rule in enumerate(rules):
                self.rules_table.setItem(row, 0, QTableWidgetItem(rule.name))
                
                enabled_item = QTableWidgetItem("Yes" if rule.enabled else "No")
                enabled_item.setForeground(QColor("green") if rule.enabled else QColor("red"))
                self.rules_table.setItem(row, 1, enabled_item)
                
                self.rules_table.setItem(row, 2, QTableWidgetItem(rule.direction.value.upper()))
                
                action_item = QTableWidgetItem(rule.action.value.upper())
                action_item.setForeground(QColor("green") if rule.action == RuleAction.ALLOW else QColor("red"))
                self.rules_table.setItem(row, 3, action_item)
                
                self.rules_table.setItem(row, 4, QTableWidgetItem(rule.protocol.value.upper()))
                self.rules_table.setItem(row, 5, QTableWidgetItem(rule.local_port))
                self.rules_table.setItem(row, 6, QTableWidgetItem(rule.remote_port))
                self.rules_table.setItem(row, 7, QTableWidgetItem(rule.program or "Any"))
            
            self.rules_table.resizeColumnsToContents()
            self.status_label.setText(f"Loaded {len(rules)} rules")
            
        except Exception as e:
            self.status_label.setText(f"Error loading rules: {str(e)}")
    
    def apply_filter(self, filter_text: str):
        """Apply filter to rules table"""
        for row in range(self.rules_table.rowCount()):
            show_row = True
            
            if filter_text == "Inbound":
                direction_item = self.rules_table.item(row, 2)
                show_row = direction_item and direction_item.text() == "IN"
            elif filter_text == "Outbound":
                direction_item = self.rules_table.item(row, 2)
                show_row = direction_item and direction_item.text() == "OUT"
            elif filter_text == "Enabled":
                enabled_item = self.rules_table.item(row, 1)
                show_row = enabled_item and enabled_item.text() == "Yes"
            elif filter_text == "Disabled":
                enabled_item = self.rules_table.item(row, 1)
                show_row = enabled_item and enabled_item.text() == "No"
            
            self.rules_table.setRowHidden(row, not show_row)
    
    def show_add_rule_dialog(self):
        """Show dialog to add new firewall rule"""
        dialog = AddFirewallRuleDialog(self)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            self.refresh_rules()
    
    def delete_selected_rule(self):
        """Delete selected firewall rule"""
        current_row = self.rules_table.currentRow()
        if current_row >= 0:
            rule_name_item = self.rules_table.item(current_row, 0)
            if rule_name_item:
                rule_name = rule_name_item.text()
                
                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Delete firewall rule '{rule_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        success = self.firewall_manager.delete_firewall_rule(rule_name)
                        if success:
                            self.refresh_rules()
                            self.status_label.setText(f"Deleted rule: {rule_name}")
                        else:
                            QMessageBox.critical(self, "Error", f"Failed to delete rule: {rule_name}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Error deleting rule: {str(e)}")
    
    def show_context_menu(self, position):
        """Show context menu for rules table"""
        # Implementation for context menu would go here
        pass

class AddFirewallRuleDialog(QMessageBox):
    """Dialog for adding new firewall rules"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.firewall_manager = WindowsFirewallManager()
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Add Firewall Rule")
        self.setModal(True)
        
        # Create custom widget for dialog content
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Rule name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Rule Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter rule name")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Direction
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Inbound", "Outbound"])
        direction_layout.addWidget(self.direction_combo)
        layout.addLayout(direction_layout)
        
        # Action
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Allow", "Block"])
        action_layout.addWidget(self.action_combo)
        layout.addLayout(action_layout)
        
        # Protocol
        protocol_layout = QHBoxLayout()
        protocol_layout.addWidget(QLabel("Protocol:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["Any", "TCP", "UDP", "ICMP"])
        protocol_layout.addWidget(self.protocol_combo)
        layout.addLayout(protocol_layout)
        
        # Local port
        local_port_layout = QHBoxLayout()
        local_port_layout.addWidget(QLabel("Local Port:"))
        self.local_port_edit = QLineEdit()
        self.local_port_edit.setPlaceholderText("Any or specific port (e.g., 80, 80-90)")
        local_port_layout.addWidget(self.local_port_edit)
        layout.addLayout(local_port_layout)
        
        # Remote port
        remote_port_layout = QHBoxLayout()
        remote_port_layout.addWidget(QLabel("Remote Port:"))
        self.remote_port_edit = QLineEdit()
        self.remote_port_edit.setPlaceholderText("Any or specific port")
        remote_port_layout.addWidget(self.remote_port_edit)
        layout.addLayout(remote_port_layout)
        
        # Program
        program_layout = QHBoxLayout()
        program_layout.addWidget(QLabel("Program:"))
        self.program_edit = QLineEdit()
        self.program_edit.setPlaceholderText("Optional: path to program")
        program_layout.addWidget(self.program_edit)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_program)
        program_layout.addWidget(self.browse_btn)
        layout.addLayout(program_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description")
        desc_layout.addWidget(self.description_edit)
        layout.addLayout(desc_layout)
        
        # Presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        self.presets_combo = QComboBox()
        self.presets_combo.addItem("Custom")
        
        presets = FirewallPresets.get_common_presets()
        for preset_name in presets.keys():
            self.presets_combo.addItem(preset_name)
        
        self.presets_combo.currentTextChanged.connect(self.load_preset)
        presets_layout.addWidget(self.presets_combo)
        layout.addLayout(presets_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("Add Rule")
        self.ok_btn.clicked.connect(self.add_rule)
        buttons_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Set the custom widget as the dialog content
        self.layout().addWidget(widget)
    
    def browse_program(self):
        """Browse for program executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Program", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.program_edit.setText(file_path)
    
    def load_preset(self, preset_name: str):
        """Load preset rule configuration"""
        if preset_name == "Custom":
            return
        
        presets = FirewallPresets.get_common_presets()
        if preset_name in presets:
            preset = presets[preset_name]
            
            self.name_edit.setText(preset.get('name', ''))
            
            direction = preset.get('direction', RuleDirection.INBOUND)
            self.direction_combo.setCurrentText(
                "Inbound" if direction == RuleDirection.INBOUND else "Outbound"
            )
            
            action = preset.get('action', RuleAction.BLOCK)
            self.action_combo.setCurrentText(
                "Allow" if action == RuleAction.ALLOW else "Block"
            )
            
            protocol = preset.get('protocol', RuleProtocol.ANY)
            protocol_text = protocol.value.upper() if protocol != RuleProtocol.ANY else "Any"
            self.protocol_combo.setCurrentText(protocol_text)
            
            self.local_port_edit.setText(preset.get('local_port', ''))
            self.remote_port_edit.setText(preset.get('remote_port', ''))
            self.description_edit.setText(preset.get('description', ''))
    
    def add_rule(self):
        """Add the firewall rule"""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Error", "Rule name is required")
                return
            
            direction = RuleDirection.INBOUND if self.direction_combo.currentText() == "Inbound" else RuleDirection.OUTBOUND
            action = RuleAction.ALLOW if self.action_combo.currentText() == "Allow" else RuleAction.BLOCK
            
            protocol_text = self.protocol_combo.currentText().lower()
            if protocol_text == "tcp":
                protocol = RuleProtocol.TCP
            elif protocol_text == "udp":
                protocol = RuleProtocol.UDP
            elif protocol_text == "icmp":
                protocol = RuleProtocol.ICMP
            else:
                protocol = RuleProtocol.ANY
            
            local_port = self.local_port_edit.text().strip() or "any"
            remote_port = self.remote_port_edit.text().strip() or "any"
            program = self.program_edit.text().strip()
            description = self.description_edit.text().strip()
            
            success = self.firewall_manager.add_firewall_rule(
                rule_name=name,
                direction=direction,
                action=action,
                protocol=protocol,
                local_port=local_port,
                remote_port=remote_port,
                program=program,
                description=description
            )
            
            if success:
                QMessageBox.information(self, "Success", f"Rule '{name}' added successfully")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", f"Failed to add rule '{name}'")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding rule: {str(e)}")

class FirewallMonitorWidget(QWidget):
    """Widget for monitoring firewall activity"""
    
    def __init__(self):
        super().__init__()
        self.firewall_manager = WindowsFirewallManager()
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.clicked.connect(self.start_monitoring)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.clear_log)
        controls_layout.addWidget(self.clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Blocked connections table
        blocked_group = QGroupBox("Recent Blocked Connections")
        blocked_layout = QVBoxLayout(blocked_group)
        
        self.blocked_table = QTableWidget()
        self.blocked_table.setColumnCount(6)
        self.blocked_table.setHorizontalHeaderLabels([
            "Timestamp", "Protocol", "Source IP", "Destination IP", 
            "Source Port", "Dest Port"
        ])
        blocked_layout.addWidget(self.blocked_table)
        
        layout.addWidget(blocked_group)
        
        # Monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_blocked_connections)
    
    def start_monitoring(self):
        """Start monitoring firewall activity"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.monitor_timer.start(2000)  # Update every 2 seconds
        self.update_blocked_connections()
    
    def stop_monitoring(self):
        """Stop monitoring firewall activity"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.monitor_timer.stop()
    
    def update_blocked_connections(self):
        """Update blocked connections display"""
        try:
            blocked = self.firewall_manager.get_blocked_connections()
            
            self.blocked_table.setRowCount(len(blocked))
            
            for row, connection in enumerate(blocked):
                self.blocked_table.setItem(row, 0, QTableWidgetItem(connection.get('timestamp', '')))
                self.blocked_table.setItem(row, 1, QTableWidgetItem(connection.get('protocol', '')))
                self.blocked_table.setItem(row, 2, QTableWidgetItem(connection.get('src_ip', '')))
                self.blocked_table.setItem(row, 3, QTableWidgetItem(connection.get('dst_ip', '')))
                self.blocked_table.setItem(row, 4, QTableWidgetItem(connection.get('src_port', '')))
                self.blocked_table.setItem(row, 5, QTableWidgetItem(connection.get('dst_port', '')))
            
            self.blocked_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating blocked connections: {e}")
    
    def clear_log(self):
        """Clear the blocked connections log"""
        self.blocked_table.setRowCount(0)
