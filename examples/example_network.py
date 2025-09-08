#!/usr/bin/env python3
"""
Example: Network connection to OWON PSU
Demonstrates how to connect to an OWON PSU via network and perform basic operations.
"""
import os
import sys

# Add the parent directory to the Python path to access the owon_psu module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from owon_psu import OwonPSU, OwonPSUError

def main():
    """Main function demonstrating network PSU control."""
    
    # Network connection parameters
    ip_address = "10.0.10.99"
    port = 3000
    
    try:
        # Create PSU instance for network connection
        psu = OwonPSU(port="COM1", serial=False)  # port parameter is for serial, not used for network
        
        # Open network connection
        psu.open_network(ip_address, port)
        
        print("=== OWON PSU Network Control Example ===")
        print(f"Connected to: {psu.get_identity()}")
        
        # Get device information
        device_info = psu.get_device_info()
        print(f"Device Info: {device_info}")
        
        # Configure output
        print("\n--- Configuring Output ---")
        psu.configure_output(voltage=12.0, current=1.0, enable=True)
        print(f"Set Voltage: {psu.get_voltage()}V")
        print(f"Set Current: {psu.get_current()}A")
        print(f"Output Enabled: {psu.get_output()}")
        
        # Monitor measurements
        print("\n--- Monitoring Measurements ---")
        for i in range(5):
            status = psu.get_measurement_status()
            print(f"Measurement {i+1}:")
            print(f"  Voltage: {status['voltage']:.3f}V")
            print(f"  Current: {status['current']:.3f}A")
            print(f"  Power: {status['power']:.3f}W")
            print(f"  Output: {'ON' if status['output_enabled'] else 'OFF'}")
            print()
        
        # Change settings
        print("--- Changing Settings ---")
        psu.set_voltage(15.0)
        psu.set_current(0.5)
        print(f"New Voltage: {psu.get_voltage()}V")
        print(f"New Current: {psu.get_current()}A")
        
        # Safe shutdown
        print("\n--- Safe Shutdown ---")
        psu.safe_shutdown()
        print("PSU safely shut down")
        
    except OwonPSUError as e:
        print(f"PSU Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Ensure connection is closed
        if 'psu' in locals():
            psu.close()

if __name__ == "__main__":
    main()