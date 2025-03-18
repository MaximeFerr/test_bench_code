#! python3

# Original authors: Nicolas Rouger, Luiz Villa
# Revised by Leijnen Lorenzo
# V1_3 Mar 2025
# To bulk generate Json config
# For opposition test bench
# GPL v3

import numpy as np
import json
import os


# -----------------------------
# Defenitions
# -----------------------------
def autoGenerateJson(Commonparameters, dest_path:str, matrix, voltageRange, mode:str)->int:
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
        subfolder_path = os.path.join(dest_path, f"Voltage_{int(voltageRange[i])}")
        
        phase_info = {
            "dataOutputFolder": subfolder_path.replace('\\','/'),
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
            "dataOutputFolder": subfolder_path.replace('\\','/'),
            "VoltageWrite": int(voltageRange[i]), # ok
            "DutyInit": min_val,
            "DutyFinal": max_val,
            "DutyStep": step,
        }

        # Finishing up...
        # - Create SubFolder
        os.makedirs(subfolder_path, exist_ok=True)  # Create subfolder1 inside Folder1

        # - Merge Parameters
        match mode:
            case "Phase":
                combined_parameters = {**Commonparameters, **phase_info}
            case "Duty":
                combined_parameters = {**Commonparameters, **duty_info}
            case _:
                return -1
        
        # - Save to JSON file
        filename = f"PhaseShift_Voltage_{int(voltageRange[i])}V_Freq{int(frequencyPWM*1e-3)}kHz.json"
        file_path = os.path.join(subfolder_path, filename)
        with open(file_path, 'w') as f:
            json.dump(combined_parameters, f, indent=4)
        
        print(f"Column {i+1} stats saved to '{subfolder_path}\{filename}'")
    
    # End of function
    return 1


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Load base config
    base_config_path = "base-config.json"
    with open(base_config_path, 'r') as f:
        base_config = json.load(f)
    
    frequencyPWM = base_config['frequencyPWM']
    InductorL = base_config['InductorL']
    TotalR = base_config['TotalR']
    Imin = base_config['Imin']
    Imax = base_config['Imax']
    Vmin = base_config['Vmin']
    Vmax = base_config['Vmax']
    nbPointsV = base_config['nbPointsV']
    nbPointsI = base_config['nbPointsI']

    Vdc=np.linspace(Vmin, Vmax, nbPointsV)
    print(f"Voltage steps:\n{Vdc}")

    Ipeak=np.linspace(Imin, Imax, nbPointsI)
    print(f"Current steps:\n{Ipeak}")

    # Phase Shift Mode
    Phi=np.round(180*Ipeak[:,None]*InductorL*frequencyPWM*1e-6/Vdc,decimals=0) # in degrees
    print(f"\nPhase shift steps in degrees:\n{Phi}")
    folder1_path = 'PhaseShift'
    autoGenerateJson(base_config, folder1_path, Phi, Vdc, mode="Phase")

    # Delta Alpha Mode
    DeltaAlpha=Ipeak[:,None]*TotalR/Vdc # in absolute value
    DeltaAlpha1000=np.floor(1000*DeltaAlpha) # Delta Alpha Value multiplied by 1 000
    print(f"\nDelta Alpha steps in x1000:\n{DeltaAlpha1000}")
    folder2_path = 'DutyShift'
    autoGenerateJson(base_config, folder2_path, DeltaAlpha1000, Vdc, mode="Duty")
