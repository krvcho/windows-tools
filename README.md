# System Maintenance Tools

A comprehensive Windows desktop application for system administration and maintenance tasks. Built with Python and PySide6, this tool provides an intuitive graphical interface for common system maintenance operations that typically require command-line access and administrator privileges.

![System Maintenance Tools](https://via.placeholder.com/800x500/2C3E50/ECF0F1?text=System+Maintenance+Tools)

## Features

### 🔧 System File Checker (SFC)
- Run `sfc /scannow` with administrator privileges
- Real-time output display in console-style interface
- Process termination capability
- Automatic error detection and reporting

### 🔧 DISM System Image Repair
- Check Windows system image health status
- Scan for component store corruption
- Run `dism /online /cleanup-image /restorehealth` with administrator privileges
- Real-time progress monitoring with percentage display
- Automatic recommendation to run SFC after DISM completion
- Process termination capability
- Estimated repair time based on system specifications

### 🌐 Network Diagnostic Tools
- **Ping Test**: Test connectivity to any host with customizable packet count
- **Traceroute**: Trace network path to destination with hop-by-hop analysis
- **IP Configuration**: Display detailed network adapter information
- **Network Statistics**: Show active connections and network usage
- **DNS Tools**: Flush DNS cache and test DNS resolution
- **Network Reset**: Reset network adapters and TCP/IP stack
- **Real-time monitoring** with process termination capability
- **Comprehensive network diagnostics** with recommendations

### 💾 Disk Check (CHKDSK)
- Interactive drive selection dropdown
- Execute `chkdsk /f /r` on selected drives
- Real-time progress monitoring
- Confirmation dialogs for destructive operations

### 🔐 Registry Management
- Disable/Enable Windows automatic updates
- Modify Windows Update, Delivery Optimization, and Windows Store settings
- Safe registry operations with detailed logging
- Backup and restore capabilities

### 👑 Administrator Privilege Management
- Automatic UAC elevation requests
- Runtime privilege checking
- Secure process elevation
- User-friendly privilege status indicators

### Main Interface
The application features a clean, tabbed interface with dedicated sections for each tool:

- **System File Checker Tab**: Console output with start/stop controls
- **Disk Check Tab**: Drive selection and progress monitoring
- **Registry Tweaks Tab**: Windows Update management controls

## System Requirements

- **Operating System**: Windows 10/11 (x64)
- **Python**: 3.7 or higher
- **RAM**: 512 MB minimum, 1 GB recommended
- **Disk Space**: 50 MB for installation
- **Privileges**: Administrator rights required for full functionality

## Installation

### Method 1: Quick Install (Recommended)

1. **Download the latest release** from the releases page or clone this repository:
   \`\`\`bash
   git clone https://github.com/krvcho/windows-tools
   cd system-maintenance-tools
   \`\`\`

2. **Install Python dependencies**:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Run the application**:
   \`\`\`bash
   python main.py
   \`\`\`

### Method 2: System-wide Installation

1. **Run the installer with administrator privileges**:
   \`\`\`bash
   python installer.py
   \`\`\`

2. **Launch from Desktop shortcut** or Start Menu

### Method 3: Portable Executable

1. **Build standalone executable**:
   \`\`\`bash
   pip install cx_Freeze
   python build_exe.py build
   \`\`\`

2. **Run the executable** from the `build` directory

### Method 4: Using Batch File (Windows)

For users who prefer not to use command line:

1. **Double-click** `run_as_admin.bat`
2. **Allow UAC elevation** when prompted
3. **Application will launch** with administrator privileges

## Dependencies

The application requires the following Python packages:

\`\`\`
PySide6>=6.5.0      # Qt-based GUI framework
psutil>=5.9.0       # System and process utilities  
pywin32>=306        # Windows API access
\`\`\`

### Installing Dependencies Manually

If you encounter issues with the requirements file:

\`\`\`bash
pip install PySide6
pip install psutil
pip install pywin32
\`\`\`

## Usage

### First Launch

1. **Start the application** using one of the installation methods above
2. **Accept UAC prompt** to grant administrator privileges
3. **Select the desired tool** from the tabbed interface

### System File Checker

1. Navigate to the **"System File Checker"** tab
2. Click **"Run SFC /scannow"** button
3. Monitor progress in the console output area
4. Use **"Stop"** button to terminate if needed

### DISM System Image Repair

1. Navigate to the **"DISM Repair"** tab
2. **Check Image Health**: Quick health status check
3. **Scan Image Health**: Detailed corruption scan (takes longer)
4. **Run DISM /RestoreHealth**: Full repair process (15-30 minutes)
5. Monitor progress with real-time percentage updates
6. Use **"Stop"** button to terminate if needed
7. **Recommended**: Run SFC scan after DISM completion

**Note**: DISM repair requires internet connection to download replacement files from Windows Update.

### 🌐 Network Tools Usage

1. Navigate to the **"Network Tools"** tab
2. **Ping Test**: Enter target host and select packet count, click "Start Ping"
3. **Traceroute**: Enter target host and click "Start Traceroute"
4. **IP Configuration**: Click to display all network adapter details
5. **Network Statistics**: View active network connections
6. **DNS Flush**: Clear DNS cache (requires admin privileges)
7. **Network Reset**: Reset network configuration (requires admin privileges)
8. Monitor real-time output in the console area
9. Use **"Stop"** buttons to terminate long-running operations

**Network Reset Process**:
- Resets Winsock catalog
- Resets TCP/IP stack
- Releases and renews IP addresses
- Flushes DNS cache
- May require system restart

### Disk Check

1. Navigate to the **"Disk Check"** tab  
2. Select target drive from the dropdown menu
3. Click **"Run CHKDSK /f /r"** button
4. Confirm the operation in the dialog box
5. Monitor progress and results

### Registry Tweaks

1. Navigate to the **"Registry Tweaks"** tab
2. Choose **"Disable Windows Updates"** or **"Enable Windows Updates"**
3. Confirm the registry modifications
4. Review the detailed log output

## Configuration

### Environment Variables

The application supports the following optional environment variables:

- `SYSTEM_TOOLS_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `SYSTEM_TOOLS_BACKUP_DIR`: Directory for registry backups
- `SYSTEM_TOOLS_THEME`: UI theme selection (light, dark)

### Registry Backup

Before making registry changes, the application can automatically create backups:

\`\`\`python
# Enable automatic backups
registry_manager.backup_registry_key(
    "SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate",
    "backup_windows_update.reg"
)
\`\`\`

## Troubleshooting

### Common Issues

#### "Administrator privileges required" error
- **Solution**: Right-click the application and select "Run as administrator"
- **Alternative**: Use the provided `run_as_admin.bat` file

#### "Module not found" errors
- **Solution**: Ensure all dependencies are installed:
  \`\`\`bash
  pip install -r requirements.txt
  \`\`\`

#### Application won't start
- **Check Python version**: Ensure Python 3.7+ is installed
- **Check PATH**: Verify Python is in your system PATH
- **Run from command line**: See detailed error messages

#### Registry modifications fail
- **Verify admin rights**: Ensure running with administrator privileges
- **Check UAC settings**: UAC must be enabled for elevation
- **Antivirus interference**: Temporarily disable real-time protection

### Debug Mode

Enable debug logging for troubleshooting:

\`\`\`bash
set SYSTEM_TOOLS_LOG_LEVEL=DEBUG
python main.py
\`\`\`

### Log Files

Application logs are stored in:
- **Windows**: `%APPDATA%\\SystemMaintenanceTools\\logs\\`
- **Portable**: `./logs/` directory

## Development

### Project Structure

\`\`\`
system-maintenance-tools/
├── main.py                 # Main application entry point
├── system_commands.py      # Command execution and process management
├── registry_manager.py     # Windows registry operations
├── admin_utils.py         # Administrator privilege utilities
├── ui_styles.py           # Qt stylesheet definitions
├── installer.py           # System installation script
├── build_exe.py          # Executable build configuration
├── requirements.txt       # Python dependencies
├── run_as_admin.bat      # Windows batch launcher
└── README.md             # This file
\`\`\`

### Adding New Features

1. **Create new module** for your feature
2. **Add UI components** in `main.py`
3. **Update styles** in `ui_styles.py`
4. **Test with admin privileges**

### Building from Source

\`\`\`bash
# Clone repository
git clone https://github.com/yourusername/system-maintenance-tools.git
cd system-maintenance-tools

# Install development dependencies
pip install -r requirements.txt
pip install cx_Freeze

# Run tests (if available)
python -m pytest tests/

# Build executable
python build_exe.py build
\`\`\`

## Security Considerations

### Administrator Privileges
- The application requests UAC elevation for security
- Registry modifications are logged for audit purposes
- Process execution is sandboxed where possible

### Registry Safety
- Automatic backups before modifications
- Validation of registry keys before changes
- Rollback capability for failed operations

### Process Security
- Command injection prevention
- Process isolation and cleanup
- Secure parameter validation

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** with appropriate tests
4. **Follow PEP 8** coding standards
5. **Submit a pull request** with detailed description

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Add docstrings for all public methods
- Include error handling for all operations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Getting Help

- **Issues**: Report bugs on the GitHub Issues page
- **Discussions**: Join community discussions
- **Documentation**: Check the wiki for detailed guides

### Known Limitations

- Windows-only compatibility (by design)
- Requires administrator privileges for full functionality
- Some antivirus software may flag registry operations
- CHKDSK operations may require system restart

## Changelog

### Version 1.0.0 (Current)
- Initial release
- System File Checker integration
- Disk Check functionality
- Registry tweaks for Windows Updates
- Modern Qt-based interface
- Administrator privilege management

### Planned Features
- System information dashboard
- Windows service management
- Startup program control
- Network diagnostic tools
- Event log viewer

## Acknowledgments

- **PySide6 Team** for the excellent Qt Python bindings
- **Microsoft** for Windows API documentation
- **Python Community** for the robust ecosystem
- **Contributors** who helped test and improve the application

---

**⚠️ Important**: This application modifies system settings and requires administrator privileges. Always create system backups before making significant changes. Use at your own risk.

**📧 Contact**: For support or questions, please open an issue on GitHub or contact the maintainers.
