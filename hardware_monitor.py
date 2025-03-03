"""
Hardware monitoring module for the PC Power Monitor application.
Handles hardware detection and power monitoring using LibreHardwareMonitor and psutil.
"""

import os
import time
import json
import threading
from typing import Dict, List, Any, Callable, Optional
import ctypes
import psutil

import config

# Try to import pythonnet for LibreHardwareMonitor
try:
    import clr
    HAS_PYTHONNET = True
except ImportError:
    HAS_PYTHONNET = False
    print("Warning: pythonnet not found. Falling back to estimation-based monitoring.")

class HardwareMonitor:
    """
    Handles hardware detection and power monitoring.
    """
    
    def __init__(self, callback: Optional[Callable[[float, Dict[str, Any]], None]] = None):
        """
        Initialize the hardware monitor.
        
        Args:
            callback: Callback function to call with power readings
        """
        self.callback = callback
        self.components = {}
        self.running = False
        self.monitor_thread = None
        self.lhm_initialized = False
        
        # Initialize LibreHardwareMonitor if available
        if HAS_PYTHONNET:
            self._initialize_lhm()
        
        # Detect hardware components
        self.detect_hardware()
    
    def _initialize_lhm(self) -> None:
        """
        Initialize LibreHardwareMonitor using pythonnet.
        """
        try:
            # Add LibreHardwareMonitor DLL reference
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "libs", "LibreHardwareMonitorLib.dll")
            
            if not os.path.exists(dll_path):
                print(f"Warning: LibreHardwareMonitorLib.dll not found at {dll_path}")
                return
            
            # Check if we're running from a network path
            is_network_path = dll_path.startswith('\\\\') or ':' in dll_path and dll_path[0].lower() not in 'abcdefghijklmnopqrstuvwxyz'
            
            if is_network_path:
                print(f"Detected network path: {dll_path}")
                print("Attempting to copy DLL to a local temporary directory...")
                
                # Create a temporary directory for the DLL
                import tempfile
                import shutil
                temp_dir = tempfile.mkdtemp(prefix="pc_power_monitor_")
                local_dll_path = os.path.join(temp_dir, "LibreHardwareMonitorLib.dll")
                
                # Copy the DLL to the temporary directory
                try:
                    shutil.copy2(dll_path, local_dll_path)
                    print(f"Successfully copied DLL to: {local_dll_path}")
                    dll_path = local_dll_path
                except Exception as copy_error:
                    print(f"Failed to copy DLL: {copy_error}")
                    print("Will try to load from network path with .NET configuration...")
            
            # Configure .NET to allow loading assemblies from network locations
            try:
                print("Configuring .NET to allow loading from remote sources...")
                import System
                from System import AppDomain
                current_domain = AppDomain.CurrentDomain
                current_domain.SetData("LoadFromRemoteSources", True)
                print(".NET configuration successful")
            except Exception as config_error:
                print(f"Error configuring .NET: {config_error}")
            
            # Add the reference to the DLL
            print(f"Attempting to load DLL from: {dll_path}")
            clr.AddReference(dll_path)
            print("DLL reference added successfully")
            
            # Import LibreHardwareMonitor namespaces
            print("Importing LibreHardwareMonitor namespaces...")
            from LibreHardwareMonitor.Hardware import Computer
            
            # Initialize computer instance
            print("Creating Computer instance...")
            self.computer = Computer()
            self.computer.IsCpuEnabled = True
            self.computer.IsGpuEnabled = True
            self.computer.IsMemoryEnabled = True
            self.computer.IsMotherboardEnabled = True
            self.computer.IsStorageEnabled = True
            
            # Open computer
            print("Opening Computer...")
            self.computer.Open()
            
            self.lhm_initialized = True
            print("LibreHardwareMonitor initialized successfully")
            
        except Exception as e:
            print(f"Error initializing LibreHardwareMonitor: {e}")
            import traceback
            traceback.print_exc()
            self.lhm_initialized = False
    
    def detect_hardware(self) -> Dict[str, Any]:
        """
        Detect hardware components and their power characteristics.
        
        Returns:
            Dictionary of detected components
        """
        components = {
            "cpu": self._detect_cpu(),
            "gpu": self._detect_gpu(),
            "motherboard": self._detect_motherboard(),
            "memory": self._detect_memory(),
            "storage": self._detect_storage()
        }
        
        self.components = components
        return components
    
    def _detect_cpu(self) -> Dict[str, Any]:
        """
        Detect CPU and its power characteristics.
        
        Returns:
            CPU information dictionary
        """
        cpu_info = {
            "type": "cpu",
            "name": "Unknown CPU",
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "max_power": config.DEFAULT_CPU_TDP,
            "details": {}
        }
        
        try:
            # Try to get CPU info from psutil
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_info["details"]["base_frequency"] = cpu_freq.current
                if hasattr(cpu_freq, "max"):
                    cpu_info["details"]["max_frequency"] = cpu_freq.max
            
            # Try to get CPU name from platform-specific methods
            if os.name == 'nt':  # Windows
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    cpu_info["name"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"Error getting CPU name from registry: {e}")
            else:  # Linux/Unix
                try:
                    # Try to get CPU info from /proc/cpuinfo
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                cpu_info["name"] = line.split(':', 1)[1].strip()
                                break
                except Exception as e:
                    print(f"Error getting CPU name from /proc/cpuinfo: {e}")
            
            # If we have LibreHardwareMonitor, try to get more detailed info
            if self.lhm_initialized:
                for hardware in self.computer.Hardware:
                    if hardware.HardwareType == 0:  # CPU
                        cpu_info["name"] = hardware.Name
                        # Update hardware sensors
                        hardware.Update()
                        
                        for sensor in hardware.Sensors:
                            # Look for TDP or power sensors
                            if sensor.SensorType == 1:  # Power
                                if "TDP" in sensor.Name or "Package" in sensor.Name:
                                    cpu_info["max_power"] = sensor.Value
                                    break
                        
                        break
        
        except Exception as e:
            print(f"Error detecting CPU: {e}")
        
        return cpu_info
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """
        Detect GPU and its power characteristics.
        
        Returns:
            GPU information dictionary
        """
        gpu_info = {
            "type": "gpu",
            "name": "Unknown GPU",
            "max_power": config.DEFAULT_GPU_TDP,
            "details": {}
        }
        
        try:
            # First try to get NVIDIA GPU info using NVIDIA SMI (works on both Windows and Linux)
            try:
                import subprocess
                print("Trying to detect NVIDIA GPU using nvidia-smi...")
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    gpu_info["name"] = result.stdout.strip()
                    print(f"Detected NVIDIA GPU: {gpu_info['name']}")
                    
                    # Try to get more details
                    power_result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=power.default_limit", "--format=csv,noheader,nounits"],
                        capture_output=True,
                        text=True
                    )
                    if power_result.returncode == 0 and power_result.stdout.strip():
                        try:
                            gpu_info["max_power"] = float(power_result.stdout.strip())
                            print(f"Detected NVIDIA GPU power limit: {gpu_info['max_power']} W")
                        except ValueError:
                            pass
            except Exception as nvidia_error:
                print(f"Error getting NVIDIA GPU info: {nvidia_error}")
            
            # If we still don't have a GPU name, try platform-specific methods
            if gpu_info["name"] == "Unknown GPU":
                if os.name == 'nt':  # Windows
                    try:
                        # Try to use WMI to get GPU info
                        import wmi
                        w = wmi.WMI()
                        for gpu in w.Win32_VideoController():
                            gpu_info["name"] = gpu.Name
                            gpu_info["details"]["adapter_ram"] = gpu.AdapterRAM
                            gpu_info["details"]["driver_version"] = gpu.DriverVersion
                            print(f"Detected GPU via WMI: {gpu_info['name']}")
                            break
                    except Exception as e:
                        print(f"Error getting GPU info from WMI: {e}")
            else:  # Linux/Unix
                try:
                    # Try to get GPU info using lspci
                    import subprocess
                    result = subprocess.run(
                        ["lspci", "-v"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        # Look for VGA or 3D controller
                        for line in result.stdout.split('\n'):
                            if "VGA" in line or "3D controller" in line:
                                # Extract GPU name
                                gpu_info["name"] = line.split(':', 2)[-1].strip()
                                break
                    
                    # Try to get NVIDIA GPU info using nvidia-smi
                    try:
                        nvidia_result = subprocess.run(
                            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                            capture_output=True,
                            text=True
                        )
                        if nvidia_result.returncode == 0 and nvidia_result.stdout.strip():
                            gpu_info["name"] = nvidia_result.stdout.strip()
                    except Exception:
                        pass
                    
                    # Try to get AMD GPU info from sysfs
                    if gpu_info["name"] == "Unknown GPU":
                        amd_cards = []
                        for card in os.listdir("/sys/class/drm/"):
                            if card.startswith("card") and os.path.isdir(f"/sys/class/drm/{card}/device"):
                                try:
                                    with open(f"/sys/class/drm/{card}/device/uevent", "r") as f:
                                        for line in f:
                                            if "DRIVER=amdgpu" in line:
                                                # Found an AMD GPU
                                                with open(f"/sys/class/drm/{card}/device/vendor", "r") as vendor_file:
                                                    vendor = vendor_file.read().strip()
                                                with open(f"/sys/class/drm/{card}/device/device", "r") as device_file:
                                                    device = device_file.read().strip()
                                                amd_cards.append(f"AMD GPU {vendor}:{device}")
                                except Exception:
                                    pass
                        
                        if amd_cards:
                            gpu_info["name"] = amd_cards[0]
                
                except Exception as e:
                    print(f"Error getting GPU info on Linux: {e}")
            
            # If we have LibreHardwareMonitor, try to get more detailed info
            if self.lhm_initialized:
                for hardware in self.computer.Hardware:
                    if hardware.HardwareType == 1:  # GPU
                        gpu_info["name"] = hardware.Name
                        # Update hardware sensors
                        hardware.Update()
                        
                        for sensor in hardware.Sensors:
                            # Look for TDP or power sensors
                            if sensor.SensorType == 1:  # Power
                                if "TDP" in sensor.Name or "Package" in sensor.Name:
                                    gpu_info["max_power"] = sensor.Value
                                    break
                        
                        break
        
        except Exception as e:
            print(f"Error detecting GPU: {e}")
        
        return gpu_info
    
    def _detect_motherboard(self) -> Dict[str, Any]:
        """
        Detect motherboard and its power characteristics.
        
        Returns:
            Motherboard information dictionary
        """
        mb_info = {
            "type": "motherboard",
            "name": "Unknown Motherboard",
            "max_power": config.DEFAULT_MOTHERBOARD_POWER,
            "details": {}
        }
        
        try:
            # Try to get motherboard info from platform-specific methods
            if os.name == 'nt':  # Windows
                try:
                    import wmi
                    w = wmi.WMI()
                    for board in w.Win32_BaseBoard():
                        mb_info["name"] = f"{board.Manufacturer} {board.Product}"
                        mb_info["details"]["manufacturer"] = board.Manufacturer
                        mb_info["details"]["model"] = board.Product
                        break
                except Exception as e:
                    print(f"Error getting motherboard info from WMI: {e}")
            else:  # Linux/Unix
                try:
                    # Try to get motherboard info from DMI
                    manufacturer = "Unknown"
                    product = "Unknown"
                    
                    if os.path.exists("/sys/devices/virtual/dmi/id/board_vendor"):
                        with open("/sys/devices/virtual/dmi/id/board_vendor", "r") as f:
                            manufacturer = f.read().strip()
                    
                    if os.path.exists("/sys/devices/virtual/dmi/id/board_name"):
                        with open("/sys/devices/virtual/dmi/id/board_name", "r") as f:
                            product = f.read().strip()
                    
                    mb_info["name"] = f"{manufacturer} {product}"
                    mb_info["details"]["manufacturer"] = manufacturer
                    mb_info["details"]["model"] = product
                except Exception as e:
                    print(f"Error getting motherboard info from DMI: {e}")
            
            # If we have LibreHardwareMonitor, try to get more detailed info
            if self.lhm_initialized:
                for hardware in self.computer.Hardware:
                    if hardware.HardwareType == 3:  # Motherboard
                        mb_info["name"] = hardware.Name
                        break
        
        except Exception as e:
            print(f"Error detecting motherboard: {e}")
        
        return mb_info
    
    def _detect_memory(self) -> Dict[str, Any]:
        """
        Detect memory and its power characteristics.
        
        Returns:
            Memory information dictionary
        """
        memory_info = {
            "type": "memory",
            "name": "System Memory",
            "max_power": config.DEFAULT_RAM_PER_STICK * 2,  # Assume 2 sticks by default
            "details": {}
        }
        
        try:
            # Get memory info from psutil
            vm = psutil.virtual_memory()
            memory_info["details"]["total"] = vm.total
            memory_info["details"]["available"] = vm.available
            
            # Try to get more detailed memory info from platform-specific methods
            if os.name == 'nt':  # Windows
                try:
                    import wmi
                    w = wmi.WMI()
                    
                    # Count memory sticks
                    memory_sticks = 0
                    total_capacity = 0
                    
                    for mem in w.Win32_PhysicalMemory():
                        memory_sticks += 1
                        if hasattr(mem, "Capacity"):
                            total_capacity += int(mem.Capacity)
                    
                    if memory_sticks > 0:
                        memory_info["max_power"] = config.DEFAULT_RAM_PER_STICK * memory_sticks
                        memory_info["details"]["sticks"] = memory_sticks
                        memory_info["details"]["total_capacity"] = total_capacity
                
                except Exception as e:
                    print(f"Error getting detailed memory info: {e}")
            else:  # Linux/Unix
                try:
                    # Try to get memory stick count using dmidecode (requires root)
                    import subprocess
                    try:
                        result = subprocess.run(
                            ["sudo", "dmidecode", "-t", "memory"],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            # Count memory devices
                            memory_sticks = result.stdout.count("Memory Device")
                            if memory_sticks > 0:
                                memory_info["max_power"] = config.DEFAULT_RAM_PER_STICK * memory_sticks
                                memory_info["details"]["sticks"] = memory_sticks
                    except Exception:
                        # dmidecode might require root privileges
                        pass
                    
                    # Get more detailed memory info from /proc/meminfo
                    if os.path.exists("/proc/meminfo"):
                        with open("/proc/meminfo", "r") as f:
                            for line in f:
                                if line.startswith("MemTotal:"):
                                    # Convert from kB to bytes
                                    total_kb = int(line.split()[1])
                                    memory_info["details"]["total_capacity"] = total_kb * 1024
                                    break
                
                except Exception as e:
                    print(f"Error getting detailed memory info on Linux: {e}")
        
        except Exception as e:
            print(f"Error detecting memory: {e}")
        
        return memory_info
    
    def _detect_storage(self) -> Dict[str, Any]:
        """
        Detect storage devices and their power characteristics.
        
        Returns:
            Storage information dictionary
        """
        storage_info = {
            "type": "storage",
            "devices": [],
            "max_power": 0,
            "details": {}
        }
        
        try:
            # Get disk info from psutil
            for disk in psutil.disk_partitions():
                if disk.device:
                    try:
                        disk_usage = psutil.disk_usage(disk.mountpoint)
                        
                        device_info = {
                            "device": disk.device,
                            "mountpoint": disk.mountpoint,
                            "fstype": disk.fstype,
                            "total": disk_usage.total,
                            "used": disk_usage.used,
                            "free": disk_usage.free,
                            "percent": disk_usage.percent,
                            "is_ssd": self._is_ssd(disk.device),
                        }
                        
                        # Estimate power based on drive type
                        if device_info["is_ssd"]:
                            device_power = config.DEFAULT_SSD_POWER
                        else:
                            device_power = config.DEFAULT_HDD_POWER
                        
                        device_info["power"] = device_power
                        storage_info["max_power"] += device_power
                        storage_info["devices"].append(device_info)
                    
                    except Exception as e:
                        print(f"Error getting disk usage for {disk.device}: {e}")
            
            # If we have LibreHardwareMonitor, try to get more detailed info
            if self.lhm_initialized:
                for hardware in self.computer.Hardware:
                    if hardware.HardwareType == 4:  # Storage
                        # Update hardware sensors
                        hardware.Update()
                        
                        # TODO: Match LHM drives with psutil drives and update info
                        pass
        
        except Exception as e:
            print(f"Error detecting storage: {e}")
        
        return storage_info
    
    def _is_ssd(self, device: str) -> bool:
        """
        Determine if a storage device is an SSD.
        
        Args:
            device: Device path
        
        Returns:
            True if the device is an SSD, False otherwise
        """
        # This is a simplified check and may not be accurate for all systems
        if os.name == 'nt':  # Windows
            try:
                # Remove trailing backslash if present
                if device.endswith('\\'):
                    device = device[:-1]
                
                # Get drive letter
                drive_letter = device.split(':')[0] if ':' in device else device
                
                # Use WMI to check if it's an SSD
                import wmi
                w = wmi.WMI()
                
                for physical_disk in w.Win32_DiskDrive():
                    for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
                        for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                            if logical_disk.DeviceID.startswith(drive_letter):
                                # Check if it's an SSD using MediaType
                                if hasattr(physical_disk, "MediaType"):
                                    return "SSD" in physical_disk.MediaType
                                
                                # Alternative check using WMI
                                for disk in w.MSFT_PhysicalDisk():
                                    if disk.DeviceID == physical_disk.Index:
                                        return disk.MediaType == 4  # 4 = SSD
                
                # Fallback: Check if seek time is very low (typical for SSDs)
                import win32file
                handle = win32file.CreateFile(
                    f"\\\\.\\{drive_letter}:",
                    win32file.GENERIC_READ,
                    win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                
                if handle:
                    # Perform a seek operation and measure time
                    start_time = time.time()
                    win32file.SetFilePointer(handle, 1024*1024, 0)
                    win32file.SetFilePointer(handle, 0, 0)
                    elapsed = time.time() - start_time
                    win32file.CloseHandle(handle)
                    
                    # If seek time is very low, it's likely an SSD
                    return elapsed < 0.005
            
            except Exception as e:
                print(f"Error checking if {device} is an SSD: {e}")
        
        elif os.name == 'posix':  # Linux/Unix
            try:
                # Extract the device name (e.g., /dev/sda1 -> sda)
                import re
                device_name = re.search(r'/dev/([a-zA-Z0-9]+)', device)
                if device_name:
                    device_name = device_name.group(1)
                    # Remove any trailing numbers (partition numbers)
                    device_name = re.sub(r'\d+$', '', device_name)
                    
                    # Check the rotational flag in /sys/block
                    # 0 = SSD, 1 = HDD
                    rotational_path = f"/sys/block/{device_name}/queue/rotational"
                    if os.path.exists(rotational_path):
                        with open(rotational_path, 'r') as f:
                            return f.read().strip() == '0'
                    
                    # Alternative: check if the device is nvme (always SSD)
                    if device_name.startswith('nvme'):
                        return True
            
            except Exception as e:
                print(f"Error checking if {device} is an SSD on Linux: {e}")
        
        # Default to False if we can't determine
        return False
    
    def start_monitoring(self, interval: int = config.DEFAULT_POLLING_INTERVAL) -> None:
        """
        Start monitoring hardware power consumption.
        
        Args:
            interval: Polling interval in seconds
        """
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """
        Stop monitoring hardware power consumption.
        """
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_loop(self, interval: int) -> None:
        """
        Main monitoring loop.
        
        Args:
            interval: Polling interval in seconds
        """
        while self.running:
            try:
                # Get power readings
                total_power, component_data = self.get_power_readings()
                
                # Call callback if provided
                if self.callback:
                    self.callback(total_power, component_data)
                
                # Sleep for the specified interval
                time.sleep(interval)
            
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(1)  # Sleep briefly before retrying
    
    def get_power_readings(self) -> tuple:
        """
        Get current power readings from hardware.
        
        Returns:
            Tuple of (total_power, component_data)
        """
        component_data = {}
        total_power = 0
        
        # If we have LibreHardwareMonitor, use it to get power readings
        if self.lhm_initialized:
            try:
                # Update all hardware
                for hardware in self.computer.Hardware:
                    hardware.Update()
                
                # Get CPU power
                cpu_power = self._get_cpu_power_lhm()
                component_data["cpu"] = cpu_power
                total_power += cpu_power["power"]
                
                # Get GPU power
                gpu_power = self._get_gpu_power_lhm()
                component_data["gpu"] = gpu_power
                total_power += gpu_power["power"]
                
                # Get other component power
                # For now, we'll use estimates for these
                
                # Add motherboard power
                mb_power = self.components["motherboard"]["max_power"]
                component_data["motherboard"] = {"power": mb_power}
                total_power += mb_power
                
                # Add memory power
                memory_power = self.components["memory"]["max_power"]
                component_data["memory"] = {"power": memory_power}
                total_power += memory_power
                
                # Add storage power
                storage_power = self.components["storage"]["max_power"]
                component_data["storage"] = {"power": storage_power}
                total_power += storage_power
            
            except Exception as e:
                print(f"Error getting power readings from LHM: {e}")
                # Fall back to estimation
                return self._estimate_power_consumption()
        
        else:
            # Fall back to estimation
            return self._estimate_power_consumption()
        
        return total_power, component_data
    
    def _get_cpu_power_lhm(self) -> Dict[str, Any]:
        """
        Get CPU power readings from LibreHardwareMonitor.
        
        Returns:
            CPU power data dictionary
        """
        cpu_data = {
            "power": 0,
            "utilization": 0,
            "temperature": 0
        }
        
        try:
            for hardware in self.computer.Hardware:
                if hardware.HardwareType == 0:  # CPU
                    for sensor in hardware.Sensors:
                        if sensor.SensorType == 1:  # Power
                            if "Package" in sensor.Name:
                                cpu_data["power"] = sensor.Value
                        
                        elif sensor.SensorType == 2:  # Temperature
                            if "Package" in sensor.Name:
                                cpu_data["temperature"] = sensor.Value
                        
                        elif sensor.SensorType == 3:  # Load
                            if "Total" in sensor.Name:
                                cpu_data["utilization"] = sensor.Value
            
            # If we couldn't get power directly, estimate it
            if cpu_data["power"] == 0:
                cpu_tdp = self.components["cpu"]["max_power"]
                cpu_util = cpu_data["utilization"] if cpu_data["utilization"] > 0 else psutil.cpu_percent()
                cpu_data["power"] = cpu_tdp * (cpu_util / 100) * config.CPU_UTILIZATION_SCALING
        
        except Exception as e:
            print(f"Error getting CPU power from LHM: {e}")
            # Fall back to estimation
            cpu_tdp = self.components["cpu"]["max_power"]
            cpu_util = psutil.cpu_percent()
            cpu_data["power"] = cpu_tdp * (cpu_util / 100) * config.CPU_UTILIZATION_SCALING
            cpu_data["utilization"] = cpu_util
        
        return cpu_data
    
    def _get_gpu_power_lhm(self) -> Dict[str, Any]:
        """
        Get GPU power readings from LibreHardwareMonitor.
        
        Returns:
            GPU power data dictionary
        """
        gpu_data = {
            "power": 0,
            "utilization": 0,
            "temperature": 0
        }
        
        try:
            for hardware in self.computer.Hardware:
                if hardware.HardwareType == 1:  # GPU
                    for sensor in hardware.Sensors:
                        if sensor.SensorType == 1:  # Power
                            if "Package" in sensor.Name:
                                gpu_data["power"] = sensor.Value
                        
                        elif sensor.SensorType == 2:  # Temperature
                            if "Core" in sensor.Name:
                                gpu_data["temperature"] = sensor.Value
                        
                        elif sensor.SensorType == 3:  # Load
                            if "Core" in sensor.Name:
                                gpu_data["utilization"] = sensor.Value
            
            # If we couldn't get power directly, estimate it
            if gpu_data["power"] == 0:
                # Try to get GPU utilization using NVIDIA SMI (works on both Windows and Linux)
                try:
                    # Try NVIDIA SMI for NVIDIA GPUs
                    import subprocess
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        gpu_util = float(result.stdout.strip())
                        gpu_data["utilization"] = gpu_util
                except Exception:
                    pass
                
                # If we still don't have utilization, use a default value
                if gpu_data["utilization"] == 0:
                    gpu_data["utilization"] = 30  # Assume 30% utilization by default
                
                gpu_tdp = self.components["gpu"]["max_power"]
                gpu_data["power"] = gpu_tdp * (gpu_data["utilization"] / 100) * config.GPU_UTILIZATION_SCALING
        
        except Exception as e:
            print(f"Error getting GPU power from LHM: {e}")
            # Fall back to estimation
            gpu_tdp = self.components["gpu"]["max_power"]
            gpu_data["power"] = gpu_tdp * 0.3 * config.GPU_UTILIZATION_SCALING  # Assume 30% utilization
            gpu_data["utilization"] = 30
        
        return gpu_data
    
    def _estimate_power_consumption(self) -> tuple:
        """
        Estimate power consumption based on component utilization.
        
        Returns:
            Tuple of (total_power, component_data)
        """
        component_data = {}
        total_power = 0
        
        try:
            # Estimate CPU power
            cpu_util = psutil.cpu_percent()
            cpu_tdp = self.components["cpu"]["max_power"]
            cpu_power = cpu_tdp * (cpu_util / 100) * config.CPU_UTILIZATION_SCALING
            
            component_data["cpu"] = {
                "power": cpu_power,
                "utilization": cpu_util,
                "temperature": 0  # We don't have temperature data
            }
            
            total_power += cpu_power
            
            # Estimate GPU power
            # Try to get GPU utilization from platform-specific methods
            gpu_util = 30  # Default to 30% utilization
            
            # Try NVIDIA SMI for NVIDIA GPUs (works on both Windows and Linux)
            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    gpu_util = float(result.stdout.strip())
            except Exception:
                pass
            
            gpu_tdp = self.components["gpu"]["max_power"]
            gpu_power = gpu_tdp * (gpu_util / 100) * config.GPU_UTILIZATION_SCALING
            
            component_data["gpu"] = {
                "power": gpu_power,
                "utilization": gpu_util,
                "temperature": 0  # We don't have temperature data
            }
            
            total_power += gpu_power
            
            # Add motherboard power
            mb_power = self.components["motherboard"]["max_power"]
            component_data["motherboard"] = {"power": mb_power}
            total_power += mb_power
            
            # Add memory power
            memory_power = self.components["memory"]["max_power"]
            component_data["memory"] = {"power": memory_power}
            total_power += memory_power
            
            # Add storage power
            storage_power = self.components["storage"]["max_power"]
            component_data["storage"] = {"power": storage_power}
            total_power += storage_power
            
            # Add idle power
            total_power += config.DEFAULT_IDLE_POWER
            component_data["idle"] = {"power": config.DEFAULT_IDLE_POWER}
        
        except Exception as e:
            print(f"Error estimating power consumption: {e}")
            # Return default values
            return 100, {"cpu": {"power": 50}, "gpu": {"power": 30}, "other": {"power": 20}}
        
        return total_power, component_data
    
    def __del__(self):
        """
        Clean up resources when the object is destroyed.
        """
        self.stop_monitoring()
        
        # Close LibreHardwareMonitor if initialized
        if self.lhm_initialized:
            try:
                self.computer.Close()
            except Exception:
                pass