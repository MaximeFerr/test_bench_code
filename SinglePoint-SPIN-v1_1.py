# Open Power Tuesday - v1_1
# Jan  2025
# Author: Nicolas ROUGER, Luiz VILLA, Joseph KEMDENG, Pauline KERGUS, Matthieu MASSON, Lorenzo LEIJNEN
#
# Joint effort: LAPLACE + LAAS + Owntech -- thanks to all other contributors!
#
# Edit, cleaning and added functions compared to v1
# License: GPL 3.0
#

# -------------------------------------------------
#
# REQUIREMENTS:
# SPIN must be loaded with v1.0.0-rc-power_tuesday branch
# The python files with key functions for SPIN must be copied in the "comm_protocol" folder
#   > The folder is located in the cloned GIT repo. at owntech\lib\USB\comm_protocol
# The DMMs used are SDM3065 from Siglent
# The power supply used is Z650+ from TDK Lambda
# The oscilloscope is SDS2000X+ or SDS2000X HD from Siglent
# -------------------------------------------------

import serial
import os
import sys

import serial.serialutil
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, parent_dir)


from comm_protocol.src import find_devices
from comm_protocol.src.Shield_Class import Shield_Device

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import xmlrpc.client as xml
import time
import matplotlib.pyplot as plt
import numpy as np
from typing import cast, Any

import os
from matplotlib import pyplot as plt
import pyvisa as visa
from pyvisa import constants
from pyvisa.resources.serial import SerialInstrument

import math

import pylab as pl 
import struct 
import gc

from datetime import datetime

import lib.Oscillo_v1b as controloscillo

# -------------------------------------------------
# PART 1: Parameters for COM and SWEEP
# -------------------------------------------------

# PWM parameters
DutyPWM = 0.485 # 48.5%   1 <> 100% duty. Must consider the deadtime and freq values for dead time compensation!
frequencyPWM = 100e3 #100 kHz switching frequency
DeadTimePWM = 300 #ns, deadtime
InitialPhaseShiftPWM = 75 #0 or 15° initial & final phase shift between Leg1 and Leg2
DeltaDutyInit = 0. # can be 0.01 for example


# CREATE ONLY A SINGLE RESOURCE MANAGER INSTANCE
rm = visa.ResourceManager()



# -------------------------------------------------
# PART 8: MAIN function
# -------------------------------------------------

def main():
    leg_to_test = "LEG1"                               #leg to be tested in this script
    reference_names = ["V1","V2","VH","I1","I2","IH"]  #names of the sensors of the board

    shield_vid = 0x2fe3
    shield_pid = 0x0101

    Shield_ports = find_devices.find_shield_device_ports(shield_vid, shield_pid)
    print(Shield_ports)

    Shield = Shield_Device(shield_port=Shield_ports[0], shield_type='TWIST')

    try:

      # ---------------HARDWARE IN THE LOOP PV EMULATOR CODE ------------------------------------
    ##  message1 = Shield.sendCommand("IDLE")
    ##  print(message1)
    ##
    ##  message = Shield.sendCommand( "BUCK", "LEG1", "OFF")
    ##  print(message)
    ##
    ##  message = Shield.sendCommand( "BUCK", "LEG2", "OFF")
    ##  print(message)

        message = Shield.sendCommand("LEG","LEG1","ON")
        print(message)

        message = Shield.sendCommand("LEG","LEG2","ON")
        print(message)

        message = Shield.sendCommand("POWER_ON")
        print(message)

        message = Shield.sendCommand("DUTY","LEG1",DutyPWM) # Initial duty cycle is 48.5%, to compensate dead time
        print(message)

        message = Shield.sendCommand("DUTY","LEG2",DutyPWM+DeltaDutyInit) # Initial duty cycle is 48.5%, to compensate dead time
        print(message)

        message1 = Shield.sendCommand("FREQUENCY", "LEG1", frequencyPWM) # 100 kHz switching freq


        message = Shield.sendCommand("DEAD_TIME_RISING","LEG2",DeadTimePWM) # 300 ns deadtime
        message = Shield.sendCommand("DEAD_TIME_RISING","LEG1",DeadTimePWM) # 300 ns deadtime
        print(message)

        message = Shield.sendCommand("DEAD_TIME_FALLING","LEG2",DeadTimePWM) # 300 ns deadtime
        message = Shield.sendCommand("DEAD_TIME_FALLING","LEG1",DeadTimePWM) # 300 ns deadtime
        print(message)


        message1 = Shield.sendCommand("PHASE_SHIFT","LEG2",InitialPhaseShiftPWM) # Initial phase shift is 15°
        print(message1)


        # Return to init Phase
        #message1 = Shield.sendCommand("PHASE_SHIFT", "LEG2", 10)
        #print(message1)

        #Turn OFF PWM signals
        #message = Shield.sendCommand( "LEG", "LEG1", "OFF")
        #print(message)
        ##
        #message = Shield.sendCommand( "LEG", "LEG2", "OFF")
        #print(message)

    finally:
        rm.close()
        print('Job Done!')


if __name__ == "__main__":

    print(rm.list_resources())
    
    main()
    # list_instruments()

