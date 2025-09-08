#!/usr/bin/env python3
"""
OWON PSU Control Library
A comprehensive Python library for controlling OWON Power Supply Units via SCPI commands.
Supports both serial and network connections.

Author: Robbe Derks
Version: 1.0.0
"""

__version__ = '1.0.0'
__author__ = 'Robbe Derks'

import serial
import socket
import time
from typing import Optional, Union, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OwonPSUError(Exception):
    """Custom exception for OWON PSU errors."""
    pass

class OwonPSU:
    """
    OWON Power Supply Unit Control Class
    
    Supports both serial and network connections to OWON PSU devices.
    Implements standard SCPI commands for power supply control.
    """
    
    # Supported OWON device identifiers
    SUPPORTED_DEVICES = {
        "OWON,SPE",      # SPE series
        "OWON,SPM",      # SPM series  
        "OWON,P4",       # P4000 series
        "OWON,P3",       # P3000 series
        "OWON,P2",       # P2000 series
        "OWON,P1",       # P1000 series
        "KIPRIM,DC",     # KIPRIM DC series
        "OWON,ODP",      # ODP series
        "OWON,ODS"       # ODS series
    }
    
    # Default communication settings
    DEFAULT_BAUDRATE = 115200
    DEFAULT_NETWORK_PORT = 3000
    DEFAULT_TIMEOUT = 1.0
    
    def __init__(self, port: str, serial: bool = True, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize OWON PSU connection.
        
        Args:
            port (str): Serial port name (e.g., "COM3") or network port number
            serial (bool): True for serial connection, False for network
            timeout (float): Communication timeout in seconds
        """
        self.port = port
        self.serial = serial
        self.network = not serial
        self.timeout = timeout
        self.connection = None
        self.device_info = None
        
        # Connection state
        self._connected = False
        self._connection_type = None
        
    def __enter__(self):
        """Context manager entry."""
        if self.serial:
            self.open_serial()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def open_serial(self) -> None:
        """
        Open serial connection to the PSU.
        
        Raises:
            OwonPSUError: If connection fails or device is not supported
        """
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.DEFAULT_BAUDRATE,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self._connected = True
            self._connection_type = 'serial'
            
            # Verify device identity
            self._verify_device()
            logger.info(f"Serial connection established to {self.port}")
            
        except serial.SerialException as e:
            raise OwonPSUError(f"Failed to open serial connection: {e}")
    
    def open_network(self, ip_address: str, port: int = DEFAULT_NETWORK_PORT) -> None:
        """
        Open network connection to the PSU.
        
        Args:
            ip_address (str): IP address of the PSU
            port (int): Network port (default: 3000)
            
        Raises:
            OwonPSUError: If connection fails or device is not supported
        """
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.connect((ip_address, port))
            self._connected = True
            self._connection_type = 'network'
            
            # Verify device identity
            self._verify_device()
            logger.info(f"Network connection established to {ip_address}:{port}")
            
        except socket.error as e:
            raise OwonPSUError(f"Failed to open network connection: {e}")
    
    def close(self) -> None:
        """Close the connection to the PSU."""
        if self.connection:
            try:
                self.connection.close()
                self._connected = False
                self._connection_type = None
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
    
    def _verify_device(self) -> None:
        """
        Verify that the connected device is a supported OWON PSU.
        
        Raises:
            OwonPSUError: If device is not supported
        """
        try:
            identity = self.query("*IDN?")
            self.device_info = identity.strip()
            
            if not any(device in identity for device in self.SUPPORTED_DEVICES):
                raise OwonPSUError(f"Unsupported device: {identity}")
                
            logger.info(f"Connected to: {identity}")
            
        except Exception as e:
            raise OwonPSUError(f"Device verification failed: {e}")
    
    def _send_command(self, command: str) -> None:
        """
        Send a command to the PSU.
        
        Args:
            command (str): SCPI command to send
            
        Raises:
            OwonPSUError: If command fails
        """
        if not self._connected:
            raise OwonPSUError("Not connected to PSU")
        
        try:
            if self._connection_type == 'serial':
                self.connection.write(f"{command}\n".encode('utf-8'))
            else:  # network
                self.connection.send(f"{command}\n".encode('utf-8'))
                
        except Exception as e:
            raise OwonPSUError(f"Failed to send command '{command}': {e}")
    
    def query(self, command: str) -> str:
        """
        Send a query command and return the response.
        
        Args:
            command (str): SCPI query command
            
        Returns:
            str: Device response
            
        Raises:
            OwonPSUError: If query fails
        """
        if not self._connected:
            raise OwonPSUError("Not connected to PSU")
        
        try:
            # Send command
            self._send_command(command)
            
            # Read response
            if self._connection_type == 'serial':
                response = self.connection.readline().decode('utf-8').strip()
            else:  # network
                response = self.connection.recv(1024).decode('utf-8').strip()
            
            # Check for errors
            if response == "ERR":
                raise OwonPSUError(f"Device returned error for command: {command}")
            
            return response
            
        except Exception as e:
            raise OwonPSUError(f"Query failed for '{command}': {e}")
    
    def write(self, command: str) -> None:
        """
        Send a command without expecting a response.
        
        Args:
            command (str): SCPI command to send
            
        Raises:
            OwonPSUError: If command fails
        """
        self._send_command(command)
        time.sleep(0.01)  # Small delay for command processing
    
    # ============================================================================
    # SYSTEM COMMANDS
    # ============================================================================
    
    def get_identity(self) -> str:
        """Get device identification string."""
        return self.query("*IDN?")
    
    def reset(self) -> None:
        """Reset the device to default settings."""
        self.write("*RST")
        time.sleep(0.1)  # Allow time for reset
    
    def clear_status(self) -> None:
        """Clear status registers."""
        self.write("*CLS")
    
    def get_operation_complete(self) -> bool:
        """Check if operation is complete."""
        return self.query("*OPC?") == "1"
    
    def wait_for_operation_complete(self) -> None:
        """Wait for operation to complete."""
        self.write("*WAI")
    
    # ============================================================================
    # OUTPUT CONTROL
    # ============================================================================
    
    def set_output(self, state: bool) -> None:
        """
        Enable or disable the output.
        
        Args:
            state (bool): True to enable output, False to disable
        """
        command = "OUTPut ON" if state else "OUTPut OFF"
        self.write(command)
    
    def get_output(self) -> bool:
        """
        Get the current output state.
        
        Returns:
            bool: True if output is enabled, False otherwise
        """
        response = self.query("OUTPut?")
        return response in ["1", "ON"]
    
    # ============================================================================
    # VOLTAGE CONTROL
    # ============================================================================
    
    def set_voltage(self, voltage: float) -> None:
        """
        Set the output voltage.
        
        Args:
            voltage (float): Voltage in volts
        """
        self.write(f"VOLTage {voltage:.3f}")
    
    def get_voltage(self) -> float:
        """
        Get the set voltage.
        
        Returns:
            float: Set voltage in volts
        """
        return float(self.query("VOLTage?"))
    
    def measure_voltage(self) -> float:
        """
        Measure the actual output voltage.
        
        Returns:
            float: Measured voltage in volts
        """
        return float(self.query("MEASure:VOLTage?"))
    
    def set_voltage_limit(self, voltage: float) -> None:
        """
        Set the voltage limit.
        
        Args:
            voltage (float): Voltage limit in volts
        """
        self.write(f"VOLTage:LIMit {voltage:.3f}")
    
    def get_voltage_limit(self) -> float:
        """
        Get the voltage limit.
        
        Returns:
            float: Voltage limit in volts
        """
        return float(self.query("VOLTage:LIMit?"))
    
    # ============================================================================
    # CURRENT CONTROL
    # ============================================================================
    
    def set_current(self, current: float) -> None:
        """
        Set the output current.
        
        Args:
            current (float): Current in amperes
        """
        self.write(f"CURRent {current:.3f}")
    
    def get_current(self) -> float:
        """
        Get the set current.
        
        Returns:
            float: Set current in amperes
        """
        return float(self.query("CURRent?"))
    
    def measure_current(self) -> float:
        """
        Measure the actual output current.
        
        Returns:
            float: Measured current in amperes
        """
        return float(self.query("MEASure:CURRent?"))
    
    def set_current_limit(self, current: float) -> None:
        """
        Set the current limit.
        
        Args:
            current (float): Current limit in amperes
        """
        self.write(f"CURRent:LIMit {current:.3f}")
    
    def get_current_limit(self) -> float:
        """
        Get the current limit.
        
        Returns:
            float: Current limit in amperes
        """
        return float(self.query("CURRent:LIMit?"))
    
    # ============================================================================
    # MEASUREMENT COMMANDS
    # ============================================================================
    
    def measure_power(self) -> float:
        """
        Measure the output power.
        
        Returns:
            float: Power in watts
        """
        return float(self.query("MEASure:POWer?"))
    
    def get_measurement_status(self) -> dict:
        """
        Get comprehensive measurement status.
        
        Returns:
            dict: Dictionary with voltage, current, power, and output state
        """
        return {
            'voltage': self.measure_voltage(),
            'current': self.measure_current(),
            'power': self.measure_power(),
            'output_enabled': self.get_output(),
            'set_voltage': self.get_voltage(),
            'set_current': self.get_current()
        }
    
    # ============================================================================
    # SYSTEM CONTROL
    # ============================================================================
    
    def set_remote_mode(self, enabled: bool) -> None:
        """
        Set remote/local mode.
        
        Args:
            enabled (bool): True for remote mode, False for local mode
        """
        command = "SYSTem:REMote" if enabled else "SYSTem:LOCal"
        self.write(command)
    
    def get_remote_mode(self) -> bool:
        """
        Get remote/local mode status.
        
        Returns:
            bool: True if in remote mode, False if in local mode
        """
        try:
            response = self.query("SYSTem:REMote?")
            return response == "1"
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("SYSTem:REMote? command timed out - command may not be supported by this device")
                return False  # Default to local mode if query fails
            else:
                raise  # Re-raise other errors
    
    def set_keylock(self, enabled: bool) -> None:
        """
        Set keylock (front panel lock) state.
        
        Args:
            enabled (bool): True to enable keylock, False to disable
        """
        command = "SYSTem:KEYLock ON" if enabled else "SYSTem:KEYLock OFF"
        self.write(command)
    
    def get_keylock(self) -> bool:
        """
        Get keylock state.
        
        Returns:
            bool: True if keylock is enabled, False otherwise
        """
        try:
            response = self.query("SYSTem:KEYLock?")
            return response == "1"
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("SYSTem:KEYLock? command timed out - command may not be supported by this device")
                return False  # Default to unlocked if query fails
            else:
                raise  # Re-raise other errors
    
    # ============================================================================
    # STATUS AND ERROR HANDLING
    # ============================================================================
    
    def get_status_byte(self) -> int:
        """
        Get the status byte.
        
        Returns:
            int: Status byte value
        """
        return int(self.query("*STB?"))
    
    def get_error_queue(self) -> list:
        """
        Get the error queue.
        
        Returns:
            list: List of error messages
        """
        errors = []
        while True:
            try:
                error = self.query("SYSTem:ERRor?")
                if error == "0,\"No error\"":
                    break
                errors.append(error)
            except:
                break
        return errors
    
    def clear_error_queue(self) -> None:
        """Clear the error queue."""
        self.write("*CLS")
    
    # ============================================================================
    # CONVENIENCE METHODS
    # ============================================================================
    
    def configure_output(self, voltage: float, current: float, enable: bool = True) -> None:
        """
        Configure output with voltage, current, and enable state.
        
        Args:
            voltage (float): Output voltage in volts
            current (float): Output current in amperes
            enable (bool): Whether to enable output
        """
        self.set_voltage(voltage)
        self.set_current(current)
        if enable:
            self.set_output(True)
    
    def safe_shutdown(self) -> None:
        """Safely shutdown the PSU by disabling output and setting voltage to 0."""
        self.set_output(False)
        self.set_voltage(0.0)
        time.sleep(0.1)
    
    def get_device_info(self) -> dict:
        """
        Get comprehensive device information.
        
        Returns:
            dict: Device information including identity, limits, and status
        """
        info = {
            'identity': self.get_identity(),
            'output_enabled': self.get_output(),
        }
        
        # Try to get additional info, but don't fail if commands timeout
        try:
            info['voltage_limit'] = self.get_voltage_limit()
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("VOLTage:LIMit? command timed out")
                info['voltage_limit'] = None
            else:
                raise
                
        try:
            info['current_limit'] = self.get_current_limit()
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("CURRent:LIMit? command timed out")
                info['current_limit'] = None
            else:
                raise
                
        try:
            info['remote_mode'] = self.get_remote_mode()
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("SYSTem:REMote? command timed out")
                info['remote_mode'] = None
            else:
                raise
                
        try:
            info['keylock'] = self.get_keylock()
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("SYSTem:KEYLock? command timed out")
                info['keylock'] = None
            else:
                raise
                
        try:
            info['status_byte'] = self.get_status_byte()
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("*STB? command timed out")
                info['status_byte'] = None
            else:
                raise
                
        try:
            info['errors'] = self.get_error_queue()
        except OwonPSUError as e:
            if "timed out" in str(e).lower():
                logger.warning("SYSTem:ERRor? command timed out")
                info['errors'] = []
            else:
                raise
                
        return info
    
    def is_connected(self) -> bool:
        """
        Check if connected to the PSU.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected and self.connection is not None


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m owon_psu <serial_port>")
        print("Example: python -m owon_psu COM3")
        sys.exit(1)
    
    port_name = sys.argv[1]
    
    try:
        # Example with context manager
        with OwonPSU(port_name) as psu:
            print("Device Identity:", psu.get_identity())
            print("Device Info:", psu.get_device_info())
            
            # Configure and enable output
            psu.configure_output(voltage=12.0, current=1.0, enable=True)
            
            # Monitor for a few seconds
            for i in range(5):
                status = psu.get_measurement_status()
                print(f"Status {i+1}: {status}")
                time.sleep(1)
            
            # Safe shutdown
            psu.safe_shutdown()
            
    except OwonPSUError as e:
        print(f"Error: {e}")
        sys.exit(1)
