#!/usr/bin/env python3
"""
Example: Serial connection to OWON PSU
Demonstrates how to connect to an OWON PSU via serial port and perform basic operations.
"""
import os
import sys

# Add the parent directory to the Python path to access the owon_psu module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from owon_psu import OwonPSU, OwonPSUError
import time

def main():
    """Main function demonstrating serial PSU control."""
    
    # Serial connection parameters
    serial_port = "COM3"  # Change this to your actual serial port
    
    try:
        # Create PSU instance and open serial connection using context manager
        with OwonPSU(serial_port, serial=True) as psu:
            print("=== OWON PSU Serial Control Example ===")
            print(f"Connected to: {psu.get_identity()}")
            
            # Get comprehensive device information
            device_info = psu.get_device_info()
            print(f"Device Info: {device_info}")
            
            # Reset device to known state
            print("\n--- Resetting Device ---")
            psu.reset()
            time.sleep(0.5)  # Allow time for reset
            
            # Configure output with limits
            print("\n--- Configuring Output ---")
            psu.set_voltage_limit(30.0)  # Set voltage limit to 30V
            psu.set_current_limit(3.0)   # Set current limit to 3A
            psu.configure_output(voltage=12.0, current=1.0, enable=True)
            
            print(f"Voltage Limit: {psu.get_voltage_limit()}V")
            print(f"Current Limit: {psu.get_current_limit()}A")
            print(f"Set Voltage: {psu.get_voltage()}V")
            print(f"Set Current: {psu.get_current()}A")
            print(f"Output Enabled: {psu.get_output()}")
            
            # Monitor measurements for 10 seconds
            print("\n--- Monitoring Measurements (10 seconds) ---")
            start_time = time.time()
            while time.time() - start_time < 10:
                status = psu.get_measurement_status()
                print(f"Time: {time.time() - start_time:.1f}s")
                print(f"  Voltage: {status['voltage']:.3f}V (set: {status['set_voltage']:.3f}V)")
                print(f"  Current: {status['current']:.3f}A (set: {status['set_current']:.3f}A)")
                print(f"  Power: {status['power']:.3f}W")
                print(f"  Output: {'ON' if status['output_enabled'] else 'OFF'}")
                print()
                time.sleep(1)
            
            # Demonstrate voltage and current changes
            print("--- Demonstrating Voltage Changes ---")
            voltages = [5.0, 10.0, 15.0, 20.0, 12.0]
            for voltage in voltages:
                psu.set_voltage(voltage)
                time.sleep(0.5)  # Allow settling time
                measured = psu.measure_voltage()
                print(f"Set: {voltage}V, Measured: {measured:.3f}V")
            
            print("\n--- Demonstrating Current Changes ---")
            currents = [0.5, 1.0, 1.5, 2.0, 1.0]
            for current in currents:
                psu.set_current(current)
                time.sleep(0.5)  # Allow settling time
                measured = psu.measure_current()
                print(f"Set: {current}A, Measured: {measured:.3f}A")
            
            # Test remote/local mode
            print("\n--- Testing Remote Mode ---")
            psu.set_remote_mode(True)
            print(f"Remote Mode: {psu.get_remote_mode()}")
            
            # Test keylock
            print("\n--- Testing Keylock ---")
            psu.set_keylock(True)
            print(f"Keylock Enabled: {psu.get_keylock()}")
            psu.set_keylock(False)
            print(f"Keylock Disabled: {psu.get_keylock()}")
            
            # Check for any errors
            errors = psu.get_error_queue()
            if errors:
                print(f"\nErrors detected: {errors}")
            else:
                print("\nNo errors detected")
            
            # Safe shutdown
            print("\n--- Safe Shutdown ---")
            psu.safe_shutdown()
            print("PSU safely shut down")
            
    except OwonPSUError as e:
        print(f"PSU Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_serial_ports():
    """List available serial ports (helper function)."""
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    if ports:
        print("Available serial ports:")
        for port in ports:
            print(f"  {port.device}: {port.description}")
    else:
        print("No serial ports found")

if __name__ == "__main__":
    # Uncomment the next line to list available ports
    # list_serial_ports()
    
    main() 