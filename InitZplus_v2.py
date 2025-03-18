#! python3

# Author: Nicolas ROUGER
# Revised by Lorenzo Leijnen
# GPL v3.0
# Mar 18th 2025

import pyvisa as visa
import sys
import time

from supervisor_script_v1_2 import runner, find_json_files
from SinglePoint_SPIN_v1_1 import single_point


# Config
tdk_addr = 'ASRL5::INSTR'
delay = 0.1 #delay in seconds (100 ms)


# -----------------------------
# Defenitions
# -----------------------------
def list_instruments(rm: visa.ResourceManager):
    instrument_list = rm.list_resources()

    for instrument in instrument_list:
        print("'{:s}': ".format(instrument), end=' ')
        try:
            device = rm.open_resource(instrument, query_delay=0.5)
            print(type(device), end=' ')
            time.sleep(1)
            print(device.query("*IDN?"), end='\n')
            time.sleep(1)
            device.close()

        except visa.errors.VisaIOError:
            print('INSTRUMENT ERROR\n')
    
    rm.close()

def output_change(smu,State):
    cmd1 = 'OUTPut:STATe '+State
    smu.write(cmd1)
    time.sleep(delay)

def test_tdk(rm: visa.ResourceManager):
    VoltageLimit = 100
    CurrentLimit = 0.3
    VoltageWrite = 5
    timestep = 0.1
    
    TDKLambda = rm.open_resource(tdk_addr, query_delay=0.5)
    TDKLambda.write('INSTrument:NSELect  1')
    '''TDKLambda.baud_rate = 9600 # 300
    TDKLambda.write_termination = ''
    TDKLambda.read_termination = '\r\n'
    TDKLambda.set_visa_attribute(constants.VI_ATTR_ASRL_FLOW_CNTRL, constants.VI_ASRL_FLOW_XON_XOFF)
    TDKLambda.stop_bits = constants.StopBits.one
    TDKLambda.parity = constants.Parity.none
    TDKLambda.data_bits = 8'''
    TDKLambda.write('VOLTage:LEV 0')
    output_change(TDKLambda,'ON')
    time.sleep(2)
    output_change(TDKLambda,'OFF')
    TDKLambda.close()
    rm.close()
    #rm.visalib._registry.clear()


# -----------------------------
# Main
# -----------------------------
def print_help():
    print("InitZplus_v2.py <mode>")
    print("  list: to list instruments")
    print("  tdk: to test connexion to the power supply")
    print("  run: starts test for all json files")
    print("  single: starts test for all json files")

if __name__ == '__main__':
    rm = visa.ResourceManager()

    if len(sys.argv)==2:
        mode=sys.argv[1]
        if mode == 'list':
            print(">> Selected mode: instruments listing")
            list_instruments(rm)
        elif mode == 'tdk':
            print(">> Selected mode: tdk test connexion")
            test_tdk(rm)
        elif mode == "run":
            print(">> Selected mode: run")
            jsonlist = find_json_files("PhaseShift")
            for jsonfile in jsonlist:
                print(jsonfile)
                runner(jsonfile)
                print("Done!\n\n")
                time.sleep(2)
        elif mode == 'single':
            print(">> Selected mode: single point SPIN test")
            rm = visa.ResourceManager()
            print(rm.list_resources())
            single_point(rm)
        else:
            print_help()
    else:
        print_help()
