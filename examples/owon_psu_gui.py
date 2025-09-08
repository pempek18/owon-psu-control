#!/usr/bin/env python3
"""
OWON PSU GUI Application - Multi-Channel Version
A modern graphical user interface for controlling OWON Power Supply Units.
Supports both serial and network connections with 3 independent channels.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime

# Add the parent directory to the Python path to access the owon_psu module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from owon_psu import OwonPSU, OwonPSUError

class ChannelControl:
    """Control class for individual PSU channel."""
    
    def __init__(self, channel_num, psu_instance=None):
        """Initialize channel control."""
        self.channel_num = channel_num
        self.psu = psu_instance
        self.frame = None
        
        # Channel variables
        self.voltage_set = [tk.DoubleVar(value=12.0) for _ in range(3)]
        self.current_set = [tk.DoubleVar(value=1.0) for _ in range(3)]
        self.output_enabled = tk.BooleanVar(value=False)
        
        # Status variables
        self.voltage_measured = tk.StringVar(value="0.000")
        self.current_measured = tk.StringVar(value="0.000")
        self.power_measured = tk.StringVar(value="0.000")
        
    def create_channel_frame(self, parent):
        """Create the channel control frame."""
        self.frame = ttk.LabelFrame(parent, text=f"Channel {self.channel_num}", padding="10")
        
        # Create two-column layout
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        
        # Left column - Voltage control
        voltage_frame = ttk.LabelFrame(self.frame, text="Voltage Control", padding="10")
        voltage_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        ttk.Label(voltage_frame, text="Set Voltage (V):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        voltage_entry = ttk.Entry(voltage_frame, textvariable=self.voltage_set[self.channel_num - 1], width=15)
        voltage_entry.grid(row=1, column=0, pady=(0, 10))
        
        ttk.Button(voltage_frame, text="Set Voltage", command=self.set_voltage).grid(row=2, column=0, pady=(0, 10))
        
        # Voltage adjustment buttons
        adj_frame = ttk.Frame(voltage_frame)
        adj_frame.grid(row=3, column=0)
        
        ttk.Button(adj_frame, text="-0.1V", command=lambda: self.adjust_voltage(-0.1)).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(adj_frame, text="-1V", command=lambda: self.adjust_voltage(-1.0)).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(adj_frame, text="+1V", command=lambda: self.adjust_voltage(1.0)).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(adj_frame, text="+0.1V", command=lambda: self.adjust_voltage(0.1)).grid(row=0, column=3)
        
        # Right column - Current control
        current_frame = ttk.LabelFrame(self.frame, text="Current Control", padding="10")
        current_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        ttk.Label(current_frame, text="Set Current (A):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        current_entry = ttk.Entry(current_frame, textvariable=self.current_set[self.channel_num - 1], width=15)
        current_entry.grid(row=1, column=0, pady=(0, 10))
        
        ttk.Button(current_frame, text="Set Current", command=self.set_current).grid(row=2, column=0, pady=(0, 10))
        
        # Current adjustment buttons
        adj_frame2 = ttk.Frame(current_frame)
        adj_frame2.grid(row=3, column=0)
        
        ttk.Button(adj_frame2, text="-0.1A", command=lambda: self.adjust_current(-0.1)).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(adj_frame2, text="-0.5A", command=lambda: self.adjust_current(-0.5)).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(adj_frame2, text="+0.5A", command=lambda: self.adjust_current(0.5)).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(adj_frame2, text="+0.1A", command=lambda: self.adjust_current(0.1)).grid(row=0, column=3)
        
        # Output control and measurements
        control_frame = ttk.LabelFrame(self.frame, text="Output Control & Measurements", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Output control
        output_frame = ttk.Frame(control_frame)
        output_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.output_check = ttk.Checkbutton(output_frame, text="Enable Output", variable=self.output_enabled, command=self.toggle_output)
        self.output_check.grid(row=0, column=0, padx=(0, 20))
        
        ttk.Button(output_frame, text="Safe Shutdown", command=self.safe_shutdown).grid(row=0, column=1, padx=(0, 20))
        
        # Measurements display
        measurements_frame = ttk.Frame(control_frame)
        measurements_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(measurements_frame, text="Measured Voltage:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(measurements_frame, textvariable=self.voltage_measured, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(measurements_frame, text="Measured Current:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        ttk.Label(measurements_frame, textvariable=self.current_measured, font=("Arial", 10, "bold")).grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(measurements_frame, text="Measured Power:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Label(measurements_frame, textvariable=self.power_measured, font=("Arial", 10, "bold")).grid(row=1, column=1, sticky=tk.W, padx=(0, 20), pady=(5, 0))
        
    def set_psu(self, psu_instance):
        """Set the PSU instance for this channel."""
        self.psu = psu_instance
        
    def set_voltage(self):
        """Set voltage for this channel."""
        if not self.psu:
            return
        try:
            self.voltage_set[self.channel_num - 1].set(self.voltage_set[self.channel_num - 1].get())
            # Use channel-specific SCPI command directly
            self.psu.write(f"APP:VOLT {self.voltage_set[0].get():.3f}, {self.voltage_set[1].get():.3f}, {self.voltage_set[2].get():.3f}")
        except Exception as e:
            print(f"Channel {self.channel_num} voltage error: {e}")
            
    def set_current(self):
        """Set current for this channel."""
        if not self.psu:
            return
        try:
            self.current_set[self.channel_num - 1].set(self.current_set[self.channel_num - 1].get())
            # Use channel-specific SCPI command directly
            self.psu.write(f"APP:CURR {self.current_set[0].get():.3f}, {self.current_set[1].get():.3f}, {self.current_set[2].get():.3f}")
        except Exception as e:
            print(f"Channel {self.channel_num} current error: {e}")
            
    def adjust_voltage(self, delta):
        """Adjust voltage by delta."""
        new_voltage = max(0, self.voltage_set.get() + delta)
        self.voltage_set.set(new_voltage)
        self.set_voltage()
        
    def adjust_current(self, delta):
        """Adjust current by delta."""
        new_current = max(0, self.current_set.get() + delta)
        self.current_set.set(new_current)
        self.set_current()
        
    def toggle_output(self):
        """Toggle output on/off."""
        if not self.psu:
            return
        try:
            # Use channel-specific SCPI command directly
            state = 1 if self.output_enabled.get() else 0
            self.psu.write(f"APP:OUTP {state},{self.channel_num}")
        except Exception as e:
            print(f"Channel {self.channel_num} output error: {e}")
            
    def safe_shutdown(self):
        """Perform safe shutdown for this channel."""
        if not self.psu:
            return
        try:
            # Set voltage to 0 and disable output for this channel
            self.psu.write(f"APP:VOLT 0.0,0.0,0.0")
            self.psu.write(f"APP:OUTP 0,0,0")
            self.output_enabled.set(False)
            self.voltage_set.set(0.0)
        except Exception as e:
            print(f"Channel {self.channel_num} shutdown error: {e}")
            
    def update_measurements(self, status):
        """Update measurement displays."""
        try:
            self.voltage_measured.set(f"{status['voltage']:.3f}")
            self.current_measured.set(f"{status['current']:.3f}")
            self.power_measured.set(f"{status['power']:.3f}")
        except Exception as e:
            print(f"Channel {self.channel_num} measurement error: {e}")

class OwonPSUGUI:
    """Main GUI application for OWON PSU control with 3 channels."""
    
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("OWON PSU Control - Multi-Channel")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # PSU connection
        self.psu = None
        self.connected = False
        self.monitoring = False
        self.monitor_thread = None
        
        # Channel controls
        self.channels = []
        for i in range(1, 4):  # Channels 1, 2, 3
            self.channels.append(ChannelControl(i))
        
        # GUI variables
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Start monitoring thread
        self.start_monitoring()
        
    def setup_variables(self):
        """Setup tkinter variables."""
        # Connection variables
        self.connection_type = tk.StringVar(value="network")
        self.ip_address = tk.StringVar(value="10.0.10.99")
        self.port = tk.StringVar(value="3000")
        self.serial_port = tk.StringVar(value="COM3")
        
        # Global status variables
        self.device_status = tk.StringVar(value="Disconnected")
        self.current_channel = tk.IntVar(value=1)  # Currently selected channel
        
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Connection panel
        self.create_connection_panel(main_frame)
        
        # Channel tabs
        self.create_channel_tabs(main_frame)
        
        # Log panel
        self.create_log_panel(main_frame)
        
    def create_connection_panel(self, parent):
        """Create connection configuration panel."""
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="10")
        conn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection type
        ttk.Radiobutton(conn_frame, text="Network", variable=self.connection_type, 
                        value="network", command=self.on_connection_type_change).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Radiobutton(conn_frame, text="Serial", variable=self.connection_type, 
                        value="serial", command=self.on_connection_type_change).grid(row=0, column=1, sticky=tk.W)
        
        # Network settings
        self.network_frame = ttk.Frame(conn_frame)
        self.network_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(self.network_frame, text="IP Address:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(self.network_frame, textvariable=self.ip_address, width=15).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(self.network_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(self.network_frame, textvariable=self.port, width=8).grid(row=0, column=3, padx=(0, 20))
        
        # Serial settings
        self.serial_frame = ttk.Frame(conn_frame)
        self.serial_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(self.serial_frame, text="Serial Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(self.serial_frame, textvariable=self.serial_port, width=15).grid(row=0, column=1, padx=(0, 20))
        
        # Connection buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.connect_btn = ttk.Button(button_frame, text="Connect", command=self.connect_psu)
        self.connect_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect", command=self.disconnect_psu, state="disabled")
        self.disconnect_btn.grid(row=0, column=1)
        
        # Initially hide serial frame
        self.serial_frame.grid_remove()
        
    def create_channel_tabs(self, parent):
        """Create tabbed interface for channels."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Create tabs for each channel
        for i, channel in enumerate(self.channels):
            tab_frame = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(tab_frame, text=f"Channel {i+1}")
            
            # Create channel control frame
            channel.create_channel_frame(tab_frame)
            channel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Configure grid weights
            tab_frame.grid_rowconfigure(0, weight=1)
            tab_frame.grid_columnconfigure(0, weight=1)
            
        # Add global controls tab
        self.create_global_controls_tab()
        
    def create_global_controls_tab(self):
        """Create global controls tab."""
        global_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(global_frame, text="Global Controls")
        
        # Device status
        status_frame = ttk.LabelFrame(global_frame, text="Device Status", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(status_frame, text="Device Status:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.status_label = ttk.Label(status_frame, textvariable=self.device_status, foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Global actions
        actions_frame = ttk.LabelFrame(global_frame, text="Global Actions", padding="10")
        actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(actions_frame, text="Reset All Channels", command=self.reset_all_channels).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(actions_frame, text="Safe Shutdown All", command=self.safe_shutdown_all).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(actions_frame, text="Enable All Outputs", command=self.enable_all_outputs).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(actions_frame, text="Disable All Outputs", command=self.disable_all_outputs).grid(row=0, column=3)
        
        # Bulk voltage/current setting
        bulk_frame = ttk.LabelFrame(global_frame, text="Bulk Settings", padding="10")
        bulk_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(bulk_frame, text="Set All Voltages (V):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.bulk_voltage_entry = ttk.Entry(bulk_frame, width=20)
        self.bulk_voltage_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(bulk_frame, text="Set All Voltages", command=self.set_all_voltages).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Label(bulk_frame, text="Set All Currents (A):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.bulk_current_entry = ttk.Entry(bulk_frame, width=20)
        self.bulk_current_entry.grid(row=1, column=1, padx=(0, 10), pady=(5, 0))
        ttk.Button(bulk_frame, text="Set All Currents", command=self.set_all_currents).grid(row=1, column=2, padx=(0, 10), pady=(5, 0))
        
        # Channel overview
        overview_frame = ttk.LabelFrame(global_frame, text="Channel Overview", padding="10")
        overview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create overview table
        columns = ("Channel", "Voltage (V)", "Current (A)", "Power (W)", "Output")
        self.overview_tree = ttk.Treeview(overview_frame, columns=columns, show="headings", height=4)
        
        for col in columns:
            self.overview_tree.heading(col, text=col)
            self.overview_tree.column(col, width=100, anchor="center")
            
        self.overview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for overview
        scrollbar = ttk.Scrollbar(overview_frame, orient="vertical", command=self.overview_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.overview_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        global_frame.grid_rowconfigure(2, weight=1)
        global_frame.grid_columnconfigure(0, weight=1)
        overview_frame.grid_rowconfigure(0, weight=1)
        overview_frame.grid_columnconfigure(0, weight=1)
        
        
    def create_log_panel(self, parent):
        """Create log display panel."""
        log_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log control buttons
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(log_button_frame, text="Clear Log", command=self.clear_log).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(log_button_frame, text="Save Log", command=self.save_log).grid(row=0, column=1)
        
    def on_connection_type_change(self):
        """Handle connection type change."""
        if self.connection_type.get() == "network":
            self.network_frame.grid()
            self.serial_frame.grid_remove()
        else:
            self.network_frame.grid_remove()
            self.serial_frame.grid()
            
    def log_message(self, message):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Clear the log."""
        self.log_text.delete(1.0, tk.END)
        
    def save_log(self):
        """Save log to file."""
        try:
            filename = f"owon_psu_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Log saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")
            
    def connect_psu(self):
        """Connect to PSU."""
        try:
            if self.connection_type.get() == "network":
                ip = self.ip_address.get()
                port = int(self.port.get())
                self.log_message(f"Connecting to {ip}:{port}...")
                
                self.psu = OwonPSU(port="COM1", serial=False)
                self.psu.open_network(ip, port)
            else:
                port = self.serial_port.get()
                self.log_message(f"Connecting to serial port {port}...")
                
                self.psu = OwonPSU(port, serial=True)
                self.psu.open_serial()
                
            self.connected = True
            self.device_status.set("Connected")
            self.status_label.config(foreground="green")
            
            # Update UI
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            
            # Get device info
            identity = self.psu.get_identity()
            self.log_message(f"Connected to: {identity}")
            
            # Update all channel controls with PSU instance
            for channel in self.channels:
                channel.set_psu(self.psu)
                # Update channel values with channel-specific commands
                try:
                    # Use channel-specific query commands
                    voltage = float(self.psu.query(f"APP:VOLT? {channel.channel_num}"))
                    current = float(self.psu.query(f"APP:CURR? {channel.channel_num}"))
                    output = self.psu.query(f"APP:OUTP? {channel.channel_num}") == "1"
                    
                    channel.voltage_set.set(voltage)
                    channel.current_set.set(current)
                    channel.output_enabled.set(output)
                except:
                    pass  # Handle case where channel-specific commands aren't available
            
        except Exception as e:
            self.log_message(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", str(e))
            
    def disconnect_psu(self):
        """Disconnect from PSU."""
        try:
            if self.psu:
                self.psu.close()
                self.psu = None
                
            self.connected = False
            self.device_status.set("Disconnected")
            self.status_label.config(foreground="red")
            
            # Update UI
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            
            # Clear all channel measurements
            for channel in self.channels:
                channel.voltage_measured.set("0.000")
                channel.current_measured.set("0.000")
                channel.power_measured.set("0.000")
                channel.set_psu(None)
            
            self.log_message("Disconnected from PSU")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {e}")
            
    def reset_all_channels(self):
        """Reset all channels to defaults."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to PSU first")
            return
            
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all channels to defaults?"):
            try:
                self.psu.reset()
                self.log_message("All channels reset to defaults")
                # Update UI after reset
                time.sleep(0.5)
                for channel in self.channels:
                    try:
                        # Use channel-specific query commands
                        voltage = float(self.psu.query(f"APP:VOLT? {channel.channel_num}"))
                        current = float(self.psu.query(f"APP:CURR? {channel.channel_num}"))
                        output = self.psu.query(f"APP:OUTP? {channel.channel_num}") == "1"
                        
                        channel.voltage_set.set(voltage)
                        channel.current_set.set(current)
                        channel.output_enabled.set(output)
                    except:
                        pass
            except Exception as e:
                self.log_message(f"Reset failed: {e}")
                messagebox.showerror("Error", f"Reset failed: {e}")
                
    def safe_shutdown_all(self):
        """Perform safe shutdown for all channels."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to PSU first")
            return
            
        try:
            # Safe shutdown each channel individually
            for channel in self.channels:
                channel.safe_shutdown()
            self.log_message("Safe shutdown completed for all channels")
        except Exception as e:
            self.log_message(f"Safe shutdown failed: {e}")
            messagebox.showerror("Error", f"Safe shutdown failed: {e}")
            
    def enable_all_outputs(self):
        """Enable output for all channels."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to PSU first")
            return
            
        try:
            for channel in self.channels:
                channel.output_enabled.set(True)
                channel.toggle_output()
            self.log_message("All outputs enabled")
        except Exception as e:
            self.log_message(f"Failed to enable all outputs: {e}")
            messagebox.showerror("Error", f"Failed to enable all outputs: {e}")
            
    def disable_all_outputs(self):
        """Disable output for all channels."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to PSU first")
            return
            
        try:
            for channel in self.channels:
                channel.output_enabled.set(False)
                channel.toggle_output()
            self.log_message("All outputs disabled")
        except Exception as e:
            self.log_message(f"Failed to disable all outputs: {e}")
            messagebox.showerror("Error", f"Failed to disable all outputs: {e}")
            
    def set_all_voltages(self):
        """Set voltage for all channels using bulk command."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to PSU first")
            return
            
        try:
            voltage_text = self.bulk_voltage_entry.get().strip()
            if not voltage_text:
                messagebox.showwarning("Invalid Input", "Please enter voltage values")
                return
                
            # Parse voltage values (comma-separated or single value)
            if ',' in voltage_text:
                voltages = [float(v.strip()) for v in voltage_text.split(',')]
                if len(voltages) != 3:
                    messagebox.showwarning("Invalid Input", "Please enter exactly 3 voltage values (comma-separated)")
                    return
            else:
                # Single value for all channels
                voltage = float(voltage_text)
                voltages = [voltage, voltage, voltage]
            
            # Send bulk voltage command
            voltage_cmd = f"APP:VOLT {voltages[0]:.3f},{voltages[1]:.3f},{voltages[2]:.3f}"
            self.psu.write(voltage_cmd)
            
            # Update GUI values
            for i, channel in enumerate(self.channels):
                channel.voltage_set.set(voltages[i])
            
            self.log_message(f"Set all voltages: CH1={voltages[0]}V, CH2={voltages[1]}V, CH3={voltages[2]}V")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers")
        except Exception as e:
            self.log_message(f"Failed to set all voltages: {e}")
            messagebox.showerror("Error", f"Failed to set all voltages: {e}")
            
    def set_all_currents(self):
        """Set current for all channels using bulk command."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to PSU first")
            return
            
        try:
            current_text = self.bulk_current_entry.get().strip()
            if not current_text:
                messagebox.showwarning("Invalid Input", "Please enter current values")
                return
                
            # Parse current values (comma-separated or single value)
            if ',' in current_text:
                currents = [float(c.strip()) for c in current_text.split(',')]
                if len(currents) != 3:
                    messagebox.showwarning("Invalid Input", "Please enter exactly 3 current values (comma-separated)")
                    return
            else:
                # Single value for all channels
                current = float(current_text)
                currents = [current, current, current]
            
            # Send bulk current command
            current_cmd = f"APP:CURR {currents[0]:.3f},{currents[1]:.3f},{currents[2]:.3f}"
            self.psu.write(current_cmd)
            
            # Update GUI values
            for i, channel in enumerate(self.channels):
                channel.current_set.set(currents[i])
            
            self.log_message(f"Set all currents: CH1={currents[0]}A, CH2={currents[1]}A, CH3={currents[2]}A")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers")
        except Exception as e:
            self.log_message(f"Failed to set all currents: {e}")
            messagebox.showerror("Error", f"Failed to set all currents: {e}")
                
    def start_monitoring(self):
        """Start monitoring thread."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
    def monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            if self.connected and self.psu:
                try:
                    # Get status for each channel separately
                    channel_statuses = []
                    for channel in self.channels:
                        try:
                            # Use channel-specific measurement commands
                            voltage = float(self.psu.query(f"APP:MEAS:VOLT? {channel.channel_num}"))
                            current = float(self.psu.query(f"APP:MEAS:CURR? {channel.channel_num}"))
                            power = float(self.psu.query(f"APP:MEAS:POW? {channel.channel_num}"))
                            output = self.psu.query(f"APP:OUTP? {channel.channel_num}") == "1"
                            
                            status = {
                                'voltage': voltage,
                                'current': current,
                                'power': power,
                                'output_enabled': output,
                                'set_voltage': channel.voltage_set.get(),
                                'set_current': channel.current_set.get()
                            }
                            channel_statuses.append((channel.channel_num, status))
                        except:
                            # If channel-specific command fails, use default
                            status = self.psu.get_measurement_status()
                            channel_statuses.append((channel.channel_num, status))
                    
                    # Update GUI in main thread
                    self.root.after(0, self.update_all_measurements, channel_statuses)
                    self.root.after(0, self.update_overview)
                    
                except Exception as e:
                    self.root.after(0, self.log_message, f"Monitoring error: {e}")
                    
            time.sleep(1)  # Update every second
            
    def update_all_measurements(self, channel_statuses):
        """Update measurement displays for all channels."""
        try:
            # Update each channel with its specific status
            for channel_num, status in channel_statuses:
                channel = self.channels[channel_num - 1]  # Convert to 0-based index
                channel.update_measurements(status)
        except Exception as e:
            self.log_message(f"Failed to update measurements: {e}")
            
    def update_overview(self):
        """Update the channel overview table."""
        try:
            # Clear existing items
            for item in self.overview_tree.get_children():
                self.overview_tree.delete(item)
                
            # Add current channel status
            for i, channel in enumerate(self.channels):
                channel_num = i + 1
                voltage = channel.voltage_measured.get()
                current = channel.current_measured.get()
                power = channel.power_measured.get()
                output = "ON" if channel.output_enabled.get() else "OFF"
                
                self.overview_tree.insert("", "end", values=(channel_num, voltage, current, power, output))
        except Exception as e:
            self.log_message(f"Failed to update overview: {e}")

def main():
    """Main function."""
    root = tk.Tk()
    app = OwonPSUGUI(root)
    
    # Handle window closing
    def on_closing():
        app.monitoring = False
        if app.connected and app.psu:
            try:
                app.psu.close()
            except:
                pass
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
