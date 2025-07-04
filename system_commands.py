import subprocess
import threading
import queue
import os
from PySide6.QtCore import QThread, Signal

class SystemCommandRunner(QThread):
    output_received = Signal(str)
    error_received = Signal(str)
    finished = Signal()
    
    def __init__(self, command, arguments, output_widget):
        super().__init__()
        self.command = command
        self.arguments = arguments
        self.output_widget = output_widget
        self.process = None
        self.should_stop = False
        
        # Connect signals
        self.output_received.connect(self.append_output)
        self.error_received.connect(self.append_error)
    
    def run(self):
        try:
            # Create the full command
            full_command = f"{self.command} {self.arguments}"
            
            # Start the process with elevated privileges
            self.process = subprocess.Popen(
                full_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Read output in real-time
            while True:
                if self.should_stop:
                    self.process.terminate()
                    break
                
                output = self.process.stdout.readline()
                if output:
                    self.output_received.emit(output.strip())
                elif self.process.poll() is not None:
                    break
            
            # Get any remaining output
            remaining_output, remaining_error = self.process.communicate()
            if remaining_output:
                self.output_received.emit(remaining_output.strip())
            if remaining_error:
                self.error_received.emit(remaining_error.strip())
            
            # Emit completion signal
            exit_code = self.process.returncode
            self.output_received.emit(f"\nProcess completed with exit code: {exit_code}")
            
        except Exception as e:
            self.error_received.emit(f"Error running command: {str(e)}")
        finally:
            self.finished.emit()
    
    def stop(self):
        self.should_stop = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def append_output(self, text):
        if text.strip():
            self.output_widget.append(text)
            # Auto-scroll to bottom
            cursor = self.output_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.output_widget.setTextCursor(cursor)
    
    def append_error(self, text):
        if text.strip():
            self.output_widget.append(f"ERROR: {text}")
            cursor = self.output_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.output_widget.setTextCursor(cursor)

class DismCommandRunner(QThread):
    """Specialized command runner for DISM operations with progress tracking"""
    
    output_received = Signal(str)
    progress_update = Signal(int)
    error_received = Signal(str)
    finished = Signal()
    
    def __init__(self, command, arguments, output_widget):
        super().__init__()
        self.command = command
        self.arguments = arguments
        self.output_widget = output_widget
        self.process = None
        self.should_stop = False
        
        # Connect signals
        self.output_received.connect(self.append_output)
        self.error_received.connect(self.append_error)
        self.progress_update.connect(self.update_progress)
    
    def run(self):
        try:
            # Create the full command
            full_command = f"{self.command} {self.arguments}"
            
            # Start the process with elevated privileges
            self.process = subprocess.Popen(
                full_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Read output in real-time
            while True:
                if self.should_stop:
                    self.process.terminate()
                    break
                
                output = self.process.stdout.readline()
                if output:
                    line = output.strip()
                    self.output_received.emit(line)
                    
                    # Try to extract progress from DISM output
                    progress = self._extract_dism_progress(line)
                    if progress is not None:
                        self.progress_update.emit(progress)
                        
                elif self.process.poll() is not None:
                    break
            
            # Get any remaining output
            remaining_output, remaining_error = self.process.communicate()
            if remaining_output:
                self.output_received.emit(remaining_output.strip())
            if remaining_error:
                self.error_received.emit(remaining_error.strip())
            
            # Emit completion signal
            exit_code = self.process.returncode
            self.output_received.emit(f"\nDISM process completed with exit code: {exit_code}")
            
        except Exception as e:
            self.error_received.emit(f"Error running DISM command: {str(e)}")
        finally:
            self.finished.emit()
    
    def _extract_dism_progress(self, line):
        """Extract progress percentage from DISM output"""
        try:
            # DISM shows progress like "[===========     ] 55.0%"
            if '%' in line and '[' in line:
                # Find the percentage
                percent_pos = line.find('%')
                if percent_pos > 0:
                    # Look backwards for the number
                    start = percent_pos - 1
                    while start >= 0 and (line[start].isdigit() or line[start] == '.'):
                        start -= 1
                    
                    if start < percent_pos - 1:
                        percent_str = line[start + 1:percent_pos]
                        return int(float(percent_str))
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def stop(self):
        self.should_stop = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def append_output(self, text):
        if text.strip():
            self.output_widget.append(text)
            cursor = self.output_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.output_widget.setTextCursor(cursor)
    
    def append_error(self, text):
        if text.strip():
            self.output_widget.append(f"ERROR: {text}")
            cursor = self.output_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.output_widget.setTextCursor(cursor)
    
    def update_progress(self, percentage):
        """Update progress display in output"""
        self.output_widget.append(f"Progress: {percentage}%")

class ElevatedCommandRunner:
    @staticmethod
    def run_as_admin(command, arguments):
        """Run a command with administrator privileges"""
        try:
            import ctypes
            import sys
            
            if ctypes.windll.shell32.IsUserAnAdmin():
                # Already running as admin, execute directly
                result = subprocess.run(
                    f"{command} {arguments}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return result.returncode, result.stdout, result.stderr
            else:
                # Request elevation
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", command, arguments, None, 1
                )
                return 0, "Command executed with elevation", ""
                
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def is_process_running(process_name):
        """Check if a process is currently running"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name.lower():
                    return True
            return False
        except:
            return False
    
    @staticmethod
    def kill_process(process_name):
        """Terminate a process by name"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name.lower():
                    proc.terminate()
                    proc.wait(timeout=5)
            return True
        except:
            return False
