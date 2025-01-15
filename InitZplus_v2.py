# Author: Nicolas ROUGER
# GPL v3.0
# Jan 14th 2025

#! python3

import os
import pyvisa as visa
from pyvisa import constants
from pyvisa.resources.serial import SerialInstrument
import sys
import time
import math
from datetime import datetime

rm = visa.ResourceManager()

delay = 0.1 #delay in seconds (100 ms)


def list_instruments():
    
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
    #rm.close()

def OutputChange(smu,State):
    cmd1 = 'OUTPut:STATe '+State
    smu.write(cmd1)
    time.sleep(delay)

def main(args):
    print(args)
    VoltageLimit = 100
    CurrentLimit = 0.3
    VoltageWrite = 5
    timestep = 0.1
    #rm = visa.ResourceManager()
    #TDK Lambda #1 in USB
    TDKLambda = rm.open_resource('ASRL27::INSTR', query_delay=0.5)
    TDKLambda.write('INSTrument:NSELect  1')
    '''TDKLambda.baud_rate = 9600 # 300
    TDKLambda.write_termination = ''
    TDKLambda.read_termination = '\r\n'
    TDKLambda.set_visa_attribute(constants.VI_ATTR_ASRL_FLOW_CNTRL, constants.VI_ASRL_FLOW_XON_XOFF)
    TDKLambda.stop_bits = constants.StopBits.one
    TDKLambda.parity = constants.Parity.none
    TDKLambda.data_bits = 8'''
    TDKLambda.write('VOLTage:LEV 0')
    OutputChange(TDKLambda,'ON')
    time.sleep(2)
    OutputChange(TDKLambda,'OFF')
    TDKLambda.close()
    rm.close()
    time.sleep(delay)

    
    #rm.visalib._registry.clear()

    

if __name__ == '__main__':
    # main(sys.argv)
    #list_instruments()
    main(sys.argv)

