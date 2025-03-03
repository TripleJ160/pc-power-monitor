"""
Visualization module for the PC Power Monitor application.
Handles data visualization using Matplotlib.
"""

import datetime
from typing import List, Dict, Any, Tuple, Optional
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for Tkinter integration
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

import config

class PowerVisualizer:
    """
    Handles data visualization for the PC Power Monitor application.
    """
    
    def __init__(self):
        """
        Initialize the power visualizer.
        """
        self.figure = None
        self.canvas = None
    
    def create_daily_cost_graph(self, data: List[Dict[str, Any]], 
                               parent_widget: tk.Widget) -> FigureCanvasTkAgg:
        """
        Create a graph showing daily power usage cost.
        
        Args:
            data: List of daily power data dictionaries
            parent_widget: Parent Tkinter widget
        
        Returns:
            Matplotlib canvas widget
        """
        # Create figure and axis
        self.figure = Figure(figsize=(config.GRAPH_WIDTH, config.GRAPH_HEIGHT), dpi=config.GRAPH_DPI)
        ax = self.figure.add_subplot(111)
        
        # Extract dates and costs
        dates = []
        costs = []
        
        for item in data:
            try:
                date = datetime.date.fromisoformat(item['date'])
                dates.append(date)
                costs.append(item['cost'])
            except (ValueError, KeyError) as e:
                print(f"Error processing data item: {e}")
        
        # Plot data
        if dates and costs:
            ax.bar(dates, costs, width=0.8, color='#3498db', alpha=0.7)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Format y-axis
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.2f}"))
            
            # Set labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('Cost ($)')
            ax.set_title('Daily PC Power Cost')
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Calculate and display average cost
            avg_cost = sum(costs) / len(costs)
            ax.axhline(y=avg_cost, color='r', linestyle='--', alpha=0.7)
            ax.text(dates[0], avg_cost * 1.05, f"Avg: ${avg_cost:.2f}", color='r')
            
            # Calculate and display total cost
            total_cost = sum(costs)
            ax.text(dates[0], max(costs) * 0.9, f"Total: ${total_cost:.2f}", 
                   bbox=dict(facecolor='white', alpha=0.7))
        
        else:
            ax.text(0.5, 0.5, "No data available", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
        
        # Adjust layout
        self.figure.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent_widget)
        self.canvas.draw()
        
        return self.canvas
    
    def create_component_power_graph(self, component_data: Dict[str, Any], 
                                    parent_widget: tk.Widget) -> FigureCanvasTkAgg:
        """
        Create a graph showing power consumption by component.
        
        Args:
            component_data: Dictionary of component power data
            parent_widget: Parent Tkinter widget
        
        Returns:
            Matplotlib canvas widget
        """
        # Create figure and axis
        self.figure = Figure(figsize=(config.GRAPH_WIDTH, config.GRAPH_HEIGHT), dpi=config.GRAPH_DPI)
        ax = self.figure.add_subplot(111)
        
        # Extract components and power values
        components = []
        power_values = []
        
        for component, data in component_data.items():
            if isinstance(data, dict) and 'power' in data:
                components.append(component.upper())
                power_values.append(data['power'])
        
        # Plot data
        if components and power_values:
            # Define colors for components
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                power_values, 
                labels=components,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(components)],
                wedgeprops={'edgecolor': 'w', 'linewidth': 1, 'antialiased': True}
            )
            
            # Style the text
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_fontweight('bold')
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Set title
            total_power = sum(power_values)
            ax.set_title(f'Power Consumption by Component (Total: {total_power:.1f}W)')
        
        else:
            ax.text(0.5, 0.5, "No data available", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent_widget)
        self.canvas.draw()
        
        return self.canvas
    
    def create_power_history_graph(self, history_data: List[Tuple[datetime.datetime, float]], 
                                  parent_widget: tk.Widget) -> FigureCanvasTkAgg:
        """
        Create a graph showing power consumption history.
        
        Args:
            history_data: List of (timestamp, power) tuples
            parent_widget: Parent Tkinter widget
        
        Returns:
            Matplotlib canvas widget
        """
        # Create figure and axis
        self.figure = Figure(figsize=(config.GRAPH_WIDTH, config.GRAPH_HEIGHT), dpi=config.GRAPH_DPI)
        ax = self.figure.add_subplot(111)
        
        # Extract timestamps and power values
        timestamps = []
        power_values = []
        
        for timestamp, power in history_data:
            timestamps.append(timestamp)
            power_values.append(power)
        
        # Plot data
        if timestamps and power_values:
            ax.plot(timestamps, power_values, '-', color='#3498db', linewidth=2, alpha=0.7)
            
            # Fill area under the curve
            ax.fill_between(timestamps, power_values, color='#3498db', alpha=0.2)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Set labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Power (W)')
            ax.set_title('Power Consumption History')
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Calculate and display average power
            avg_power = sum(power_values) / len(power_values)
            ax.axhline(y=avg_power, color='r', linestyle='--', alpha=0.7)
            ax.text(timestamps[0], avg_power * 1.05, f"Avg: {avg_power:.1f}W", color='r')
        
        else:
            ax.text(0.5, 0.5, "No data available", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
        
        # Adjust layout
        self.figure.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent_widget)
        self.canvas.draw()
        
        return self.canvas
    
    def create_monthly_projection_graph(self, daily_avg_cost: float, kwh_cost: float,
                                       parent_widget: tk.Widget) -> FigureCanvasTkAgg:
        """
        Create a graph showing monthly cost projection.
        
        Args:
            daily_avg_cost: Average daily cost
            kwh_cost: Cost per kWh
            parent_widget: Parent Tkinter widget
        
        Returns:
            Matplotlib canvas widget
        """
        # Create figure and axis
        self.figure = Figure(figsize=(config.GRAPH_WIDTH, config.GRAPH_HEIGHT), dpi=config.GRAPH_DPI)
        ax = self.figure.add_subplot(111)
        
        # Generate usage scenarios
        hours_per_day = [4, 8, 12, 16, 24]
        monthly_costs = []
        
        # Calculate monthly cost for each usage scenario
        for hours in hours_per_day:
            # Calculate ratio compared to current usage
            ratio = hours / 8  # Assuming 8 hours is the baseline
            monthly_costs.append(daily_avg_cost * 30 * ratio)
        
        # Plot data
        ax.bar(hours_per_day, monthly_costs, width=3, color='#3498db', alpha=0.7)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.2f}"))
        
        # Set labels and title
        ax.set_xlabel('Hours of Use per Day')
        ax.set_ylabel('Monthly Cost ($)')
        ax.set_title(f'Monthly Cost Projection (${kwh_cost:.2f}/kWh)')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        for i, cost in enumerate(monthly_costs):
            ax.text(hours_per_day[i], cost + 1, f"${cost:.2f}", 
                   ha='center', va='bottom', fontweight='bold')
        
        # Adjust layout
        self.figure.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent_widget)
        self.canvas.draw()
        
        return self.canvas
    
    def update_graph(self, data: Any) -> None:
        """
        Update the current graph with new data.
        
        Args:
            data: New data for the graph
        """
        if self.figure and self.canvas:
            # Clear the figure
            self.figure.clear()
            
            # Recreate the graph with new data
            # This would depend on the type of graph and data
            # For now, just redraw the canvas
            self.canvas.draw()