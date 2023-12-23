# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 16:19:07 2020

@author: ranib
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 10:43:33 2020

@author: ranib
"""

from PyQt5 import QtWidgets, QtTest
import numpy as np

import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42 # important for vector text output
matplotlib.rcParams['ps.fonttype'] = 42  # important for vector text output

from matplotlib import pyplot as plt
from scipy.ndimage import gaussian_filter1d
import math
import nidaqmx
from nidaqmx import stream_writers
from PyQt5.QtCore import pyqtSignal, QObject

from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import time


class signals(QObject):
    
    
    def __init__(self, parent=None):
        super().__init__()
        
        
        self.mainWindow = parent
        
        self.sampling_rate = 500000
        self.precision = float(1000)/float(self.sampling_rate)
        self.cycle_duration = [1000]  # param 0
        self.num_planes = [45] # param 1
        self.ms_per_plane = [18] # param 2
        self.ms_exposure_per_plane = [16] # param 3
        self.acquiring_duration = self.num_planes[0] * self.ms_per_plane[0]
        self.gap_duration = self.cycle_duration[0] - self.acquiring_duration
        self.num_end_trigger = 10 
        self.device = 'PXI1Slot4'
        self.scan_mode=self.mainWindow.scanning.scan_mode
        self.scan_per_line=0.004867647
        self.pix_size=0.405
        self.height_init=2304
        self.width_init=2304
        self.daq_connected =True
        self.galvoY1_interpf = interp1d([-500,500],[-500,500],kind='linear',bounds_error=False,fill_value="extrapolate")
        self.galvoY2_interpf = interp1d([-500,500],[-500,500],kind='linear',bounds_error=False,fill_value="extrapolate")
        
        self.scale_factor=[[-0.025, 10], # piezo [scale, offset]
                           [0.0057, -0.8475], #galvoX1 
                           [-0.0058, 1], #galvoY1 
                           [-0.0057, -1.157], #galvoX2
                           [0.0058, -1.9], #galvoY2
                           [0.0057, 0 ], #galvoX3 
                           [0.0058, 0 ]] #galvoY3 
    
        self.signal_limit=[[  0, 10], # piezo [scale, offset]
                           [-10, 10], #galvoX1 
                           [-10, 10], #galvoY1 
                           [-10, 10], #galvoX2
                           [-10, 10], #galvoY2
                           [-10, 10], #galvoX3 
                           [-10, 10]] #galvoY3 
                            
        
        self.analog_output = []
        self.digital_output = []
        self.awriter= []
        self.dwriter= []
        
        self.smooth_sd = 0.1
        
        self.steps_num = self.cycle_duration[0] / self.precision
        
        self.camera_first_trigger_v = [4.5] # param 4, fixed
        self.camera_trigger_v = [4.0] # param 5, fixed
        self.camera_end_v = [3.5] # fixed
        
        self.piezo_start = [0] # param 6
        self.piezo_end = [200] # param 7
        self.piezo_shift = [20]  # param 8
        
        self.galvo1X_center = [0]   # param 9
        self.galvo1X_width = [933]    # param 10
        
        
        self.galvo1Y_start = [0]    # param 11
        self.galvo1Y_end = [200]    # param 12
        
        self.galvo2X_center = [0]    # param 13
        self.galvo2X_width = [300]     # param 14
        
        
        self.galvo2Y_start = [0]     # param 15
        self.galvo2Y_end = [200]     # param 16
        
        self.galvo3X_center = [0]     # param 17
        self.galvo3X_width = [300]      # param 18
        
        
        self.galvo3Y_start = [0]       # param 19
        self.galvo3Y_end = [200]       # param 20
        
        self.laser1_enable=[True]   # param 21
        self.laser2_enable=[False]  # param 22
        self.laser3_enable=[False]  # param 23
        self.lasers_enable=[self.laser1_enable, self.laser2_enable, self.laser3_enable]
        
        self.signal_parameter_list=[self.cycle_duration, self.num_planes,
                                    self.ms_per_plane, self.ms_exposure_per_plane,
                                    self.camera_first_trigger_v, self.camera_trigger_v,
                                    self.piezo_start,self.piezo_end,self.piezo_shift,
                                    self.galvo1X_center, self.galvo1X_width, #9,#10
                                    self.galvo1Y_start, self.galvo1Y_end,    #11,#12
                                    self.galvo2X_center, self.galvo2X_width ,#13,#14
                                    self.galvo2Y_start, self.galvo2Y_end,    #15,#16
                                    self.galvo3X_center, self.galvo3X_width, #17,#18
                                    self.galvo3Y_start, self.galvo3Y_end,    #19,#20
                                    self.laser1_enable, self.laser2_enable, self.laser3_enable] #21,#22,#23
        
     
        
        self.signal_parameter_box_list=[self.mainWindow.LE_cycle_duration, self.mainWindow.LE_num_planes,
                                        self.mainWindow.LE_time_plane, self.mainWindow.LE_exposure_plane,
                                        self.mainWindow.LE_cam_trigger_first_v, self.mainWindow.LE_cam_trigger_width,
                                        self.mainWindow.LE_piezo_start,self.mainWindow.LE_piezo_end,self.mainWindow.LE_piezo_pre_shift,
                                        self.mainWindow.LE_center_X1, self.mainWindow.LE_width_X1,
                                        self.mainWindow.LE_start_Y1, self.mainWindow.LE_end_Y1,
                                        self.mainWindow.LE_center_X2, self.mainWindow.LE_width_X2,
                                        self.mainWindow.LE_start_Y2, self.mainWindow.LE_end_Y2,
                                        self.mainWindow.LE_center_X3, self.mainWindow.LE_width_X3,
                                        self.mainWindow.LE_start_Y3, self.mainWindow.LE_end_Y3,
                                        self.mainWindow.LE_laser1, self.mainWindow.LE_laser2, self.mainWindow.LE_laser3]
        
        
        self.axial_parameter_box_list=[self.mainWindow.LE_piezo_start, self.mainWindow.LE_piezo_end,
                                       self.mainWindow.LE_start_Y1, self.mainWindow.LE_end_Y1,
                                       self.mainWindow.LE_start_Y2, self.mainWindow.LE_end_Y2,
                                       self.mainWindow.LE_start_Y3, self.mainWindow.LE_end_Y3] #21,#22,#23
  
        self.mainWindow.LE_exposure_plane.valueChanged.connect(self.cam_exposure_changed)
        
        self.waveform_xaxis=1000
        
        
        ### Set up waveform viewer
        
        self.scene = QtWidgets.QGraphicsScene()
        self.mainWindow.waveform_view.setScene(self.scene)
        
        
        ### Link to the button
        
        
        self.set_gui_init()
        self.update_params()
        self.recalculate_signal=False
        
        self.mainWindow.waveform_update_btn.clicked.connect(self.set_waveform_params)
        self.mainWindow.start_signals_btn.clicked.connect(self.start_signals)
        self.mainWindow.stop_signals_btn.clicked.connect(self.stop_signals)
        
        
        for b in self.axial_parameter_box_list:
            b.valueChanged.connect(self.reset_auto_focus)

        self.mainWindow.LE_laser1.clicked.connect(self.draw_signals)
        self.mainWindow.LE_laser2.clicked.connect(self.draw_signals)
        self.mainWindow.LE_laser3.clicked.connect(self.draw_signals)
        
        self.mainWindow.waveform_x_slider.valueChanged.connect(self.slider_changed)
        
        ### check parameter function
        
        for i in range(len(self.signal_parameter_list)):
            if type(self.signal_parameter_list[i][0])==bool:
                self.signal_parameter_box_list[i].clicked.connect(self.check_params_live)
            else:
                self.signal_parameter_box_list[i].valueChanged.connect(self.check_params_live)
        
        ### configure analog output 
        try:
            self.analog_output = nidaqmx.Task()
            self.analog_output.ao_channels.add_ao_voltage_chan(self.device+'/ao0:7')
            self.analog_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
            
            self.awriter = stream_writers.AnalogMultiChannelWriter(self.analog_output.out_stream, auto_start=False)
            
            ### configure digital output
            
            self.digital_output = nidaqmx.Task()
            self.digital_output.do_channels.add_do_chan(self.device+'/port0')
            self.digital_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, source='ao/SampleClock', sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
            
            self.dwriter=stream_writers.DigitalSingleChannelWriter(self.digital_output.out_stream, auto_start=False)
            
            
            print('DAQ connected')
            
            self.mainWindow.param_info.setStyleSheet('color: green')
            self.daq_connected = True
            self.draw_signals()
            
        except:
            
            print('DAQ not available')
            
            self.daq_connected = False
            self.analog_output = None
            self.awriter= None
            self.digital_output = None
            self.dwriter= None
            
            
            self._isRunning=False
        
        
        
    def close(self):
        
        if self.daq_connected:
            
            self.digital_output.close()
            self.analog_output.close()
            print("DAQ disconnected")
        
        self.deleteLater()
        
    def set_gui_init(self):
        
        # set initial value
        
        for i in range(len(self.signal_parameter_list)):
            if type(self.signal_parameter_list[i][0])==bool:
                self.signal_parameter_box_list[i].setChecked(self.signal_parameter_list[i][0])
            else:
                self.signal_parameter_box_list[i].setValue(self.signal_parameter_list[i][0])
    
    
    def cam_exposure_changed(self):
        
        
        # if self.signal_parameter_box_list[3].value() >= self.signal_parameter_box_list[2].value():
        #     self.signal_parameter_list[2][0]=self.signal_parameter_box_list[3].value()+1 ## currently it's set as same value
        #     self.signal_parameter_box_list[2].setValue(self.signal_parameter_list[2][0])
        self.signal_parameter_list[2][0]=self.signal_parameter_box_list[3].value()
        self.signal_parameter_box_list[2].setValue(self.signal_parameter_list[2][0])
        
        isValid=self.check_params()
    
        if isValid:
            self.signal_parameter_list[3][0]=self.signal_parameter_box_list[3].value()
            
            
    
    def check_params_live(self):
        
        isValid=self.check_params()
        
        if self.mainWindow.scanning.scan_started:
            
            # should be changed to update signals
            self.recalculate_signal=True
            
            #self.mainWindow.scanning.stopScanning() # original code
            #self.mainWindow.scanning.startScanning()  # original code
    
            
    def check_params(self):
        
        output=True
        
        
        
        # ms_per_plane needs to be longer than ms_exposure_per_plane
        
        if self.signal_parameter_box_list[3].value() > (self.signal_parameter_box_list[2].value()):
            
            self.mainWindow.param_info.setText('camera exposure needs to be shorter than time per plane')
            output=False
    
        # Prevent too short camera exposure
    
        min_cam_exposure=[2,2]
        for cam in range(2):
            
            if self.mainWindow.cam_on_list[cam]:
                min_cam_exposure[cam]=(1000/self.mainWindow.cam_list[cam].max_frame_rate)
                
            if self.signal_parameter_box_list[3].value() < min_cam_exposure[cam]:
                
                self.mainWindow.param_info.setText('camera exposure too short for the current ROI: minimum {:.2f} ms'.format(min_cam_exposure[cam]))
                output=False
                
                
        # Stack parameter wrong 
        if self.mainWindow.scanning.scan_mode==1:
            
            stack_duration=(self.signal_parameter_box_list[1].value()+1)*self.signal_parameter_box_list[2].value()
            if self.signal_parameter_box_list[0].value()<=(stack_duration+100):
                              
                self.mainWindow.param_info.setText('Cycle duration should be longer than  {:d} ms'.format(int(stack_duration+100)))
 
                output=False
                
            if (self.signal_parameter_box_list[0].value()/self.signal_parameter_box_list[2].value())<33:
                
                upper_limit=int(self.signal_parameter_box_list[0].value()/33)
                self.mainWindow.param_info.setText('Exposure time is too short compared to cycle duration: needs to be <='+ str(upper_limit) +' ms')
 
                output=False
            
            
                
                
        
        if output:            
            self.mainWindow.param_info.setText('Parameters OK')
            self.mainWindow.param_info.setStyleSheet('color: green')
        else:
            self.mainWindow.param_info.setStyleSheet('color: rgb(150, 0, 0)')                
            
            
        return output
        
    def update_params(self):
        
        
        ## update_parameters ##
        
        for i in range(len(self.signal_parameter_list)):
            
            if type(self.signal_parameter_list[i][0])==bool:
                self.signal_parameter_list[i][0] = self.signal_parameter_box_list[i].isChecked()
            else:
                self.signal_parameter_list[i][0] = self.signal_parameter_box_list[i].value()
        
              
        self.acquiring_duration = self.num_planes[0] * self.ms_per_plane[0]
        self.gap_duration = self.cycle_duration[0] - self.acquiring_duration
        
                
        ## acquire scan parameters ##
        
        self.scan_mode=self.mainWindow.scanning.scan_mode
        self.precision = float(1000)/float(self.sampling_rate)
        
        
        if self.scan_mode==0:
            self.steps_num = self.ms_per_plane[0] / self.precision
            self.ms_per_plane[0] = self.ms_exposure_per_plane[0]
        else:
            self.steps_num = self.cycle_duration[0] / self.precision
        
        ## generate signal ##
            
        self.generate_output_signals()
        
        self.mainWindow.setting_unsaved.setText("Current parameters unsaved")
            
        
    def draw_signals(self):
        
        self.scene.clear()
        self.figure = Figure(figsize=(5.76,2.4))
        self.axes = self.figure.gca()
        self.axes.set_position([0.08,0.1,0.7,0.85])
        self.canvas = FigureCanvas(self.figure)
        self.scene.addWidget(self.canvas)
        
        names=[]
        x_axis=np.arange(len(self.galvo1X))*self.precision
        
        self.axes.plot(x_axis,self.cam_trigger)
        names.append('Cam')            
        self.axes.plot(x_axis,self.object_piezo)
        names.append('Piezo')
            
        if self.mainWindow.LE_laser1.isChecked():
            self.axes.plot(x_axis,self.galvo1X)
            self.axes.plot(x_axis,self.galvo1Y)
            self.axes.plot(x_axis,np.asarray(self.laser1).astype(int))
            names.append('X1')
            names.append('Y1')
            names.append('Laser1')
            
        if self.mainWindow.LE_laser2.isChecked():
            self.axes.plot(x_axis,self.galvo2X)
            self.axes.plot(x_axis,self.galvo2Y)
            self.axes.plot(x_axis,np.asarray(self.laser2).astype(int))
            names.append('X2')
            names.append('Y2')
            names.append('Laser2')
            
        if self.mainWindow.LE_laser3.isChecked():
            self.axes.plot(x_axis,self.galvo3X)
            self.axes.plot(x_axis,self.galvo3Y)
            self.axes.plot(x_axis,np.asarray(self.laser3).astype(int))
            names.append('X3')
            names.append('Y3')
            names.append('Laser3')


            
        self.axes.legend(labels=names, bbox_to_anchor=(1.05,1), loc='upper left')
        
        self.mainWindow.waveform_x_slider.blockSignals(True)
        tlen=len(self.galvo1X)*self.precision
        self.mainWindow.waveform_x_slider.setValue(int(tlen))
        self.waveform_xaxis=tlen
        self.mainWindow.waveform_x_slider.blockSignals(False)
        
        self.axes.set_xlim(-self.waveform_xaxis*0.05,self.waveform_xaxis*1.05)
        
        
    def slider_changed(self):
              
        self.waveform_xaxis=self.mainWindow.waveform_x_slider.value()
        self.draw_signals()
        
        
    def set_waveform_params(self):
        
        isValid=self.check_params()
        
        if isValid:
            self.update_params()
            
            self.waveform_xaxis=len(self.galvo1X)*self.precision
            self.mainWindow.waveform_x_slider.setValue(int(self.waveform_xaxis))        
            self.draw_signals()
     
            if self.mainWindow.scanning.scan_started:
                
                self.mainWindow.scanning.stopScanning()
                self.mainWindow.scanning.startScanning()
                
                
                
    def scale(self,s,n,offset=True):
        
        if offset:
            return s*self.scale_factor[n][0]+self.scale_factor[n][1]
        else:
            return s*self.scale_factor[n][0]
        
                
    
    def generate_output_signals(self):
        
        self.cam_trigger    = self.generate_camera_trigger()
        self.object_piezo   = self.generate_piezo_galvoY(self.piezo_start[0],self.piezo_end[0],0,0,'piezo')
        
        self.galvo1X, self.laser1 = self.generate_galvoX_laser(self.galvo1X_center[0], self.galvo1X_width[0],1)
        self.galvo2X, self.laser2 = self.generate_galvoX_laser(self.galvo2X_center[0], self.galvo2X_width[0],3)
        self.galvo3X, self.laser3 = self.generate_galvoX_laser(self.galvo3X_center[0], self.galvo3X_width[0],5)
        
        self.galvo1Y        = self.generate_piezo_galvoY(self.galvo1Y_start[0],self.galvo1Y_end[0],2,self.piezo_shift[0],'galvo')
        self.galvo2Y        = self.generate_piezo_galvoY(self.galvo2Y_start[0],self.galvo2Y_end[0],4,self.piezo_shift[0],'galvo')
        self.galvo3Y        = self.generate_piezo_galvoY(self.galvo3Y_start[0],self.galvo3Y_end[0],6,self.piezo_shift[0],'galvo')
        
    
    def generate_galvoX_laser(self,center,width,ao_num):
        
        
        centerV = self.scale(center,ao_num)
        widthV  = self.scale(width,ao_num,offset=False)
        
        shift = int(self.piezo_shift[0]/self.precision)
        
        aboveBelow = widthV/2
        startV = centerV-aboveBelow
        endV = centerV+aboveBelow
        
        waveformX = np.ones((int(self.steps_num),))*startV
        
        height = self.height_init
        width  = self.width_init
        
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                height=self.mainWindow.cam_list[cam].roi_dims[2]
                width =self.mainWindow.cam_list[cam].roi_dims[3]

            
        if self.scan_mode ==0:
            
            rise = int((self.ms_per_plane[0]/self.precision)/2)
            fall = self.steps_num-rise
                
            waveformX[:int(rise)]=np.linspace(startV,endV,int(rise))
            waveformX[int(rise):]=np.linspace(endV,startV,int(fall))
            
            laser = [True]*int(self.steps_num)
        
        else:            
            
            
            interval = int(self.ms_per_plane[0]/self.precision)
            laser = [False]*int(self.steps_num)
               
            # Calculate the delay of rolling shutter
            
            camera_sweep_dur = int(self.scan_per_line*width/self.precision) 
            
            delay = camera_sweep_dur                
            rise  = interval-camera_sweep_dur
            fall  = interval-rise
            
            for i in range(self.num_planes[0]+1):
                
                waveformX[int(i*interval+shift):int(i*interval+rise+shift)]=np.linspace(startV,endV,int(rise))
                waveformX[int(i*interval+rise+shift):int((i+1)*interval+shift)]=np.linspace(endV,startV,int(fall))
                laser[int(i*interval+shift):int(i*interval+rise+shift)] = [True]*rise
            
            
            # Eye exclusion
            
            if self.mainWindow.eye_exclusion.exclusion and ((ao_num ==1) or (ao_num ==5)) :
                
                exclusion_list=self.mainWindow.eye_exclusion.exclusion_list
                

                height_um = height*self.pix_size
                
                for i in range(len(exclusion_list)):
                    
                    start=-(exclusion_list[i][1]*height_um-(height_um/2))
                    end=-((exclusion_list[i][1]+exclusion_list[i][2])*height_um-(height_um/2))
                    waveX=(waveformX[shift:(shift+interval)]-self.scale_factor[1][1])/self.scale_factor[1][0]
                    index=np.where((waveX>end) & (waveX<start))[0]
                    
                    for j in index:
                        laser[exclusion_list[i][0]*interval+shift+j] = False
                        
                     
            # Shift laser and galvo to compensate for scanning
            
            waveformX=np.roll(waveformX,delay)
            laser=np.roll(laser,delay)
                
            
        # final_output       
        
        if self.lasers_enable[int(ao_num / 2)][0]==False:
            laser =  [False]*int(self.steps_num)
            
        waveformX=gaussian_filter1d(waveformX, self.smooth_sd/self.precision,mode="wrap").clip(self.signal_limit[ao_num][0],self.signal_limit[ao_num][1])
            
        return waveformX,laser
    
    def generate_piezo_galvoY(self,start,end,ao_num,pshift,mode):
        
        
        startV = self.scale(start,ao_num)
        endV   = self.scale(end,ao_num)
        
        waveformY = np.ones((int(self.steps_num),))*startV
        
        if self.scan_mode ==1:
            
            shift = int(pshift/self.precision)
            step_dur =  int(self.ms_per_plane[0]/self.precision)            
            duration=(self.num_planes[0]+1)*step_dur            
            gap_dur = int(self.steps_num-(self.num_planes[0]+1)*step_dur)
            
            incrementV = (endV-startV)/self.num_planes[0]
            endV2 = endV+incrementV
            
            if mode=='piezo':                
                
                waveformY[shift:duration+shift]=np.linspace(startV,endV2,duration)       
                
                
                # interval = int(self.ms_per_plane[0]/self.precision)
                
                # for i in range(self.num_planes[0]+1):                    
                #     waveformY[int(i*interval+shift):int((i+1)*interval+shift)]=startV+incrementV*i
                        
            else: # Galvo, nonlinear conversion based on autofocusing
            
            
                waveform_pos = np.ones((int(self.steps_num),))*start                
                increment = (end-start)/self.num_planes[0]
                end2 = end+increment                
                waveform_pos[shift:duration+shift]=np.linspace(start,end2,duration)      
                
                # warp transformation based on autofocusing
                
                if ao_num==2:
                    waveform_pos=self.scale(self.galvoY1_interpf(waveform_pos),ao_num)
                if ao_num==4:
                    waveform_pos=self.scale(self.galvoY2_interpf(waveform_pos),ao_num)                    
                    
                waveformY[shift:duration+shift]=waveform_pos[shift:duration+shift]  
                    
            waveformY[int((self.num_planes[0]+1)*step_dur):]=np.linspace(endV2,startV,gap_dur)
                
                
        
        waveformY = gaussian_filter1d(waveformY, self.smooth_sd/self.precision,mode="wrap").clip(self.signal_limit[ao_num][0],self.signal_limit[ao_num][1])
            
        return waveformY
    
    


    def generate_camera_trigger(self):
        
        trigger_signal = np.zeros((int(self.steps_num),))
    
        if self.scan_mode == 0:
     
            trigger_signal[1:int(1/self.precision)+1] = self.camera_first_trigger_v
        
        else:
            
            # start of the stack
            
            shift = int(self.piezo_shift[0]/self.precision)
            trigger_signal[0+shift:int(1/self.precision)+shift] = self.camera_first_trigger_v
            
            # second to last planes 
            
            for i in range(self.num_planes[0]-1):
                trigger_signal[int(((i+1)*self.ms_per_plane[0])/self.precision)+shift:
                               int(((i+1)*self.ms_per_plane[0]+1)/self.precision)+shift]=self.camera_trigger_v[0] 
            #last empty plane
            
            self.num_end_trigger = int(self.signal_parameter_box_list[0].value()/self.signal_parameter_box_list[2].value()-self.signal_parameter_box_list[1].value()) # temporary solution
            #self.num_end_trigger = 1
            
            for i in range(self.num_end_trigger):
                trigger_signal[int(((self.num_planes[0]+i)*self.ms_per_plane[0])/self.precision)+shift:
                               int(((self.num_planes[0]+i)*self.ms_per_plane[0]+1)/self.precision)+shift]=self.camera_end_v[0] 
                    
            # trigger_signal[int((self.num_planes[0]*self.ms_per_plane[0])/self.precision)+shift:
            #                int((self.num_planes[0]*self.ms_per_plane[0]+1)/self.precision)+shift]=self.camera_end_v[0] 
           
        return trigger_signal
    
    
    def generate_camera_end_trigger(self):
        
        shift = int(self.piezo_shift[0]/self.precision)
        trigger_signal = np.zeros((int(self.steps_num),))
    
        if self.scan_mode == 0:
     
            trigger_signal[1:int(1/self.precision)+1] = self.camera_end_v[0] 
        else:            
            
            for i in range(self.num_planes[0]):
                trigger_signal[int((i*self.ms_per_plane[0])/self.precision)+shift:
                               int((i*self.ms_per_plane[0]+1)/self.precision)+shift]=self.camera_end_v[0] 
           
        return trigger_signal
        
        
 
    
    def lasers_to_digital(self):
        
        # you can write 8 lines of digital port at once by a single UINT8 value
        # UINT8 can be expressed as an array of 8 boolian values, likle [0 1 0 1 0 1 0 1]
        # Each bool correspond to a single line of a digital port
        # Here we generate UINT8 array from boolian arrays for lasers
        
        laser1_tmp=np.asarray(self.laser1).astype(np.uint8)
        laser2_tmp=np.asarray(self.laser2).astype(np.uint8)
        laser3_tmp=np.asarray(self.laser3).astype(np.uint8)
        
        out = (laser1_tmp+laser2_tmp*2+laser3_tmp*4).astype(np.uint8)
        
        return out
            
    
    
    def reset_auto_focus(self):
        
        if (self.mainWindow.af_status_1.text()=='Set') and (not self.mainWindow.scanning.auto_focusing.autofocus):
            self.galvoY1_interpf = interp1d([-500,500],[-500,500],kind='linear',bounds_error=False,fill_value="extrapolate")
            self.mainWindow.af_status_1.setText('None')
            self.mainWindow.af_status_1.setStyleSheet('color: black')    
            
        if (self.mainWindow.af_status_2.text()=='Set') and (not self.mainWindow.scanning.auto_focusing.autofocus):
            self.galvoY2_interpf = interp1d([-500,500],[-500,500],kind='linear',bounds_error=False,fill_value="extrapolate")
            self.mainWindow.af_status_2.setText('None')
            self.mainWindow.af_status_2.setStyleSheet('color: black')


    def start_signals(self):
        
        parameter_valid=self.check_params() 
        
        if parameter_valid and self.daq_connected:
            
            
            if self.mainWindow.scanning.scan_started:
                self.sampling_rate = 20000
                
            if self.mainWindow.scanning.rec_started:
                self.sampling_rate = 200000
                
            ##prepare signals (camera, piezo, 6 galvos)
            
            self.update_params()
            
            self.analog_signals=np.vstack((self.cam_trigger,self.object_piezo,
                                      self.galvo1X,self.galvo1Y,self.galvo2X,
                                      self.galvo2Y,self.galvo3X,self.galvo3Y))
            
            self.digital_signals=self.lasers_to_digital()
                
            ### configure analog output
             
            self.analog_output.close()
            self.analog_output = nidaqmx.Task()
            self.analog_output.ao_channels.add_ao_voltage_chan(self.device+'/ao0:7')
             
            if (self.mainWindow.scanning.scan_started) and (self.mainWindow.scanning.scan_mode==1):
                self.analog_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                                              samps_per_chan=self.analog_signals.shape[1])   
            else:
                self.analog_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                              samps_per_chan=self.analog_signals.shape[1])
            
            #self.analog_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
            
            self.awriter = stream_writers.AnalogMultiChannelWriter(self.analog_output.out_stream, auto_start=False)
            
            ### configure digital output
            
            self.digital_output.close()
            self.digital_output = nidaqmx.Task()
            self.digital_output.do_channels.add_do_chan(self.device+'/port0')
            
            if (self.mainWindow.scanning.scan_started) and (self.mainWindow.scanning.scan_mode==1):
                self.digital_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, source='ao/SampleClock', sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                                               samps_per_chan=len(self.digital_signals))
            else:
                self.digital_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, source='ao/SampleClock', sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                               samps_per_chan=len(self.digital_signals))
           
            #self.digital_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, source='ao/SampleClock', sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)     
            
            self.dwriter=stream_writers.DigitalSingleChannelWriter(self.digital_output.out_stream, auto_start=False)
               
            
            
            ## set analog NI outputs         
            
            self.awriter.write_many_sample(self.analog_signals)
            
            ## set digital NI outputs         
            
            self.dwriter.write_many_sample_port_byte(self.digital_signals)
    
            ''' This is where everything starts and should be synced'''
            self.digital_output.start()
            self.analog_output.start()
            
            self.mainWindow.scanning.rec_start_time = str(datetime.now()) 
            
            
            
            self.mainWindow.start_signals_btn.setEnabled(False)
            self.mainWindow.stop_signals_btn.setEnabled(True)
            
            
            self.mainWindow.signal_on=True
            
            while self.mainWindow.signal_on:
                
                if self.recalculate_signal==True:
                    
                    self.update_params()
                    self.analog_signals=np.vstack((self.cam_trigger,self.object_piezo,
                                              self.galvo1X,self.galvo1Y,self.galvo2X,
                                              self.galvo2Y,self.galvo3X,self.galvo3Y))
                    self.digital_signals=self.lasers_to_digital()
                    
                    #self.digital_output.stop()
                    #self.analog_output.stop()
                    
                    
                    
                    self.awriter.write_many_sample(self.analog_signals)
                    self.dwriter.write_many_sample_port_byte(self.digital_signals)
                    
                    #self.digital_output.start()
                    #self.analog_output.start()
                    
                    print('updated signals')
                    
                    self.recalculate_signal=False
                            
                    
                QtTest.QTest.qWait(5)
                
            if (self.mainWindow.scanning.scan_started) and (self.mainWindow.scanning.scan_mode==1):
                self.digital_output.wait_until_done()
                
            
            self.digital_output.stop()                
            self.analog_output.stop()
            
            # make sure laser is off each time
            
            self.digital_output.close()
            self.digital_output = nidaqmx.Task()
            self.digital_output.do_channels.add_do_chan(self.device+'/port0')            
           
            self.dwriter=stream_writers.DigitalSingleChannelWriter(self.digital_output.out_stream, auto_start=True)
            self.dwriter.write_one_sample_port_byte(np.zeros((1,),dtype=np.uint8))   
            
            QtTest.QTest.qWait(10)
            self.digital_output.stop()     
            
            
            # change button
            
            self.mainWindow.start_signals_btn.setEnabled(True)
            self.mainWindow.stop_signals_btn.setEnabled(False)
            
            
    def stop_signals(self):
            
        self.mainWindow.signal_on=False
        
    
            
    def finishing_trigger(self):
        
        # function for stopping the camera by sending trigger signals. 
        # No digital activation needed.
        
        parameter_valid=self.check_params() 
        
        if parameter_valid and self.daq_connected:
            
            
            self.sampling_rate = 50000                
            self.generate_camera_end_trigger()
             
            self.analog_output.close()
            self.analog_output = nidaqmx.Task()
            self.analog_output.ao_channels.add_ao_voltage_chan(self.device+'/ao0')
            self.analog_output.timing.cfg_samp_clk_timing(rate=self.sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)  
       
            self.awriter = stream_writers.AnalogSingleChannelWriter(self.analog_output.out_stream, auto_start=False)
            self.awriter.write_many_sample(self.cam_trigger)
            self.analog_output.start()
            
        
    def stop_finishing_trigger(self):
        
        # function for stopping the camera by sending trigger signals
            
        if self.daq_connected:
            
            self.analog_output.stop()
                
                
            
    