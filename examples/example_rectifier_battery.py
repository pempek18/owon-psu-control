#!/usr/bin/env python3
"""
Example: Gel Accumulator Charging with OWON PSU
Demonstrates how to safely charge a gel accumulator (battery) using an OWON PSU.
Includes multi-stage charging, monitoring, and safety features.

Author: Robbe Derks
Version: 1.0.0
"""
import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path to access the owon_psu module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from owon_psu import OwonPSU, OwonPSUError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('battery_charging.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GelAccumulatorCharger:
    """
    Gel Accumulator Charging Controller
    
    Implements a safe multi-stage charging protocol for gel lead-acid batteries
    using an OWON PSU as the power source.
    """
    
    def __init__(self, psu: OwonPSU, battery_specs: dict):
        """
        Initialize the battery charger.
        
        Args:
            psu: OWON PSU instance
            battery_specs: Dictionary containing battery specifications
        """
        self.psu = psu
        self.battery_specs = battery_specs
        self.charging_stage = "idle"
        self.start_time = None
        self.stage_start_time = None
        
        # Validate battery specifications
        self._validate_battery_specs()
        
        # Initialize charging parameters
        self._init_charging_params()
        
    def _validate_battery_specs(self):
        """Validate battery specifications."""
        required_keys = ['nominal_voltage', 'capacity_ah', 'max_charge_current', 'float_voltage']
        for key in required_keys:
            if key not in self.battery_specs:
                raise ValueError(f"Missing required battery specification: {key}")
        
        # Set default values for optional parameters
        if 'min_voltage' not in self.battery_specs:
            self.battery_specs['min_voltage'] = self.battery_specs['nominal_voltage'] * 0.8
        
        if 'temperature_compensation' not in self.battery_specs:
            self.battery_specs['temperature_compensation'] = -0.0033  # V/°C for lead-acid
        
        if 'max_temperature' not in self.battery_specs:
            self.battery_specs['max_temperature'] = 50.0  # °C
        
        if 'min_temperature' not in self.battery_specs:
            self.battery_specs['min_temperature'] = 0.0   # °C
    
    def _init_charging_params(self):
        """Initialize charging parameters based on battery specifications."""
        nominal_v = self.battery_specs['nominal_voltage']
        capacity = self.battery_specs['capacity_ah']
        
        # Calculate charging parameters
        self.charge_params = {
            'bulk_voltage': nominal_v * 1.45,  # 14.5V for 12V battery
            'absorption_voltage': nominal_v * 1.40,  # 14.0V for 12V battery
            'float_voltage': self.battery_specs['float_voltage'],
            'max_current': min(self.battery_specs['max_charge_current'], capacity * 0.1),
            'absorption_time': max(4, capacity / 10),  # Hours, minimum 4 hours
            'float_time': 2,  # Hours in float stage
            'termination_current': capacity * 0.01,  # 1% of capacity
            'safety_timeout': capacity * 2  # Hours, maximum charging time
        }
        
        logger.info(f"Charging parameters initialized:")
        logger.info(f"  Bulk voltage: {self.charge_params['bulk_voltage']:.2f}V")
        logger.info(f"  Absorption voltage: {self.charge_params['absorption_voltage']:.2f}V")
        logger.info(f"  Float voltage: {self.charge_params['float_voltage']:.2f}V")
        logger.info(f"  Max current: {self.charge_params['max_current']:.2f}A")
    
    def start_charging(self):
        """Start the battery charging process."""
        logger.info("=== Starting Gel Accumulator Charging Process ===")
        logger.info(f"Battery: {self.battery_specs['nominal_voltage']}V, {self.battery_specs['capacity_ah']}Ah")
        
        try:
            # Set start time
            self.start_time = time.time()
            
            # Reset PSU to known state
            self.psu.reset()
            time.sleep(1)
            
            # Configure PSU for charging
            self.psu.set_voltage_limit(self.charge_params['bulk_voltage'] + 1.0)
            self.psu.set_current_limit(self.charge_params['max_current'])
            
            # Start with bulk charging
            self._start_bulk_charging()
            
        except Exception as e:
            logger.error(f"Failed to start charging: {e}")
            self._emergency_shutdown()
            raise
    
    def _start_bulk_charging(self):
        """Start bulk charging stage."""
        self.charging_stage = "bulk"
        self.stage_start_time = time.time()
        
        logger.info("--- Starting Bulk Charging Stage ---")
        logger.info(f"Target voltage: {self.charge_params['bulk_voltage']:.2f}V")
        logger.info(f"Current limit: {self.charge_params['max_current']:.2f}A")
        
        # Set PSU to bulk charging parameters
        self.psu.configure_output(
            voltage=self.charge_params['bulk_voltage'],
            current=self.charge_params['max_current'],
            enable=True
        )
        
        # Monitor bulk charging
        self._monitor_bulk_charging()
    
    def _monitor_bulk_charging(self):
        """Monitor bulk charging stage."""
        logger.info("Monitoring bulk charging...")
        
        while self.charging_stage == "bulk":
            try:
                # Get current measurements
                status = self.psu.get_measurement_status()
                voltage = status['voltage']
                current = status['current']
                power = status['power']
                
                # Log progress
                elapsed = time.time() - self.stage_start_time
                logger.info(f"Bulk: {elapsed/3600:.1f}h - V: {voltage:.3f}V, I: {current:.3f}A, P: {power:.2f}W")
                
                # Check if ready to transition to absorption
                if voltage >= self.charge_params['absorption_voltage']:
                    logger.info("Bulk charging complete, transitioning to absorption stage")
                    self._start_absorption_charging()
                    break
                
                # Check safety conditions
                if self._check_safety_conditions(voltage, current):
                    break
                
                # Check timeout
                if elapsed > self.charge_params['safety_timeout'] * 3600:
                    logger.warning("Bulk charging timeout reached")
                    self._start_absorption_charging()
                    break
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error during bulk charging: {e}")
                self._emergency_shutdown()
                break
    
    def _start_absorption_charging(self):
        """Start absorption charging stage."""
        self.charging_stage = "absorption"
        self.stage_start_time = time.time()
        
        logger.info("--- Starting Absorption Charging Stage ---")
        logger.info(f"Target voltage: {self.charge_params['absorption_voltage']:.2f}V")
        logger.info(f"Duration: {self.charge_params['absorption_time']:.1f} hours")
        
        # Set PSU to absorption voltage
        self.psu.set_voltage(self.charge_params['absorption_voltage'])
        
        # Monitor absorption charging
        self._monitor_absorption_charging()
    
    def _monitor_absorption_charging(self):
        """Monitor absorption charging stage."""
        logger.info("Monitoring absorption charging...")
        
        while self.charging_stage == "absorption":
            try:
                # Get current measurements
                status = self.psu.get_measurement_status()
                voltage = status['voltage']
                current = status['current']
                power = status['power']
                
                # Log progress
                elapsed = time.time() - self.stage_start_time
                remaining = self.charge_params['absorption_time'] - elapsed/3600
                logger.info(f"Absorption: {elapsed/3600:.1f}h - V: {voltage:.3f}V, I: {current:.3f}A, P: {power:.2f}W")
                logger.info(f"  Time remaining: {remaining:.1f}h")
                
                # Check if absorption time is complete
                if elapsed >= self.charge_params['absorption_time'] * 3600:
                    logger.info("Absorption charging complete, transitioning to float stage")
                    self._start_float_charging()
                    break
                
                # Check if current has dropped to termination level
                if current <= self.charge_params['termination_current']:
                    logger.info("Termination current reached, transitioning to float stage")
                    self._start_float_charging()
                    break
                
                # Check safety conditions
                if self._check_safety_conditions(voltage, current):
                    break
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error during absorption charging: {e}")
                self._emergency_shutdown()
                break
    
    def _start_float_charging(self):
        """Start float charging stage."""
        self.charging_stage = "float"
        self.stage_start_time = time.time()
        
        logger.info("--- Starting Float Charging Stage ---")
        logger.info(f"Target voltage: {self.charge_params['float_voltage']:.2f}V")
        logger.info(f"Duration: {self.charge_params['float_time']:.1f} hours")
        
        # Set PSU to float voltage
        self.psu.set_voltage(self.charge_params['float_voltage'])
        
        # Monitor float charging
        self._monitor_float_charging()
    
    def _monitor_float_charging(self):
        """Monitor float charging stage."""
        logger.info("Monitoring float charging...")
        
        while self.charging_stage == "float":
            try:
                # Get current measurements
                status = self.psu.get_measurement_status()
                voltage = status['voltage']
                current = status['current']
                power = status['power']
                
                # Log progress
                elapsed = time.time() - self.stage_start_time
                remaining = self.charge_params['float_time'] - elapsed/3600
                logger.info(f"Float: {elapsed/3600:.1f}h - V: {voltage:.3f}V, I: {current:.3f}A, P: {power:.2f}W")
                logger.info(f"  Time remaining: {remaining:.1f}h")
                
                # Check if float time is complete
                if elapsed >= self.charge_params['float_time'] * 3600:
                    logger.info("Float charging complete")
                    self._complete_charging()
                    break
                
                # Check safety conditions
                if self._check_safety_conditions(voltage, current):
                    break
                
                time.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Error during float charging: {e}")
                self._emergency_shutdown()
                break
    
    def _check_safety_conditions(self, voltage: float, current: float) -> bool:
        """
        Check safety conditions during charging.
        
        Returns:
            True if safety condition violated, False otherwise
        """
        # Check voltage limits
        if voltage > self.charge_params['bulk_voltage'] + 1.0:
            logger.error(f"Voltage too high: {voltage:.3f}V")
            self._emergency_shutdown()
            return True
        
        if voltage < self.battery_specs['min_voltage']:
            logger.error(f"Voltage too low: {voltage:.3f}V")
            self._emergency_shutdown()
            return True
        
        # Check current limits
        if current > self.charge_params['max_current'] * 1.1:
            logger.error(f"Current too high: {current:.3f}A")
            self._emergency_shutdown()
            return True
        
        # Check for negative current (battery discharging)
        if current < -0.1:
            logger.warning(f"Battery discharging: {current:.3f}A")
            # This might be normal during float stage, just log it
        
        return False
    
    def _complete_charging(self):
        """Complete the charging process."""
        self.charging_stage = "complete"
        total_time = time.time() - self.start_time
        
        logger.info("=== Charging Process Complete ===")
        logger.info(f"Total charging time: {total_time/3600:.1f} hours")
        
        # Get final measurements
        status = self.psu.get_measurement_status()
        logger.info(f"Final voltage: {status['voltage']:.3f}V")
        logger.info(f"Final current: {status['current']:.3f}A")
        logger.info(f"Final power: {status['power']:.2f}W")
        
        # Safe shutdown
        self.psu.safe_shutdown()
        logger.info("PSU safely shut down")
    
    def _emergency_shutdown(self):
        """Emergency shutdown in case of safety violation."""
        logger.error("=== EMERGENCY SHUTDOWN ===")
        
        try:
            # Disable output immediately
            self.psu.set_output(False)
            logger.info("Output disabled")
            
            # Set voltage and current to safe levels
            self.psu.set_voltage(self.battery_specs['nominal_voltage'])
            self.psu.set_current(0.1)
            logger.info("PSU set to safe levels")
            
        except Exception as e:
            logger.error(f"Error during emergency shutdown: {e}")
        
        self.charging_stage = "emergency"
    
    def get_charging_status(self) -> dict:
        """Get current charging status."""
        if not self.start_time:
            return {"stage": "not_started"}
        
        elapsed = time.time() - self.start_time
        stage_elapsed = time.time() - self.stage_start_time if self.stage_start_time else 0
        
        return {
            "stage": self.charging_stage,
            "total_elapsed_hours": elapsed / 3600,
            "stage_elapsed_hours": stage_elapsed / 3600,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None
        }

def main():
    """Main function demonstrating gel accumulator charging."""
    
    # Battery specifications (12V 100Ah gel battery example)
    battery_specs = {
        'nominal_voltage': 12.0,      # V
        'capacity_ah': 100.0,         # Ah
        'max_charge_current': 10.0,   # A (10% of capacity)
        'float_voltage': 13.8,        # V
        'min_voltage': 10.0,          # V
        'max_temperature': 50.0,      # °C
        'min_temperature': 0.0        # °C
    }
    
    # Serial connection parameters
    serial_port = "COM3"  # Change this to your actual serial port
    
    try:
        # Create PSU instance and open serial connection
        with OwonPSU(serial_port, serial=True) as psu:
            print("=== OWON PSU Gel Accumulator Charging Example ===")
            print(f"Connected to: {psu.get_identity()}")
            
            # Get device information
            device_info = psu.get_device_info()
            print(f"Device Info: {device_info}")
            
            # Create battery charger instance
            charger = GelAccumulatorCharger(psu, battery_specs)
            
            # Start charging process
            charger.start_charging()
            
            # Monitor charging progress
            while charger.charging_stage not in ["complete", "emergency"]:
                status = charger.get_charging_status()
                print(f"\rCharging: {status['stage']} - "
                      f"Total: {status['total_elapsed_hours']:.1f}h - "
                      f"Stage: {status['stage_elapsed_hours']:.1f}h", end="")
                time.sleep(5)
            
            print(f"\nCharging completed. Final stage: {charger.charging_stage}")
            
    except OwonPSUError as e:
        print(f"PSU Error: {e}")
        logger.error(f"PSU Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")

def list_serial_ports():
    """List available serial ports (helper function)."""
    try:
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        if ports:
            print("Available serial ports:")
            for port in ports:
                print(f"  {port.device}: {port.description}")
        else:
            print("No serial ports found")
    except ImportError:
        print("pyserial not installed. Install with: pip install pyserial")

if __name__ == "__main__":
    # Uncomment the next line to list available ports
    # list_serial_ports()
    
    main()
