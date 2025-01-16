###############################################
# test_script.py
#
# Example code demonstrating how to use the
# updated Supervisor class for a test bench.
###############################################

import time
import matplotlib.pyplot as plt

# Import the updated Supervisor class
from Supervisor_v2 import Supervisor

#######################################
# 1) INITIALIZATION PHASE
#######################################
def main():
    # Create Supervisor instance (loads config from parameters.json)
    sup = Supervisor(config_path="parameters.json")

    # Open all devices: HV power supply, DMMs, oscilloscope, microcontroller
    # sup.open_all_devices()  #This opens all the devices. To be tested.
    # sup.list_instruments()  #This lists the instruments.
    sup.open_dmm_for_current()
    sup.open_dmm_for_voltage()
    sup.open_hv_power_supply()
    sup.open_microcontroller()
    sup.open_oscilloscope()

    try:
        #######################################
        # 2) TEST PHASE
        #######################################

        # Example microcontroller setup
        # Turn on legs, set Duty, Frequency, Dead Time, etc.
        # Instead of using Shield, we now call sup.microcontroller_send_command(...)
        sup.microcontroller_send_command("LEG", "LEG1", "ON")
        sup.microcontroller_send_command("LEG", "LEG2", "ON")
        sup.microcontroller_send_command("POWER_ON")

        # We assume the JSON config defines sup.DutyPWM, sup.frequencyPWM, sup.DeadTimePWM, etc.
        sup.microcontroller_send_command("DUTY", "LEG1", sup.DutyPWM)
        sup.microcontroller_send_command("DUTY", "LEG2", sup.DutyPWM)

        sup.microcontroller_send_command("FREQUENCY", "LEG1", sup.frequencyPWM)
        sup.microcontroller_send_command("DEAD_TIME_RISING", "LEG2", sup.DeadTimePWM)
        sup.microcontroller_send_command("DEAD_TIME_RISING", "LEG1", sup.DeadTimePWM)
        sup.microcontroller_send_command("DEAD_TIME_FALLING", "LEG2", sup.DeadTimePWM)
        sup.microcontroller_send_command("DEAD_TIME_FALLING", "LEG1", sup.DeadTimePWM)

        sup.microcontroller_send_command("PHASE_SHIFT", "LEG2", sup.InitialPhaseShiftPWM)

        # Configure and initialize DMMs (already opened in sup.dmm_for_current, sup.dmm_for_voltage)
        # For example, we can send SCPI commands to set them up
        dmm_current = sup.dmm_for_current
        dmm_voltage = sup.dmm_for_voltage

        sup.dmm_send_cmd(dmm_current, [
            "*RST",
            "CONF:CURR:DC AUTO",
            "TRIG:SOUR EXT",
            "TRIG:COUN 1",
            "SAMP:COUN 1",
            "CURR:DC:NPLC 1",
            "INITiate"
        ], delay=0.1)
        sup.dmm_send_cmd(dmm_voltage, [
            "*RST",
            "CONF:VOLT:DC AUTO",
            "TRIG:SOUR EXT",
            "TRIG:COUN 1",
            "SAMP:COUN 1",
            "VOLT:DC:NPLC 1",
            "INITiate"
        ], delay=0.1)

        # Initialize and configure the oscilloscope
        sup.oscilloscope_init()

        # Example: HV power supply usage (we can ramp up, sweep phase, ramp down, etc.)
        # Turn on power supply
        sup.power_supply_output_change("ON")

        # Ramp up voltage
        sup.power_supply_voltage_ramp_up(sup.VoltageWrite, sup.voltage_step, start_value=0)
        print("Source ramped up OK")

        # Sweep phase shift
        sup.microcontroller_sweep_phase_shift(sup.PhaseInit, sup.PhaseFinal, sup.PhaseStep)
        print("Sweep phase done OK")

        # Ramp down
        sup.power_supply_voltage_ramp_down(sup.VoltageWrite, -sup.voltage_step)
        print("Source ramped down OK")

        # Turn off power supply
        sup.power_supply_output_change("OFF")

        # Return to initial Phase
        sup.microcontroller_send_command("PHASE_SHIFT", "LEG2", sup.InitialPhaseShiftPWM)

        # Turn off the legs
        sup.microcontroller_send_command("LEG", "LEG1", "OFF")
        sup.microcontroller_send_command("LEG", "LEG2", "OFF")

        # Read data from the DMM buffers
        voltage_data = sup.dmm_get_buffer(dmm_voltage, wait_meas_complete=False)
        current_data = sup.dmm_get_buffer(dmm_current, wait_meas_complete=False)

        #######################################
        # 3) SAVE RESULTS PHASE
        #######################################

        # Save raw data to CSV
        sup.export_result_to_csv(str(voltage_data),"Voltage")
        sup.export_result_to_csv(str(current_data),"Current")

        # Optionally read or save oscilloscope history
        sup.oscilloscope_read_history_and_choose_to_save()

        # Plot data
        plt.figure(1)
        plt.title("Voltage Data Points")
        plt.plot(voltage_data, marker='o', linestyle='none')

        plt.figure(2)
        plt.title("Current Data Points")
        plt.plot(current_data, marker='o', linestyle='none')

        power_data = [v * i for v, i in zip(voltage_data, current_data)]
        plt.figure(3)
        plt.title("Power Data Points")
        plt.plot(power_data, marker='o', linestyle='none')

        plt.show()

    finally:

        errors = []

        # Attempt to close HV power supply
        try:
            sup.close_hv_power_supply()
            print("HV power supply closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close HV power supply: {e}")

        # Attempt to close DMM for current
        try:
            sup.close_dmm_for_current()
            print("DMM for current closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close DMM for current: {e}")

        # Attempt to close DMM for voltage
        try:
            sup.close_dmm_for_voltage()
            print("DMM for voltage closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close DMM for voltage: {e}")

        # Attempt to close oscilloscope
        try:
            sup.close_oscilloscope()
            print("Oscilloscope closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close oscilloscope: {e}")

        # Attempt to close microcontroller
        try:
            sup.close_microcontroller()
            print("Microcontroller closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close microcontroller: {e}")

        # If any errors were collected, raise them as a combined RuntimeError
        if errors:
            raise RuntimeError(
                "One or more devices failed to close:\n" + "\n".join(errors)
            )
        else:
            print("All devices closed successfully. Test complete!")


if __name__ == "__main__":
    main()
