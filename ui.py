"""
User interface module for the PC Power Monitor application.
Implements the Tkinter GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import datetime
from typing import Dict, Any, List, Tuple, Optional, Callable

import config
from visualization import PowerVisualizer
from hardware_monitor import HardwareMonitor
from data_storage import DataStorage

class PowerMonitorUI:
    """
    Main UI class for the PC Power Monitor application.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the UI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title(config.APP_NAME)
        self.root.geometry(f"{config.UI_WIDTH}x{config.UI_HEIGHT}")
        self.root.minsize(800, 500)
        
        print("Initializing data storage...")
        # Initialize components
        self.data_storage = DataStorage()
        
        print("Initializing hardware monitor...")
        self.hardware_monitor = HardwareMonitor(callback=self._on_power_reading)
        
        print("Initializing visualizer...")
        self.visualizer = PowerVisualizer()
        
        # UI state variables
        try:
            print("Getting kWh cost from database...")
            kwh_cost = self.data_storage.get_kwh_cost()
            print(f"kWh cost retrieved: {kwh_cost}")
            self.kwh_cost = tk.DoubleVar(value=kwh_cost)
        except Exception as e:
            print(f"Error getting kWh cost: {e}")
            # Use default value if database access fails
            self.kwh_cost = tk.DoubleVar(value=config.DEFAULT_KWH_COST)
            
        self.current_power = tk.DoubleVar(value=0)
        self.current_cost = tk.DoubleVar(value=0)
        self.monthly_cost = tk.DoubleVar(value=0)
        
        # Power history data (for real-time graph)
        self.power_history = []
        
        # Component frames
        self.header_frame = None
        self.main_frame = None
        self.status_bar = None
        
        # Tabs
        self.tab_control = None
        self.dashboard_tab = None
        self.history_tab = None
        self.components_tab = None
        self.settings_tab = None
        
        # Dashboard widgets
        self.current_power_label = None
        self.current_cost_label = None
        self.monthly_cost_label = None
        self.power_graph_frame = None
        self.component_graph_frame = None
        
        # History widgets
        self.history_graph_frame = None
        
        # Components widgets
        self.components_tree = None
        
        # Settings widgets
        self.kwh_cost_entry = None
        
        # Create UI
        self._create_ui()
        
        # Start monitoring
        self._start_monitoring()
        
        # Set up periodic UI updates
        self._schedule_ui_update()
    
    def _create_ui(self) -> None:
        """
        Create the UI components.
        """
        # Create styles
        self._create_styles()
        
        # Create header
        self._create_header()
        
        # Create main frame with tabs
        self._create_main_frame()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_styles(self) -> None:
        """
        Create ttk styles for the UI.
        """
        style = ttk.Style()
        
        # Configure the theme
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background='#f5f5f5')
        style.configure('Header.TFrame', background='#2c3e50')
        style.configure('Header.TLabel', background='#2c3e50', foreground='white', font=('Arial', 14, 'bold'))
        style.configure('Status.TFrame', background='#ecf0f1')
        style.configure('Status.TLabel', background='#ecf0f1', foreground='#7f8c8d', font=('Arial', 9))
        
        # Configure tab style
        style.configure('TNotebook', background='#f5f5f5', borderwidth=0)
        style.configure('TNotebook.Tab', padding=[10, 5], font=('Arial', 10))
        
        # Configure button style
        style.configure('TButton', padding=5, font=('Arial', 10))
        
        # Configure entry style
        style.configure('TEntry', padding=5, font=('Arial', 10))
        
        # Configure label style
        style.configure('TLabel', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Value.TLabel', font=('Arial', 24, 'bold'), foreground='#2980b9')
        style.configure('Unit.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        
        # Configure treeview style
        style.configure('Treeview', font=('Arial', 10))
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
    
    def _create_header(self) -> None:
        """
        Create the header frame.
        """
        self.header_frame = ttk.Frame(self.root, style='Header.TFrame')
        self.header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # App title
        title_label = ttk.Label(
            self.header_frame, 
            text=config.APP_NAME, 
            style='Header.TLabel'
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Version
        version_label = ttk.Label(
            self.header_frame, 
            text=f"v{config.APP_VERSION}", 
            style='Header.TLabel'
        )
        version_label.pack(side=tk.RIGHT, padx=10, pady=10)
    
    def _create_main_frame(self) -> None:
        """
        Create the main frame with tabs.
        """
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tab control
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_dashboard_tab()
        self._create_history_tab()
        self._create_components_tab()
        self._create_settings_tab()
    
    def _create_dashboard_tab(self) -> None:
        """
        Create the dashboard tab.
        """
        self.dashboard_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dashboard_tab, text="Dashboard")
        
        # Create left panel for current stats
        left_panel = ttk.Frame(self.dashboard_tab)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Current power consumption
        power_frame = ttk.LabelFrame(left_panel, text="Current Power Consumption")
        power_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.current_power_label = ttk.Label(
            power_frame, 
            textvariable=self.current_power, 
            style='Value.TLabel'
        )
        self.current_power_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(power_frame, text="Watts", style='Unit.TLabel').pack(side=tk.LEFT, pady=10)
        
        # Current cost
        cost_frame = ttk.LabelFrame(left_panel, text="Current Cost")
        cost_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(cost_frame, text="$", style='Value.TLabel').pack(side=tk.LEFT, padx=5, pady=10)
        
        self.current_cost_label = ttk.Label(
            cost_frame, 
            textvariable=self.current_cost, 
            style='Value.TLabel'
        )
        self.current_cost_label.pack(side=tk.LEFT, pady=10)
        
        ttk.Label(cost_frame, text="per hour", style='Unit.TLabel').pack(side=tk.LEFT, padx=5, pady=10)
        
        # Monthly cost projection
        monthly_frame = ttk.LabelFrame(left_panel, text="Monthly Cost Projection")
        monthly_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(monthly_frame, text="$", style='Value.TLabel').pack(side=tk.LEFT, padx=5, pady=10)
        
        self.monthly_cost_label = ttk.Label(
            monthly_frame, 
            textvariable=self.monthly_cost, 
            style='Value.TLabel'
        )
        self.monthly_cost_label.pack(side=tk.LEFT, pady=10)
        
        ttk.Label(monthly_frame, text="per month", style='Unit.TLabel').pack(side=tk.LEFT, padx=5, pady=10)
        
        # Create right panel for graphs
        right_panel = ttk.Frame(self.dashboard_tab)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Power consumption graph
        self.power_graph_frame = ttk.LabelFrame(right_panel, text="Power Consumption")
        self.power_graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Component power graph
        self.component_graph_frame = ttk.LabelFrame(right_panel, text="Component Power Distribution")
        self.component_graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _create_history_tab(self) -> None:
        """
        Create the history tab.
        """
        self.history_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.history_tab, text="History")
        
        # Daily cost graph
        self.history_graph_frame = ttk.LabelFrame(self.history_tab, text="Daily Power Cost")
        self.history_graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get daily power data
        daily_data = self.data_storage.get_daily_power_data()
        
        # If we have data, create the graph
        if daily_data:
            self.visualizer.create_daily_cost_graph(daily_data, self.history_graph_frame).get_tk_widget().pack(
                fill=tk.BOTH, expand=True, padx=5, pady=5
            )
        else:
            ttk.Label(
                self.history_graph_frame, 
                text="No historical data available yet. Data will appear here as it's collected.",
                wraplength=400,
                justify=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def _create_components_tab(self) -> None:
        """
        Create the components tab.
        """
        self.components_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.components_tab, text="Components")
        
        # Create treeview for components
        columns = ("name", "type", "power", "details")
        self.components_tree = ttk.Treeview(
            self.components_tab, 
            columns=columns, 
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.components_tree.heading("name", text="Component")
        self.components_tree.heading("type", text="Type")
        self.components_tree.heading("power", text="Power (W)")
        self.components_tree.heading("details", text="Details")
        
        # Define columns
        self.components_tree.column("name", width=200)
        self.components_tree.column("type", width=100)
        self.components_tree.column("power", width=100)
        self.components_tree.column("details", width=400)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            self.components_tab, 
            orient=tk.VERTICAL, 
            command=self.components_tree.yview
        )
        self.components_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.components_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Populate components
        self._populate_components_tree()
    
    def _create_settings_tab(self) -> None:
        """
        Create the settings tab.
        """
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Settings")
        
        # Create settings form
        settings_frame = ttk.LabelFrame(self.settings_tab, text="Power Cost Settings")
        settings_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)
        
        # kWh cost setting
        ttk.Label(settings_frame, text="Cost per kWh ($):").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        
        self.kwh_cost_entry = ttk.Entry(
            settings_frame, 
            textvariable=self.kwh_cost, 
            width=10
        )
        self.kwh_cost_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Save button
        save_button = ttk.Button(
            settings_frame, 
            text="Save", 
            command=self._save_settings
        )
        save_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Add some explanation text
        ttk.Label(
            settings_frame, 
            text="Enter the cost per kilowatt-hour (kWh) from your electricity bill.",
            wraplength=400
        ).grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Add a separator
        ttk.Separator(self.settings_tab, orient=tk.HORIZONTAL).pack(
            fill=tk.X, padx=10, pady=10
        )
        
        # Add about section
        about_frame = ttk.LabelFrame(self.settings_tab, text="About")
        about_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)
        
        about_text = f"{config.APP_NAME} v{config.APP_VERSION}\n\n" \
                    f"A PC power monitoring application that estimates power consumption " \
                    f"and calculates electricity costs.\n\n" \
                    f"License: {config.LICENSE}"
        
        ttk.Label(
            about_frame, 
            text=about_text,
            wraplength=600,
            justify=tk.LEFT
        ).pack(padx=10, pady=10, anchor=tk.W)
    
    def _create_status_bar(self) -> None:
        """
        Create the status bar.
        """
        self.status_bar = ttk.Frame(self.root, style='Status.TFrame')
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)
        
        # Status label
        self.status_label = ttk.Label(
            self.status_bar, 
            text="Ready", 
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Last updated label
        self.last_updated_label = ttk.Label(
            self.status_bar, 
            text="", 
            style='Status.TLabel'
        )
        self.last_updated_label.pack(side=tk.RIGHT, padx=10, pady=2)
    
    def _populate_components_tree(self) -> None:
        """
        Populate the components treeview with detected components.
        """
        # Clear existing items
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)
        
        # Get components from hardware monitor
        components = self.hardware_monitor.components
        
        # Add CPU
        if "cpu" in components:
            cpu = components["cpu"]
            self.components_tree.insert(
                "", "end", 
                values=(
                    cpu["name"], 
                    "CPU", 
                    f"{cpu['max_power']:.1f}", 
                    f"Cores: {cpu['cores']}, Threads: {cpu['threads']}"
                )
            )
        
        # Add GPU
        if "gpu" in components:
            gpu = components["gpu"]
            self.components_tree.insert(
                "", "end", 
                values=(
                    gpu["name"], 
                    "GPU", 
                    f"{gpu['max_power']:.1f}", 
                    ""
                )
            )
        
        # Add motherboard
        if "motherboard" in components:
            mb = components["motherboard"]
            self.components_tree.insert(
                "", "end", 
                values=(
                    mb["name"], 
                    "Motherboard", 
                    f"{mb['max_power']:.1f}", 
                    ""
                )
            )
        
        # Add memory
        if "memory" in components:
            memory = components["memory"]
            self.components_tree.insert(
                "", "end", 
                values=(
                    memory["name"], 
                    "Memory", 
                    f"{memory['max_power']:.1f}", 
                    f"Total: {memory['details'].get('total', 0) / (1024**3):.1f} GB"
                )
            )
        
        # Add storage devices
        if "storage" in components:
            storage = components["storage"]
            for i, device in enumerate(storage.get("devices", [])):
                self.components_tree.insert(
                    "", "end", 
                    values=(
                        f"Storage {i+1}: {device.get('device', 'Unknown')}",
                        "Storage",
                        f"{device.get('power', 0):.1f}",
                        f"{'SSD' if device.get('is_ssd', False) else 'HDD'}, " \
                        f"Total: {device.get('total', 0) / (1024**3):.1f} GB"
                    )
                )
    
    def _start_monitoring(self) -> None:
        """
        Start monitoring hardware power consumption.
        """
        try:
            # Start the hardware monitor
            self.hardware_monitor.start_monitoring()
            
            # Update status
            self._update_status("Monitoring started")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
            self._update_status(f"Error: {e}")
    
    def _on_power_reading(self, total_power: float, component_data: Dict[str, Any]) -> None:
        """
        Callback for power readings from the hardware monitor.
        
        Args:
            total_power: Total power consumption in watts
            component_data: Dictionary of component-specific power data
        """
        try:
            # Update UI variables
            self.current_power.set(round(total_power, 1))
            
            # Calculate current cost per hour
            kwh_cost = self.kwh_cost.get()
            hourly_cost = (total_power / 1000) * kwh_cost
            self.current_cost.set(round(hourly_cost, 2))
            
            # Calculate monthly cost (assuming 8 hours per day)
            monthly_cost = hourly_cost * 8 * 30
            self.monthly_cost.set(round(monthly_cost, 2))
            
            # Add to power history
            timestamp = datetime.datetime.now()
            self.power_history.append((timestamp, total_power))
            
            # Keep only the last hour of data (assuming 5-second intervals)
            max_history_points = 3600 // config.DEFAULT_POLLING_INTERVAL
            if len(self.power_history) > max_history_points:
                self.power_history = self.power_history[-max_history_points:]
            
            # Save to database
            self.data_storage.save_power_reading(total_power, component_data, kwh_cost)
            
            # Update status
            self._update_status("Monitoring active")
            self._update_last_updated()
        
        except Exception as e:
            print(f"Error processing power reading: {e}")
    
    def _update_status(self, status: str) -> None:
        """
        Update the status bar.
        
        Args:
            status: Status message
        """
        self.status_label.config(text=status)
    
    def _update_last_updated(self) -> None:
        """
        Update the last updated timestamp.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_updated_label.config(text=f"Last updated: {timestamp}")
    
    def _save_settings(self) -> None:
        """
        Save settings to the database.
        """
        try:
            # Get kWh cost from entry
            kwh_cost = self.kwh_cost.get()
            
            # Validate
            if kwh_cost <= 0:
                messagebox.showerror("Error", "Cost per kWh must be greater than zero")
                return
            
            # Save to database
            self.data_storage.set_kwh_cost(kwh_cost)
            
            # Update status
            self._update_status("Settings saved")
            
            # Show confirmation
            messagebox.showinfo("Settings", "Settings saved successfully")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _schedule_ui_update(self) -> None:
        """
        Schedule periodic UI updates.
        """
        # Update graphs
        self._update_graphs()
        
        # Schedule next update
        self.root.after(config.UI_REFRESH_RATE, self._schedule_ui_update)
    
    def _update_graphs(self) -> None:
        """
        Update the graphs with current data.
        """
        try:
            # Update power history graph if we have data
            if self.power_history and hasattr(self, 'power_graph_frame'):
                # Clear existing widgets
                for widget in self.power_graph_frame.winfo_children():
                    widget.destroy()
                
                # Create new graph
                self.visualizer.create_power_history_graph(
                    self.power_history, 
                    self.power_graph_frame
                ).get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Update component power graph if we have data
            if hasattr(self, 'component_graph_frame'):
                # Get latest component data
                _, component_data = self.hardware_monitor.get_power_readings()
                
                # Clear existing widgets
                for widget in self.component_graph_frame.winfo_children():
                    widget.destroy()
                
                # Create new graph
                self.visualizer.create_component_power_graph(
                    component_data, 
                    self.component_graph_frame
                ).get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        except Exception as e:
            print(f"Error updating graphs: {e}")
    
    def run(self) -> None:
        """
        Run the application.
        """
        self.root.mainloop()
    
    def cleanup(self) -> None:
        """
        Clean up resources before exiting.
        """
        # Stop hardware monitoring
        if self.hardware_monitor:
            self.hardware_monitor.stop_monitoring()
        
        # Close database connection
        if self.data_storage:
            self.data_storage.close()