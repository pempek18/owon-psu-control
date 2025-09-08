#!/usr/bin/env python3
"""
Test script to verify owon_psu module access
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_import():
    """Test that the owon_psu module can be imported."""
    try:
        from owon_psu import OwonPSU, OwonPSUError
        print("✅ Successfully imported owon_psu module")
        print(f"   - OwonPSU class: {OwonPSU}")
        print(f"   - OwonPSUError class: {OwonPSUError}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import owon_psu module: {e}")
        return False

def test_module_attributes():
    """Test that the module has the expected attributes."""
    try:
        from owon_psu import OwonPSU
        
        # Test class attributes
        expected_attrs = [
            'SUPPORTED_DEVICES',
            'DEFAULT_BAUDRATE',
            'DEFAULT_NETWORK_PORT',
            'DEFAULT_TIMEOUT'
        ]
        
        for attr in expected_attrs:
            if hasattr(OwonPSU, attr):
                print(f"✅ Found attribute: {attr}")
            else:
                print(f"❌ Missing attribute: {attr}")
                return False
        
        # Test method existence
        expected_methods = [
            'open_serial',
            'open_network',
            'close',
            'get_identity',
            'set_voltage',
            'get_voltage',
            'measure_voltage',
            'set_current',
            'get_current',
            'measure_current',
            'set_output',
            'get_output',
            'safe_shutdown'
        ]
        
        for method in expected_methods:
            if hasattr(OwonPSU, method):
                print(f"✅ Found method: {method}")
            else:
                print(f"❌ Missing method: {method}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing module attributes: {e}")
        return False

def test_version():
    """Test that the module has a version."""
    try:
        from owon_psu import __version__
        print(f"✅ Module version: {__version__}")
        return True
    except ImportError:
        print("❌ No version found in module")
        return False

def main():
    """Run all tests."""
    print("Testing owon_psu module access...")
    print("=" * 40)
    
    tests = [
        ("Module Import", test_module_import),
        ("Module Attributes", test_module_attributes),
        ("Version Check", test_version),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Module access is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 