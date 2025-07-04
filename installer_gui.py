"""
GUI for creating installers - provides a user-friendly interface
"""

import sys
import os
import threading
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                               QCheckBox, QProgressBar, QGroupBox, QMessageBox)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont

from create_installer import InstallerBuilder

class InstallerThread(QThread):
    progress_update = Signal(str)
    finished_signal = Signal(bool)
    
    def __init__(self, installer_types):
        super().__init__()
        self.installer_types = installer_types
        self.builder = InstallerBuilder()
    
    def run(self):
        try:
            self.progress_update.emit("Building executable...")
            if not self.builder.build_executable():
                self.progress_update.emit("Failed to build executable!")
                self.finished_signal.emit(False)
                return
            
            success_count = 0
            
            if 'portable' in self.installer_types:
                self.progress_update.emit("Creating portable package...")
                if self.builder.create_portable_package():
                    success_count += 1
                    self.progress_update.emit("✓ Portable package created")
                else:
                    self.progress_update.emit("✗ Portable package failed")
            
            if 'nsis' in self.installer_types:
                self.progress_update.emit("Creating NSIS installer...")
                if self.builder.create_nsis_installer():
                    success_count += 1
                    self.progress_update.emit("✓ NSIS installer created")
                else:
                    self.progress_update.emit("✗ NSIS installer failed")
            
            if 'inno' in self.installer_types:
                self.progress_update.emit("Creating Inno Setup installer...")
                if self.builder.create_inno_setup_installer():
                    success_count += 1
                    self.progress_update.emit("✓ Inno Setup installer created")
                else:
                    self.progress_update.emit("✗ Inno Setup installer failed")
            
            if 'msi' in self.installer_types:
                self.progress_update.emit("Creating MSI installer...")
                if self.builder.create_msi_installer():
                    success_count += 1
                    self.progress_update.emit("✓ MSI installer created")
                else:
                    self.progress_update.emit("✗ MSI installer failed")
            
            self.progress_update.emit(f"\nCompleted: {success_count}/{len(self.installer_types)} installers created successfully")
            self.finished_signal.emit(success_count > 0)
            
        except Exception as e:
            self.progress_update.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False)

class InstallerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Maintenance Tools - Installer Builder")
        self.setGeometry(100, 100, 800, 600)
        
        self.installer_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("System Maintenance Tools - Installer Builder")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Installer type selection
        installer_group = QGroupBox("Select Installer Types")
        installer_layout = QVBoxLayout(installer_group)
        
        self.portable_cb = QCheckBox("Portable ZIP Package")
        self.portable_cb.setChecked(True)
        installer_layout.addWidget(self.portable_cb)
        
        self.nsis_cb = QCheckBox("NSIS Installer (.exe)")
        installer_layout.addWidget(self.nsis_cb)
        
        self.inno_cb = QCheckBox("Inno Setup Installer (.exe)")
        installer_layout.addWidget(self.inno_cb)
        
        self.msi_cb = QCheckBox("MSI Installer (.msi)")
        installer_layout.addWidget(self.msi_cb)
        
        layout.addWidget(installer_group)
        
        # Progress area
        progress_group = QGroupBox("Build Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(200)
        progress_layout.addWidget(self.progress_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.build_button = QPushButton("Build Installers")
        self.build_button.clicked.connect(self.build_installers)
        button_layout.addWidget(self.build_button)
        
        self.open_folder_button = QPushButton("Open Output Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready to build installers")
    
    def build_installers(self):
        # Get selected installer types
        installer_types = []
        if self.portable_cb.isChecked():
            installer_types.append('portable')
        if self.nsis_cb.isChecked():
            installer_types.append('nsis')
        if self.inno_cb.isChecked():
            installer_types.append('inno')
        if self.msi_cb.isChecked():
            installer_types.append('msi')
        
        if not installer_types:
            QMessageBox.warning(self, "Warning", "Please select at least one installer type.")
            return
        
        # Disable UI during build
        self.build_button.setEnabled(False)
        self.progress_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start build thread
        self.installer_thread = InstallerThread(installer_types)
        self.installer_thread.progress_update.connect(self.update_progress)
        self.installer_thread.finished_signal.connect(self.build_finished)
        self.installer_thread.start()
        
        self.statusBar().showMessage("Building installers...")
    
    def update_progress(self, message):
        self.progress_text.append(message)
        self.progress_text.ensureCursorVisible()
    
    def build_finished(self, success):
        self.build_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.open_folder_button.setEnabled(success)
        
        if success:
            self.statusBar().showMessage("Build completed successfully!")
            QMessageBox.information(self, "Success", "Installers created successfully!")
        else:
            self.statusBar().showMessage("Build failed!")
            QMessageBox.critical(self, "Error", "Failed to create installers. Check the log for details.")
    
    def open_output_folder(self):
        import subprocess
        import platform
        
        installer_dir = Path(__file__).parent / "installers"
        
        if platform.system() == "Windows":
            subprocess.run(["explorer", str(installer_dir)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(installer_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(installer_dir)])

def main():
    app = QApplication(sys.argv)
    window = InstallerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
