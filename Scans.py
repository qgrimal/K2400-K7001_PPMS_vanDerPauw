import scipy as sp
import matplotlib.pyplot as pp
import pyvisa
import MultiPyVu as mpv
import time
import pandas as pd
from scipy.optimize import curve_fit
from Instruments import K2400_Instrument,K7001_Instrument,PPMS_Instrument

''' It is probably better to make this file into a full data collection program. Implement data saving here. '''


### This is for all experimental settings and data collection
class Measurements():
    def __init__(self,K2400_instr,K7001_instr,PPMS_instr):
        self.K2400 = K2400_instr
        self.K7001 = K7001_instr
        self.PPMS = PPMS_instr

        self.current = 10e-6   #source current
        self.delay = 0.2   #source delay
        self.A = 4          # K7001 A probe
        self.B = 7          # K7001 B probe
        self.C = 5          # K7001 C probe
        self.D = 6          # K7001 D probe

        self.save_file = ''
        self.data = pd.DataFrame(columns=['timestamp','temp','field','angle',\
                                           'Rxx+','Rxx-','Rxx',\
                                           'Ryy+','Ryy-','Ryy',\
                                           'Rxy+','Rxy-','Rxy',\
                                           'Ryx+','Ryx-','Ryx',\
                                           'Rs','Rh'])


    ## add single reading from vanderPauw_singleI() to self.data
    def add_to_data(self,reading):
        self.data = pd.concat([self.data,reading],ignore_index=True)


    #get measurement parameters
    def get_mmt_params(self):
        pass


    ##save the single data point to datafile
    ## datafile should have the full path
    ## data is a single row dataframe
    def save_to_file(self,datafile,data):
        data.to_csv(datafile, mode='a', header=False,sep='\t',index=False)
      #  with open(datafile, "a") as file:
      #      file.write(new_data)


    ## Using single shot current and current reversal 
    ### Check the picture in the markdown to identify all the proper channels 
    ### delay is in seconds 
    def vanderPauw_singleI(self):
        I_val = self.current
        delay = self.delay
        A = self.A
        B = self.B
        C = self.C
        D = self.D

        # Rxx 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Rxx_channels = self.K7001.close_channels(A,B,C,D)   ### Close appropriate channels to do Rxx measurement 
        Rxx_plus = self.K2400.measure_single(I_val,delay)['R']        # Note the return value is a dictionary with {V,I,R} values
        Rxx_minus = self.K2400.measure_single(-I_val,delay)['R']      # Note the return value is a dictionary with {V,I,R} values
        Rxx = (Rxx_plus+Rxx_minus)/2.             # Maybe do this for both V and R (?)
        
        # Ryy 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Ryy_channels = self.K7001.close_channels(A,C,B,D)   ### Close appropriate channels to do Ryy measurement 
        Ryy_plus = self.K2400.measure_single(I_val,delay)['R']        # Note the return value is a dictionary with {V,I,R} values
        Ryy_minus = self.K2400.measure_single(-I_val,delay)['R']      # Note the return value is a dictionary with {V,I,R} values
        Ryy = (Ryy_plus+Ryy_minus)/2.             # Maybe do this for both V and R (?)

        # Rxy 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Rxy_channels = self.K7001.close_channels(A,D,B,C)   ### Close appropriate channels to do Rxy measurement 
        Rxy_plus = self.K2400.measure_single(I_val,delay)['R']        # Note the return value is a dictionary with {V,I,R} values
        Rxy_minus = self.K2400.measure_single(-I_val,delay)['R']      # Note the return value is a dictionary with {V,I,R} values
        Rxy = (Rxy_plus+Rxy_minus)/2.             # Maybe do this for both V and R (?)
        
        # Ryx 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Ryx_channels = self.K7001.close_channels(B,C,D,A)   ### Close appropriate channels to do Ryx measurement 
        Ryx_plus = self.K2400.measure_single(I_val,delay)['R']        # Note the return value is a dictionary with {V,I,R} values
        Ryx_minus = self.K2400.measure_single(-I_val,delay)['R']      # Note the return value is a dictionary with {V,I,R} values
        Ryx = (Ryx_plus+Ryx_minus)/2.             # Maybe do this for both V and R (?)

        ## Get the relevant parameters
        Rs = (Rxx+Ryy)/2.       # The sheet resistance
        Rh = (Rxy+Ryx)/2.       # The Hall resistance
        #print('\t Rs = ',Rs,'Rh = ',Rh)
        
        self.K7001.open_all()                               ### Open all channels to ensure no switches are closed 

        ## get vals 
        timestamp = time.time()
        temp = self.PPMS.get_temp()
        field = self.PPMS.get_field()
        angle = self.PPMS.get_angle()
        #print(temp,field,angle,Rxx,Ryy,Rxy,Ryx,Rs,Rh)
        
        new_data =  pd.DataFrame([{'timestamp':timestamp,\
                                'temp':temp,'field':field,'angle':angle,\
                                'Rxx+':Rxx_plus,'Rxx-':Rxx_minus,'Rxx':Rxx,\
                                'Ryy+':Ryy_plus,'Ryy-':Ryy_minus,'Ryy':Ryy,\
                                'Rxy+':Rxy_plus,'Rxy-':Rxy_minus,'Rxy':Rxy,\
                                'Ryx+':Ryx_plus,'Ryx-':Ryx_minus,'Ryx':Ryx,\
                                'Rs':Rs,'Rh':Rh}])
#        print('new data\t',new_data.shape)
        self.add_to_data(new_data)
        return new_data
        

    ## Using IV
    ### >>>>>>>>>>>>>>>>>>>>>>>>>  Not complete  <<<<<<<<<<<<<<<<<
    ## This does not make sense for vdP measurement - but best to test on a sample and see how it behaves
    def vanderPauw_IV(self,I_start,I_end,I_stepSize,A,B,C,D,delay=0.5):
        # Rxx 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Rxx_channels = self.K7001.close_channels(A,B,C,D)   ### Close appropriate channels to do Rxx measurement 
        Rxx_IV_data = self.K2400.measure_IV(I_start,I_end,I_stepSize)        # Note the return value is a dictionary with {V,I,R} values
        Rxx = self.K2400.get_R_from_IV(Rxx_IV_data)    #Not yet implemented
        time.sleep(delay)
        
        # Ryy 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Ryy_channels = self.K7001.close_channels(A,C,B,D)   ### Close appropriate channels to do Ryy measurement 
        Ryy_IV_data = self.K2400.measure_IV(I_start,I_end,I_stepSize)        # Note the return value is a dictionary with {V,I,R} values
        Ryy = self.K2400.get_R_from_IV(Ryy_IV_data)    #Not yet implemented
        time.sleep(delay)
        
        # Rxy 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Rxy_channels = self.K7001.close_channels(A,D,B,C)   ### Close appropriate channels to do Rxy measurement 
        Rxy_IV_data = self.K2400.measure_IV(I_start,I_end,I_stepSize)        # Note the return value is a dictionary with {V,I,R} values
        Rxy = get_R_from_IV(Rxy_IV_data)    #Not yet implemented
        time.sleep(delay)
        
        # Ryx 
        self.K7001.open_all()                               ### First open all channels to ensure no switches are closed 
        Ryx_channels = self.K7001.close_channels(B,C,D,A)   ### Close appropriate channels to do Ryx measurement 
        Ryx_IV_data = self.K2400.measure_IV(I_start,I_end,I_stepSize)        # Note the return value is a dictionary with {V,I,R} values
        Ryx = get_R_from_IV(Ryx_IV_data)    #Not yet implemented
        time.sleep(delay)

        ## Get the relevant parameters
        Rs = (Rxx+Ryy)/2.       # The sheet resistance
        Rh = (Rxy+Ryx)/2.       # The Hall resistance
        print('\t Rs = ',Rs,'Rh = ', Rh)
        
        self.K7001.open_all()                               ### Open all channels to ensure no switches are closed 

        ## This is the full dataset. 
        ## Maybe also save the raw data, if a flag applied 
        ## Will need to properly modify 
        return {'Rxx':Rxx, 'Ryy':Ryy, 'Rxy':Rxy, 'Ryx':Ryx, 'Rs':Rs, 'Rh':Rh}
