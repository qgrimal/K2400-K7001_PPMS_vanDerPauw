import scipy as sp
import matplotlib.pyplot as pp
import pyvisa
import MultiPyVu as mpv
import time
import pandas as pd
from scipy.optimize import curve_fit
from Instruments import K2400_Instrument,K7001_Instrument,PPMS_Instrument
from Scans import Measurements


#### Test out a simple run 
### First make sure that PPMS server is running
### If not running, you can invoke the server by using: 
### python -m MultiPyVu  or python -m MultiPyVu -s dynacool to simulate the instrument

# Note::: 
### For sourcing current, the precision of source depends on the current range selected. For best results, select the appropriate range (Eg: you get bad results if you have uA current but select range of 1 A)


### initialize instrument and resources here
rm = pyvisa.ResourceManager()
rm.list_resources()
K2400_adr = 'GPIB0::11::INSTR'
K2400 = K2400_Instrument(rm,K2400_adr)
K7001_adr = 'GPIB0::15::INSTR'
K7001 = K7001_Instrument(rm,K7001_adr)
PPMS = PPMS_Instrument('127.0.0.1')

test_mmt = Measurements(K2400,K7001,PPMS)
#print(test_mmt.data)
test_mmt.current = 20e-6
test_mmt.delay = 0.5
test_mmt.A = 4
test_mmt.B = 7
test_mmt.C = 5
test_mmt.D = 6


### Test out a quick R-T or M-H measurement 
print('\n\n #################### Data follows #####################') 
PPMS.set_temp(200,5)
PPMS.set_field(2000,50)
time.sleep(1)
for i in range(2):
    #PPMS.get_temp()
   # PPMS.get_field()
   # current_temp = PPMS.temp
   # current_field = PPMS.field
    vdP_mmt = test_mmt.vanderPauw_singleI()
    #test_mmt.add_to_data(vdP_mmt)
    #print(current_temp,current_field, vdP_mmt['Rs'],vdP_mmt['Rh'])
    #print(test_mmt.data.shape)

#print(test_mmt.data)
#rm.close()

