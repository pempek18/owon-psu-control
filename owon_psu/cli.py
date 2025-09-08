#!/usr/bin/env python3
"""
Command Line Interface for OWON PSU Control Library
"""

import argparse
import sys
import time
from typing import Optional

from . import OwonPSU, OwonPSUError


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='OWON PSU Control Library CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Serial connection
  owon-psu --port COM3 --serial
  
  # Network connection
  owon-psu --ip 192.168.1.100 --port 3000 --network
  
  # Get device info
  owon-psu --port COM3 --info
  
  # Set voltage and current
  owon-psu --port COM3 --voltage 12.0 --current 1.0 --enable
  
  # Monitor measurements
  owon-psu --port COM3 --monitor --duration 10
        """
    )
    
    # Connection arguments
    connection_group = parser.add_mutually_exclusive_group(required=True)
    connection_group.add_argument('--serial', action='store_true', help='Use serial connection')
    connection_group.add_argument('--network', action='store_true', help='Use network connection')
    
    # Serial connection arguments
    parser.add_argument('--port', type=str, help='Serial port (e.g., COM3) or network port number')
    parser.add_argument('--ip', type=str, help='IP address for network connection')
    
    # Operation arguments
    parser.add_argument('--info', action='store_true', help='Get device information')
    parser.add_argument('--voltage', type=float, help='Set voltage (V)')
    parser.add_argument('--current', type=float, help='Set current (A)')
    parser.add_argument('--enable', action='store_true', help='Enable output')
    parser.add_argument('--disable', action='store_true', help='Disable output')
    parser.add_argument('--monitor', action='store_true', help='Monitor measurements')
    parser.add_argument('--duration', type=int, default=10, help='Monitoring duration in seconds')
    parser.add_argument('--reset', action='store_true', help='Reset device')
    parser.add_argument('--shutdown', action='store_true', help='Safe shutdown')
    
    args = parser.parse_args()
    
    try:
        if args.serial:
            if not args.port:
                parser.error("--port is required for serial connection")
            run_serial_connection(args)
        elif args.network:
            if not args.ip or not args.port:
                parser.error("--ip and --port are required for network connection")
            run_network_connection(args)
            
    except OwonPSUError as e:
        print(f"PSU Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def run_serial_connection(args):
    """Run serial connection operations."""
    with OwonPSU(args.port, serial=True) as psu:
        run_operations(psu, args)


def run_network_connection(args):
    """Run network connection operations."""
    psu = OwonPSU("COM1", serial=False)  # port not used for network
    psu.open_network(args.ip, int(args.port))
    
    try:
        run_operations(psu, args)
    finally:
        psu.close()


def run_operations(psu: OwonPSU, args):
    """Run the requested operations."""
    print(f"Connected to: {psu.get_identity()}")
    
    if args.reset:
        print("Resetting device...")
        psu.reset()
        time.sleep(0.5)
    
    if args.info:
        print_device_info(psu)
    
    if args.voltage is not None:
        print(f"Setting voltage to {args.voltage}V...")
        psu.set_voltage(args.voltage)
    
    if args.current is not None:
        print(f"Setting current to {args.current}A...")
        psu.set_current(args.current)
    
    if args.enable:
        print("Enabling output...")
        psu.set_output(True)
    
    if args.disable:
        print("Disabling output...")
        psu.set_output(False)
    
    if args.monitor:
        print(f"Monitoring for {args.duration} seconds...")
        monitor_measurements(psu, args.duration)
    
    if args.shutdown:
        print("Performing safe shutdown...")
        psu.safe_shutdown()
    
    # If no specific operation was requested, show current status
    if not any([args.info, args.voltage, args.current, args.enable, 
                args.disable, args.monitor, args.shutdown, args.reset]):
        print_current_status(psu)


def print_device_info(psu: OwonPSU):
    """Print comprehensive device information."""
    device_info = psu.get_device_info()
    
    print("\n=== Device Information ===")
    print(f"Identity: {device_info['identity']}")
    print(f"Voltage Limit: {device_info['voltage_limit']:.3f}V")
    print(f"Current Limit: {device_info['current_limit']:.3f}A")
    print(f"Output Enabled: {device_info['output_enabled']}")
    print(f"Remote Mode: {device_info['remote_mode']}")
    print(f"Keylock: {device_info['keylock']}")
    print(f"Status Byte: {device_info['status_byte']}")
    
    if device_info['errors']:
        print(f"Errors: {device_info['errors']}")
    else:
        print("No errors detected")


def print_current_status(psu: OwonPSU):
    """Print current device status."""
    status = psu.get_measurement_status()
    
    print("\n=== Current Status ===")
    print(f"Voltage: {status['voltage']:.3f}V (set: {status['set_voltage']:.3f}V)")
    print(f"Current: {status['current']:.3f}A (set: {status['set_current']:.3f}A)")
    print(f"Power: {status['power']:.3f}W")
    print(f"Output: {'ON' if status['output_enabled'] else 'OFF'}")


def monitor_measurements(psu: OwonPSU, duration: int):
    """Monitor measurements for specified duration."""
    print(f"{'Time':>6} {'Voltage':>8} {'Current':>8} {'Power':>8} {'Output':>6}")
    print("-" * 40)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            status = psu.get_measurement_status()
            elapsed = time.time() - start_time
            
            print(f"{elapsed:6.1f} {status['voltage']:8.3f} {status['current']:8.3f} "
                  f"{status['power']:8.3f} {'ON' if status['output_enabled'] else 'OFF':>6}")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
            break
        except Exception as e:
            print(f"\nMonitoring error: {e}")
            break


if __name__ == "__main__":
    main() 