"""
Configuration settings for the PC Power Monitor application.
"""

# Application settings
APP_NAME = "PC Power Monitor"
APP_VERSION = "1.0.0"
AUTHOR = "Johan John Joji"
LICENSE = "MIT"

# Default values
DEFAULT_KWH_COST = 0.15  # Default cost per kWh in USD
DEFAULT_POLLING_INTERVAL = 5  # Default polling interval in seconds
DEFAULT_AGGREGATION_INTERVAL = 60  # Default data aggregation interval in seconds

# Database settings
DB_FILENAME = "power_monitor.db"
DB_VERSION = 1

# UI settings
UI_WIDTH = 900
UI_HEIGHT = 600
UI_REFRESH_RATE = 1000  # UI refresh rate in milliseconds
GRAPH_DPI = 100
GRAPH_HEIGHT = 4
GRAPH_WIDTH = 8

# Power estimation settings
# Default power consumption values when direct readings are not available
DEFAULT_CPU_TDP = 65  # Default CPU TDP in watts
DEFAULT_GPU_TDP = 150  # Default GPU TDP in watts
DEFAULT_MOTHERBOARD_POWER = 30  # Default motherboard power consumption in watts
DEFAULT_RAM_PER_STICK = 5  # Default power per RAM stick in watts
DEFAULT_SSD_POWER = 3  # Default SSD power consumption in watts
DEFAULT_HDD_POWER = 7  # Default HDD power consumption in watts
DEFAULT_FAN_POWER = 2  # Default fan power consumption in watts
DEFAULT_IDLE_POWER = 20  # Default idle power consumption in watts

# Component utilization to power mapping
# These are scaling factors for estimating power based on utilization
CPU_UTILIZATION_SCALING = 0.7  # CPU utilization to power scaling factor
GPU_UTILIZATION_SCALING = 0.8  # GPU utilization to power scaling factor