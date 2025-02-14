# Author Nicolas Rouger + Luiz Villa
# V1_1 Jan 2025
# To generate several Json
# For opposition test bench
# GPL v3

import math
import matplotlib.pyplot as plt
import numpy as np
import json
import os


# Settings
# Fixed values - your settings
InductorL = 50 #µH
InductorR = 0.03 # Ohms
RdsON = 0.18 # Ohms
CircuitR = 0.2 # Ohms
#>
TotalR=InductorR+RdsON*2+CircuitR # Ohms

# Sweep values - your inputs
Imin = 0.5 # A
Imax = 3 # A
nbPointsI = 6

# Step values - your inputs
Vmin = 40 # V
Vmax = 80 # V
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
# OSCILLO
delayOscillo=0.5 # Longer delay for oscillloscope
SaveEachFramePICTURE = 0 # 0 NO, 1 YES
SaveEachFrameDATA = 0 # 0 NO, 1 YES


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

##    # Phase sweep
##    "PhaseInit": 15,         # Start phase in degrees
##    "PhaseFinal": 60,        # End phase in degrees
##    "PhaseStep": 30,         # Phase step in degrees

##    # Duty sweep
##    "DutyInit": 485,         # Start duty * 1000 (e.g., 485 => 0.485)
##    "DutyFinal": 495,        # End duty * 1000 (e.g., 495 => 0.495)
##    "DutyStep": 1,           # Increment step for duty sweep

    # Instrument resource names
    "HVpowerSupply": "ASRL27::INSTR",             # HV power supply VISA address
    "DMMforCurrent": "USB0::0xF4EC::0x1203::SDM36HCX800420::INSTR",            # DMM for current
    "DMMforVoltage": "USB0::0xF4EC::0x1203::SDM36HCX800421::INSTR",            # DMM for voltage
    "AddressOSCILLO": "USB0::0xF4EC::0x1011::SDS2PFFX801302::INSTR", # Oscilloscope resource
    # "AddressOSCILLO": 'USB0::0xF4EC::0x1011::SDS2PDDX6R0968::INSTR', # for testing

    # Oscilloscope config
##    "Sequence": 3,          # Mode or ID for sequence config
    "delayOscillo": delayOscillo,      # Additional wait time for oscilloscope actions
    "SaveEachFramePICTURE": SaveEachFramePICTURE,# 1 to save pictures each frame, 0 otherwise
    "SaveEachFrameDATA": SaveEachFrameDATA,   # 1 to save data each frame, 0 otherwise
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

### Concatenate parameter1 and parameter2 (combine them into a single dictionary)
##combined_parameters = {**Commonparameters, **parameter2}

# PHASE SHIFT MODE
#Voltage=[i for i in range(Vmin, Vmax, StepsV)]
Vdc=np.linspace(Vmin, Vmax, nbPointsV)
print('Voltage steps:')
print(Vdc)

#Current=[i for i in range(Imin, Imax, StepsI)]
Ipeak=np.linspace(Imin, Imax, nbPointsI)
print('Current steps:')
print(Ipeak)
print('\n')

# Phase Shift Mode
Phi=np.round(180*Ipeak[:,None]*InductorL*frequencyPWM*1e-3/Vdc,decimals=0) # in °
print('Phase shift steps in °:')
print(Phi)
print('\n')

# Create Folder1
folder1_path = 'PhaseShift'
#os.makedirs(folder1_path, exist_ok=True)  # Creates Folder1 if it doesn't exist



# Process each column and save as a separate JSON file
for i in range(Phi.shape[1]):  # iterate over columns
    column_data = Phi[:, i]
    min_val = int(np.min(column_data))
    #max_val = np.max(column_data)
    step = int(np.round(np.mean(np.diff(np.sort(column_data)))))  # Calculate the average step
    
    max_val = int(step*(nbPointsI-1) + min_val)
    
    # The value of VoltageWorte corresponds to the respective value in 'a'
    voltage_write = int(Vdc[i])
    
    # Create the structure for this column
    column_info = {
        #"frequencyPWM": 1000*frequencyPWM, # Hz
        "InitialPhaseShiftPWM": min_val, # Initial phase shift (cf Imin)
        "PhaseInit": min_val,
        "PhaseFinal": max_val+1,
        "PhaseStep": step,
        "VoltageWrite": voltage_write,
        "Sequence": nbPointsI,
        "Imin":Imin,
        "Imax":Imax,
        "DutyInit": 0,         # Start duty * 1000 (e.g., 485 => 0.485)
        "DutyFinal": 0,        # End duty * 1000 (e.g., 495 => 0.495)
        "DutyStep": 0           # Increment step for duty sweep
    }
    # Merge Parameters
    combined_parameters = {**Commonparameters, **column_info}
    
    # Create SubFolder1
    subfolder1_path = os.path.join(folder1_path, f"Voltage_{voltage_write}")
    os.makedirs(subfolder1_path, exist_ok=True)  # Create subfolder1 inside Folder1
    
    # Save to JSON file
    filename = f"PhaseShift_Voltage_{voltage_write}V_Freq{frequencyPWM}kHz.json"
    file1_path = os.path.join(subfolder1_path, filename)
    with open(file1_path, 'w') as f:
        json.dump(combined_parameters, f, indent=4)
    
    print(f"Column {i+1} stats saved to '{filename}'")


# DELTA ALPHA mode
DeltaAlpha=Ipeak[:,None]*TotalR/Vdc # in absolute value
DeltaAlpha1000=np.floor(1000*DeltaAlpha) # Delta Alpha Value multiplied by 1 000
print('Delta Alpha steps in x1000:')
print(DeltaAlpha1000)
print('\n')

# Create Folder2
folder2_path = 'DutyShift'



# Process each column and save as a separate JSON file
for i in range(DeltaAlpha1000.shape[1]):  # iterate over columns
    column_data = DeltaAlpha1000[:, i]
    min_val = np.min(column_data)
    max_val = np.max(column_data)
    step = np.mean(np.diff(np.sort(column_data)))  # Calculate the average step
    
    # The value of VoltageWorte corresponds to the respective value in 'a'
    voltage_write = Vdc[i]
    
    # Create the structure for this column
    column_info = {
        "frequencyPWM": frequencyPWM,
        "DutyInit": min_val,
        "DutyFinal": max_val,
        "DutyStep": step,
        "VoltageWrite": voltage_write,
        "Sequence": nbPointsI,
        "Imin":Imin,
        "Imax":Imax
    }
    # Create SubFolder1
    subfolder2_path = os.path.join(folder2_path, f"Voltage_{voltage_write}")
    os.makedirs(subfolder2_path, exist_ok=True)  # Create subfolder2 inside Folder2
    
    # Save to JSON file
    filename2 = f"DeltaAlpha_Voltage_{voltage_write}V_Freq{frequencyPWM}kHz.json"
    file2_path = os.path.join(subfolder2_path, filename2)
    with open(file2_path, 'w') as f:
        json.dump(column_info, f, indent=4)
    
    print(f"Column {i+1} stats saved to '{filename2}'")
