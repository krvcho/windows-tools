using System;
using System.Diagnostics;
using System.Threading.Tasks;

namespace SystemMaintenanceTools
{
    public static class ProcessManager
    {
        public static async Task<int> RunElevatedCommandAsync(string command, string arguments, 
            Action<string> outputCallback = null, Action<string> errorCallback = null)
        {
            return await Task.Run(() =>
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = command,
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    Verb = "runas"
                };

                using (var process = new Process { StartInfo = processInfo })
                {
                    if (outputCallback != null)
                    {
                        process.OutputDataReceived += (sender, e) =>
                        {
                            if (!string.IsNullOrEmpty(e.Data))
                                outputCallback(e.Data);
                        };
                    }

                    if (errorCallback != null)
                    {
                        process.ErrorDataReceived += (sender, e) =>
                        {
                            if (!string.IsNullOrEmpty(e.Data))
                                errorCallback(e.Data);
                        };
                    }

                    process.Start();
                    
                    if (outputCallback != null)
                        process.BeginOutputReadLine();
                    
                    if (errorCallback != null)
                        process.BeginErrorReadLine();
                    
                    process.WaitForExit();
                    return process.ExitCode;
                }
            });
        }

        public static bool IsProcessRunning(string processName)
        {
            var processes = Process.GetProcessesByName(processName);
            return processes.Length > 0;
        }

        public static void KillProcess(string processName)
        {
            var processes = Process.GetProcessesByName(processName);
            foreach (var process in processes)
            {
                try
                {
                    process.Kill();
                    process.WaitForExit();
                }
                catch (Exception)
                {
                    // Process may have already exited
                }
            }
        }
    }
}
