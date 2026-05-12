import json
import os
import sys
import time
import math
from datetime import datetime
from typing import cast, Any

import serial.serialutil
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt


class TDKZ650_1_U:
    """
    Class to manage TDK_Lambda_Z650_1_U resources.
    """

    def __init__(self, config_path: str = None):
        """
        Initialize the TDK_Lambda_Z650_1_U.
        
        Parameters
        ----------
        config_path : str, optional
            Path to JSON config file containing power supply parameters
        """

        # Create PyVISA Resource Manager
        self.rm = visa.ResourceManager()
        
        self.hv_power_supply = None
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.power_supply_output_delay = config.get('power_supply_output_delay', 0.3)
            self.power_supply_ramp_delay = config.get('power_supply_ramp_delay', 0.1)  
            
            self.hv_power_supply_name = config['HVpowerSupply']
            self.VoltageLimit = config['VoltageLimit']
            self.CurrentLimit = config['CurrentLimit']
            self.VoltageWrite = config['VoltageWrite']
            self.timestep = config['timestep']
            self.voltage_step = config['voltage_step']
        else:
            print(f"Config file not found at {config_path}. Using default parameters.")
            # Default parameters if no config file
            self.power_supply_output_delay = 0.3
            self.power_supply_ramp_delay = 0.1
            self.hv_power_supply_name = 'ASRL3::INSTR'
            self.VoltageLimit = 100
            self.CurrentLimit = 0.3
            self.VoltageWrite = 40
            self.timestep = 0.1
            self.voltage_step = 4


    def open_hv_power_supply(self):
        """
        Opens the HV power supply if not already open.
        """
        if self.hv_power_supply is not None:
            print("HV power supply is already opened.")
            return
        try:
            self.hv_power_supply = self.rm.open_resource(self.hv_power_supply_name, query_delay=0.5)
            # Ajout Nico - à tester
            self.hv_power_supply.baud_rate = 9600 # 300
##            self.hv_power_supply.write_termination = ''
##            self.hv_power_supply.read_termination = '\r\n'
##            self.hv_power_supply.set_visa_attribute(constants.VI_ATTR_ASRL_FLOW_CNTRL, constants.VI_ASRL_FLOW_XON_XOFF)
##            self.hv_power_supply.stop_bits = constants.StopBits.one
##            self.hv_power_supply.parity = constants.Parity.none
##            self.hv_power_supply.data_bits = 8
            self.hv_power_supply.write('INSTrument:NSELect  1')
            print(f"Opened HV power supply => {self.hv_power_supply_name}")
##            # Clear and flush buffer
##            self.hv_power_supply.flush()
##            time.sleep(0.5)
##            self.hv_power_supply.clear()
##            time.sleep(0.5)
##            print('Flushed HV power supply')
        except Exception as e:
            print(f"Failed to open HV power supply => {self.hv_power_supply_name}: {e}")

    def close_hv_power_supply(self):
        """
        Closes the HV power supply if it is open.
        """
        if self.hv_power_supply is not None:
            try:
                self.hv_power_supply.close()
                print("Closed HV power supply.")
                time.sleep(0.5)
                del self.hv_power_supply
                print("Deleted HV power supply.")
            except Exception as e:
                print(f"Error closing HV power supply: {e}")
            finally:
                self.hv_power_supply = None


    def power_supply_output_change(self, state: str, delay = 0.3):
            """
            Changes the output state of the HV power supply (e.g., 'ON' or 'OFF').

            Parameters
            ----------
            state : str
                The desired output state, typically 'ON' or 'OFF'.
            """
            if self.hv_power_supply is None:
                raise ValueError("HV power supply is not opened.")

            cmd = f'OUTPut:STATe {state}'
            self.hv_power_supply.write(cmd)
            time.sleep(delay)

    def power_supply_check_voltage(self, delay = 0.3) -> float:
        """
        Queries the HV power supply for the measured voltage.

        Returns
        -------
        float
            The measured voltage as a float.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        cmd = 'MEASure:VOLTage?'
        result = self.hv_power_supply.query(cmd)
        time.sleep(delay)
        return float(result)

    def power_supply_check_current(self, delay = 0.3) -> float:
        """
        Queries the HV power supply for the measured current.

        Returns
        -------
        float
            The measured current as a float.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        cmd = 'MEASure:CURRent?'
        result = self.hv_power_supply.query(cmd)
        time.sleep(delay)
        return float(result)

    def power_supply_voltage_ramp_up(self, voltage: float, step_value: float, start_value=0, delay = 0.1):
        """
        Ramps up the voltage of the HV power supply from start_value to 'voltage', 
        in steps of step_value, waiting self.timestep between steps.

        Parameters
        ----------
        voltage : float
            Target voltage to reach.
        step_value : float
            The increment in voltage for each step.
        start_value : float, optional
            The initial voltage. Defaults to 0.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        self.hv_power_supply.write('VOLTage:MODE FIX')
        steps = np.arange(start_value, voltage + step_value, step_value)
        for x in steps:
            x2=round(x)
            cmd2 = f'VOLT:LEV {x2}'
            self.hv_power_supply.write(cmd2)
            time.sleep(delay)
        time.sleep(delay)

    def power_supply_voltage_ramp_down(self, start_voltage: float, end_value: float, step_value: float, delay = 0.1):
        """
        Ramps down the voltage of the HV power supply from 'start_voltage' to 'end_value', 
        in negative increments (step_value < 0), waiting self.timestep between steps.

        Parameters
        ----------
        start_voltage : float
            The starting voltage.
        end_value : float
            The final voltage to reach.
        step_value : float
            The negative increment for each step, e.g., -1.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        self.hv_power_supply.write('VOLTage:MODE FIX')
        steps = np.arange(start_voltage, end_value, step_value)
        for x in steps:
            x2=round(x)
            cmd2 = f'VOLT:LEV {x2}'
            self.hv_power_supply.write(cmd2)
            time.sleep(delay)
        time.sleep(delay)

    def power_set_voltage(self, voltage: int, delay = 0.1):
        """
        Sets the voltage of the HV power supply.

        Parameters
        ----------
        voltage : int 
            The voltage to set.
        delay : float, optional
            The delay between commands, by default 0.3 seconds.

        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        value = voltage
        cmd = f'VOLT:LEV {value}'
        self.hv_power_supply.write(cmd)
        time.sleep(delay)


def find_json_files(folder):
    json_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.relpath(os.path.join(root, file), "./"))
    return json_files

# ======================== USAGE EXAMPLE ========================
if __name__ == "__main__":
    """
    Example usage of the TDKZ650_1_U class for power supply control.
    """
    print("\n" + "="*60)
    print("  TDKZ650_1_U Power Supply Controller - Example Usage")
    print("="*60 + "\n")
    
    jsonlist = find_json_files("../PhaseShift")

    # Initialize with configuration file
    tdk = TDKZ650_1_U(config_path=jsonlist[0])
    
    try:
        # Open the HV power supply
        print("\n1. Opening HV power supply...")
        tdk.open_hv_power_supply()
        print("   ✓ HV power supply opened successfully\n")
        
        # Set initial voltage to 0V
        print("2. Setting initial voltage to 0V...")
        tdk.power_set_voltage(voltage=0)
        print("   ✓ Initial voltage set to 0V\n")

        # Enable the HV power supply output
        tdk.power_supply_output_change("ON", delay=tdk.power_supply_output_delay)
        print('HV supply ON')
        
        # Ramp up voltage        
        print(f"4. Ramping up voltage to {tdk.VoltageWrite}V...")
        tdk.power_supply_voltage_ramp_up(voltage=tdk.VoltageWrite, step_value=tdk.voltage_step, start_value=0, delay=tdk.power_supply_ramp_delay)
        print("   ✓ Voltage ramp-up complete\n")

        time.sleep(2)  # Stabilization delay before measurements
        # ramp down voltage
        print(f"5. Ramping down voltage to 0V...")
        tdk.power_supply_voltage_ramp_down(start_voltage=tdk.VoltageWrite, end_value=0, step_value=-tdk.voltage_step, delay=tdk.power_supply_ramp_delay)
        print("   ✓ Voltage ramp-down complete\n")

        #disable output
        print("6. Disabling HV power supply output...")
        tdk.power_supply_output_change(state='OFF', delay=tdk.power_supply_output_delay)
        print("   ✓ HV power supply output disabled\n")

        # Set initial voltage to 0V
        print("2. Setting initial voltage to 0V...")
        tdk.power_set_voltage(voltage=0)
        print("   ✓ Initial voltage set to 0V\n")

        # Close the HV power supply
        print("7. Closing HV power supply...")
        tdk.close_hv_power_supply()
        print("   ✓ HV power supply closed successfully\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        # Always cleanup
        print("5. Cleanup...")
        print("   ✓ Resources released.\n")
        print("="*60)
        print("  Example completed")
        print("="*60 + "\n")
