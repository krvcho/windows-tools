"""
Advanced installer creator for System Maintenance Tools
Supports multiple installer types: MSI, NSIS, and Inno Setup
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

class InstallerBuilder:
    def __init__(self):
        self.app_name = "System Maintenance Tools"
        self.app_version = "1.0.0"
        self.app_publisher = "System Administrator"
        self.app_url = "https://github.com/yourusername/system-maintenance-tools"
        self.app_description = "Windows System Maintenance and Administration Tools"
        
        self.source_dir = Path(__file__).parent
        self.build_dir = self.source_dir / "build"
        self.dist_dir = self.source_dir / "dist"
        self.installer_dir = self.source_dir / "installers"
        
        # Create directories
        for dir_path in [self.build_dir, self.dist_dir, self.installer_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def build_executable(self):
        """Build standalone executable using cx_Freeze"""
        print("Building standalone executable...")
        
        try:
            # Run cx_Freeze build
            result = subprocess.run([
                sys.executable, "build_exe.py", "build"
            ], cwd=self.source_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Executable built successfully")
                return True
            else:
                print(f"✗ Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Build error: {str(e)}")
            return False
    
    def create_nsis_installer(self):
        """Create NSIS installer script and build installer"""
        print("Creating NSIS installer...")
        
        nsis_script = self.create_nsis_script()
        script_path = self.installer_dir / "installer.nsi"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(nsis_script)
        
        # Try to build with NSIS
        try:
            nsis_path = self.find_nsis_compiler()
            if nsis_path:
                result = subprocess.run([
                    nsis_path, str(script_path)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✓ NSIS installer created successfully")
                    return True
                else:
                    print(f"✗ NSIS build failed: {result.stderr}")
            else:
                print("✗ NSIS compiler not found. Please install NSIS.")
                print("Download from: https://nsis.sourceforge.io/")
                
        except Exception as e:
            print(f"✗ NSIS error: {str(e)}")
        
        return False
    
    def create_inno_setup_installer(self):
        """Create Inno Setup installer script"""
        print("Creating Inno Setup installer...")
        
        inno_script = self.create_inno_script()
        script_path = self.installer_dir / "installer.iss"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(inno_script)
        
        # Try to build with Inno Setup
        try:
            inno_path = self.find_inno_compiler()
            if inno_path:
                result = subprocess.run([
                    inno_path, str(script_path)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✓ Inno Setup installer created successfully")
                    return True
                else:
                    print(f"✗ Inno Setup build failed: {result.stderr}")
            else:
                print("✗ Inno Setup compiler not found. Please install Inno Setup.")
                print("Download from: https://jrsoftware.org/isinfo.php")
                
        except Exception as e:
            print(f"✗ Inno Setup error: {str(e)}")
        
        return False
    
    def create_msi_installer(self):
        """Create MSI installer using WiX Toolset"""
        print("Creating MSI installer...")
        
        # Create WiX source files
        wxs_content = self.create_wix_script()
        wxs_path = self.installer_dir / "installer.wxs"
        
        with open(wxs_path, 'w', encoding='utf-8') as f:
            f.write(wxs_content)
        
        try:
            wix_path = self.find_wix_compiler()
            if wix_path:
                # Compile WiX source
                candle_path = wix_path / "candle.exe"
                light_path = wix_path / "light.exe"
                
                # Step 1: Compile .wxs to .wixobj
                result1 = subprocess.run([
                    str(candle_path), str(wxs_path), 
                    f"-out", str(self.installer_dir / "installer.wixobj")
                ], capture_output=True, text=True)
                
                if result1.returncode == 0:
                    # Step 2: Link .wixobj to .msi
                    result2 = subprocess.run([
                        str(light_path), str(self.installer_dir / "installer.wixobj"),
                        f"-out", str(self.installer_dir / f"{self.app_name.replace(' ', '')}.msi")
                    ], capture_output=True, text=True)
                    
                    if result2.returncode == 0:
                        print("✓ MSI installer created successfully")
                        return True
                    else:
                        print(f"✗ MSI linking failed: {result2.stderr}")
                else:
                    print(f"✗ WiX compilation failed: {result1.stderr}")
            else:
                print("✗ WiX Toolset not found. Please install WiX Toolset.")
                print("Download from: https://wixtoolset.org/")
                
        except Exception as e:
            print(f"✗ MSI error: {str(e)}")
        
        return False
    
    def create_portable_package(self):
        """Create portable ZIP package"""
        print("Creating portable package...")
        
        try:
            import zipfile
            
            # Find the built executable
            exe_dir = self.build_dir / "exe.win-amd64-3.11"  # Adjust based on your Python version
            if not exe_dir.exists():
                # Try to find any exe directory
                exe_dirs = list(self.build_dir.glob("exe.*"))
                if exe_dirs:
                    exe_dir = exe_dirs[0]
                else:
                    print("✗ No executable directory found. Run build_executable() first.")
                    return False
            
            # Create ZIP file
            zip_path = self.installer_dir / f"{self.app_name.replace(' ', '')}_v{self.app_version}_Portable.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from exe directory
                for file_path in exe_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(exe_dir)
                        zipf.write(file_path, arcname)
                
                # Add additional files
                additional_files = ['README.md', 'LICENSE', 'requirements.txt']
                for file_name in additional_files:
                    file_path = self.source_dir / file_name
                    if file_path.exists():
                        zipf.write(file_path, file_name)
            
            print(f"✓ Portable package created: {zip_path}")
            return True
            
        except Exception as e:
            print(f"✗ Portable package error: {str(e)}")
            return False
    
    def create_nsis_script(self):
        """Generate NSIS installer script"""
        return f'''
; System Maintenance Tools NSIS Installer Script
; Generated automatically - do not edit manually

!define APP_NAME "{self.app_name}"
!define APP_VERSION "{self.app_version}"
!define APP_PUBLISHER "{self.app_publisher}"
!define APP_URL "{self.app_url}"
!define APP_DESCRIPTION "{self.app_description}"

; Modern UI
!include "MUI2.nsh"

; General settings
Name "${{APP_NAME}}"
OutFile "${{APP_NAME}} Setup v${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES64\\${{APP_NAME}}"
InstallDirRegKey HKLM "Software\\${{APP_NAME}}" "InstallDir"
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version information
VIProductVersion "${{APP_VERSION}}.0"
VIAddVersionKey "ProductName" "${{APP_NAME}}"
VIAddVersionKey "ProductVersion" "${{APP_VERSION}}"
VIAddVersionKey "CompanyName" "${{APP_PUBLISHER}}"
VIAddVersionKey "FileDescription" "${{APP_DESCRIPTION}}"
VIAddVersionKey "FileVersion" "${{APP_VERSION}}"

; Installer sections
Section "Core Application" SecCore
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Add files from build directory
    File /r "build\\exe.win-amd64-*\\*"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\SystemMaintenanceTools.exe"
    CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\SystemMaintenanceTools.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\${{APP_NAME}}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\\${{APP_NAME}}" "Version" "${{APP_VERSION}}"
    
    ; Uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    ; Add/Remove Programs entry
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayVersion" "${{APP_VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "Publisher" "${{APP_PUBLISHER}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "URLInfoAbout" "${{APP_URL}}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "NoRepair" 1
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\SystemMaintenanceTools.exe"
SectionEnd

; Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${{SecCore}} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${{SecDesktop}} "Create desktop shortcut"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    RMDir /r "$SMPROGRAMS\\${{APP_NAME}}"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\\${{APP_NAME}}"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
SectionEnd
'''
    
    def create_inno_script(self):
        """Generate Inno Setup installer script"""
        return f'''
; System Maintenance Tools Inno Setup Script
; Generated automatically - do not edit manually

[Setup]
AppId={{{{12345678-1234-1234-1234-123456789012}}}}
AppName={self.app_name}
AppVersion={self.app_version}
AppPublisher={self.app_publisher}
AppPublisherURL={self.app_url}
AppSupportURL={self.app_url}
AppUpdatesURL={self.app_url}
DefaultDirName={{autopf}}\\{self.app_name}
DefaultGroupName={self.app_name}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installers
OutputBaseFilename={self.app_name.replace(" ", "")}Setup_v{self.app_version}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "build\\exe.win-amd64-*\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{self.app_name}"; Filename: "{{app}}\\SystemMaintenanceTools.exe"
Name: "{{group}}\\{{cm:ProgramOnTheWeb,{self.app_name}}}"; Filename: "{self.app_url}"
Name: "{{group}}\\{{cm:UninstallProgram,{self.app_name}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{self.app_name}"; Filename: "{{app}}\\SystemMaintenanceTools.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{self.app_name}"; Filename: "{{app}}\\SystemMaintenanceTools.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\SystemMaintenanceTools.exe"; Description: "{{cm:LaunchProgram,{self.app_name}}}"; Flags: nowait postinstall skipifsilent runascurrentuser

[Registry]
Root: HKLM; Subkey: "Software\\{self.app_name}"; ValueType: string; ValueName: "InstallDir"; ValueData: "{{app}}"
Root: HKLM; Subkey: "Software\\{self.app_name}"; ValueType: string; ValueName: "Version"; ValueData: "{self.app_version}"

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}"
'''
    
    def create_wix_script(self):
        """Generate WiX installer script"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
    <Product Id="*" 
             Name="{self.app_name}" 
             Language="1033" 
             Version="{self.app_version}.0" 
             Manufacturer="{self.app_publisher}" 
             UpgradeCode="12345678-1234-1234-1234-123456789012">
        
        <Package InstallerVersion="200" 
                 Compressed="yes" 
                 InstallScope="perMachine" 
                 Platform="x64"
                 Description="{self.app_description}" />
        
        <MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed." />
        <MediaTemplate EmbedCab="yes" />
        
        <Feature Id="ProductFeature" Title="{self.app_name}" Level="1">
            <ComponentGroupRef Id="ProductComponents" />
        </Feature>
        
        <Directory Id="TARGETDIR" Name="SourceDir">
            <Directory Id="ProgramFiles64Folder">
                <Directory Id="INSTALLFOLDER" Name="{self.app_name}" />
            </Directory>
            <Directory Id="ProgramMenuFolder">
                <Directory Id="ApplicationProgramsFolder" Name="{self.app_name}"/>
            </Directory>
            <Directory Id="DesktopFolder" Name="Desktop"/>
        </Directory>
        
        <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
            <Component Id="MainExecutable" Guid="*">
                <File Id="SystemMaintenanceToolsExe" 
                      Source="build\\exe.win-amd64-3.11\\SystemMaintenanceTools.exe" 
                      KeyPath="yes" />
            </Component>
            
            <!-- Add more components for other files -->
            
            <Component Id="StartMenuShortcuts" Directory="ApplicationProgramsFolder" Guid="*">
                <Shortcut Id="ApplicationStartMenuShortcut"
                         Name="{self.app_name}"
                         Description="{self.app_description}"
                         Target="[INSTALLFOLDER]SystemMaintenanceTools.exe"
                         WorkingDirectory="INSTALLFOLDER"/>
                <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall"/>
                <RegistryValue Root="HKCU" 
                              Key="Software\\{self.app_publisher}\\{self.app_name}"
                              Name="installed" 
                              Type="integer" 
                              Value="1" 
                              KeyPath="yes"/>
            </Component>
            
            <Component Id="DesktopShortcut" Directory="DesktopFolder" Guid="*">
                <Shortcut Id="ApplicationDesktopShortcut"
                         Name="{self.app_name}"
                         Description="{self.app_description}"
                         Target="[INSTALLFOLDER]SystemMaintenanceTools.exe"
                         WorkingDirectory="INSTALLFOLDER"/>
                <RegistryValue Root="HKCU" 
                              Key="Software\\{self.app_publisher}\\{self.app_name}"
                              Name="desktop" 
                              Type="integer" 
                              Value="1" 
                              KeyPath="yes"/>
            </Component>
        </ComponentGroup>
    </Product>
</Wix>
'''
    
    def find_nsis_compiler(self):
        """Find NSIS compiler executable"""
        possible_paths = [
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "NSIS" / "makensis.exe",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "NSIS" / "makensis.exe",
            Path("C:\\NSIS") / "makensis.exe"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def find_inno_compiler(self):
        """Find Inno Setup compiler executable"""
        possible_paths = [
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "Inno Setup 6" / "ISCC.exe",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "Inno Setup 6" / "ISCC.exe",
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "Inno Setup 5" / "ISCC.exe",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "Inno Setup 5" / "ISCC.exe"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def find_wix_compiler(self):
        """Find WiX Toolset compiler directory"""
        possible_paths = [
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "WiX Toolset v3.11" / "bin",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "WiX Toolset v3.11" / "bin",
            Path("C:\\WiX") / "bin"
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "candle.exe").exists():
                return path
        
        return None
    
    def create_all_installers(self):
        """Create all types of installers"""
        print(f"Creating installers for {self.app_name} v{self.app_version}")
        print("=" * 50)
        
        # Step 1: Build executable
        if not self.build_executable():
            print("Failed to build executable. Aborting installer creation.")
            return False
        
        success_count = 0
        total_count = 4
        
        # Step 2: Create different installer types
        if self.create_portable_package():
            success_count += 1
        
        if self.create_nsis_installer():
            success_count += 1
        
        if self.create_inno_setup_installer():
            success_count += 1
        
        if self.create_msi_installer():
            success_count += 1
        
        print("\n" + "=" * 50)
        print(f"Installer creation completed: {success_count}/{total_count} successful")
        
        if success_count > 0:
            print(f"\nInstallers created in: {self.installer_dir}")
            print("Available installers:")
            for installer_file in self.installer_dir.glob("*"):
                if installer_file.is_file():
                    print(f"  - {installer_file.name}")
        
        return success_count > 0

def main():
    """Main function to create installers"""
    builder = InstallerBuilder()
    
    if len(sys.argv) > 1:
        installer_type = sys.argv[1].lower()
        
        if installer_type == "nsis":
            builder.create_nsis_installer()
        elif installer_type == "inno":
            builder.create_inno_setup_installer()
        elif installer_type == "msi":
            builder.create_msi_installer()
        elif installer_type == "portable":
            builder.create_portable_package()
        elif installer_type == "all":
            builder.create_all_installers()
        else:
            print("Usage: python create_installer.py [nsis|inno|msi|portable|all]")
    else:
        builder.create_all_installers()

if __name__ == "__main__":
    main()
