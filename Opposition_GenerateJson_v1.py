# Author Nicolas Rouger
# V1 Jan 2025
# To generate several Json
# For opposition test bench
# GPL v3

import math
import matplotlib.pyplot as plt
import numpy as np
import json


# Settings
# Fixed values - your settings
freq = 100 #kHz
InductorL = 50 #µH
InductorR = 0.01 # Ohms
RdsON = 0.18 # Ohms
CircuitR = 0.1 # Ohms
#>
TotalR=InductorR+RdsON*2+CircuitR # Ohms

# Sweep values
Imin = 0.5 # A
Imax = 3 # A
nbPointsI = 6

# Step values
Vmin = 40 # V
Vmax = 80 # V
nbPointsV = 3

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
Phi=180*Ipeak[:,None]*InductorL*freq*1e-3/Vdc # in °
print('Phase shift steps in °:')
print(Phi)
print('\n')


# Process each column and save as a separate JSON file
for i in range(Phi.shape[1]):  # iterate over columns
    column_data = Phi[:, i]
    min_val = np.min(column_data)
    max_val = np.max(column_data)
    step = np.mean(np.diff(np.sort(column_data)))  # Calculate the average step
    
    # The value of VoltageWorte corresponds to the respective value in 'a'
    voltage_write = Vdc[i]
    
    # Create the structure for this column
    column_info = {
        "frequencyPWM": freq,
        "PhaseInit": min_val,
        "PhaseFinal": max_val,
        "PhaseStep": step,
        "VoltageWrite": voltage_write,
        "Sequence": nbPointsI,
        "Imin":Imin,
        "Imax":Imax
    }
    
    # Save to JSON file
    filename = f"PhaseShift_Voltage_{voltage_write}V_Freq{freq}kHz.json"
    with open(filename, 'w') as f:
        json.dump(column_info, f, indent=4)
    
    print(f"Column {i+1} stats saved to '{filename}'")


# DELTA ALPHA mode
DeltaAlpha=Ipeak[:,None]*TotalR/Vdc # in absolute value
DeltaAlpha1000=np.floor(1000*DeltaAlpha) # Delta Alpha Value multiplied by 1 000
print('Delta Alpha steps in x1000:')
print(DeltaAlpha1000)
print('\n')



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
        "frequencyPWM": freq,
        "DutyInit": min_val,
        "DutyFinal": max_val,
        "DutyStep": step,
        "VoltageWrite": voltage_write,
        "Sequence": nbPointsI,
        "Imin":Imin,
        "Imax":Imax
    }
    
    # Save to JSON file
    filename = f"DeltaAlpha_Voltage_{voltage_write}V_Freq{freq}kHz.json"
    with open(filename, 'w') as f:
        json.dump(column_info, f, indent=4)
    
    print(f"Column {i+1} stats saved to '{filename}'")
