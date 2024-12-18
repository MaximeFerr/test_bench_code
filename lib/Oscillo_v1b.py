import time
import pylab as pl 
import struct 
import gc
import os
import pyvisa as visa
from pyvisa import constants
from pyvisa.resources.serial import SerialInstrument
import sys
import time
import math
from datetime import datetime



# Global variables 
# (Modify the following global variables according to the model). 
# --------------------------------------------------------- 
#SDS_RSC = "USB0::0xF4EC::0x1011::SDS2PEEC6R0224::INSTR"

#CHANNEL = "C1" 
HORI_NUM = 10 
tdiv_enum = [200e-12,500e-12, 1e-9, 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,              1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000] 



def ExportResultToCSV(String,Name):
    f = open('csv-'+Name+'.csv','w')
    f.write(String) #Give your csv text here.
    ## Python will convert \n to os.linesep
    f.close()


def PlotValues(data):
    x=data.split(",")
    dataFormatted=[float(i) for i in x]
    plt.plot(dataFormatted)
    plt.ylabel('current')
    #plt.show()


def ConfigTrigger(smu,nbFrames):
    smu.write('TRIG:TYPE  EDGE ') # Edge
    smu.write(':TRIGger:EDGE:SLOPe  RISing') # Rising Edge
    smu.write(':TRIGger:EDGE:HOLDoff  TIME') #HOLDoff with TIME
    smu.write(':TRIGger:EDGE:HLDTime  50E-03') # HOLDoff TIME 50ms
    smu.write(':TRIGger:EDGE:SOURce  C1') #Trigger Source C1
    #smu.write(':TRIGger:EDGE:SOURce  EX') #Trigger Source External
    #smu.write(':TRIGger:EDGE:SOURce  EX5') #Trigger Source External /5
    #smu.write(':TRIGger:EDGE:LEVel  0.00E-01') #Trigger Level 0V
    smu.write(':TRIGger:EDGE:LEVel  2.00E00') #Trigger Level 0V
    smu.write(':ACQuire:SEQuence ON') #Segmented Memory ON
    #smu.write(':ACQuire:SEQuence:COUNt 200') # 200 Sequential Segments
    smu.write(':ACQuire:SEQuence:COUNt '+nbFrames) # 200 Sequential Segments
    smu.write('TRIG:MODE  SINGle') # Single
    
def ConfigDisplay(smu):
    #smu.write(':TIMebase:SCALe  5.00E-06') #Timebase 5us / div
    smu.write(':TIMebase:SCALe  2.00E-06') #Timebase 2us / div


def GETPicture(smu,frame):
    file_name = ".\Picture"+frame+".bmp" #Make sure that the drive specified is available on your computer
    smu.chunk_size = 20*1024*1024 #default value is 20*1024(20k bytes) 
    #smu.write("SCDP")
    smu.write("PRIN? BMP") # BMP
    #smu.write("PRIN? PNG")
    result_str = smu.read_raw()
    f = open(file_name,'wb')
    f.write(result_str)
    f.flush()
    file_name2 = ".\PictureInverted"+frame+".bmp"
    smu.write("PRIN? BMP,INVerted")
    result_str = smu.read_raw()
    f = open(file_name2,'wb')
    f.write(result_str)
    f.flush() 



#smu > instrument
#nbFrames > String, max number of frames
#SaveBitmap > save each frame as bitmap 1 for YES
#SaveDate > export all channels as CSV, 1 for YES
#delay > waiting delay between each frame
def ReadHistory(smu,nbFrames,SaveBitmap,SaveData,delay):
    smu.write(':HISTORy ON')
    smu.write(':HISTORy:INTERval 200.00E-03') #200 ms time interval for playing history
    smu.write(':HISTORy:PLAy FORWards') # PLay automatically all frames
    #Must wait here !!!! otherwise useless
    nbFramesMax=int(nbFrames)
    for frame in range(1,nbFramesMax+1,1):
        frameString=str(frame)
        smu.write(':HISTORy:FRAMe '+frameString)
        time.sleep(delay)
        if (SaveBitmap==1):
            GETPicture(smu,frameString)
        if (SaveData==1):
            SaveDataOscillo(smu,'C1',frameString)
            #pl.figure(1)
            SaveDataOscillo(smu,'C2',frameString)
            #pl.figure(2)
            SaveDataOscillo(smu,'C3',frameString)
            #pl.figure(3)
            SaveDataOscillo(smu,'C4',frameString)
            #pl.figure(4)
            #pl.show()
    



# ========================================================= 
# main_desc:Analyzing waveform parameters from data blocks 
# ========================================================= 
def main_desc(recv): 
    WAVE_ARRAY_1 = recv[0x3c:0x3f + 1]
    wave_array_count = recv[0x74:0x77 + 1] 
    first_point = recv[0x84:0x87 + 1] 
    sp = recv[0x88:0x8b + 1] 
    v_scale = recv[0x9c:0x9f + 1] 
    v_offset = recv[0xa0:0xa3 + 1] 
    interval = recv[0xb0:0xb3 + 1] 
    code_per_div = recv[0xa4:0Xa7 + 1] 
    adc_bit = recv[0xac:0Xad + 1] 
    delay = recv[0xb4:0xbb + 1] 
    tdiv = recv[0x144:0x145 + 1] 
    probe = recv[0x148:0x14b + 1] 
 
    data_bytes = struct.unpack('i', WAVE_ARRAY_1)[0] 
    point_num = struct.unpack('i', wave_array_count)[0] 
    fp = struct.unpack('i', first_point)[0] 
    sp = struct.unpack('i', sp)[0] 
    interval = struct.unpack('f', interval)[0] 
    delay = struct.unpack('d', delay)[0] 
    tdiv_index = struct.unpack('h', tdiv)[0] 
    probe = struct.unpack('f', probe)[0] 
    vdiv = struct.unpack('f', v_scale)[0] * probe 
    offset = struct.unpack('f', v_offset)[0] * probe 
    code = struct.unpack('f', code_per_div)[0] 
    adc_bit = struct.unpack('h', adc_bit)[0] 
    tdiv = tdiv_enum[tdiv_index] 
    return vdiv, offset, interval, delay, tdiv, code, adc_bit 
 
# ========================================================= 
# Main program: 
# ========================================================= 
def SaveDataOscillo(sds,CHANNEL,Name): 
    #_rm = visa.ResourceManager() 
    #sds = _rm.open_resource(smu) 
    sds.timeout = 2000  # default value is 2000(2s) 
    sds.chunk_size = 20 * 1024 * 1024  # default value is 20*1024(20k bytes) 
 
    # Get the channel waveform parameter data blocks and parse them 
    sds.write(":WAVeform:STARt 0")
    sds.write("WAV:SOUR {}".format(CHANNEL)) 
    sds.write("WAV:PREamble?") 
    recv_all = sds.read_raw() 
    recv = recv_all[recv_all.find(b'#') + 11:] 
    print(len(recv)) 
    vdiv, ofst, interval, trdl, tdiv, vcode_per, adc_bit = main_desc(recv) 
    print(vdiv, ofst, interval, trdl, tdiv,vcode_per,adc_bit) 
 
    # Get the waveform points and confirm the number of waveform slice reads 
    points = float(sds.query(":ACQuire:POINts?").strip()) 
    one_piece_num = float(sds.query(":WAVeform:MAXPoint?").strip()) 
    read_times = math.ceil(points / one_piece_num) 
    #Set the number of read points per slice, if the waveform points is greater than the maximumnumber of slice reads 
    if points > one_piece_num: 
        sds.write(":WAVeform:POINt {}".format(one_piece_num)) 
    # Choose the format of the data returned 
    sds.write(":WAVeform:WIDTh BYTE") 
    if adc_bit > 8: 
        sds.write(":WAVeform:WIDTh WORD") 
 
    #Get the waveform data for each slice 
    recv_byte = b'' 
    for i in range(0, read_times): 
        start = i * one_piece_num 
        #Set the starting point of each slice 
        sds.write(":WAVeform:STARt {}".format(start)) 
        #Get the waveform data of each slice 
        sds.write("WAV:DATA?") 
        recv_rtn = sds.read_raw().rstrip() 
        #Splice each waveform data based on data block information 
        block_start = recv_rtn.find(b'#') 
        data_digit = int(recv_rtn[block_start + 1:block_start + 2]) 
        data_start = block_start + 2 + data_digit 
        recv_byte += recv_rtn[data_start:] 
    # Unpack signed byte data. 
    if adc_bit > 8: 
        convert_data = struct.unpack("%dh"%points, recv_byte)
    else: 
        convert_data = struct.unpack("%db"%points, recv_byte) 
    del recv_byte 
    gc.collect() 
    #Calculate the voltage value and time value 
    time_value = [] 
    volt_value = [] 
    for idx in range(0, len(convert_data)): 
        volt_value.append(convert_data[idx] / vcode_per * float(vdiv) - float(ofst)) 
        time_data = - (float(tdiv) * HORI_NUM / 2) + idx * interval + float(trdl) 
        time_value.append(time_data) 
    print(len(volt_value)) 
    #Draw Waveform 
    #pl.figure(figsize=(7, 5)) 
    #pl.plot(time_value, volt_value, markersize=2, label=u"Y-T") 
    #pl.legend() 
    #pl.grid() 
    #pl.show()
    #
    # Save as CSV
    ExportResultToCSV(str(time_value),CHANNEL+'-'+Name+'-timeX')
    ExportResultToCSV(str(volt_value),CHANNEL+'-'+Name+'-valueY')
    print('Channel: '+CHANNEL)
    print('Frame / Name: '+Name)

