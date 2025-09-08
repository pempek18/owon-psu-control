# Installation Guide

This guide explains how to install and set up the OWON PSU Control Library.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation Methods

### Method 1: Install from Source (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/owon-psu-control.git
   cd owon-psu-control
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

   This installs the package in "editable" mode, meaning changes to the source code will be immediately available without reinstalling.

### Method 2: Install from PyPI (When Available)

```bash
pip install owon-psu-control
```

### Method 3: Manual Installation

1. **Download the source code**
2. **Navigate to the project directory**
3. **Install manually:**
   ```bash
   python setup.py install
   ```

## Verification

After installation, you can verify that the module is accessible:

```bash
python test_module_access.py
```

This should output:
```
Testing owon_psu module access...
========================================

--- Module Import ---
✅ Successfully imported owon_psu module
   - OwonPSU class: <class 'owon_psu.OwonPSU'>
   - OwonPSUError class: <class 'owon_psu.OwonPSUError'>

--- Module Attributes ---
✅ Found attribute: SUPPORTED_DEVICES
✅ Found attribute: DEFAULT_BAUDRATE
✅ Found attribute: DEFAULT_NETWORK_PORT
✅ Found attribute: DEFAULT_TIMEOUT
✅ Found method: open_serial
✅ Found method: open_network
✅ Found method: close
✅ Found method: get_identity
✅ Found method: set_voltage
✅ Found method: get_voltage
✅ Found method: measure_voltage
✅ Found method: set_current
✅ Found method: get_current
✅ Found method: measure_current
✅ Found method: set_output
✅ Found method: get_output
✅ Found method: safe_shutdown

--- Version Check ---
✅ Module version: 1.0.0

========================================
Tests passed: 3/3
🎉 All tests passed! Module access is working correctly.
```

## Usage Examples

### Basic Usage

```python
from owon_psu import OwonPSU

# Serial connection
with OwonPSU("COM3") as psu:
    print(f"Connected to: {psu.get_identity()}")
    psu.configure_output(voltage=12.0, current=1.0, enable=True)
```

### Network Connection

```python
from owon_psu import OwonPSU

psu = OwonPSU("COM1", serial=False)
psu.open_network("192.168.1.100", 3000)
try:
    print(f"Connected to: {psu.get_identity()}")
    # Your code here
finally:
    psu.close()
```

## Command Line Interface

After installation, you can use the command-line interface:

```bash
# Get device information
owon-psu --port COM3 --serial --info

# Set voltage and current
owon-psu --port COM3 --serial --voltage 12.0 --current 1.0 --enable

# Monitor measurements
owon-psu --port COM3 --serial --monitor --duration 10

# Network connection
owon-psu --ip 192.168.1.100 --port 3000 --network --info
```

## Troubleshooting

### Import Errors

If you get import errors, make sure:

1. **The package is installed correctly:**
   ```bash
   pip list | grep owon-psu
   ```

2. **Python path includes the project directory:**
   ```python
   import sys
   sys.path.insert(0, '/path/to/owon-psu-control')
   ```

3. **You're using the correct Python environment:**
   ```bash
   which python
   pip --version
   ```

### Connection Issues

1. **Check serial port availability:**
   ```python
   import serial.tools.list_ports
   ports = serial.tools.list_ports.comports()
   for port in ports:
       print(f"{port.device}: {port.description}")
   ```

2. **Verify network connectivity:**
   ```bash
   ping 192.168.1.100
   telnet 192.168.1.100 3000
   ```

### Permission Issues

On Linux/macOS, you might need to add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

## Development Setup

For development, install with additional dependencies:

```bash
pip install -e .[dev]
```

This includes:
- pytest (testing)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)

## Uninstallation

To uninstall the package:

```bash
pip uninstall owon-psu-control
```

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run the test script: `python test_module_access.py`
3. Check the logs for detailed error messages
4. Open an issue on the GitHub repository 