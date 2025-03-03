# PC Power Monitor

A Python application that monitors your PC's power consumption and calculates electricity costs using a Tkinter GUI.

## Features

- Real-time monitoring of PC power consumption
- Automatic detection of hardware components
- Calculation of electricity costs based on user-provided kWh rates
- Daily and monthly cost projections
- Historical data tracking and visualization
- Component-specific power consumption breakdown

## Screenshots

(Screenshots will be available after running the application)

## Requirements

- Python 3.8 or higher
- Windows operating system (the application is designed to run natively on Windows)
- Required Python packages (see `requirements.txt`)

> **Note:** While the application includes some cross-platform compatibility code, it is primarily designed for Windows where hardware monitoring capabilities are most accurate. Running on other operating systems will fall back to estimation-based monitoring with reduced accuracy.

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) For more accurate power monitoring, download LibreHardwareMonitor:
   - Download from: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
   - Extract `LibreHardwareMonitorLib.dll` from the release
   - Create a `libs` directory in the application folder
   - Place the DLL in the `libs` directory

## Usage

1. Run the application:

   - On Windows: Double-click `run.bat` or run:
   ```bash
   python main.py
   ```
   
   - On other platforms (limited functionality):
   ```bash
   python main.py
   ```

2. Enter your electricity cost per kWh in the Settings tab
3. The application will automatically detect your hardware and start monitoring
4. View real-time power consumption and cost information in the Dashboard tab
5. Check historical data in the History tab
6. View detailed component information in the Components tab

## Windows-Specific Features

The following features are only available when running on Windows:
- Detailed hardware detection using WMI
- Accurate power monitoring using LibreHardwareMonitor
- SSD/HDD detection
- Memory stick counting

## How It Works

The application uses a combination of methods to estimate your PC's power consumption:

1. **Direct Hardware Monitoring**: When available, the application uses LibreHardwareMonitor to directly read power consumption data from supported hardware components.

2. **Utilization-Based Estimation**: For components without direct power readings, the application estimates power consumption based on utilization percentages and known TDP (Thermal Design Power) values.

3. **Component Detection**: The application automatically detects your PC's hardware components and their specifications to improve estimation accuracy.

4. **Data Storage**: Power consumption data is stored in a local SQLite database for historical tracking and analysis.

## Project Structure

- `main.py` - Application entry point
- `ui.py` - Tkinter GUI implementation
- `hardware_monitor.py` - Hardware detection and power monitoring
- `data_storage.py` - SQLite database operations
- `visualization.py` - Data visualization using Matplotlib
- `config.py` - Application configuration and constants
- `requirements.txt` - Required Python packages

## Limitations

- Power consumption is estimated and may not be 100% accurate
- Some hardware components may not provide direct power readings
- The application is primarily designed for Windows systems

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) for hardware monitoring
- [psutil](https://github.com/giampaolo/psutil) for system information
- [Matplotlib](https://matplotlib.org/) for data visualization
- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI