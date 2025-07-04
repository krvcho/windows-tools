# Installer Creation Guide

This guide explains how to create professional Windows installers for the System Maintenance Tools application.

## Quick Start

### Method 1: Automated Build (Recommended)
\`\`\`bash
# Run the automated installer builder
python create_installer.py all
\`\`\`

### Method 2: GUI Builder
\`\`\`bash
# Launch the graphical installer builder
python installer_gui.py
\`\`\`

### Method 3: Batch File (Windows)
\`\`\`bash
# Double-click the batch file
build_installers.bat
\`\`\`

## Installer Types

### 1. Portable ZIP Package
- **No installation required**
- **Extract and run**
- **Best for**: Testing, temporary use, USB drives

**Creation**:
\`\`\`bash
python create_installer.py portable
\`\`\`

### 2. NSIS Installer
- **Professional Windows installer**
- **Small file size**
- **Custom UI and branding**

**Requirements**:
- Download and install [NSIS](https://nsis.sourceforge.io/)
- Add NSIS to your PATH

**Creation**:
\`\`\`bash
python create_installer.py nsis
\`\`\`

### 3. Inno Setup Installer
- **Popular Windows installer**
- **Rich feature set**
- **Professional appearance**

**Requirements**:
- Download and install [Inno Setup](https://jrsoftware.org/isinfo.php)

**Creation**:
\`\`\`bash
python create_installer.py inno
\`\`\`

### 4. MSI Installer
- **Microsoft standard**
- **Enterprise deployment**
- **Group Policy support**

**Requirements**:
- Download and install [WiX Toolset](https://wixtoolset.org/)

**Creation**:
\`\`\`bash
python create_installer.py msi
\`\`\`

## Prerequisites

### Required Software
1. **Python 3.7+** with pip
2. **cx_Freeze** for building executables:
   \`\`\`bash
   pip install cx_Freeze
   \`\`\`

### Optional Software (for specific installer types)
- **NSIS** - For .exe installers with NSIS
- **Inno Setup** - For .exe installers with Inno Setup  
- **WiX Toolset** - For .msi installers

## Step-by-Step Process

### Step 1: Prepare the Environment
\`\`\`bash
# Install dependencies
pip install -r requirements.txt
pip install cx_Freeze

# Verify Python version
python --version
\`\`\`

### Step 2: Build the Executable
\`\`\`bash
# Build standalone executable
python build_exe.py build
\`\`\`

### Step 3: Create Installers
\`\`\`bash
# Create all installer types
python create_installer.py all

# Or create specific types
python create_installer.py portable
python create_installer.py nsis
python create_installer.py inno
python create_installer.py msi
\`\`\`

## Customization

### Application Information
Edit `create_installer.py` to customize:

\`\`\`python
self.app_name = "System Maintenance Tools"
self.app_version = "1.0.0"
self.app_publisher = "Your Company Name"
self.app_url = "https://your-website.com"
self.app_description = "Your app description"
\`\`\`

### Installer Features
Each installer type supports different customization options:

#### NSIS Features
- Custom icons and graphics
- License agreement display
- Component selection
- Registry entries
- Shortcuts creation
- Uninstaller generation

#### Inno Setup Features
- Modern wizard interface
- Conditional installations
- Custom pages
- Registry modifications
- File associations
- Digital signing support

#### MSI Features
- Windows Installer compliance
- Rollback capabilities
- Administrative installations
- Transform files support
- Patch support

## Advanced Configuration

### Digital Signing
To digitally sign your installers:

1. **Obtain a code signing certificate**
2. **Install SignTool** (Windows SDK)
3. **Add signing to build process**:

\`\`\`bash
# Sign the installer
signtool sign /f certificate.pfx /p password installer.exe
\`\`\`

### Custom Icons
1. **Create .ico file** (16x16, 32x32, 48x48, 256x256)
2. **Place in project directory**
3. **Update installer scripts** to reference icon

### Branding
- **Custom graphics** for installer backgrounds
- **Company logos** and branding
- **Custom color schemes**
- **Branded shortcuts** and Start Menu entries

## Troubleshooting

### Common Issues

#### "Python not found"
- **Solution**: Install Python and add to PATH
- **Verify**: `python --version`

#### "cx_Freeze build failed"
- **Solution**: Check Python version compatibility
- **Try**: `pip install --upgrade cx_Freeze`

#### "NSIS compiler not found"
- **Solution**: Install NSIS and add to PATH
- **Verify**: Check installation directory

#### "Permission denied" errors
- **Solution**: Run as administrator
- **Alternative**: Check file permissions

#### "Missing dependencies"
- **Solution**: Install all requirements
- **Command**: `pip install -r requirements.txt`

### Debug Mode
Enable verbose output for troubleshooting:

\`\`\`bash
# Enable debug logging
set DEBUG=1
python create_installer.py all
\`\`\`

## Distribution

### File Naming Convention
Generated installers follow this pattern:
- **Portable**: `SystemMaintenanceTools_v1.0.0_Portable.zip`
- **NSIS**: `System Maintenance Tools Setup v1.0.0.exe`
- **Inno Setup**: `SystemMaintenanceToolsSetup_v1.0.0.exe`
- **MSI**: `SystemMaintenanceTools.msi`

### Upload Locations
Consider these distribution channels:
- **GitHub Releases** - For open source projects
- **Company website** - For internal distribution
- **Microsoft Store** - For wider distribution
- **Enterprise deployment** - For corporate environments

## Security Considerations

### Code Signing
- **Always sign** production installers
- **Use trusted certificates** from recognized CAs
- **Verify signatures** before distribution

### Antivirus Compatibility
- **Test with major antivirus** software
- **Submit to vendors** for whitelisting if needed
- **Use established signing certificates**

### User Account Control (UAC)
- **Request elevation** when needed
- **Minimize privilege requirements**
- **Clear privilege explanations** to users

## Automation

### CI/CD Integration
Example GitHub Actions workflow:

\`\`\`yaml
name: Build Installers
on: [push, release]
jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Build installers
      run: python create_installer.py all
    - name: Upload artifacts
      uses: actions/upload-artifact@v2
      with:
        name: installers
        path: installers/
\`\`\`

### Scheduled Builds
Set up automated builds for:
- **Nightly builds** from development branch
- **Release candidates** from staging
- **Production releases** from main branch

## Best Practices

### Version Management
- **Semantic versioning** (MAJOR.MINOR.PATCH)
- **Consistent version** across all installer types
- **Version in filenames** for easy identification

### Testing
- **Test on clean systems** without development tools
- **Verify all features** work after installation
- **Test uninstallation** process
- **Check registry cleanup**

### Documentation
- **Installation instructions** for end users
- **System requirements** clearly stated
- **Troubleshooting guide** for common issues
- **Contact information** for support

## Support

For issues with installer creation:
1. **Check the troubleshooting section** above
2. **Review build logs** for specific errors
3. **Verify all prerequisites** are installed
4. **Test on clean Windows system**
5. **Open GitHub issue** with detailed information

---

**Note**: This guide assumes Windows 10/11 development environment. Some steps may vary on different Windows versions.
\`\`\`

```python file="installer_config.py"
"""
Configuration file for installer customization
Modify these settings to customize your installers
"""

import os
from pathlib import Path

class InstallerConfig:
    # Application Information
    APP_NAME = "System Maintenance Tools"
    APP_VERSION = "1.0.0"
    APP_PUBLISHER = "System Administrator"
    APP_URL = "https://github.com/yourusername/system-maintenance-tools"
    APP_DESCRIPTION = "Windows System Maintenance and Administration Tools"
    APP_COPYRIGHT = f"Copyright © 2024 {APP_PUBLISHER}"
    
    # File Information
    EXECUTABLE_NAME = "SystemMaintenanceTools.exe"
    MAIN_SCRIPT = "main.py"
    
    # Directories
    SOURCE_DIR = Path(__file__).parent
    BUILD_DIR = SOURCE_DIR / "build"
    DIST_DIR = SOURCE_DIR / "dist"
    INSTALLER_DIR = SOURCE_DIR / "installers"
    ASSETS_DIR = SOURCE_DIR / "assets"
    
    # Installer Options
    CREATE_DESKTOP_SHORTCUT = True
    CREATE_START_MENU_SHORTCUT = True
    CREATE_QUICK_LAUNCH_SHORTCUT = False
    
    # Registry Settings
    REGISTRY_KEY = f"Software\\{APP_PUBLISHER}\\{APP_NAME}"
    UNINSTALL_KEY = f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
    
    # File Associations (if needed)
    FILE_ASSOCIATIONS = {
        # ".smt": "System Maintenance Tools File"
    }
    
    # Required Files to Include
    REQUIRED_FILES = [
        "main.py",
        "system_commands.py", 
        "registry_manager.py",
        "admin_utils.py",
        "ui_styles.py"
    ]
    
    # Optional Files to Include
    OPTIONAL_FILES = [
        "README.md",
        "LICENSE",
        "requirements.txt",
        "CHANGELOG.md"
    ]
    
    # Installer Customization
    INSTALLER_ICON = "icon.ico"  # Path to installer icon
    APPLICATION_ICON = "app.ico"  # Path to application icon
    LICENSE_FILE = "LICENSE"
    
    # NSIS Specific Settings
    NSIS_SETTINGS = {
        "compression": "lzma",
        "solid_compression": True,
        "modern_ui": True,
        "request_execution_level": "admin"
    }
    
    # Inno Setup Specific Settings
    INNO_SETTINGS = {
        "wizard_style": "modern",
        "compression": "lzma",
        "solid_compression": True,
        "architectures_allowed": "x64",
        "privileges_required": "admin"
    }
    
    # MSI Specific Settings
    MSI_SETTINGS = {
        "platform": "x64",
        "install_scope": "perMachine",
        "upgrade_code": "12345678-1234-1234-1234-123456789012"  # Generate unique GUID
    }
    
    # Build Settings
    BUILD_SETTINGS = {
        "optimize": 2,
        "excludes": ["tkinter", "matplotlib", "numpy"],
        "include_files": [],
        "zip_include_packages": ["PySide6", "psutil"]
    }
    
    @classmethod
    def get_version_info(cls):
        """Get version information for executable"""
        return {
            "version": cls.APP_VERSION + ".0",
            "description": cls.APP_DESCRIPTION,
            "company": cls.APP_PUBLISHER,
            "product": cls.APP_NAME,
            "copyright": cls.APP_COPYRIGHT,
            "trademarks": ""
        }
    
    @classmethod
    def get_installer_filename(cls, installer_type):
        """Generate installer filename based on type"""
        safe_name = cls.APP_NAME.replace(" ", "")
        
        filenames = {
            "portable": f"{safe_name}_v{cls.APP_VERSION}_Portable.zip",
            "nsis": f"{cls.APP_NAME} Setup v{cls.APP_VERSION}.exe",
            "inno": f"{safe_name}Setup_v{cls.APP_VERSION}.exe",
            "msi": f"{safe_name}.msi"
        }
        
        return filenames.get(installer_type, f"{safe_name}_installer")
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check required directories
        if not cls.SOURCE_DIR.exists():
            errors.append(f"Source directory not found: {cls.SOURCE_DIR}")
        
        # Check required files
        for file_name in cls.REQUIRED_FILES:
            file_path = cls.SOURCE_DIR / file_name
            if not file_path.exists():
                errors.append(f"Required file not found: {file_name}")
        
        # Check version format
        version_parts = cls.APP_VERSION.split('.')
        if len(version_parts) != 3:
            errors.append("Version must be in format MAJOR.MINOR.PATCH")
        
        return errors
