#! python3

###############################################
# supervisor_script.py
#
# updated 21/05/2026
# > Adapted to run all json files in a folder
###############################################

import os
import time
import matplotlib.pyplot as plt

from supervisor_class import Supervisor

import lib.SDM3065X as SDM3065X
import lib.SDS2104X_plus as SDS2104X_plus
import lib.TDKZ650_1_U as TDKZ650_1_U

from lib.tools import TOOL

# -----------------------------
# Defenitions
# -----------------------------
def runner(config_path):
    # Create Supervisor instance (loads config from specified .json file)

    sdm3065x_for_current = SDM3065X.SDM3065X("current", config_path)
    sdm3065x_for_voltage = SDM3065X.SDM3065X("voltage", config_path)
    sds2104x_plus = SDS2104X_plus.SDS2104X_plus(config_path)
    tdkz650_1_u = TDKZ650_1_U.TDKZ650_1_U(config_path)

    sup = Supervisor(config_path,
                     sdm_current=sdm3065x_for_current,
                     sdm_voltage=sdm3065x_for_voltage,
                     sds_oscilloscope=sds2104x_plus,
                     tdk_power_supply=tdkz650_1_u)


    timestamp=sup.TimeStamp()
    errors = []
    try:
        #######################################
        # 1) INITIALIZATION PHASE
        #######################################

        # Open all devices: HV power supply, DMMs, oscilloscope, microcontroller


        sup.open_all_devices()  #This opens all the devices. #todo
    except Exception as e:
        errors.append(f"Failed to initialize devices: {e}")


    #     # Setup microcontroller, oscilloscope and dmm
    #     # Turn on legs, set Duty, Frequency, Dead Time, etc.
    #     # Instead of using Shield, we now call sup.microcontroller_send_command(...)
    #     sup.microcontroller_setup()
    #     sup.oscilloscope_setup()
    #     sup.dmm_setup()

    #     time.sleep(sup.dmm_init_delay) # Wait DMM initialized
    #     print('Config OK')


    #     #######################################
    #     # 2) TEST PHASE
    #     #######################################
    #     # Example: HV power supply usage (we can ramp up, sweep phase, ramp down, etc.)
    #     # Turn on power supply
    #     sup.power_supply_output_change("ON", delay=sup.power_supply_output_delay)
    #     print('HV supply ON')

    #     # Ramp up voltage
    #     sup.power_supply_voltage_ramp_up(
    #         sup.VoltageWrite,
    #         sup.voltage_step,
    #         start_value=0,
    #         delay=sup.power_supply_ramp_delay
    #     )
    #     print("Source ramped up OK")

    #     # Sweep phase shift
    #     sup.microcontroller_sweep_phase_shift(sup.PhaseInit, sup.PhaseFinal, sup.PhaseStep)
    #     print("Sweep phase done OK")

    #     # Ramp down
    #     sup.power_supply_voltage_ramp_down(
    #         sup.VoltageWrite,
    #         -sup.voltage_step,
    #         -sup.voltage_step,
    #         delay=sup.power_supply_ramp_delay
    #     )
    #     print("Source ramped down OK")
    # except Exception as e:
    #         errors.append(f"Failed to finish run: {e}")
    # finally:
    #     try:
    #         # Turn off power supply
    #         sup.power_supply_output_change("OFF")
    #         print("HV power supply OFF successfully.")
    #     except Exception as e:
    #         errors.append(f"Failed to turn OFF HV power supply: {e}")


    #     # Return to initial Phase
    #     sup.microcontroller_send_command("PHASE_SHIFT", "LEG2", sup.InitialPhaseShiftPWM)

    #     # Turn off the legs
    #     sup.microcontroller_send_command("LEG", "LEG1", "OFF")
    #     sup.microcontroller_send_command("LEG", "LEG2", "OFF")

    #     # Read data from the DMM buffers
    #     time.sleep(1)
    #     voltage_data = sup.dmm_get_buffer(sup.dmm_for_voltage, wait_meas_complete=False)
    #     time.sleep(1)
    #     current_data = sup.dmm_get_buffer(sup.dmm_for_current, wait_meas_complete=False)


    #     #######################################
    #     # 3) SAVE RESULTS PHASE
    #     #######################################
        
    #     # Save raw data to CSV
    #     sup.export_result_to_csv(str(voltage_data),"Voltage")
    #     sup.export_result_to_csv(str(current_data),"Current")

    #     # Plot data
    #     plt.figure()
    #     plt.title("Voltage Data Points")
    #     plt.plot(voltage_data, marker='o', linestyle='none')
    #     plt.savefig(sup.result_output_path+'/01-Voltage-'+timestamp+'.svg', format='svg', dpi=300)

    #     plt.figure()
    #     plt.title("Current Data Points")
    #     plt.plot(current_data, marker='o', linestyle='none')
    #     plt.savefig(sup.result_output_path+'/02-Current-'+timestamp+'.svg', format='svg', dpi=300)

    #     power_data = [v * i for v, i in zip(voltage_data, current_data)]
    #     plt.figure()
    #     plt.title("Power Data Points")
    #     plt.plot(power_data, marker='o', linestyle='none')
    #     plt.savefig(sup.result_output_path+'/03-Power-'+timestamp+'.svg', format='svg', dpi=300)
        
    #     plt.show(block=False)
        
    #     plt.pause(5)
    #     plt.close()

    #     try:
    #         # Optionally read or save oscilloscope history
    #         # sup.oscilloscope_read_history_and_choose_to_save()

    #         # new function that deals with screenshots, csv data, and measure for each frame
    #         sup.oscilloscope_save_results()
    #     except Exception as e:
    #         errors.append(f"Failed to read and/or save Oscilloscope: {e}")
        

    sup.close_all_devices()





# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    tool = TOOL()
    jsonlist = tool.find_json_files("PhaseShift")
    
    for jsonfile in jsonlist:
        print(jsonfile)
        runner(jsonfile)
        print("Done!\n\n")
        time.sleep(2)
