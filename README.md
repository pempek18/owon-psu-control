# OWON PSU Control Library

A comprehensive Python library for controlling OWON Power Supply Units via SCPI commands. Supports both serial and network connections with full error handling and comprehensive device management.

## Features

- **Dual Connection Support**: Serial and network connections
- **Comprehensive SCPI Commands**: Full implementation of standard OWON PSU SCPI commands
- **Error Handling**: Robust error detection and handling
- **Device Verification**: Automatic device identification and verification
- **Context Manager Support**: Safe resource management with `with` statements
- **Type Hints**: Full type annotation support
- **Logging**: Built-in logging for debugging and monitoring
- **Safe Operations**: Built-in safety features like safe shutdown

## Supported Devices

- OWON SPE series
- OWON SPM series
- OWON P4000 series (P4603, P4605, etc.)
- OWON P3000 series
- OWON P2000 series
- OWON P1000 series
- KIPRIM DC series
- OWON ODP series
- OWON ODS series

## Installation

```bash
pip install owon-psu-control
```

Or install from source:

```bash
git clone https://github.com/your-repo/owon-psu-control.git
cd owon-psu-control
pip install -e .
```

## Quick Start

### Serial Connection

```python
from owon_psu import OwonPSU

# Using context manager (recommended)
with OwonPSU("COM3") as psu:
    print(f"Connected to: {psu.get_identity()}")
    
    # Configure and enable output
    psu.configure_output(voltage=12.0, current=1.0, enable=True)
    
    # Monitor measurements
    status = psu.get_measurement_status()
    print(f"Voltage: {status['voltage']:.3f}V")
    print(f"Current: {status['current']:.3f}A")
    print(f"Power: {status['power']:.3f}W")
    
    # Safe shutdown
    psu.safe_shutdown()
```

### Network Connection

```python
from owon_psu import OwonPSU

# Create PSU instance
psu = OwonPSU("COM1", serial=False)  # port parameter not used for network

# Open network connection
psu.open_network("192.168.1.100", 3000)

try:
    print(f"Connected to: {psu.get_identity()}")
    
    # Configure output
    psu.configure_output(voltage=15.0, current=2.0, enable=True)
    
    # Get comprehensive device info
    device_info = psu.get_device_info()
    print(f"Device Info: {device_info}")
    
finally:
    psu.close()
```

## API Reference

### Core Methods

#### Connection Management

- `open_serial()` - Open serial connection
- `open_network(ip_address, port=3000)` - Open network connection
- `close()` - Close connection
- `is_connected()` - Check connection status

#### Device Information

- `get_identity()` - Get device identification string
- `get_device_info()` - Get comprehensive device information
- `reset()` - Reset device to default settings

#### Output Control

- `set_output(state)` - Enable/disable output
- `get_output()` - Get output state
- `configure_output(voltage, current, enable=True)` - Configure output with voltage and current

#### Voltage Control

- `set_voltage(voltage)` - Set output voltage
- `get_voltage()` - Get set voltage
- `measure_voltage()` - Measure actual voltage
- `set_voltage_limit(voltage)` - Set voltage limit
- `get_voltage_limit()` - Get voltage limit

#### Current Control

- `set_current(current)` - Set output current
- `get_current()` - Get set current
- `measure_current()` - Measure actual current
- `set_current_limit(current)` - Set current limit
- `get_current_limit()` - Get current limit

#### Measurement

- `measure_power()` - Measure output power
- `get_measurement_status()` - Get comprehensive measurement status

#### System Control

- `set_remote_mode(enabled)` - Set remote/local mode
- `get_remote_mode()` - Get remote mode status
- `set_keylock(enabled)` - Set keylock (front panel lock)
- `get_keylock()` - Get keylock status

#### Error Handling

- `get_status_byte()` - Get status byte
- `get_error_queue()` - Get error queue
- `clear_error_queue()` - Clear error queue

#### Safety

- `safe_shutdown()` - Safely shutdown PSU (disable output, set voltage to 0)

## Examples

### Basic Usage

```python
from owon_psu import OwonPSU, OwonPSUError

try:
    with OwonPSU("COM3") as psu:
        # Get device info
        print(f"Device: {psu.get_identity()}")
        
        # Configure output
        psu.set_voltage_limit(30.0)
        psu.set_current_limit(3.0)
        psu.configure_output(voltage=12.0, current=1.0, enable=True)
        
        # Monitor for 10 seconds
        import time
        start = time.time()
        while time.time() - start < 10:
            status = psu.get_measurement_status()
            print(f"V: {status['voltage']:.3f}V, I: {status['current']:.3f}A, P: {status['power']:.3f}W")
            time.sleep(1)
        
        # Safe shutdown
        psu.safe_shutdown()
        
except OwonPSUError as e:
    print(f"PSU Error: {e}")
```

### Advanced Usage

```python
from owon_psu import OwonPSU
import time

with OwonPSU("COM3") as psu:
    # Reset device
    psu.reset()
    time.sleep(0.5)
    
    # Set remote mode
    psu.set_remote_mode(True)
    
    # Configure with limits
    psu.set_voltage_limit(25.0)
    psu.set_current_limit(2.5)
    psu.configure_output(voltage=15.0, current=1.5, enable=True)
    
    # Monitor with error checking
    for i in range(5):
        try:
            status = psu.get_measurement_status()
            print(f"Measurement {i+1}: {status}")
            
            # Check for errors
            errors = psu.get_error_queue()
            if errors:
                print(f"Errors: {errors}")
                
        except Exception as e:
            print(f"Measurement error: {e}")
        
        time.sleep(1)
    
    # Safe shutdown
    psu.safe_shutdown()
```

## Error Handling

The library provides comprehensive error handling:

```python
from owon_psu import OwonPSU, OwonPSUError

try:
    with OwonPSU("COM3") as psu:
        # Your code here
        pass
        
except OwonPSUError as e:
    print(f"PSU-specific error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Logging

The library includes built-in logging:

```python
import logging

# Set logging level
logging.getLogger('owon_psu').setLevel(logging.DEBUG)

# Use the library
with OwonPSU("COM3") as psu:
    # Logs will show connection status, commands, etc.
    pass
```

## Safety Features

- **Safe Shutdown**: Automatically disables output and sets voltage to 0
- **Device Verification**: Verifies connected device is supported
- **Error Detection**: Comprehensive error checking and reporting
- **Resource Management**: Automatic cleanup with context managers

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check if the port is correct
   - Ensure the PSU is powered on
   - Verify the cable connection

2. **Device Not Supported**
   - Check if your device is in the supported list
   - Verify the device identification string

3. **Communication Errors**
   - Check baud rate settings
   - Verify cable quality
   - Try different timeout values

### Debug Mode

Enable debug logging to see detailed communication:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

with OwonPSU("COM3") as psu:
    # Debug information will be printed
    pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Complete rewrite with comprehensive SCPI support
- Added network connection support
- Improved error handling and logging
- Added safety features
- Comprehensive documentation and examples
