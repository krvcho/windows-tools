"""
GUI components for network tools
Advanced network diagnostic interface components
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QLineEdit, QPushButton, QComboBox, 
                               QTextEdit, QTableWidget, QTableWidgetItem,
                               QTabWidget, QProgressBar, QCheckBox, QSpinBox)
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from network_tools import NetworkToolsManager, NetworkDiagnostics

class NetworkSpeedTestWidget(QWidget):
    """Widget for network speed testing"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.speed_test_thread = None
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Speed test controls
        controls_layout = QHBoxLayout()
        
        self.start_speed_test_btn = QPushButton("Start Speed Test")
        self.start_speed_test_btn.clicked.connect(self.start_speed_test)
        controls_layout.addWidget(self.start_speed_test_btn)
        
        self.stop_speed_test_btn = QPushButton("Stop")
        self.stop_speed_test_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_speed_test_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Results display
        results_group = QGroupBox("Speed Test Results")
        results_layout = QVBoxLayout(results_group)
        
        # Download speed
        download_layout = QHBoxLayout()
        download_layout.addWidget(QLabel("Download Speed:"))
        self.download_speed_label = QLabel("-- Mbps")
        self.download_speed_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        download_layout.addWidget(self.download_speed_label)
        download_layout.addStretch()
        results_layout.addLayout(download_layout)
        
        # Upload speed
        upload_layout = QHBoxLayout()
        upload_layout.addWidget(QLabel("Upload Speed:"))
        self.upload_speed_label = QLabel("-- Mbps")
        self.upload_speed_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        upload_layout.addWidget(self.upload_speed_label)
        upload_layout.addStretch()
        results_layout.addLayout(upload_layout)
        
        # Ping
        ping_layout = QHBoxLayout()
        ping_layout.addWidget(QLabel("Ping:"))
        self.ping_label = QLabel("-- ms")
        self.ping_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        ping_layout.addWidget(self.ping_label)
        ping_layout.addStretch()
        results_layout.addLayout(ping_layout)
        
        # Progress bar
        self.speed_progress = QProgressBar()
        self.speed_progress.setVisible(False)
        results_layout.addWidget(self.speed_progress)
        
        layout.addWidget(results_group)
    
    def start_speed_test(self):
        """Start network speed test"""
        self.start_speed_test_btn.setEnabled(False)
        self.stop_speed_test_btn.setEnabled(True)
        self.speed_progress.setVisible(True)
        self.speed_progress.setRange(0, 0)  # Indeterminate
        
        # Reset labels
        self.download_speed_label.setText("Testing...")
        self.upload_speed_label.setText("Testing...")
        self.ping_label.setText("Testing...")
        
        # Start speed test thread
        self.speed_test_thread = NetworkSpeedTestThread()
        self.speed_test_thread.progress_update.connect(self.update_progress)
        self.speed_test_thread.finished_signal.connect(self.speed_test_finished)
        self.speed_test_thread.start()
    
    def update_progress(self, results):
        """Update speed test progress"""
        if 'download_speed' in results:
            self.download_speed_label.setText(f"{results['download_speed']:.1f} Mbps")
        if 'upload_speed' in results:
            self.upload_speed_label.setText(f"{results['upload_speed']:.1f} Mbps")
        if 'ping' in results:
            self.ping_label.setText(f"{results['ping']:.0f} ms")
    
    def speed_test_finished(self):
        """Speed test completed"""
        self.start_speed_test_btn.setEnabled(True)
        self.stop_speed_test_btn.setEnabled(False)
        self.speed_progress.setVisible(False)

class NetworkSpeedTestThread(QThread):
    """Thread for running network speed tests"""
    
    progress_update = Signal(dict)
    finished_signal = Signal()
    
    def run(self):
        """Run speed test"""
        try:
            # Simulate speed test (replace with actual implementation)
            import time
            import random
            
            # Simulate ping test
            time.sleep(1)
            ping_result = random.uniform(10, 50)
            self.progress_update.emit({'ping': ping_result})
            
            # Simulate download test
            time.sleep(2)
            download_speed = random.uniform(50, 200)
            self.progress_update.emit({'download_speed': download_speed})
            
            # Simulate upload test
            time.sleep(2)
            upload_speed = random.uniform(20, 100)
            self.progress_update.emit({'upload_speed': upload_speed})
            
        except Exception as e:
            print(f"Speed test error: {e}")
        finally:
            self.finished_signal.emit()

class NetworkInterfaceWidget(QWidget):
    """Widget for displaying network interface information"""
    
    def __init__(self):
        super().__init__()
        self.network_tools = NetworkToolsManager()
        self.setup_ui()
        self.refresh_interfaces()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Interfaces")
        self.refresh_btn.clicked.connect(self.refresh_interfaces)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Interface table
        self.interface_table = QTableWidget()
        self.interface_table.setColumnCount(7)
        self.interface_table.setHorizontalHeaderLabels([
            "Name", "IP Address", "Subnet Mask", "Gateway", 
            "DNS Servers", "MAC Address", "DHCP"
        ])
        layout.addWidget(self.interface_table)
    
    def refresh_interfaces(self):
        """Refresh network interface information"""
        interfaces = self.network_tools.get_network_interfaces()
        
        self.interface_table.setRowCount(len(interfaces))
        
        for row, interface in enumerate(interfaces):
            self.interface_table.setItem(row, 0, QTableWidgetItem(interface.name))
            self.interface_table.setItem(row, 1, QTableWidgetItem(interface.ip_address))
            self.interface_table.setItem(row, 2, QTableWidgetItem(interface.subnet_mask))
            self.interface_table.setItem(row, 3, QTableWidgetItem(interface.default_gateway))
            self.interface_table.setItem(row, 4, QTableWidgetItem(", ".join(interface.dns_servers)))
            self.interface_table.setItem(row, 5, QTableWidgetItem(interface.mac_address))
            self.interface_table.setItem(row, 6, QTableWidgetItem("Yes" if interface.dhcp_enabled else "No"))
        
        self.interface_table.resizeColumnsToContents()

class NetworkConnectionsWidget(QWidget):
    """Widget for displaying active network connections"""
    
    def __init__(self):
        super().__init__()
        self.network_tools = NetworkToolsManager()
        self.setup_ui()
        self.refresh_connections()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_connections)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_connections)
        controls_layout.addWidget(self.refresh_btn)
        
        self.auto_refresh_cb = QCheckBox("Auto-refresh")
        self.auto_refresh_cb.toggled.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_cb)
        
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(1, 60)
        self.refresh_interval.setValue(5)
        self.refresh_interval.setSuffix(" sec")
        controls_layout.addWidget(self.refresh_interval)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Connections table
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(4)
        self.connections_table.setHorizontalHeaderLabels([
            "Protocol", "Local Address", "Foreign Address", "State"
        ])
        layout.addWidget(self.connections_table)
    
    def refresh_connections(self):
        """Refresh active connections"""
        connections = self.network_tools.get_active_connections()
        
        self.connections_table.setRowCount(len(connections))
        
        for row, conn in enumerate(connections):
            self.connections_table.setItem(row, 0, QTableWidgetItem(conn['protocol']))
            self.connections_table.setItem(row, 1, QTableWidgetItem(conn['local_address']))
            self.connections_table.setItem(row, 2, QTableWidgetItem(conn['foreign_address']))
            self.connections_table.setItem(row, 3, QTableWidgetItem(conn['state']))
        
        self.connections_table.resizeColumnsToContents()
    
    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh of connections"""
        if enabled:
            interval = self.refresh_interval.value() * 1000  # Convert to milliseconds
            self.refresh_timer.start(interval)
        else:
            self.refresh_timer.stop()

class NetworkDiagnosticsWidget(QWidget):
    """Widget for comprehensive network diagnostics"""
    
    def __init__(self):
        super().__init__()
        self.diagnostics = NetworkDiagnostics()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Diagnostic controls
        controls_layout = QHBoxLayout()
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target host (e.g., google.com)")
        self.target_input.setText("google.com")
        controls_layout.addWidget(QLabel("Target:"))
        controls_layout.addWidget(self.target_input)
        
        self.run_diagnostics_btn = QPushButton("Run Diagnostics")
        self.run_diagnostics_btn.clicked.connect(self.run_diagnostics)
        controls_layout.addWidget(self.run_diagnostics_btn)
        
        layout.addLayout(controls_layout)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
    
    def run_diagnostics(self):
        """Run comprehensive network diagnostics"""
        target = self.target_input.text().strip() or "google.com"
        
        self.results_text.clear()
        self.results_text.append(f"Running comprehensive network diagnostics for {target}...")
        self.results_text.append("=" * 50)
        
        # Run diagnostics in thread to avoid blocking UI
        self.diagnostic_thread = NetworkDiagnosticThread(target)
        self.diagnostic_thread.result_ready.connect(self.display_results)
        self.diagnostic_thread.start()
    
    def display_results(self, results):
        """Display diagnostic results"""
        self.results_text.append("\n=== DNS Resolution Test ===")
        dns_result = results['tests']['dns_resolution']
        if dns_result['success']:
            self.results_text.append(f"✓ {dns_result['hostname']} resolves to {dns_result['ip_address']}")
            self.results_text.append(f"  Resolution time: {dns_result['resolution_time_ms']:.1f} ms")
        else:
            self.results_text.append(f"✗ DNS resolution failed: {dns_result['error']}")
        
        self.results_text.append("\n=== Ping Test ===")
        ping_result = results['tests']['ping']
        if ping_result.success:
            self.results_text.append(f"✓ Ping successful to {ping_result.host}")
            self.results_text.append(f"  Packets: {ping_result.packets_sent} sent, {ping_result.packets_received} received, {ping_result.packets_lost} lost ({ping_result.packet_loss_percent}% loss)")
            self.results_text.append(f"  Times: min={ping_result.min_time}ms, max={ping_result.max_time}ms, avg={ping_result.avg_time}ms")
        else:
            self.results_text.append(f"✗ Ping failed: {ping_result.error}")
        
        self.results_text.append("\n=== Port Connectivity Tests ===")
        port_tests = results['tests']['port_connectivity']
        for port_name, port_result in port_tests.items():
            port = port_result['port']
            if port_result['success']:
                self.results_text.append(f"✓ Port {port}: Connected ({port_result['connection_time_ms']:.1f} ms)")
            else:
                self.results_text.append(f"✗ Port {port}: {port_result['error']}")
        
        self.results_text.append("\n=== Network Information ===")
        if results['public_ip']:
            self.results_text.append(f"Public IP: {results['public_ip']}")
        
        self.results_text.append(f"\nActive Network Interfaces: {len(results['network_interfaces'])}")
        for interface in results['network_interfaces']:
            self.results_text.append(f"  • {interface.name}: {interface.ip_address}")

class NetworkDiagnosticThread(QThread):
    """Thread for running network diagnostics"""
    
    result_ready = Signal(dict)
    
    def __init__(self, target_host):
        super().__init__()
        self.target_host = target_host
        self.diagnostics = NetworkDiagnostics()
    
    def run(self):
        """Run diagnostics"""
        try:
            results = self.diagnostics.run_comprehensive_test(self.target_host)
            self.result_ready.emit(results)
        except Exception as e:
            error_result = {
                'error': str(e),
                'tests': {},
                'network_interfaces': [],
                'public_ip': None
            }
            self.result_ready.emit(error_result)
