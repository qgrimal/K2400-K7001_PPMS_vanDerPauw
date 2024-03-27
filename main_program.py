import numpy as np
import threading
import queue
import pyvisa
import MultiPyVu as mpv
import PySimpleGUI as sg
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
from matplotlib.ticker import NullFormatter  # useful for `logit` scale
matplotlib.use('TkAgg')
import matplotlib.pyplot as pp
import time
from datetime import datetime
import pandas as pd
import os
from GUI import GUI
from Instruments import K2400_Instrument,K7001_Instrument,PPMS_Instrument
from Scans import Measurements


## Initialize file
## put all necessary information here 
## current, probes, sample info, etc...
def initialize_saveFile(gui):
    ## First check if the file has the proper extension
    save_path = gui.save_path
    if not save_path.endswith('.txt'):
        gui.savepath = save_path+'.txt'
    
    ### add timestamp
    timestamp = time.time()
    date_time = str(datetime.fromtimestamp(timestamp))
    print('\n\t\t###'+date_time+'\nInitializing savefile...')
    current_used = str(gui.values['-SRC_CURRENT-'])
    probes_used = '\n# 7011 probes used : \n \t# A='+\
                    str(gui.mpx_A)+'\t# B='+\
                    str(gui.mpx_B)+'\t# C='+\
                    str(gui.mpx_C)+'\t# D='+\
                    str(gui.mpx_D)
    comments = gui.values['-COMMENTS-']
    data_cols = 'timestamp(s)  temp(K)  field(Oe)  angle(deg)  Rxx+  Rxx-  Rxx Ryy+  Ryy- Ryy  Rxy+ Rxy- Rxy  Ryx+  Ryx-  Ryx  R_sheet(Ohm)    R_Hall(Ohm)'
    write_string = '#\n\t\t####   ' + date_time + \
            '\n# Current used = ' + current_used + probes_used + \
            '\n# COMMENTS: \n#' + '\n#'.join(comments.split('\n')) + \
            '\n#\n#' + data_cols + '\n'
    append_to_file(save_path,write_string)
    print(' Done')


## write any string to a file
def append_to_file(file_path,str_to_write):
    with open(file_path, "a") as myfile:
        myfile.write(str_to_write+'\n')


### set instrument parameters from GUI 
def set_instr_from_gui(instr_resource,gui):
    try:
        K2400_addr = 'GPIB0::'+str(gui.K2400_GPIB)+'::INSTR'
        K2400_instr = K2400_Instrument(instr_resource,K2400_addr)
        K7001_addr = 'GPIB0::'+str(gui.K7001_GPIB)+'::INSTR'
        K7001_instr = K7001_Instrument(instr_resource,K7001_addr)
        PPMS_IP = gui.PPMS_IP
        PPMS_instr = PPMS_Instrument(PPMS_IP)
        return K2400_instr,K7001_instr,PPMS_instr
    except:
        print('Error in initializing instrument. Check that the instruments are connected or proper addresses are given')


### set measurement parameters from GUI 
def set_mmt(gui,K2400_instr,K7001_instr,PPMS_instr):
    mmt = Measurements(K2400_instr,K7001_instr,PPMS_instr)
    GUI.data = mmt.data    # the dataframe is properly defined in mmt class
    mmt.current = gui.current_val
    mmt.delay = gui.current_delay
    mmt.A = gui.mpx_A
    mmt.B = gui.mpx_B
    mmt.C = gui.mpx_C
    mmt.D = gui.mpx_D
    return mmt
 

### do continuous van der Pauw measurement
def do_vdP_mmt(gui, mmt):
    gui.singleScan_running = True
    vdP_vals = mmt.vanderPauw_singleI()
    mmt.save_to_file(gui.save_path,vdP_vals)
    gui.update_data(vdP_vals)
    gui.singleScan_running = False
    try:
        gui.window['-CONTINUE-'].click()
    except:
        print('Something went wrong trying to do continuous measurement')


############################################################################################

### Initialize
rm = pyvisa.ResourceManager()
use_GUI = GUI()
try:
    K2400,K7001,PPMS = set_instr_from_gui(rm,use_GUI)
    use_mmt = set_mmt(use_GUI,K2400,K7001,PPMS)
except:
    print('*** Could not initiazlize instruments ***')
    print('*** Check GPIB adresses or if multivu server is running ***')

###for testing purpose
### remove when properly implemented
## field and temp control should be from within MultiVu
#PPMS.set_temp(200,40)
#PPMS.set_field(20000,40)

if __name__ == '__main__':
    while True:
        try:
            use_GUI.main()   #running the GUI 
            ret_code = use_GUI.return_code
            print(ret_code,use_GUI.event)

            if ret_code=='RESET':
                use_GUI.data = use_GUI.data.iloc[0:0]

            if ret_code=='I_CHANGED':
                write_str = '\n# Current changed to '+str(use_GUI.values['-SRC_CURRENT-'])
                use_mmt.current = float(use_GUI.current_val)
                append_to_file(use_GUI.save_path,write_str)

            if ret_code=='DELAY_CHANGED':
                write_str = '\n# Delay changed to '+str(use_GUI.values['-SRC_DELAY-'])
                use_mmt.delay = float(use_GUI.current_delay)
                append_to_file(use_GUI.save_path,write_str)

            ## This is obtained from the GUI that tells the loop to end 
            if ret_code is False:
                break

            if use_GUI.mmt_started:
                # use_GUI.window.write_event_value('-CONTINUE-',1)
                if use_GUI.event == '-START-' or not os.path.exists(use_GUI.save_path): #When the measurement is first started or if filename is changed
                    use_GUI.get_savePath()
                    initialize_saveFile(use_GUI)
                    use_mmt.current = float(use_GUI.values['-SRC_CURRENT-'])
                    use_mmt.delay = float(use_GUI.values['-SRC_DELAY-'])

                if not use_GUI.singleScan_running: ## To not cause problems while instruments are measuring 
                    threading.Thread(target=do_vdP_mmt,args=(use_GUI,use_mmt),daemon=True).start()

        except:
            print('A demon just ate a bug; continuing in 3 s ...')
            time.sleep(3)


