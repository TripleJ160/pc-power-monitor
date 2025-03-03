"""
PC Power Monitor - Main Application Entry Point

A PC power monitoring application that estimates power consumption and calculates electricity costs.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# Add the current directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from ui import PowerMonitorUI
from hardware_monitor import HardwareMonitor
import config

def check_dependencies():
    """
    Check if all required dependencies are installed.
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    missing_deps = []
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    # Check for optional dependencies
    try:
        import clr
    except ImportError:
        print("Warning: pythonnet not installed. Falling back to estimation-based monitoring.")
    
    try:
        import wmi
    except ImportError:
        print("Warning: wmi not installed. Some hardware detection features may be limited.")
    
    if missing_deps:
        print(f"Missing required dependencies: {', '.join(missing_deps)}")
        print("Please install them using: pip install " + " ".join(missing_deps))
        return False
    
    return True

def check_lhm_library():
    """
    Check if LibreHardwareMonitor library is available.
    If not, create the libs directory and display instructions.
    """
    libs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
    lhm_path = os.path.join(libs_dir, "LibreHardwareMonitorLib.dll")
    
    if not os.path.exists(lhm_path):
        # Create libs directory if it doesn't exist
        if not os.path.exists(libs_dir):
            os.makedirs(libs_dir)
        
        print("LibreHardwareMonitorLib.dll not found.")
        print(f"For more accurate power monitoring, please download LibreHardwareMonitor and copy the DLL to: {lhm_path}")
        print("Download from: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases")
        print("After downloading, extract LibreHardwareMonitorLib.dll from the release and place it in the 'libs' directory.")
        print("The application will continue with estimation-based monitoring.")

def create_first_run_message():
    """
    Create a message to display on first run.
    
    Returns:
        str: First run message
    """
    message = f"""Welcome to {config.APP_NAME}!

This application monitors your PC's power consumption and calculates electricity costs.

For the most accurate results:
1. Enter your electricity cost per kWh in the Settings tab
2. Let the application run while you use your PC normally
3. Check the Dashboard and History tabs for power consumption and cost information

Note: Power consumption is estimated based on component utilization. For more accurate readings, download LibreHardwareMonitor.

Important: This application is designed for Windows. While it includes some cross-platform compatibility,
the most accurate hardware monitoring is only available on Windows systems.

Enjoy using {config.APP_NAME}!
"""
    return message

def is_first_run():
    """
    Check if this is the first time the application is run.
    
    Returns:
        bool: True if this is the first run, False otherwise
    """
    db_path = config.DB_FILENAME
    return not os.path.exists(db_path)

def check_windows():
    """
    Check if the application is running on Windows.
    
    Returns:
        bool: True if running on Windows, False otherwise
    """
    import platform
    return platform.system() == 'Windows'

def main():
    """
    Main application entry point.
    """
    print("Starting application...")
    
    # Check if running on Windows
    if not check_windows():
        print("Warning: This application is designed to run on Windows.")
        print("Running on other operating systems will use estimation-based monitoring with reduced accuracy.")
        print("For best results, run on Windows with LibreHardwareMonitor.")
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        print("Exiting due to missing dependencies.")
        return
    
    # Check for LibreHardwareMonitor library
    print("Checking LibreHardwareMonitor library...")
    check_lhm_library()
    
    try:
        # Create the main window
        print("Creating main window...")
        root = tk.Tk()
        
        # Set icon if available
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        
        # Create a simplified UI that doesn't use data storage
        print("Initializing simplified UI...")
        
        # Create a simple UI class directly here
        class SimplePowerMonitorUI:
            def __init__(self, root):
                self.root = root
                self.root.title(config.APP_NAME + " (Simplified)")
                self.root.geometry(f"{config.UI_WIDTH}x{config.UI_HEIGHT}")
                self.root.minsize(800, 500)
                
                # Create styles
                style = ttk.Style()
                if 'clam' in style.theme_names():
                    style.theme_use('clam')
                style.configure('TFrame', background='#f5f5f5')
                style.configure('TLabelframe', background='#f5f5f5')
                style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'))
                style.configure('TLabel', font=('Arial', 11))
                style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
                style.configure('Subheader.TLabel', font=('Arial', 12))
                style.configure('TButton', font=('Arial', 11))
                
                # Create a simple label
                main_frame = ttk.Frame(root)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                # Header
                header_frame = ttk.Frame(main_frame)
                header_frame.pack(fill=tk.X, pady=10)
                
                ttk.Label(
                    header_frame,
                    text="PC Power Monitor - Simplified Version",
                    style="Header.TLabel"
                ).pack(side=tk.LEFT, pady=10)
                
                # System Power Summary display
                self.power_frame = ttk.LabelFrame(main_frame, text="System Power Summary")
                self.power_frame.pack(fill=tk.X, padx=10, pady=10)
                
                # Create a grid layout for the power summary
                power_grid = ttk.Frame(self.power_frame)
                power_grid.pack(fill=tk.X, padx=20, pady=10)
                
                # Current Power
                ttk.Label(
                    power_grid,
                    text="Current Power:",
                    font=("Arial", 12)
                ).grid(row=0, column=0, sticky=tk.W, pady=5)
                
                self.power_var = tk.StringVar(value="Calculating...")
                ttk.Label(
                    power_grid,
                    textvariable=self.power_var,
                    font=("Arial", 16, "bold"),
                    foreground="#2980b9"
                ).grid(row=0, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(
                    power_grid,
                    text="Watts",
                    font=("Arial", 12)
                ).grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
                
                # Average Power
                ttk.Label(
                    power_grid,
                    text="Average Power (1 min):",
                    font=("Arial", 12)
                ).grid(row=1, column=0, sticky=tk.W, pady=5)
                
                self.avg_power_var = tk.StringVar(value="Calculating...")
                ttk.Label(
                    power_grid,
                    textvariable=self.avg_power_var,
                    font=("Arial", 16, "bold"),
                    foreground="#2980b9"
                ).grid(row=1, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(
                    power_grid,
                    text="Watts",
                    font=("Arial", 12)
                ).grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
                
                # Monthly Cost
                ttk.Label(
                    power_grid,
                    text="Estimated Monthly Cost (24/7):",
                    font=("Arial", 12)
                ).grid(row=2, column=0, sticky=tk.W, pady=5)
                
                self.monthly_cost_var = tk.StringVar(value="Calculating...")
                ttk.Label(
                    power_grid,
                    textvariable=self.monthly_cost_var,
                    font=("Arial", 16, "bold"),
                    foreground="#2980b9"
                ).grid(row=2, column=1, sticky=tk.W, pady=5)
                
                # kWh Cost Input
                cost_frame = ttk.Frame(power_grid)
                cost_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=10)
                
                ttk.Label(
                    cost_frame,
                    text="kWh Cost ($):",
                    font=("Arial", 12)
                ).pack(side=tk.LEFT, padx=5)
                
                self.kwh_cost_var = tk.StringVar(value=str(config.DEFAULT_KWH_COST))
                kwh_entry = ttk.Entry(
                    cost_frame,
                    textvariable=self.kwh_cost_var,
                    width=6,
                    font=("Arial", 12)
                )
                kwh_entry.pack(side=tk.LEFT, padx=5)
                
                ttk.Button(
                    cost_frame,
                    text="Update",
                    command=self.update_kwh_cost
                ).pack(side=tk.LEFT, padx=5)
                
                # Status message
                self.status_var = tk.StringVar(value="Initializing...")
                status_label = ttk.Label(
                    main_frame,
                    textvariable=self.status_var,
                    font=("Arial", 10, "italic")
                )
                status_label.pack(fill=tk.X, padx=10, pady=5)
                
                # Create a frame for hardware info
                hw_frame = ttk.LabelFrame(main_frame, text="Hardware Information")
                hw_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Create a frame for the text widget and scrollbar
                text_frame = ttk.Frame(hw_frame)
                text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Add scrollbar
                scrollbar = ttk.Scrollbar(text_frame)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Configure text widget with better formatting
                self.hw_text = tk.Text(
                    text_frame,
                    height=20,
                    width=80,
                    font=("Consolas", 11),
                    background="#f8f8f8",
                    foreground="#333333",
                    padx=10,
                    pady=10,
                    wrap=tk.WORD,
                    yscrollcommand=scrollbar.set
                )
                self.hw_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.config(command=self.hw_text.yview)
                
                # Configure text tags for formatting
                self.hw_text.tag_configure("header", font=("Consolas", 12, "bold"), foreground="#2c3e50")
                self.hw_text.tag_configure("subheader", font=("Consolas", 11, "bold"), foreground="#3498db")
                self.hw_text.tag_configure("value", foreground="#27ae60")
                self.hw_text.tag_configure("warning", foreground="#e74c3c")
                
                # Add information about power estimation
                info_frame = ttk.LabelFrame(main_frame, text="Power Estimation Information")
                info_frame.pack(fill=tk.X, padx=10, pady=10)
                
                info_text = tk.Text(
                    info_frame,
                    height=6,
                    width=80,
                    font=("Arial", 10),
                    background="#f8f8f8",
                    foreground="#333333",
                    padx=10,
                    pady=10,
                    wrap=tk.WORD
                )
                info_text.pack(fill=tk.X, padx=5, pady=5)
                
                # Add explanation text about power estimation
                estimation_info = (
                    "Power Estimation Method:\n"
                    "• CPU: Estimated based on TDP (Thermal Design Power) and current utilization. "
                    f"Default TDP: {config.DEFAULT_CPU_TDP}W with {int(config.CPU_UTILIZATION_SCALING*100)}% scaling factor.\n"
                    "• GPU: Estimated based on TDP and current utilization. "
                    f"Default TDP: {config.DEFAULT_GPU_TDP}W with {int(config.GPU_UTILIZATION_SCALING*100)}% scaling factor.\n"
                    f"• Motherboard: Fixed estimate of {config.DEFAULT_MOTHERBOARD_POWER}W\n"
                    f"• Memory: {config.DEFAULT_RAM_PER_STICK}W per RAM stick\n"
                    f"• Storage: {config.DEFAULT_SSD_POWER}W per SSD, {config.DEFAULT_HDD_POWER}W per HDD\n"
                    f"• Idle Power: Additional {config.DEFAULT_IDLE_POWER}W for fans, peripherals, etc.\n"
                    "Note: These are estimates and may vary from actual power consumption."
                )
                
                info_text.insert(tk.END, estimation_info)
                info_text.config(state=tk.DISABLED)  # Make it read-only
                
                # Add a refresh button
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill=tk.X, pady=10)
                
                ttk.Button(
                    button_frame,
                    text="Refresh Now",
                    command=self.refresh_hw_info
                ).pack(side=tk.RIGHT, padx=10)
                
                # Initialize hardware monitor without callback
                self.hardware_monitor = None
                self.update_interval = 2000  # 2 seconds in milliseconds (more frequent updates)
                self.power_history = []
                
                try:
                    print("Initializing hardware monitor...")
                    self.hardware_monitor = HardwareMonitor()
                    self.refresh_hw_info()
                    
                    # Schedule periodic updates
                    self.schedule_update()
                except Exception as e:
                    print(f"Error initializing hardware monitor: {e}")
                    self.hw_text.insert(tk.END, f"Error initializing hardware monitor: {e}\n", "warning")
                    self.status_var.set(f"Error: {e}")
            
            def schedule_update(self):
                """Schedule the next update"""
                self.root.after(self.update_interval, self.auto_update)
            
            def auto_update(self):
                """Automatically update hardware info"""
                self.refresh_hw_info()
                self.schedule_update()
            
            def refresh_hw_info(self):
                """Refresh hardware information display"""
                # Save current scroll position
                current_position = self.hw_text.yview()
                
                # Clear the text widget
                self.hw_text.delete(1.0, tk.END)
                
                if not self.hardware_monitor:
                    self.hw_text.insert(tk.END, "Hardware monitor not available.\n", "warning")
                    self.status_var.set("Error: Hardware monitor not available")
                    return
                
                try:
                    # Get current power readings first
                    total_power, component_data = self.hardware_monitor.get_power_readings()
                    
                    # Update the power history
                    import datetime
                    self.power_history.append((datetime.datetime.now(), total_power))
                    
                    # Keep only the last 12 readings (1 minute at 5-second intervals)
                    if len(self.power_history) > 12:
                        self.power_history = self.power_history[-12:]
                    
                    # Calculate average power over the last minute
                    avg_power = sum(p[1] for p in self.power_history) / len(self.power_history)
                    
                    # Update the power displays
                    self.power_var.set(f"{total_power:.1f}")
                    self.avg_power_var.set(f"{avg_power:.1f}")
                    
                    # Calculate cost if running 24/7 for a month at current power
                    try:
                        kwh_cost = float(self.kwh_cost_var.get())
                    except ValueError:
                        kwh_cost = config.DEFAULT_KWH_COST
                        self.kwh_cost_var.set(str(kwh_cost))
                    
                    monthly_kwh = (total_power / 1000) * 24 * 30
                    monthly_cost = monthly_kwh * kwh_cost
                    
                    # Update monthly cost display
                    self.monthly_cost_var.set(f"${monthly_cost:.2f}")
                    
                    # Update status with timestamp
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    self.status_var.set(f"Last updated: {current_time}")
                    
                    # Get components
                    components = self.hardware_monitor.components
                    
                    # Skip the system summary section in the text widget since we have it in the UI now
                    
                    # COMPONENT POWER BREAKDOWN
                    self.hw_text.insert(tk.END, "COMPONENT POWER BREAKDOWN\n", "header")
                    self.hw_text.insert(tk.END, "═════════════════════════\n\n")
                    
                    # Display component power data
                    for component, data in component_data.items():
                        if isinstance(data, dict) and 'power' in data:
                            component_name = component.capitalize()
                            power_value = data['power']
                            percent = (power_value / total_power) * 100 if total_power > 0 else 0
                            
                            self.hw_text.insert(tk.END, f"{component_name}: ", "subheader")
                            self.hw_text.insert(tk.END, f"{power_value:.1f} W ({percent:.1f}% of total)\n", "value")
                            
                            if 'utilization' in data:
                                self.hw_text.insert(tk.END, f"  Utilization: {data['utilization']:.1f}%\n")
                            if 'temperature' in data and data['temperature'] > 0:
                                self.hw_text.insert(tk.END, f"  Temperature: {data['temperature']:.1f}°C\n")
                            self.hw_text.insert(tk.END, "\n")
                    
                    # HARDWARE DETAILS SECTION
                    self.hw_text.insert(tk.END, "HARDWARE DETAILS\n", "header")
                    self.hw_text.insert(tk.END, "════════════════\n\n")
                    
                    # Display CPU info
                    if "cpu" in components:
                        cpu = components["cpu"]
                        self.hw_text.insert(tk.END, "CPU: ", "subheader")
                        self.hw_text.insert(tk.END, f"{cpu['name']}\n", "value")
                        self.hw_text.insert(tk.END, f"  Cores: {cpu['cores']}, Threads: {cpu['threads']}\n")
                        self.hw_text.insert(tk.END, f"  Estimated Max Power: {cpu['max_power']} W\n\n")
                    
                    # Display GPU info
                    if "gpu" in components:
                        gpu = components["gpu"]
                        self.hw_text.insert(tk.END, "GPU: ", "subheader")
                        self.hw_text.insert(tk.END, f"{gpu['name']}\n", "value")
                        self.hw_text.insert(tk.END, f"  Estimated Max Power: {gpu['max_power']} W\n\n")
                    
                    # Display motherboard info
                    if "motherboard" in components:
                        mb = components["motherboard"]
                        self.hw_text.insert(tk.END, "Motherboard: ", "subheader")
                        self.hw_text.insert(tk.END, f"{mb['name']}\n", "value")
                        self.hw_text.insert(tk.END, f"  Estimated Power: {mb['max_power']} W\n\n")
                    
                    # Display memory info
                    if "memory" in components:
                        memory = components["memory"]
                        total_gb = memory['details'].get('total', 0) / (1024**3)
                        self.hw_text.insert(tk.END, "Memory: ", "subheader")
                        self.hw_text.insert(tk.END, f"{memory['name']}\n", "value")
                        self.hw_text.insert(tk.END, f"  Total: {total_gb:.1f} GB\n")
                        self.hw_text.insert(tk.END, f"  Estimated Power: {memory['max_power']} W\n\n")
                    
                    # Display storage info
                    if "storage" in components:
                        storage = components["storage"]
                        self.hw_text.insert(tk.END, "Storage Devices:\n", "subheader")
                        
                        # Try to get more detailed storage info
                        storage_details = {}
                        
                        # First try to get storage info using platform-specific methods
                        if os.name == 'nt':  # Windows
                            try:
                                # Try using WMI for detailed disk info
                                import wmi
                                w = wmi.WMI()
                                
                                # Get physical disk information
                                for disk in w.Win32_DiskDrive():
                                    # Get model and manufacturer
                                    model = disk.Model.strip() if disk.Model else "Unknown Model"
                                    manufacturer = disk.Manufacturer.strip() if disk.Manufacturer else ""
                                    
                                    if manufacturer and manufacturer.lower() not in model.lower():
                                        model = f"{manufacturer} {model}"
                                    
                                    # Store disk details with both DeviceID and Name as keys for better matching
                                    storage_details[disk.DeviceID] = {
                                        "model": model,
                                        "size": disk.Size,
                                        "interface": disk.InterfaceType if hasattr(disk, "InterfaceType") else "Unknown"
                                    }
                                    
                                    # Also store with the device name for better matching
                                    if hasattr(disk, "Name") and disk.Name:
                                        storage_details[disk.Name] = storage_details[disk.DeviceID]
                                
                                # Try to get logical disk to physical disk mapping
                                logical_to_physical = {}
                                for partition in w.Win32_DiskPartition():
                                    for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                                        for physical_disk in partition.associators("Win32_DiskDriveToDiskPartition"):
                                            logical_to_physical[logical_disk.DeviceID] = physical_disk.DeviceID
                                
                                # Add logical disk mappings to storage_details
                                for logical, physical in logical_to_physical.items():
                                    if physical in storage_details:
                                        storage_details[logical] = storage_details[physical]
                                
                            except Exception as e:
                                print(f"Error getting detailed storage info from WMI: {e}")
                                
                            # Try using PowerShell as a fallback
                            if not storage_details:
                                try:
                                    import subprocess
                                    # Run PowerShell command to get disk info
                                    ps_command = "Get-PhysicalDisk | Select-Object DeviceID,FriendlyName,MediaType,Size | ConvertTo-Json"
                                    result = subprocess.run(["powershell", "-Command", ps_command],
                                                          capture_output=True, text=True)
                                    
                                    if result.returncode == 0 and result.stdout.strip():
                                        import json
                                        disks = json.loads(result.stdout)
                                        # Handle single disk result (not in a list)
                                        if isinstance(disks, dict):
                                            disks = [disks]
                                            
                                        for disk in disks:
                                            model = disk.get("FriendlyName", "Unknown Model")
                                            device_id = f"\\\\.\\PHYSICALDRIVE{disk.get('DeviceID', 0)}"
                                            storage_details[device_id] = {
                                                "model": model,
                                                "size": disk.get("Size", 0),
                                                "interface": disk.get("MediaType", "Unknown")
                                            }
                                except Exception as e:
                                    print(f"Error getting disk info from PowerShell: {e}")
                        else:  # Linux/Unix
                            try:
                                # Try to get disk info using lsblk
                                import subprocess
                                result = subprocess.run(
                                    ["lsblk", "-o", "NAME,MODEL,SIZE,TYPE", "-J"],
                                    capture_output=True, text=True
                                )
                                
                                if result.returncode == 0 and result.stdout.strip():
                                    import json
                                    try:
                                        blk_data = json.loads(result.stdout)
                                        for device in blk_data.get("blockdevices", []):
                                            if device.get("type") == "disk":
                                                dev_name = f"/dev/{device.get('name', '')}"
                                                model = device.get("model", "").strip() or "Unknown Model"
                                                storage_details[dev_name] = {
                                                    "model": model,
                                                    "size": device.get("size", ""),
                                                    "type": device.get("type", "")
                                                }
                                    except json.JSONDecodeError:
                                        print("Error parsing lsblk JSON output")
                            except Exception as e:
                                print(f"Error getting disk info on Linux: {e}")
                        
                        # Filter out network drives and cloud storage
                        physical_devices = []
                        for device in storage.get("devices", []):
                            device_path = device.get('device', 'Unknown')
                            mountpoint = device.get('mountpoint', '').lower()
                            fstype = device.get('fstype', '').lower()
                            
                            # Skip network and virtual drives
                            if (fstype in ['nfs', 'cifs', 'smb', 'smbfs', 'netfs', 'webdav'] or
                                'network' in fstype or
                                'onedrive' in mountpoint or 'google' in mountpoint or 'gdrive' in mountpoint or
                                'dropbox' in mountpoint or 'box' in mountpoint or 'icloud' in mountpoint or
                                'remote' in device_path.lower()):
                                print(f"Skipping network drive: {device_path}")
                                continue
                                
                            # Skip very small partitions (likely recovery or system partitions)
                            total_gb = device.get('total', 0) / (1024**3)
                            if total_gb < 1.0:  # Skip partitions smaller than 1GB
                                continue
                                
                            physical_devices.append(device)
                        
                        for i, device in enumerate(physical_devices):
                            total_gb = device.get('total', 0) / (1024**3)
                            device_path = device.get('device', 'Unknown')
                            
                            # Try to get the device model
                            device_model = "Unknown Model"
                            for disk_id, details in storage_details.items():
                                if disk_id.lower() in device_path.lower() or device_path.lower() in disk_id.lower():
                                    device_model = details["model"]
                                    break
                            
                            self.hw_text.insert(tk.END, f"  Device {i+1}: ", "subheader")
                            self.hw_text.insert(tk.END, f"{device_model} ({device_path})\n", "value")
                            self.hw_text.insert(tk.END, f"    Type: {'SSD' if device.get('is_ssd', False) else 'HDD'}\n")
                            self.hw_text.insert(tk.END, f"    Capacity: {total_gb:.1f} GB\n")
                            self.hw_text.insert(tk.END, f"    Estimated Power: {device.get('power', 0)} W\n\n")
                    
                except Exception as e:
                    self.hw_text.insert(tk.END, f"Error getting hardware information: {e}\n", "warning")
                    import traceback
                    self.hw_text.insert(tk.END, traceback.format_exc(), "warning")
                    self.status_var.set(f"Error: {e}")
                
                # Restore scroll position after updating the text
                self.hw_text.update_idletasks()  # Make sure the widget is updated
                self.hw_text.yview_moveto(current_position[0])
            
            def update_kwh_cost(self):
                """Update the kWh cost and refresh calculations"""
                try:
                    # Validate the input
                    kwh_cost = float(self.kwh_cost_var.get())
                    if kwh_cost <= 0:
                        raise ValueError("Cost must be greater than zero")
                    
                    # Refresh the display with the new cost
                    self.refresh_hw_info()
                    
                    # Show confirmation
                    self.status_var.set(f"kWh cost updated to ${kwh_cost:.2f}")
                except ValueError as e:
                    # Reset to default if invalid
                    self.kwh_cost_var.set(str(config.DEFAULT_KWH_COST))
                    self.status_var.set(f"Error: {e}. Using default cost.")
            
            def run(self):
                """Run the application"""
                self.root.mainloop()
            
            def cleanup(self):
                """Clean up resources"""
                if self.hardware_monitor:
                    self.hardware_monitor.stop_monitoring()
        
        # Create and run the simplified UI
        app = SimplePowerMonitorUI(root)
        
        # Set up cleanup on exit
        def on_closing():
            if hasattr(app, 'cleanup'):
                app.cleanup()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Run the application
        print("Starting main loop...")
        try:
            app.run()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            print(f"Error: {e}")
        finally:
            if hasattr(app, 'cleanup'):
                app.cleanup()
    except Exception as e:
        print(f"Critical error during initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()