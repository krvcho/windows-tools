using System;
using System.Collections.Generic;
using Microsoft.Win32;

namespace SystemMaintenanceTools
{
    public static class RegistryHelper
    {
        public static void SetRegistryValue(string keyPath, string valueName, object value, RegistryValueKind valueKind = RegistryValueKind.DWord)
        {
            try
            {
                using (var key = Registry.LocalMachine.CreateSubKey(keyPath))
                {
                    key?.SetValue(valueName, value, valueKind);
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to set registry value {keyPath}\\{valueName}: {ex.Message}");
            }
        }

        public static object GetRegistryValue(string keyPath, string valueName, object defaultValue = null)
        {
            try
            {
                using (var key = Registry.LocalMachine.OpenSubKey(keyPath))
                {
                    return key?.GetValue(valueName, defaultValue) ?? defaultValue;
                }
            }
            catch
            {
                return defaultValue;
            }
        }

        public static void DeleteRegistryValue(string keyPath, string valueName)
        {
            try
            {
                using (var key = Registry.LocalMachine.OpenSubKey(keyPath, true))
                {
                    key?.DeleteValue(valueName, false);
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to delete registry value {keyPath}\\{valueName}: {ex.Message}");
            }
        }

        public static bool KeyExists(string keyPath)
        {
            try
            {
                using (var key = Registry.LocalMachine.OpenSubKey(keyPath))
                {
                    return key != null;
                }
            }
            catch
            {
                return false;
            }
        }
    }
}
