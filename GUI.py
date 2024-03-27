from matplotlib.ticker import NullFormatter  # useful for `logit` scale
import matplotlib.pyplot as pp
import threading
import queue
import numpy as np
import scipy as sp
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
import PySimpleGUI as sg
import matplotlib
matplotlib.use('TkAgg')
import time
import psutil
import pandas as pd
import random 
import os

''' This is the main GUI class for the van der Pauw measurement program. 
Import this class into whatever running program 
For more information, contact Gaurab Rimal, gaurab.rimal@wmich.edu 
'''


#### Need to implement: 
## For each of the instruments, add a popup window (don't use popup but use a secondary window)
## Best to make a secondary window class for each instrument type and import them here 
## These windows can be used to control instrument parameters 
## Eg: set temperature, field, get other parameters or send GPIB commands 

### TO Do: 
### Instead of input field, make GPIB addresses a dropdown menu based on available instruments 


#This is the main GUI class 
class GUI():
    def __init__(self):
        #self.queue = queue.Queue()    # queue to communicate between gui and threads 
        self.mmt_started = False
        self.singleScan_running = False
        self.return_code = None

        # Instrument and input parameters
        self.K2400_GPIB = 11
        self.K7001_GPIB = 15
        self.PPMS_IP = '127.0.0.1'
        self.current_val = 10e-6
        self.current_delay = 0.5
        self.mpx_A = 4
        self.mpx_B = 7
        self.mpx_C = 5
        self.mpx_D = 6

        ## Initialize data paramters
        self.save_dir = 'C:\\Users\\QDUser\\Desktop\\PPMS User Data\\Rimal\\data\\data_dump'
        #self.save_dir = 'C:\\Users\\gmv3464\\Dropbox\\WMU\\Research\\instrumentation\\transport-mmt_python\\mmt_suite\\GUI'
        self.save_file = 'test.txt'
        #self.save_path = os.path.join(self.save_dir,self.save_file)
        self.data = None


        ## Initialize window, plus other window stuffs 
        self.make_window()
        self.bind_keys()
        self.get_savePath()

        ## plot region and paramters
        self.y1label = r'R$_{sheet}$ ($\Omega$)'
        self.y2label = r'R$_{Hall}$ ($\Omega$)'
        self.canvas_Rs = self.window['-CANVAS1-'].TKCanvas
        self.canvas_Rh = self.window['-CANVAS2-'].TKCanvas
        self.fig1_canvas_agg,self.fig1,self.ax1 = self.initialize_canvas(self.canvas_Rs,self.y1label)    
        self.tbar1 = NavigationToolbar2Tk(self.fig1_canvas_agg, self.canvas_Rs, pack_toolbar=True)
        self.fig2_canvas_agg,self.fig2,self.ax2 = self.initialize_canvas(self.canvas_Rh,self.y2label)    
        self.tbar2 = NavigationToolbar2Tk(self.fig2_canvas_agg, self.canvas_Rh, pack_toolbar=True)


    # get savepath
    def get_savePath(self):
        self.save_dir = self.window['-SAVE_DIR-'].get()
        self.save_file = self.window['-SAVE_FILE-'].get()
        self.save_path = os.path.join(self.save_dir,self.save_file)


    ### main loop. call this from the frontend program to get events
    def main(self):
        self.return_code = None
        self.event, self.values = self.window.read()
        self.get_events()

        if self.event==sg.WIN_CLOSED or self.event=='-EXIT-':
            ### add a popup asking if you really want to exit (in case experiment running) 
            if self.mmt_started:
                if sg.popup_yes_no('Measurement is running. Are you sure you want to exit?')=='No':
                    print('Not exiting')
                    return None
            self.window.close() 
            self.return_code = False

        # Implement all data update codes here
        ## For continuous update, can implement an invisible "update graph" button that is pressed at regular intervals 
        if self.mmt_started:
            # check if a single measurement is currently running
            pass


    ### initialize the matplotlib figure and assign to the respective canvas 
    def initialize_canvas(self,canvas,ylabel):
        figure,axis = pp.subplots(figsize=(4, 3), dpi=100)
        axis.set_xlabel(r'Temperature (K)',fontsize=14)    
        axis.set_ylabel(ylabel,fontsize=14)
        figure.tight_layout()
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        pp.close(figure)
        return figure_canvas_agg,figure,axis

    ### add an update method for updating GPIB
    ## Need to add "GPIB0::xx::INSTR" type string to number
    ## Is easier to feed directly from pyvisa list_resources() to GUI

    ### set xlabel based on measurement type
    def set_xyLabels(self):
        self.ax1.set_xlabel(self.xlabel,fontsize=14)
        self.ax2.set_xlabel(self.xlabel,fontsize=14)
        self.ax1.set_ylabel(self.y1label,fontsize=14)
        self.ax2.set_ylabel(self.y2label,fontsize=14)
        self.fig1.tight_layout()
        self.fig2.tight_layout()
        self.fig1_canvas_agg.draw()
        self.fig2_canvas_agg.draw()


    #clear the graph and the data in buffer 
    def reset_all(self):
        self.data = self.data.iloc[0:0]
        self.ax1.cla()
        self.ax2.cla()
        self.set_xyLabels()
        self.update_figure()
        self.return_code = 'RESET'


    ## use this to update the figure
    def update_figure(self):
        self.ax1.plot(self.data[self.scantype],self.data['Rs'],'ro-')  
        self.ax2.plot(self.data[self.scantype],self.data['Rh'],'bs-')  
        self.set_xyLabels()
        
        
    ### save the R_s and R_H plots
    def save_plots(self): 
        ### Need to find a way to combine the two plots into one
        timestamp = str(time.time())
        save_fn_Rs = self.save_path+'_Rs_'+timestamp+'.png'
        save_fn_Rh = self.save_path+'_Rh_'+timestamp+'.png'
        print('Saving plots ...')
        self.fig1.savefig(save_fn_Rs,bbox_inches='tight')
        self.fig2.savefig(save_fn_Rh,bbox_inches='tight')
       # pp.close(fig=fig)


    ### This creates raw data plot windows
    def raw_data_plots(self):
        self.fig3a,ax3aa = pp.subplots()
        ax3ab = ax3aa.twinx()
        ax3aa.set_xlabel(self.xlabel,fontsize=14)
        ax3aa.set_ylabel(r'R$_{xx}$ ($\Omega$)',fontsize=18,color='red')
        ax3ab.set_ylabel(r'R$_{yy}$ ($\Omega$)',fontsize=18,color='blue')

        self.fig3b,ax3ba = pp.subplots()
        ax3bb = ax3ba.twinx()
        ax3ba.set_xlabel(self.xlabel,fontsize=14)
        ax3ba.set_ylabel(r'R$_{xy}$ ($\Omega$)',fontsize=18,color='red') 
        ax3bb.set_ylabel(r'R$_{yx}$ ($\Omega$)',fontsize=18,color='blue')

        #print(self.scantype)
        ax3aa.plot(self.data[self.scantype],self.data['Rxx'],'ro-')
        ax3ab.plot(self.data[self.scantype],self.data['Ryy'],'b^-')
        ax3ba.plot(self.data[self.scantype],self.data['Rxy'],'ro-')
        ax3bb.plot(self.data[self.scantype],self.data['Ryx'],'b^-')

        self.fig3a.tight_layout()
        self.fig3b.tight_layout()
        
        pp.show(block=False)


    ### update the indicators with new values. Get a row of data 
    def update_data(self,new_data):
        self.data = pd.concat([self.data,new_data])
        try:
            self.window['-PPMS_TEMP-'].update('{:.1f}'.format(self.data.iloc[-1]['temp']))
            self.window['-PPMS_FIELD-'].update('{:.2e}'.format(self.data.iloc[-1]['field']))
            self.window['-PPMS_ANGLE-'].update('{:.1f}'.format(self.data.iloc[-1]['angle']))
            self.window['-VXX_PLUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Rxx+']))
            self.window['-VXX_MINUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Rxx-']))
            self.window['-RYY_PLUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Ryy+']))
            self.window['-RYY_MINUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Ryy-']))
            self.window['-VXY_PLUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Rxy+']))
            self.window['-VXY_MINUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Rxy-']))
            self.window['-RYX_PLUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Ryx+']))
            self.window['-RYX_MINUS-'].update('{:.2e}'.format(self.data.iloc[-1]['Ryx-']))
            self.window['-R_SHEET-'].update('{:.2e}'.format(self.data.iloc[-1]['Rs']))
            self.window['-R_HALL-'].update('{:.2e}'.format(self.data.iloc[-1]['Rh']))
            self.update_figure()
        except:
            print('GUI.update_data:: cannot update data')


    ## This is to draw the window layout 
    def make_window(self):
            self.instr_params = [[sg.Text('Instrument address ',background_color='grey'),\
                             sg.Text('  K2400 GPIB'), sg.In(self.K2400_GPIB,key='-K2400_GPIB-',size=(3,1),enable_events=False),\
                             sg.Text('  K7001 GPIB'), sg.In(self.K7001_GPIB,key='-K7001_GPIB-',size=(3,1),enable_events=False),\
                             sg.Text('  PPMS server'), sg.In(self.PPMS_IP,key='-K2400_GPIB-',size=(10,1),enable_events=False),]]

            self.mmt_type = [sg.Text('Measurement Type',background_color='grey'),\
                        sg.Radio('R vs T   ','mmt_type',key='-RvsT-',default='True',enable_events=True),\
                        sg.Radio('R vs H   ','mmt_type',key='-RvsH-',enable_events=True),\
                        sg.Radio('R vs theta  ','mmt_type',key='-RvsTheta-',enable_events=True,disabled=True),\
                        ]

            self.src_params = [[sg.Text('Source Parameters',background_color='grey'),\
                           sg.Text('current (A) ='), 
                           sg.Input('10e-6',key='-SRC_CURRENT-',size=(6,10),tooltip='Hit enter to submit',enable_events=False),\
                           sg.Button('Update', visible=False,key='-SUBMIT_CURRENT-',bind_return_key=True),\
                           sg.Text('     delay (s) ='), 
                           sg.Input('0.5',key='-SRC_DELAY-',size=(5,10),tooltip='Hit enter to submit',enable_events=False),
                           sg.Button('Update', visible=False,key='-SUBMIT_DELAY-',bind_return_key=True),]]

            self.dir_params = [[sg.Text('Save Dir ',background_color='grey'),\
                           sg.Multiline(self.save_dir,key='-SAVE_DIR-',size=(54,2),enable_events=True),\
                           sg.FolderBrowse(key='-SAVE_DIR_NAME-')]]

            self.file_params = [[sg.Text('Save File',background_color='grey'),\
                           sg.Input(self.save_file,key='-SAVE_FILE-',size=(55,20),enable_events=False,tooltip='Hit enter or "Update" to submit'),
                           sg.Button('Update ', visible=True,key='-SUBMIT_FILENAME-',bind_return_key=True)]]

            self.comment_box = [[sg.Text('Comments: ',background_color='grey'),\
                           sg.Multiline('',key='-COMMENTS-',size=(44,3),enable_events=False,\
                           tooltip='Enter any experimental or sample comments here'),]]


            self.K7001_contacts = [sg.Text('Switching Contacts',background_color='grey'),\
                           sg.Button('Update', visible=False,key='-SUBMIT_MPX-',bind_return_key=True),\
                           sg.Text('   A'), sg.In('4',key='-MPX_A-',size=(2,1)),\
                           sg.Text('   B'), sg.In('7',key='-MPX_B-',size=(2,1)),\
                           sg.Text('   C'), sg.In('5',key='-MPX_C-',size=(2,1)),\
                           sg.Text('   D'), sg.In('6',key='-MPX_D-',size=(2,1))]

### Need to force the display to show only a certain length, and format as exponential number as necessary
            self.PPMS_params = [sg.Text('PPMS ',background_color='grey'),
                           sg.Text('   T (K) ='), sg.Text('      ',key='-PPMS_TEMP-',background_color='silver',size=(6,1),enable_events=True),\
                           sg.Text('   H (Oe) ='), sg.Text('      ',key='-PPMS_FIELD-',background_color='silver',size=(7,1),enable_events=True),\
                           sg.Text('   Angle (deg) ='), sg.Text('      ',key='-PPMS_ANGLE-',background_color='silver',size=(6,1),enable_events=True)]

            self.measure_params_long = [sg.Text('Measure ',background_color='grey'),\
                           sg.Text('Rxx(+) ='), sg.Text('      ',key='-VXX_PLUS-',background_color='silver',size=(8,1),enable_events=True),\
                           sg.Text('Rxx(-) ='), sg.Text('      ',key='-VXX_MINUS-',background_color='silver',size=(8,1),enable_events=True),\
                           sg.Text('Ryy(+) ='), sg.Text('      ',key='-RYY_PLUS-',background_color='silver',size=(8,1),enable_events=True),\
                           sg.Text('Ryy(-) ='), sg.Text('      ',key='-RYY_MINUS-',background_color='silver',size=(8,1),enable_events=True),]
                             
            self.measure_params_trans = [sg.Text('                '),
                           sg.Text('Rxy(+) ='), sg.Text('      ',key='-VXY_PLUS-',background_color='silver',size=(8,1),enable_events=True),\
                           sg.Text('Rxy(-) ='), sg.Text('      ',key='-VXY_MINUS-',background_color='silver',size=(8,1),enable_events=True),\
                           sg.Text('Ryx(+) ='), sg.Text('      ',key='-RYX_PLUS-',background_color='silver',size=(8,1),enable_events=True),
                           sg.Text('Ryx(-) ='), sg.Text('      ',key='-RYX_MINUS-',background_color='silver',size=(8,1),enable_events=True),]

            self.resistance_vals = [sg.Text('Resistance ',background_color='grey'),\
                           sg.Text('   R_sheet ='), sg.Text('      ',key='-R_SHEET-',background_color='silver',size=(10,1),enable_events = True),
                           sg.Text('   R_Hall ='), sg.Text('      ',key='-R_HALL-',background_color='silver',size=(10,1),enable_events = True),]

            self.plot_canvas = [sg.Canvas(key='-CANVAS1-'),sg.Canvas(key='-CANVAS2-')]

            self.control_buttons = [sg.Button('Start', size=(10, 2), key='-START-'),\
                                  sg.Button('Stop', size=(10, 2),key='-STOP-'),\
                                  sg.Button('Continue', size=(10, 2),visible=False,enable_events=True,key='-CONTINUE-'),\
                                  sg.Button('Reset', size=(10, 2),key='-RESET-'),\
                                  sg.Button('Show raw data', size=(12, 2),key='-SHOW-RAW-'),\
                                  sg.Button('Save plots', size=(12, 2),key='-SAVE-PLOTS-'),\
                                  sg.Button('Exit', size=(10, 2),key='-EXIT-'), ]

            self.layout = [[self.instr_params,[sg.Text('')],\
                       self.mmt_type,\
                       self.src_params,\
                       self.K7001_contacts,
                       self.dir_params,\
                       self.file_params,\
                       self.comment_box,[sg.Text('')],\
                       self.PPMS_params,\
                       self.measure_params_long,\
                       self.measure_params_trans,\
                       self.resistance_vals,[sg.Text('')],\
                       self.plot_canvas],[sg.Text('')],\
                       self.control_buttons,\
                      ]

            self.window = sg.Window('van der Pauw transport using Keithley 2400 and Keithley 7001', self.layout,\
                                    finalize=True, element_justification='left', font='Helvetica 14',\
                                    return_keyboard_events=True, resizable=True,) #size=(800, 900) <- another option in case you need a definite window size

    def bind_keys(self):
        self.window['-SAVE_FILE-'].bind("<Return>", "_ENTER")
        self.window['-SRC_CURRENT-'].bind("<Return>", "_ENTER")
        self.window['-SRC_DELAY-'].bind("<Return>", "_ENTER")
        self.window['-MPX_A-'].bind("<Return>", "_ENTER")
        self.window['-MPX_B-'].bind("<Return>", "_ENTER")
        self.window['-MPX_C-'].bind("<Return>", "_ENTER")
        self.window['-MPX_D-'].bind("<Return>", "_ENTER")

                    
    def get_events(self):
       # try:
       #     print(self.event)
       # except:
       #     print()

        if self.window['-RvsT-'].get():
            #print(self.window['-RvsT-'].get())
            self.xlabel = r'Temperature (K)'
            self.scantype = 'temp'
        elif self.window['-RvsH-'].get():
            #print(self.window['-RvsH-'].get())
            self.xlabel = r'Field (T)'
            self.scantype = 'field'
        elif self.window['-RvsTheta-'].get():
            #print(self.window['-RvsTheta-'].get())
            self.xlabel = r'Angle (deg)'
            self.scantype = 'angle'
        self.set_xyLabels()

        if self.event == '-START-':
            print('Measurement started') 
            self.window.refresh()
            self.mmt_started = True
            self.singleScan_running = False
           # self.window['-START-'].update(disabled=True,)
            #self.save_file = self.window['-SAVE_FILE-'].get()
            
        
        if self.event == '-STOP-':
            ### make this stop only the main data collection program 
            self.mmt_started = False
            self.continue_scan = False
            self.window['-START-'].update(disabled=False,)
            #pp.show()

        ###continue running scan 
        if self.event == '-CONTINUE-':
            if self.mmt_started:
                self.continue_scan = True
            self.return_code = None

        if self.event == '-RESET-':
            try:
                self.reset_all()
            except:
                print('Something went wrong while resetting')

        ## Show raw data
        if self.event == '-SHOW-RAW-':   #can also use right click menu to do this
            self.raw_data_plots()
            
        ## Save plots shown in the canvas 
        if self.event == '-SAVE-PLOTS-':   #can also use right click menu to do this
            self.save_plots()

        ### directory name
        if self.event in ('-SAVE_DIR_NAME-','-SAVE_DIR-'):
            self.save_dir = self.window['-SAVE_DIR-'].get()

        ### file name
        if self.event in ('-SUBMIT_FILENAME-','-SAVE_FILE-_ENTER'):
            if self.mmt_started:
                #add a popup asking if you want to change during a measurement
                if sg.popup_yes_no('Measurement is running. Are you sure you want to change the filename?')=='No':
                    return None
            self.save_file = self.window['-SAVE_FILE-'].get()
            self.save_path = os.path.join(self.save_dir,self.save_file)

        ### Current value
        if self.event in ('-SUBMIT_CURRENT-','-SRC_CURRENT-_ENTER'):
            self.current_val = self.window['-SRC_CURRENT-'].get()
            print('Source current changed to ',self.current_val)
            self.return_code = 'I_CHANGED'

        if self.event in ('-SUBMIT_DELAY-','-SRC_DELAY-_ENTER'):
            self.current_delay = self.window['-SRC_DELAY-'].get()
            print('Source delay changed to ',self.current_delay)
            self.return_code = 'DELAY_CHANGED'

        if self.event in ('-SUBMIT_MPX-','-MPX_A-_ENTER','-MPX_B-_ENTER','-MPX_C-_ENTER','-MPX_D-_ENTER'):
            self.mpx_A = self.window['-MPX_A-'].get()
            self.mpx_B = self.window['-MPX_B-'].get()
            self.mpx_C = self.window['-MPX_C-'].get()
            self.mpx_D = self.window['-MPX_D-'].get()
            print('Multiplexer values changed ')
            self.return_code = 'MPX_CHANGED'
