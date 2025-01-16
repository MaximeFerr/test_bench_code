"""
parameters.py

This script documents the parameters used by the test bench system and writes them
to a JSON file (by default named 'parameters.json').

Usage:
    python parameters.py

After running, you'll have a file named `parameters.json` containing all the
configurable parameters for the Supervisor class and related functionalities.
"""

import json

# A dictionary containing the parameters. Explanations are in Python comments.
parameters = {
    # Delays (in seconds)
    "delay": 0.1,            # General small delay, e.g., for communication
    "delay2": 0.2,           # Another delay slot (used if needed for distinct actions)
    "delay3": 0.4,           # Longer delay, e.g., for cooldown, dwell time
    "delay_com": 0.1,        # Delay specifically for microcontroller communication

    # PWM parameters
    "DutyPWM": 0.485,        # Default duty cycle (48.5%)
    "frequencyPWM": 100000,  # Switching frequency in Hz (100kHz)
    "DeadTimePWM": 300,      # Dead time in ns (300ns)
    "InitialPhaseShiftPWM": 15, # Initial phase shift (15°)

    # Voltage/current limits and ramp parameters
    "VoltageLimit": 100,     # Max permissible DC Voltage
    "CurrentLimit": 0.3,     # Max permissible DC Current
    "VoltageWrite": 50,      # Target DC voltage for ramp-up
    "timestep": 0.1,         # Delay between each voltage step
    "voltage_step": 1,       # Voltage increment for ramp steps

    # Phase sweep
    "PhaseInit": 15,         # Start phase in degrees
    "PhaseFinal": 60,        # End phase in degrees
    "PhaseStep": 30,         # Phase step in degrees

    # Duty sweep
    "DutyInit": 485,         # Start duty * 1000 (e.g., 485 => 0.485)
    "DutyFinal": 495,        # End duty * 1000 (e.g., 495 => 0.495)
    "DutyStep": 1,           # Increment step for duty sweep

    # Instrument resource names
    "HVpowerSupply": "ASRL27::INSTR",             # HV power supply VISA address
    "DMMforCurrent": "SDM36HCX800420",            # DMM for current
    "DMMforVoltage": "SDM36HCX800421",            # DMM for voltage
    "AddressOSCILLO": "USB0::0xF4EC::0x1011::SDS2PFFX801302::INSTR", # Oscilloscope resource

    # Oscilloscope config
    "Sequence": "3",          # Mode or ID for sequence config
    "delayOscillo": 0.5,      # Additional wait time for oscilloscope actions
    "SaveEachFramePICTURE": 0,# 1 to save pictures each frame, 0 otherwise
    "SaveEachFrameDATA": 0,   # 1 to save data each frame, 0 otherwise

    # Microcontroller (shield) parameters
    "shield_vid": 7667,       # e.g., 0x2fe3 => decimal 7667
    "shield_pid": 257         # e.g., 0x0101 => decimal 257
}

def write_parameters_to_json(filename: str = "parameters.json"):
    """
    Writes the 'parameters' dictionary to a JSON file with indentation.

    Parameters
    ----------
    filename : str
        The JSON file to be created or overwritten (default: parameters.json).
    """
    with open(filename, "w") as f:
        json.dump(parameters, f, indent=4)
    print(f"Parameters written to {filename}")

def main():
    """
    Documents the parameters used by the test bench system and writes them 
    to a JSON file. You can run this script directly to produce/update the file.
    """
    print("Documenting parameters and generating JSON configuration...\n")

    # Print some of the docstrings or further commentary if desired
    print("Parameters to be saved:")
    for key, val in parameters.items():
        print(f"  {key}: {val}")

    # Write to JSON
    write_parameters_to_json("parameters.json")

    print("\nDone. 'parameters.json' created or updated.")

if __name__ == "__main__":
    main()
