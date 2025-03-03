"""
Data storage module for the PC Power Monitor application.
Handles database operations for storing and retrieving power usage data.
"""

import sqlite3
import os
import datetime
import json
from typing import Dict, List, Tuple, Any, Optional

import config

class DataStorage:
    """
    Handles all database operations for the PC Power Monitor application.
    """
    
    def __init__(self, db_path: str = config.DB_FILENAME):
        """
        Initialize the data storage module.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """
        Initialize the database connection and create tables if they don't exist.
        """
        db_exists = os.path.exists(self.db_path)
        
        # Add timeout and enable URI mode to handle database locks better
        self.conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level=None)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        
        # Enable WAL mode for better concurrency
        self.cursor.execute("PRAGMA journal_mode=WAL")
        
        if not db_exists:
            self._create_tables()
        
        # Check if we need to update the database schema
        self._check_db_version()
    
    def _create_tables(self) -> None:
        """
        Create the necessary database tables.
        """
        # Settings table
        self.cursor.execute('''
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        # Store the database version
        self.cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("db_version", str(config.DB_VERSION))
        )
        
        # Store default kWh cost
        self.cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("kwh_cost", str(config.DEFAULT_KWH_COST))
        )
        
        # Components table
        self.cursor.execute('''
        CREATE TABLE components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            details TEXT,
            max_power REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Power readings table
        self.cursor.execute('''
        CREATE TABLE power_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_power REAL NOT NULL,
            component_data TEXT,
            cost REAL
        )
        ''')
        
        # Daily aggregated data
        self.cursor.execute('''
        CREATE TABLE daily_power (
            date TEXT PRIMARY KEY,
            avg_power REAL NOT NULL,
            max_power REAL NOT NULL,
            total_energy REAL NOT NULL,
            cost REAL NOT NULL,
            usage_hours REAL NOT NULL
        )
        ''')
        
        self.conn.commit()
    
    def _check_db_version(self) -> None:
        """
        Check the database version and update schema if necessary.
        """
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = 'db_version'")
            db_version = int(self.cursor.fetchone()['value'])
            
            if db_version < config.DB_VERSION:
                # Implement database migration logic here
                # For now, we just update the version
                self.cursor.execute(
                    "UPDATE settings SET value = ? WHERE key = 'db_version'",
                    (str(config.DB_VERSION),)
                )
                self.conn.commit()
        except (sqlite3.Error, TypeError, ValueError) as e:
            print(f"Error checking database version: {e}")
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
    
    def save_components(self, components: List[Dict[str, Any]]) -> None:
        """
        Save detected components to the database.
        
        Args:
            components: List of component dictionaries
        """
        # Clear existing components
        self.cursor.execute("DELETE FROM components")
        
        # Insert new components
        for component in components:
            self.cursor.execute(
                "INSERT INTO components (type, name, details, max_power) VALUES (?, ?, ?, ?)",
                (
                    component['type'],
                    component['name'],
                    json.dumps(component.get('details', {})),
                    component.get('max_power', 0)
                )
            )
        
        self.conn.commit()
    
    def get_components(self) -> List[Dict[str, Any]]:
        """
        Get all components from the database.
        
        Returns:
            List of component dictionaries
        """
        self.cursor.execute("SELECT * FROM components")
        rows = self.cursor.fetchall()
        
        components = []
        for row in rows:
            component = dict(row)
            component['details'] = json.loads(component['details'])
            components.append(component)
        
        return components
    
    def save_power_reading(self, total_power: float, component_data: Dict[str, Any], 
                          kwh_cost: Optional[float] = None) -> None:
        """
        Save a power reading to the database.
        
        Args:
            total_power: Total power consumption in watts
            component_data: Dictionary of component-specific power data
            kwh_cost: Cost per kWh (if None, will use the stored value)
        """
        if kwh_cost is None:
            self.cursor.execute("SELECT value FROM settings WHERE key = 'kwh_cost'")
            kwh_cost = float(self.cursor.fetchone()['value'])
        
        # Calculate cost for this reading (assuming the reading represents 1 hour)
        # Convert watts to kilowatts and multiply by cost per kWh
        cost = (total_power / 1000) * kwh_cost
        
        self.cursor.execute(
            "INSERT INTO power_readings (total_power, component_data, cost) VALUES (?, ?, ?)",
            (total_power, json.dumps(component_data), cost)
        )
        
        self.conn.commit()
        
        # Update daily aggregated data
        self._update_daily_aggregation()
    
    def _update_daily_aggregation(self) -> None:
        """
        Update the daily power aggregation table.
        """
        today = datetime.date.today().isoformat()
        
        # Get today's readings
        self.cursor.execute(
            "SELECT * FROM power_readings WHERE date(timestamp) = date(?)",
            (today,)
        )
        readings = self.cursor.fetchall()
        
        if not readings:
            return
        
        # Calculate aggregated values
        total_power = sum(r['total_power'] for r in readings)
        avg_power = total_power / len(readings)
        max_power = max(r['total_power'] for r in readings)
        
        # Calculate energy in kWh (assuming readings are taken at config.DEFAULT_POLLING_INTERVAL)
        hours_per_reading = config.DEFAULT_POLLING_INTERVAL / 3600
        total_energy = sum((r['total_power'] / 1000) * hours_per_reading for r in readings)
        
        # Calculate cost
        total_cost = sum(r['cost'] for r in readings)
        
        # Calculate usage hours
        usage_hours = len(readings) * hours_per_reading
        
        # Update or insert daily record
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO daily_power 
            (date, avg_power, max_power, total_energy, cost, usage_hours)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (today, avg_power, max_power, total_energy, total_cost, usage_hours)
        )
        
        self.conn.commit()
    
    def get_daily_power_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily power data for the specified number of days.
        
        Args:
            days: Number of days to retrieve data for
        
        Returns:
            List of daily power data dictionaries
        """
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        self.cursor.execute(
            "SELECT * FROM daily_power WHERE date >= ? AND date <= ? ORDER BY date",
            (start_date.isoformat(), end_date.isoformat())
        )
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_kwh_cost(self) -> float:
        """
        Get the current kWh cost.
        
        Returns:
            Current kWh cost
        """
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = 'kwh_cost'")
            row = self.cursor.fetchone()
            
            if row:
                return float(row['value'])
            
            # If no row found, insert the default value
            print(f"No kWh cost found in database, using default: {config.DEFAULT_KWH_COST}")
            self.set_kwh_cost(config.DEFAULT_KWH_COST)
            return config.DEFAULT_KWH_COST
            
        except sqlite3.Error as e:
            print(f"Database error when getting kWh cost: {e}")
            # Return default value if there's a database error
            return config.DEFAULT_KWH_COST
    
    def set_kwh_cost(self, cost: float) -> None:
        """
        Set the kWh cost.
        
        Args:
            cost: New kWh cost
        """
        try:
            self.cursor.execute(
                "UPDATE settings SET value = ? WHERE key = 'kwh_cost'",
                (str(cost),)
            )
            self.conn.commit()
            print(f"Successfully updated kWh cost to {cost}")
        except sqlite3.Error as e:
            print(f"Database error when setting kWh cost: {e}")
            # Try to insert if update failed
            try:
                self.cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("kwh_cost", str(cost))
                )
                self.conn.commit()
                print(f"Successfully inserted kWh cost {cost} using INSERT OR REPLACE")
            except sqlite3.Error as e2:
                print(f"Failed to insert kWh cost after update failed: {e2}")