# Original authors: Nicolas Rouger, Luiz Villa
# Revised by Leijnen Lorenzo
# V1_3 Feb 2025
# To bulk generate Json config
# For opposition test bench
# GPL v3

import numpy as np
import json
import os


############
# Settings #
############
# Fixed values - your settings
#         L            R
# +---)()()()(-----/\/\/\/\----+
InductorL = 50      # µH
InductorR = 0.03    # Ohms
RdsON = 0.18        # Ohms
CircuitR = 0.2      # Ohms
TotalR=InductorR+RdsON*2+CircuitR # Ohms

# Sweep values - your inputs
Imin, Imax = 0.5, 3 # A
nbPointsI = 6

# Step values - your inputs
Vmin, Vmax = 40, 80 # V
nbPointsV = 3
VoltageLimit = 100 # V, limit for HV DC source
CurrentLimit = 0.3 # A, limit for HV DC source
timestep = 0.1
voltage_step = 4

# Sweep values for Phase Shift:
DutyPWM=0.485 # Default duty cycle (48.5%)
DeadTimePWM=300 # Dead time in ns (300ns)
frequencyPWM = 100 #kHz
InitialPhaseShiftPWM = 15 # Initial phase shift (15°)

# COM parameters
delay=0.1 # General small delay, e.g., for communication
delay2=0.2 # Another delay slot (used if needed for distinct actions)
delay3=0.4 # Longer delay, e.g., for cooldown, dwell time
delay_com=0.1 # Delay specifically for microcontroller communication

# Oscilloscope
delayOscillo=0.5 # Longer delay for oscillloscope
SaveEachFramePICTURE = False # True, False
SaveEachFrameDATA = False # True, False


# A dictionary containing the parameters. Explanations are in Python comments.
Commonparameters = {
    # Delays (in seconds)
    "delay": delay,            # General small delay, e.g., for communication
    "delay2": delay2,           # Another delay slot (used if needed for distinct actions)
    "delay3": delay3,           # Longer delay, e.g., for cooldown, dwell time
    "delay_com": delay_com,        # Delay specifically for microcontroller communication

    # PWM parameters
    "DutyPWM": DutyPWM,        # Default duty cycle (48.5%)
    "frequencyPWM": 1000*frequencyPWM,  # Switching frequency in Hz (100kHz)
    "DeadTimePWM": DeadTimePWM,      # Dead time in ns (300ns)
    #"InitialPhaseShiftPWM": 15, # Initial phase shift (15°)

    # Voltage/current limits and ramp parameters
    "VoltageLimit": VoltageLimit,     # Max permissible DC Voltage
    "CurrentLimit": CurrentLimit,     # Max permissible DC Current
    #"VoltageWrite": 50,      # Target DC voltage for ramp-up
    "timestep": timestep,         # Delay between each voltage step
    "voltage_step": voltage_step,       # Voltage increment for ramp steps

    "Sequence": nbPointsI, # ok
    "Imin":Imin, # ok
    "Imax":Imax, # ok

    # Instrument resource names
    "HVpowerSupply": "ASRL27::INSTR",             # HV power supply VISA address
    "DMMforCurrent": "USB0::0xF4EC::0x1203::SDM36HCX800420::INSTR",            # DMM for current
    "DMMforVoltage": "USB0::0xF4EC::0x1203::SDM36HCX800421::INSTR",            # DMM for voltage
    "AddressOSCILLO": "USB0::0xF4EC::0x1011::SDS2PFFX801302::INSTR", # Oscilloscope resource
    # "AddressOSCILLO": 'USB0::0xF4EC::0x1011::SDS2PDDX6R0968::INSTR', # for testing

    # Oscilloscope config
    "delayOscillo": delayOscillo,      # Additional wait time for oscilloscope actions
    "SaveEachFramePICTURE": int(SaveEachFramePICTURE),# 1 to save pictures each frame, 0 otherwise
    "SaveEachFrameDATA": int(SaveEachFrameDATA),   # 1 to save data each frame, 0 otherwise
    "ScopeAutoMeasure": [                   # Configure scope measurements list
        {'type': 'FREQ', 'channel': 1},
        {'type': 'AMPL', 'channel': 2}
    ],

    # Microcontroller (shield) parameters
    "shield_vid": 12259,       # e.g., 0x2fe3 => decimal 7667
    "shield_pid": 257,         # e.g., 0x0101 => decimal 257

    #Parameters
    "TotalR": TotalR,
    "InductorL": InductorL,
    
    # Results output folder
    "dataOutputFolder": "DataResults"
}



def autoGenerateJson(dest_path:str, matrix, voltageRange, mode:str):
    """ Generates JSON file structure in specifier path.
        from input matrix scenario 
        The voltage range
    """
    # Process each column and save as a separate JSON file
    for i in range(matrix.shape[1]):  # iterate over columns
        column_data = matrix[:, i]
        step = np.mean(np.diff(np.sort(column_data)))  # Calculate the average step
        min_val = int(np.min(column_data))
        max_val = np.max(column_data)
        
        phase_info = {
            "VoltageWrite": int(voltageRange[i]), # ok
            "InitialPhaseShiftPWM": min_val, # Initial phase shift (cf Imin)
            "PhaseInit": min_val,
            "PhaseFinal": int(step*(nbPointsI-1) + min_val)+1,
            "PhaseStep": int(np.round(step)),
            "DutyInit": 0,         # Start duty * 1000 (e.g., 485 => 0.485)
            "DutyFinal": 0,        # End duty * 1000 (e.g., 495 => 0.495)
            "DutyStep": 0          # Increment step for duty sweep
        }

        duty_info = {
            "VoltageWrite": int(voltageRange[i]), # ok
            "DutyInit": min_val,
            "DutyFinal": max_val,
            "DutyStep": step,
        }

        # Finishing up...
        # - Merge Parameters
        match mode:
            case "Phase":
                combined_parameters = {**Commonparameters, **phase_info}
            case "Duty":
                combined_parameters = {**Commonparameters, **duty_info}
            case _:
                combined_parameters = {**Commonparameters}
        
        # - Create SubFolder
        subfolder_path = os.path.join(dest_path, f"Voltage_{int(voltageRange[i])}")
        os.makedirs(subfolder_path, exist_ok=True)  # Create subfolder1 inside Folder1
        
        # - Save to JSON file
        filename = f"PhaseShift_Voltage_{int(voltageRange[i])}V_Freq{frequencyPWM}kHz.json"
        file_path = os.path.join(subfolder_path, filename)
        with open(file_path, 'w') as f:
            json.dump(combined_parameters, f, indent=4)
        
        print(f"Column {i+1} stats saved to '{subfolder_path}\{filename}'")
    
    # End of function
    return


########
# Main #
########
if __name__ == "__main__":
    Vdc=np.linspace(Vmin, Vmax, nbPointsV)
    print(f"Voltage steps:\n{Vdc}")

    Ipeak=np.linspace(Imin, Imax, nbPointsI)
    print(f"Current steps:\n{Ipeak}")

    # Phase Shift Mode
    Phi=np.round(180*Ipeak[:,None]*InductorL*frequencyPWM*1e-3/Vdc,decimals=0) # in degrees
    print(f"\nPhase shift steps in degrees:\n{Phi}")
    folder1_path = 'PhaseShift'
    autoGenerateJson(folder1_path, Phi, Vdc, mode="Phase")

    # Delta Alpha Mode
    DeltaAlpha=Ipeak[:,None]*TotalR/Vdc # in absolute value
    DeltaAlpha1000=np.floor(1000*DeltaAlpha) # Delta Alpha Value multiplied by 1 000
    print(f"\nDelta Alpha steps in x1000:\n{DeltaAlpha1000}")
    folder2_path = 'DutyShift'
    autoGenerateJson(folder2_path, DeltaAlpha1000, Vdc, mode="Duty")
