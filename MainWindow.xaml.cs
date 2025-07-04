using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Principal;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;

namespace SystemMaintenanceTools
{
    public partial class MainWindow : Window
    {
        private Process _currentSfcProcess;
        private Process _currentChkdskProcess;

        public MainWindow()
        {
            InitializeComponent();
            InitializeApplication();
        }

        private void InitializeApplication()
        {
            // Check if running as administrator
            if (!IsRunningAsAdministrator())
            {
                MessageBox.Show("This application requires administrator privileges to function properly.\n\nPlease restart as administrator.", 
                    "Administrator Required", MessageBoxButton.OK, MessageBoxImage.Warning);
            }

            // Populate drive combo box
            PopulateDriveComboBox();
            
            // Add initial messages to output boxes
            SfcOutputTextBox.Text = "Ready to run System File Checker...\n";
            ChkdskOutputTextBox.Text = "Ready to run Disk Check...\n";
            RegistryOutputTextBox.Text = "Ready to apply registry tweaks...\n";
        }

        private bool IsRunningAsAdministrator()
        {
            var identity = WindowsIdentity.GetCurrent();
            var principal = new WindowsPrincipal(identity);
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }

        private void PopulateDriveComboBox()
        {
            var drives = DriveInfo.GetDrives()
                .Where(d => d.DriveType == DriveType.Fixed)
                .Select(d => d.Name.Replace("\\", ""))
                .ToList();

            DriveComboBox.ItemsSource = drives;
            if (drives.Any())
                DriveComboBox.SelectedIndex = 0;
        }

        #region SFC Commands

        private async void RunSfcButton_Click(object sender, RoutedEventArgs e)
        {
            if (!IsRunningAsAdministrator())
            {
                MessageBox.Show("Administrator privileges required to run SFC.", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            RunSfcButton.IsEnabled = false;
            StopSfcButton.IsEnabled = true;
            SfcOutputTextBox.Clear();
            SfcOutputTextBox.AppendText("Starting System File Checker...\n");

            try
            {
                await RunCommandAsync("sfc", "/scannow", SfcOutputTextBox, 
                    process => _currentSfcProcess = process);
            }
            catch (Exception ex)
            {
                SfcOutputTextBox.AppendText($"Error: {ex.Message}\n");
            }
            finally
            {
                RunSfcButton.IsEnabled = true;
                StopSfcButton.IsEnabled = false;
                _currentSfcProcess = null;
            }
        }

        private void StopSfcButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                _currentSfcProcess?.Kill();
                SfcOutputTextBox.AppendText("\nProcess terminated by user.\n");
            }
            catch (Exception ex)
            {
                SfcOutputTextBox.AppendText($"\nError stopping process: {ex.Message}\n");
            }
        }

        #endregion

        #region CHKDSK Commands

        private async void RunChkdskButton_Click(object sender, RoutedEventArgs e)
        {
            if (!IsRunningAsAdministrator())
            {
                MessageBox.Show("Administrator privileges required to run CHKDSK.", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            if (DriveComboBox.SelectedItem == null)
            {
                MessageBox.Show("Please select a drive to check.", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var selectedDrive = DriveComboBox.SelectedItem.ToString();
            var result = MessageBox.Show(
                $"CHKDSK will check drive {selectedDrive} and may require a system restart.\n\nContinue?",
                "Confirm CHKDSK", MessageBoxButton.YesNo, MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes)
                return;

            RunChkdskButton.IsEnabled = false;
            StopChkdskButton.IsEnabled = true;
            ChkdskOutputTextBox.Clear();
            ChkdskOutputTextBox.AppendText($"Starting Disk Check on drive {selectedDrive}...\n");

            try
            {
                await RunCommandAsync("chkdsk", $"{selectedDrive} /f /r", ChkdskOutputTextBox, 
                    process => _currentChkdskProcess = process);
            }
            catch (Exception ex)
            {
                ChkdskOutputTextBox.AppendText($"Error: {ex.Message}\n");
            }
            finally
            {
                RunChkdskButton.IsEnabled = true;
                StopChkdskButton.IsEnabled = false;
                _currentChkdskProcess = null;
            }
        }

        private void StopChkdskButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                _currentChkdskProcess?.Kill();
                ChkdskOutputTextBox.AppendText("\nProcess terminated by user.\n");
            }
            catch (Exception ex)
            {
                ChkdskOutputTextBox.AppendText($"\nError stopping process: {ex.Message}\n");
            }
        }

        #endregion

        #region Registry Tweaks

        private void DisableUpdatesButton_Click(object sender, RoutedEventArgs e)
        {
            if (!IsRunningAsAdministrator())
            {
                MessageBox.Show("Administrator privileges required to modify registry.", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            var result = MessageBox.Show(
                "This will disable Windows automatic updates, Delivery Optimization, and Windows Store auto updates.\n\nContinue?",
                "Confirm Registry Changes", MessageBoxButton.YesNo, MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes)
                return;

            RegistryOutputTextBox.Clear();
            RegistryOutputTextBox.AppendText("Disabling Windows Updates...\n");

            try
            {
                ApplyRegistryTweaks(false);
                RegistryOutputTextBox.AppendText("✓ Windows Updates disabled successfully!\n");
                MessageBox.Show("Windows Updates have been disabled successfully.", "Success", 
                    MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                RegistryOutputTextBox.AppendText($"Error: {ex.Message}\n");
                MessageBox.Show($"Error applying registry changes: {ex.Message}", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void EnableUpdatesButton_Click(object sender, RoutedEventArgs e)
        {
            if (!IsRunningAsAdministrator())
            {
                MessageBox.Show("Administrator privileges required to modify registry.", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            var result = MessageBox.Show(
                "This will re-enable Windows automatic updates and related services.\n\nContinue?",
                "Confirm Registry Changes", MessageBoxButton.YesNo, MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes)
                return;

            RegistryOutputTextBox.Clear();
            RegistryOutputTextBox.AppendText("Enabling Windows Updates...\n");

            try
            {
                ApplyRegistryTweaks(true);
                RegistryOutputTextBox.AppendText("✓ Windows Updates enabled successfully!\n");
                MessageBox.Show("Windows Updates have been enabled successfully.", "Success", 
                    MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                RegistryOutputTextBox.AppendText($"Error: {ex.Message}\n");
                MessageBox.Show($"Error applying registry changes: {ex.Message}", "Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ApplyRegistryTweaks(bool enableUpdates)
        {
            var registryChanges = new Dictionary<string, Dictionary<string, object>>
            {
                // Windows Update Service
                [@"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"] = new Dictionary<string, object>
                {
                    ["NoAutoUpdate"] = enableUpdates ? 0 : 1,
                    ["AUOptions"] = enableUpdates ? 4 : 1
                },
                
                // Delivery Optimization
                [@"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization"] = new Dictionary<string, object>
                {
                    ["DODownloadMode"] = enableUpdates ? 1 : 0
                },
                
                // Windows Store Auto Updates
                [@"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\WindowsStore"] = new Dictionary<string, object>
                {
                    ["AutoDownload"] = enableUpdates ? 4 : 2
                }
            };

            foreach (var keyPath in registryChanges.Keys)
            {
                try
                {
                    using (var key = Registry.LocalMachine.CreateSubKey(keyPath.Replace(@"HKEY_LOCAL_MACHINE\", "")))
                    {
                        if (key != null)
                        {
                            foreach (var value in registryChanges[keyPath])
                            {
                                key.SetValue(value.Key, value.Value, RegistryValueKind.DWord);
                                RegistryOutputTextBox.AppendText($"Set {keyPath}\\{value.Key} = {value.Value}\n");
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    RegistryOutputTextBox.AppendText($"Failed to modify {keyPath}: {ex.Message}\n");
                }
            }
        }

        #endregion

        #region Helper Methods

        private async Task RunCommandAsync(string command, string arguments, TextBox outputTextBox, Action<Process> processCallback)
        {
            await Task.Run(() =>
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = command,
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    Verb = "runas" // Request elevation
                };

                using (var process = new Process { StartInfo = processInfo })
                {
                    processCallback(process);

                    process.OutputDataReceived += (sender, e) =>
                    {
                        if (!string.IsNullOrEmpty(e.Data))
                        {
                            Dispatcher.Invoke(() =>
                            {
                                outputTextBox.AppendText(e.Data + "\n");
                                outputTextBox.ScrollToEnd();
                            });
                        }
                    };

                    process.ErrorDataReceived += (sender, e) =>
                    {
                        if (!string.IsNullOrEmpty(e.Data))
                        {
                            Dispatcher.Invoke(() =>
                            {
                                outputTextBox.AppendText($"ERROR: {e.Data}\n");
                                outputTextBox.ScrollToEnd();
                            });
                        }
                    };

                    process.Start();
                    process.BeginOutputReadLine();
                    process.BeginErrorReadLine();
                    process.WaitForExit();

                    Dispatcher.Invoke(() =>
                    {
                        outputTextBox.AppendText($"\nProcess completed with exit code: {process.ExitCode}\n");
                        outputTextBox.ScrollToEnd();
                    });
                }
            });
        }

        #endregion
    }
}
