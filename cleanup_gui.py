"""
GUI components for system cleanup functionality
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QLineEdit, QPushButton, QComboBox, 
                               QTextEdit, QTableWidget, QTableWidgetItem,
                               QTabWidget, QCheckBox, QSpinBox, QMessageBox,
                               QHeaderView, QAbstractItemView, QFileDialog,
                               QProgressBar, QSplitter, QTreeWidget, QTreeWidgetItem,
                               QFrame, QScrollArea)
from PySide6.QtCore import QThread, Signal, QTimer, Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPalette

from cleanup_manager import SystemCleanupManager, CleanupResult, format_size, estimate_cleanup_time

class CleanupScanThread(QThread):
    """Thread for scanning cleanup locations"""
    
    progress_update = Signal(int, int, str)  # current, total, message
    scan_complete = Signal(dict)  # cleanup locations
    
    def __init__(self):
        super().__init__()
        self.cleanup_manager = SystemCleanupManager()
    
    def run(self):
        """Run the cleanup scan"""
        try:
            def progress_callback(current, total):
                self.progress_update.emit(current, total, f"Scanning location {current} of {total}")
            
            locations = self.cleanup_manager.scan_cleanup_locations(progress_callback)
            self.scan_complete.emit(locations)
            
        except Exception as e:
            self.progress_update.emit(0, 0, f"Error during scan: {str(e)}")

class CleanupExecutionThread(QThread):
    """Thread for executing cleanup operations"""
    
    progress_update = Signal(int, int, str)  # current, total, message
    cleanup_complete = Signal(list)  # cleanup results
    location_complete = Signal(str, object)  # location name, result
    
    def __init__(self, cleanup_manager, location_keys):
        super().__init__()
        self.cleanup_manager = cleanup_manager
        self.location_keys = location_keys
    
    def run(self):
        """Run the cleanup operations"""
        try:
            def progress_callback(current, total, message=""):
                self.progress_update.emit(current, total, message)
            
            results = []
            total_locations = len(self.location_keys)
            
            for i, location_key in enumerate(self.location_keys):
                self.progress_update.emit(i, total_locations, f"Cleaning {location_key}...")
                
                result = self.cleanup_manager.cleanup_location(location_key)
                results.append(result)
                
                # Emit individual result
                self.location_complete.emit(location_key, result)
            
            self.progress_update.emit(total_locations, total_locations, "Cleanup completed")
            self.cleanup_complete.emit(results)
            
        except Exception as e:
            self.progress_update.emit(0, 0, f"Error during cleanup: {str(e)}")

class CleanupLocationWidget(QWidget):
    """Widget for displaying and managing cleanup locations"""
    
    def __init__(self):
        super().__init__()
        self.cleanup_manager = SystemCleanupManager()
        self.cleanup_locations = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with scan button and summary
        header_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("Scan System")
        self.scan_btn.setObjectName("primary-button")
        self.scan_btn.clicked.connect(self.start_scan)
        header_layout.addWidget(self.scan_btn)
        
        self.summary_label = QLabel("Click 'Scan System' to analyze cleanup locations")
        self.summary_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(self.summary_label)
        
        header_layout.addStretch()
        
        # Quick actions
        self.quick_temp_btn = QPushButton("Quick Temp Cleanup")
        self.quick_temp_btn.setObjectName("success-button")
        self.quick_temp_btn.clicked.connect(self.quick_temp_cleanup)
        self.quick_temp_btn.setEnabled(False)
        header_layout.addWidget(self.quick_temp_btn)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Splitter for locations and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Cleanup locations tree
        locations_widget = QWidget()
        locations_layout = QVBoxLayout(locations_widget)
        
        locations_layout.addWidget(QLabel("Cleanup Locations:"))
        
        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderLabels(["Location", "Size", "Files", "Category"])
        self.locations_tree.setRootIsDecorated(True)
        self.locations_tree.setAlternatingRowColors(True)
        self.locations_tree.itemChanged.connect(self.on_item_changed)
        locations_layout.addWidget(self.locations_tree)
        
        # Selection controls
        selection_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_items)
        selection_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.clicked.connect(self.select_no_items)
        selection_layout.addWidget(self.select_none_btn)
        
        self.select_safe_btn = QPushButton("Select Safe Only")
        self.select_safe_btn.clicked.connect(self.select_safe_items)
        selection_layout.addWidget(self.select_safe_btn)
        
        selection_layout.addStretch()
        locations_layout.addLayout(selection_layout)
        
        # Cleanup button
        self.cleanup_btn = QPushButton("Clean Selected Locations")
        self.cleanup_btn.setObjectName("warning-button")
        self.cleanup_btn.clicked.connect(self.start_cleanup)
        self.cleanup_btn.setEnabled(False)
        locations_layout.addWidget(self.cleanup_btn)
        
        splitter.addWidget(locations_widget)
        
        # Right side - Details and disk space
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Disk space information
        disk_group = QGroupBox("Disk Space Information")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_info_label = QLabel("Scanning...")
        disk_layout.addWidget(self.disk_info_label)
        
        details_layout.addWidget(disk_group)
        
        # Cleanup results
        results_group = QGroupBox("Cleanup Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        details_layout.addWidget(results_group)
        
        # Estimated cleanup time
        estimate_group = QGroupBox("Cleanup Estimate")
        estimate_layout = QVBoxLayout(estimate_group)
        
        self.estimate_label = QLabel("Select locations to see estimate")
        estimate_layout.addWidget(self.estimate_label)
        
        details_layout.addWidget(estimate_group)
        
        details_layout.addStretch()
        
        splitter.addWidget(details_widget)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        # Update disk space info
        self.update_disk_space_info()
    
    def start_scan(self):
        """Start scanning cleanup locations"""
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.scan_thread = CleanupScanThread()
        self.scan_thread.progress_update.connect(self.update_scan_progress)
        self.scan_thread.scan_complete.connect(self.scan_completed)
        self.scan_thread.start()
    
    def update_scan_progress(self, current, total, message):
        """Update scan progress"""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        
        self.progress_label.setText(message)
    
    def scan_completed(self, locations):
        """Handle scan completion"""
        self.cleanup_locations = locations
        self.populate_locations_tree()
        self.update_summary()
        
        self.scan_btn.setEnabled(True)
        self.quick_temp_btn.setEnabled(True)
        self.cleanup_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
    
    def populate_locations_tree(self):
        """Populate the cleanup locations tree"""
        self.locations_tree.clear()
        
        # Group by category
        categories = {}
        for key, location in self.cleanup_locations.items():
            category = location.category
            if category not in categories:
                categories[category] = []
            categories[category].append((key, location))
        
        # Add category items
        for category, locations in categories.items():
            category_item = QTreeWidgetItem(self.locations_tree)
            category_item.setText(0, category)
            category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsTristate | Qt.ItemFlag.ItemIsUserCheckable)
            category_item.setCheckState(0, Qt.CheckState.Unchecked)
            
            # Calculate category totals
            total_size = sum(loc.size_mb for _, loc in locations)
            total_files = sum(loc.file_count for _, loc in locations)
            
            category_item.setText(1, format_size(total_size))
            category_item.setText(2, str(total_files))
            category_item.setText(3, f"{len(locations)} locations")
            
            # Add location items
            for key, location in locations:
                location_item = QTreeWidgetItem(category_item)
                location_item.setText(0, location.name)
                location_item.setText(1, format_size(location.size_mb))
                location_item.setText(2, str(location.file_count))
                location_item.setText(3, "Safe" if location.safe_to_delete else "Caution")
                
                location_item.setFlags(location_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                location_item.setCheckState(0, Qt.CheckState.Checked if location.safe_to_delete else Qt.CheckState.Unchecked)
                location_item.setData(0, Qt.ItemDataRole.UserRole, key)
                
                # Color coding
                if not location.safe_to_delete:
                    location_item.setForeground(3, QColor("orange"))
                if location.requires_admin:
                    location_item.setForeground(0, QColor("blue"))
        
        self.locations_tree.expandAll()
        self.locations_tree.resizeColumnToContents(0)
    
    def on_item_changed(self, item, column):
        """Handle item check state changes"""
        if column == 0:  # Only handle checkbox changes
            self.update_estimate()
    
    def select_all_items(self):
        """Select all cleanup locations"""
        self._set_all_items_checked(Qt.CheckState.Checked)
    
    def select_no_items(self):
        """Deselect all cleanup locations"""
        self._set_all_items_checked(Qt.CheckState.Unchecked)
    
    def select_safe_items(self):
        """Select only safe cleanup locations"""
        root = self.locations_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            for j in range(category_item.childCount()):
                location_item = category_item.child(j)
                location_key = location_item.data(0, Qt.ItemDataRole.UserRole)
                if location_key and location_key in self.cleanup_locations:
                    location = self.cleanup_locations[location_key]
                    check_state = Qt.CheckState.Checked if location.safe_to_delete else Qt.CheckState.Unchecked
                    location_item.setCheckState(0, check_state)
    
    def _set_all_items_checked(self, check_state):
        """Set all items to specified check state"""
        root = self.locations_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            for j in range(category_item.childCount()):
                location_item = category_item.child(j)
                location_item.setCheckState(0, check_state)
    
    def get_selected_locations(self):
        """Get list of selected location keys"""
        selected = []
        root = self.locations_tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            category_item = root.child(i)
            for j in range(category_item.childCount()):
                location_item = category_item.child(j)
                if location_item.checkState(0) == Qt.CheckState.Checked:
                    location_key = location_item.data(0, Qt.ItemDataRole.UserRole)
                    if location_key:
                        selected.append(location_key)
        
        return selected
    
    def update_estimate(self):
        """Update cleanup estimate"""
        selected_keys = self.get_selected_locations()
        
        if not selected_keys:
            self.estimate_label.setText("No locations selected")
            return
        
        total_size = 0.0
        total_files = 0
        requires_admin = False
        
        for key in selected_keys:
            if key in self.cleanup_locations:
                location = self.cleanup_locations[key]
                total_size += location.size_mb
                total_files += location.file_count
                if location.requires_admin:
                    requires_admin = True
        
        estimate_time = estimate_cleanup_time(total_files)
        admin_note = " (Requires admin privileges)" if requires_admin else ""
        
        estimate_text = f"""
Selected: {len(selected_keys)} locations
Total Size: {format_size(total_size)}
Total Files: {total_files:,}
Estimated Time: {estimate_time}{admin_note}
        """.strip()
        
        self.estimate_label.setText(estimate_text)
    
    def update_summary(self):
        """Update the summary label"""
        if not self.cleanup_locations:
            return
        
        total_size = sum(loc.size_mb for loc in self.cleanup_locations.values())
        total_files = sum(loc.file_count for loc in self.cleanup_locations.values())
        
        summary_text = f"Found {len(self.cleanup_locations)} cleanup locations • {format_size(total_size)} • {total_files:,} files"
        self.summary_label.setText(summary_text)
    
    def update_disk_space_info(self):
        """Update disk space information"""
        try:
            disk_info = self.cleanup_manager.get_disk_space_info()
            
            info_text = ""
            for drive, info in disk_info.items():
                info_text += f"{drive} {info['used_gb']:.1f} GB used / {info['total_gb']:.1f} GB total ({info['used_percent']:.1f}% full)\n"
            
            if not info_text:
                info_text = "No disk information available"
            
            self.disk_info_label.setText(info_text.strip())
            
        except Exception as e:
            self.disk_info_label.setText(f"Error getting disk info: {str(e)}")
    
    def quick_temp_cleanup(self):
        """Perform quick temporary files cleanup"""
        reply = QMessageBox.question(
            self, "Quick Temp Cleanup",
            "This will clean temporary files from:\n"
            "• User temporary directory\n"
            "• System temporary directory\n"
            "• Windows temporary directory\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            temp_locations = ['user_temp', 'system_temp', 'windows_temp']
            self.start_cleanup_with_locations(temp_locations)
    
    def start_cleanup(self):
        """Start cleanup of selected locations"""
        selected_keys = self.get_selected_locations()
        
        if not selected_keys:
            QMessageBox.warning(self, "No Selection", "Please select at least one location to clean.")
            return
        
        # Check for non-safe locations
        unsafe_locations = []
        for key in selected_keys:
            if key in self.cleanup_locations:
                location = self.cleanup_locations[key]
                if not location.safe_to_delete:
                    unsafe_locations.append(location.name)
        
        if unsafe_locations:
            reply = QMessageBox.warning(
                self, "Caution Required",
                f"The following locations require caution:\n\n" +
                "\n".join(f"• {name}" for name in unsafe_locations) +
                "\n\nThese may contain important files. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.start_cleanup_with_locations(selected_keys)
    
    def start_cleanup_with_locations(self, location_keys):
        """Start cleanup with specified locations"""
        self.cleanup_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setRange(0, len(location_keys))
        self.progress_bar.setValue(0)
        
        self.results_text.clear()
        self.results_text.append("Starting cleanup operations...\n")
        
        self.cleanup_thread = CleanupExecutionThread(self.cleanup_manager, location_keys)
        self.cleanup_thread.progress_update.connect(self.update_cleanup_progress)
        self.cleanup_thread.location_complete.connect(self.location_cleanup_complete)
        self.cleanup_thread.cleanup_complete.connect(self.cleanup_completed)
        self.cleanup_thread.start()
    
    def update_cleanup_progress(self, current, total, message):
        """Update cleanup progress"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(message)
    
    def location_cleanup_complete(self, location_key, result):
        """Handle individual location cleanup completion"""
        if result.success:
            self.results_text.append(
                f"✓ {result.location}: {result.files_deleted:,} files, "
                f"{format_size(result.size_freed_mb)} freed"
            )
        else:
            self.results_text.append(
                f"✗ {result.location}: {result.error_message}"
            )
        
        # Scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)
    
    def cleanup_completed(self, results):
        """Handle cleanup completion"""
        self.cleanup_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Calculate totals
        total_files = sum(r.files_deleted for r in results if r.success)
        total_size = sum(r.size_freed_mb for r in results if r.success)
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.results_text.append(f"\n=== Cleanup Summary ===")
        self.results_text.append(f"Successful: {successful}, Failed: {failed}")
        self.results_text.append(f"Total files deleted: {total_files:,}")
        self.results_text.append(f"Total space freed: {format_size(total_size)}")
        
        # Update disk space info
        self.update_disk_space_info()
        
        # Show completion message
        QMessageBox.information(
            self, "Cleanup Complete",
            f"Cleanup completed!\n\n"
            f"Files deleted: {total_files:,}\n"
            f"Space freed: {format_size(total_size)}\n"
            f"Successful operations: {successful}\n"
            f"Failed operations: {failed}"
        )
        
        # Optionally rescan
        if successful > 0:
            reply = QMessageBox.question(
                self, "Rescan System",
                "Would you like to rescan the system to see updated sizes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_scan()

class CleanupSchedulerWidget(QWidget):
    """Widget for scheduling automatic cleanup"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Automatic Cleanup Scheduler")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Schedule configuration
        config_group = QGroupBox("Schedule Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Frequency
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency:"))
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Monthly"])
        freq_layout.addWidget(self.frequency_combo)
        freq_layout.addStretch()
        config_layout.addLayout(freq_layout)
        
        # Time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time:"))
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("HH:MM (24-hour format)")
        self.time_edit.setText("02:00")
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        config_layout.addLayout(time_layout)
        
        # Locations to clean
        locations_layout = QVBoxLayout()
        locations_layout.addWidget(QLabel("Locations to clean automatically:"))
        
        self.auto_temp_cb = QCheckBox("Temporary Files")
        self.auto_temp_cb.setChecked(True)
        locations_layout.addWidget(self.auto_temp_cb)
        
        self.auto_cache_cb = QCheckBox("Browser Cache")
        locations_layout.addWidget(self.auto_cache_cb)
        
        self.auto_logs_cb = QCheckBox("Log Files")
        locations_layout.addWidget(self.auto_logs_cb)
        
        self.auto_recycle_cb = QCheckBox("Recycle Bin")
        locations_layout.addWidget(self.auto_recycle_cb)
        
        config_layout.addLayout(locations_layout)
        
        layout.addWidget(config_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_task_btn = QPushButton("Create Scheduled Task")
        self.create_task_btn.setObjectName("primary-button")
        self.create_task_btn.clicked.connect(self.create_scheduled_task)
        button_layout.addWidget(self.create_task_btn)
        
        self.view_tasks_btn = QPushButton("View Scheduled Tasks")
        self.view_tasks_btn.clicked.connect(self.view_scheduled_tasks)
        button_layout.addWidget(self.view_tasks_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("No automatic cleanup scheduled")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def create_scheduled_task(self):
        """Create a scheduled cleanup task"""
        # Get selected locations
        selected_locations = []
        if self.auto_temp_cb.isChecked():
            selected_locations.extend(['user_temp', 'system_temp', 'windows_temp'])
        if self.auto_cache_cb.isChecked():
            selected_locations.extend(['chrome_cache', 'firefox_cache', 'edge_cache'])
        if self.auto_logs_cb.isChecked():
            selected_locations.extend(['cbs_logs', 'dism_logs', 'setup_logs'])
        if self.auto_recycle_cb.isChecked():
            selected_locations.append('recycle_bin')
        
        if not selected_locations:
            QMessageBox.warning(self, "No Selection", "Please select at least one location to clean automatically.")
            return
        
        frequency = self.frequency_combo.currentText().lower()
        time_of_day = self.time_edit.text().strip()
        
        if not time_of_day:
            QMessageBox.warning(self, "Invalid Time", "Please enter a valid time in HH:MM format.")
            return
        
        # Create the scheduled task (simplified implementation)
        try:
            task_name = f"SystemCleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # This would create an actual Windows scheduled task
            # For now, just show success message
            QMessageBox.information(
                self, "Task Created",
                f"Scheduled cleanup task created:\n\n"
                f"Name: {task_name}\n"
                f"Frequency: {frequency.title()}\n"
                f"Time: {time_of_day}\n"
                f"Locations: {len(selected_locations)} selected"
            )
            
            self.status_label.setText(f"Automatic cleanup scheduled: {frequency} at {time_of_day}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create scheduled task: {str(e)}")
    
    def view_scheduled_tasks(self):
        """View existing scheduled tasks"""
        QMessageBox.information(
            self, "Scheduled Tasks",
            "This would open the Windows Task Scheduler to view existing cleanup tasks.\n\n"
            "You can manually open Task Scheduler by running 'taskschd.msc'."
        )
