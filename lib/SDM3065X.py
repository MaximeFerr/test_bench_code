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


class SDM3065X:
    """
    Class to manage DMM (Siglent SDM3065) resources for current and voltage measurements.
    
    This class handles opening, closing, and configuring two Siglent SDM3065 digital multimeters
    for DC current and DC voltage measurements with external triggering.
    
    Parameters
    ----------
    config_path : str, optional
        Path to JSON configuration file. If None, uses default parameters.
    dmm_current_addr : str, optional
        VISA address for current DMM. Default: from config or TCPIP0::169.254.126.119::inst0::INSTR
    dmm_voltage_addr : str, optional
        VISA address for voltage DMM. Default: from config or TCPIP0::169.254.126.120::inst0::INSTR
    
    Example
    -------
    >>> sdm = SDM3065X(config_path='base-config.json')
    >>> sdm.open_all_dmm()
    >>> sdm.dmm_setup()
    >>> # ... measurements ...
    >>> voltage_data = sdm.dmm_get_buffer(sdm.dmm_for_voltage)
    >>> current_data = sdm.dmm_get_buffer(sdm.dmm_for_current)
    >>> sdm.close_all_dmm()
    """

    def __init__(self, config_path: str = None, dmm_current_addr: str = None, dmm_voltage_addr: str = None):
        """
        Initialize the SDM3065X DMM controller.
        
        Parameters
        ----------
        config_path : str, optional
            Path to JSON config file containing DMM parameters
        dmm_current_addr : str, optional
            Override current DMM address
        dmm_voltage_addr : str, optional
            Override voltage DMM address
        """
        # Create PyVISA Resource Manager
        self.rm = visa.ResourceManager()
        
        # Initialize DMM resource attributes
        self.dmm_for_current = None
        self.dmm_for_voltage = None
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"Config file found at {config_path}. Loading parameters...")
            # Load DMM addresses
            self.dmm_for_current_name = dmm_current_addr or config.get('DMMforCurrent', 'TCPIP0::169.254.126.119::inst0::INSTR')
            self.dmm_for_voltage_name = dmm_voltage_addr or config.get('DMMforVoltage', 'TCPIP0::169.254.126.120::inst0::INSTR')
            
            # Load DMM parameters
            self.dmm_init_delay = config.get('dmm_init_delay', 2)
            self.dmm_cmd_delay = config.get('dmm_cmd_delay', 0.1)
            self.dmm_current_nplc = config.get('dmm_current_nplc', 0.5)
            self.dmm_voltage_nplc = config.get('dmm_voltage_nplc', 0.5)
            self.dmm_current_sample_count = config.get('dmm_current_sample_count', 3)
            self.dmm_voltage_sample_count = config.get('dmm_voltage_sample_count', 3)
            self.nb_points_i = config.get('nbPointsI', 10)
        else:
            print(f"Config file not found at {config_path}. Using default parameters.")
            # Default parameters if no config file
            self.dmm_for_current_name = dmm_current_addr or 'TCPIP0::169.254.126.119::inst0::INSTR'
            self.dmm_for_voltage_name = dmm_voltage_addr or 'TCPIP0::169.254.126.120::inst0::INSTR'
            
            self.dmm_init_delay = 2
            self.dmm_cmd_delay = 0.1
            self.dmm_current_nplc = 0.5
            self.dmm_voltage_nplc = 0.5
            self.dmm_current_sample_count = 3
            self.dmm_voltage_sample_count = 3
            self.nb_points_i = 10
        
        print(f"SDM3065X controller initialized")
        print(f"  Current DMM: {self.dmm_for_current_name}")
        print(f"  Voltage DMM: {self.dmm_for_voltage_name}")

#A tester
    def open_all_dmm(self):
        """Opens both DMM resources (current and voltage)."""
        self.open_dmm_for_current()
        time.sleep(0.3)
        self.open_dmm_for_voltage()
        time.sleep(0.3)
#A tester
    def close_all_dmm(self):
        """Closes both DMM resources (current and voltage)."""
        self.close_dmm_for_current()
        time.sleep(0.3)
        self.close_dmm_for_voltage()
        time.sleep(0.3)

    def open_dmm_for_current(self):
        """
        Opens the DMM used for current measurements if not already open.
        """
        if self.dmm_for_current is not None:
            print("DMM for current is already opened.")
            return
        try:
            self.dmm_for_current = self.rm.open_resource(self.dmm_for_current_name, query_delay=0.5)
            print(f"Opened DMM for current => {self.dmm_for_current_name}")
##            # Clear and flush buffer
##            self.dmm_for_current.flush()
##            time.sleep(0.5)
##            self.dmm_for_current.clear()
##            time.sleep(0.5)
##            print('Flushed DMM for current')
        except Exception as e:
            print(f"Failed to open DMM for current => {self.dmm_for_current_name}: {e}")

    def close_dmm_for_current(self):
        """
        Closes the DMM for current measurements if open.
        """
        if self.dmm_for_current is not None:
            try:
                self.dmm_for_current.close()
                print("Closed DMM for current.")
                time.sleep(0.5)
                del self.dmm_for_current
                print("Deleted DMM for current.")
            except Exception as e:
                print(f"Error closing DMM for current: {e}")
            finally:
                self.dmm_for_current = None

    def open_dmm_for_voltage(self):
        """
        Opens the DMM used for voltage measurements if not already open.
        """
        if self.dmm_for_voltage is not None:
            print("DMM for voltage is already opened.")
            return
        try:
            self.dmm_for_voltage = self.rm.open_resource(self.dmm_for_voltage_name, query_delay=0.5)
            print(f"Opened DMM for voltage => {self.dmm_for_voltage_name}")
##            # Clear and flush buffer
##            self.dmm_for_voltage.flush()
##            time.sleep(0.5)
##            self.dmm_for_voltage.clear()
##            time.sleep(0.5)
##            print('Flushed DMM for voltage')
            
        except Exception as e:
            print(f"Failed to open DMM for voltage => {self.dmm_for_voltage_name}: {e}")

    def close_dmm_for_voltage(self):
        """
        Closes the DMM for voltage measurements if open.
        """
        if self.dmm_for_voltage is not None:
            try:
                self.dmm_for_voltage.close()
                print("Closed DMM for voltage.")
                time.sleep(0.5)
                del self.dmm_for_voltage
                print("Deleted DMM for voltage.")
            except Exception as e:
                print(f"Error closing DMM for voltage: {e}")
            finally:
                self.dmm_for_voltage = None


    def dmm_setup(self):
        # Configure DMMs (already opened in sup.dmm_for_current, sup.dmm_for_voltage)
        # For example, we can send SCPI commands to set them up
        self.dmm_send_cmd(self.dmm_for_current, [
            "*RST",
            "CONF:CURR:DC 0.2",
            "CURR:DC:AZ OFF",
            #"CONF:CURR:DC AUTO",
            "TRIG:SOUR EXT;SLOP POS",
            f"TRIG:COUN {self.nb_points_i}",
            f"SAMP:COUN {self.dmm_current_sample_count}",
            "TRIG:DEL 1E-6",# double check if TRIG:DEL:AUTO 0 is required or not!!!
            f"CURR:DC:NPLC {self.dmm_current_nplc}",
            "INITiate"
        ], delay=self.dmm_cmd_delay)
        self.dmm_send_cmd(self.dmm_for_voltage, [
            "*RST",
            "CONF:VOLT:DC 200",
            "VOLT:DC:AZ OFF",
            #"CONF:VOLT:DC AUTO",
            "TRIG:SOUR EXT;SLOP POS",
            f"TRIG:COUN {self.nb_points_i}",
            f"SAMP:COUN {self.dmm_voltage_sample_count}",
            "TRIG:DEL 1E-6",
            f"VOLT:DC:NPLC {self.dmm_voltage_nplc}",
            "INITiate"
        ], delay=self.dmm_cmd_delay)            
    
    def dmm_send_cmd(self, dmm, cmd_list: list[str], delay = 0.1):
        """
        Sends a list of SCPI commands to a given DMM resource, printing them for visibility.
        Optionally waits 'delay' seconds between commands.

        Parameters
        ----------
        dmm : resource
            The DMM resource object from self.dmm_for_current or self.dmm_for_voltage
        cmd_list : list of str
            The list of SCPI command strings to send.
        delay : float, optional
            Seconds to wait between each command. Default is 0.
        """
        if dmm is None:
            raise ValueError("DMM is not opened.")
        print(f"{dmm.resource_name} sending commands:")
        for cmd in cmd_list:
            dmm.write(cmd)
            print(f"\t - {cmd}")
            time.sleep(delay)

    def dmm_get_buffer(self, dmm, wait_meas_complete: bool = True) -> list[float]:
        """
        Reads data points in the measurement buffer of a given DMM resource and clears it afterward.

        Parameters
        ----------
        dmm : resource
            The DMM resource object from self.dmm_for_current or self.dmm_for_voltage
        wait_meas_complete : bool, optional
            If True, attempts to query 'READ?' which waits for measurement completion.
            If False, queries 'R?' to fetch any data already in the buffer.

        Returns
        -------
        list of float
            The measured values as floats.
        """
        if dmm is None:
            raise ValueError("DMM is not opened.")

        buffer_str = ''
        if wait_meas_complete:
            time.sleep(4)
            read_ok = False
            while not read_ok:
                try:
                    buffer_str = dmm.query('READ?')
                    read_ok = True
                except visa.errors.VisaIOError:
                    print("Wait for measurement to complete")
        else:
            buffer_str = dmm.query('R?')
            time.sleep(2)

        # handle the #nxxx prefix
        digits = int(buffer_str[1])
        return [float(e) for e in buffer_str[digits + 2:].strip().split(',')]

    def dmm_abort_measure(self, dmm, delay = 0.2):
        """
        Aborts any ongoing measurement in the given DMM resource.

        Parameters
        ----------
        dmm : resource
            The DMM resource object to abort measurement on.
        """
        if dmm is None:
            raise ValueError("DMM is not opened.")
        dmm.write('ABORt')
        time.sleep(delay)

#  A tester
    def cleanup(self):
        """
        Closes all open resources including both DMMs and the PyVISA resource manager.
        """
        self.close_all_dmm()
        if self.rm is not None:
            try:
                self.rm.close()
                print("PyVISA ResourceManager closed.")
            except Exception as e:
                print(f"Error closing ResourceManager: {e}")

    def __del__(self):
        """Destructor to ensure resources are cleaned up when object is deleted."""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    

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
    Example usage of the SDM3065X class for DMM control.
    """
    print("\n" + "="*60)
    print("  SDM3065X DMM Controller - Example Usage")
    print("="*60 + "\n")
    
  
    jsonlist = find_json_files("../PhaseShift")

    # Initialize with configuration file
    
    sdm = SDM3065X(config_path=jsonlist[0])

    try:
        # Open both DMMs
        print("\n1. Opening DMMs...")
        sdm.open_all_dmm()
        print("   ✓ DMMs opened successfully\n")
        
        # Configure for measurements
        print("2. Configuring DMMs for DC measurements...")
        sdm.dmm_setup()
        print("   ✓ DMM setup complete!\n")
        
        # Wait for initialization
        print(f"3. Waiting for initialization ({sdm.dmm_init_delay}s)...")
        time.sleep(sdm.dmm_init_delay)
        print("   ✓ Ready for measurements\n")
        
        print("4. Measurements would be triggered by external signal (oscilloscope)...")
        print("   Status: Waiting for trigger...\n")
        
        # Get data from buffers (when data is available)
        # voltage_data = sdm.dmm_get_buffer(sdm.dmm_for_voltage)
        # current_data = sdm.dmm_get_buffer(sdm.dmm_for_current)
        # print(f"   Voltage measurements: {voltage_data}")
        # print(f"   Current measurements: {current_data}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        # Always cleanup
        print("5. Cleanup...")
        sdm.cleanup()
        print("   ✓ Resources released.\n")
        print("="*60)
        print("  Example completed")
        print("="*60 + "\n")
