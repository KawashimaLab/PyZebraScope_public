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

from datetime import datetime
from PyQt5 import QtWidgets, QtTest
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import QTimer
import time
from eye_exclusion import eye_exc_win
import sys, os
import time
import threading
from auto_focusing import Auto_focusing




from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class Scanning(QObject):
    
    exclusionSignal = pyqtSignal(object, object)
    
    def __init__(self, parent=None):
        super().__init__()
        
        
        self.mainWindow = parent
        
        self.mainWindow.rec_btn.clicked.connect(self.startRecording)
        
        
        ### Auto-focusing
        
        self.auto_focusing=Auto_focusing(self)
        
        
        self.rec_started=False
        self.scan_started=False
        
        self.rec_time=0
        self.rec_file=0
        self.sync_event=False
        
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scanning_timer)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.recording_timer)
        
        self.start_t=0
        
        
        self.rec_start_time = ""
        self.rec_stop_time = "" 
        self.rec_info_file=""
        
        self.scan_mode = 0
        self.stop_mode = 0
        
        self.mainWindow.scan_plane.clicked.connect(lambda mode: self.scan_mode_changed(mode=0))
        self.mainWindow.scan_stack.clicked.connect(lambda mode: self.scan_mode_changed(mode=1))
        self.mainWindow.scan_btn.clicked.connect(self.startScanning)
        
        self.scan_mode_managed_btns=[self.mainWindow.LE_end_Y1, self.mainWindow.LE_end_Y2,
                                     self.mainWindow.LE_piezo_end,
                                     self.mainWindow.LE_cycle_duration, self.mainWindow.LE_num_planes,
#                                    self.mainWindow.LE_time_plane,
                                    self.mainWindow.label_17,self.mainWindow.label_42,
                                    self.mainWindow.label_41,self.mainWindow.label_48,
                                    self.mainWindow.label_32,self.mainWindow.label_45,
#                                    self.mainWindow.onoff_frame_gap,self.mainWindow.onoff_stack_gap,
                                    self.mainWindow.eye_exclude_btn]
        
        self.scan_rec_managed_btns=[self.mainWindow.scan_stack,self.mainWindow.scan_plane,
                                    self.mainWindow.stop_time,self.mainWindow.stop_count,
                                    self.mainWindow.stop_time_box,self.mainWindow.stop_count_box,
                                    self.mainWindow.stop_none]
        
        
        
        self.scan_mode_manage()
        
        self.limit_time=1000
        self.limit_image=1000
        self.stop_mode_manage()
        
        self.mainWindow.stop_count.clicked.connect(lambda mode: self.stop_mode_changed(mode=0))
        self.mainWindow.stop_time.clicked.connect(lambda mode:  self.stop_mode_changed(mode=1))
        self.mainWindow.stop_none.clicked.connect(lambda mode:  self.stop_mode_changed(mode=2))
        self.mainWindow.stop_count_box.valueChanged.connect(self.set_limit_image)
        self.mainWindow.stop_time_box.valueChanged.connect(self.set_limit_time)
        
    
    
    def close(self):
        
        self.auto_focusing.close()
        self.deleteLater()
        
        
    def scan_mode_changed(self,mode):
        
        self.scan_mode=mode
        self.scan_mode_manage()
        
        
        isParamValid=self.mainWindow.signals.check_params()            
        self.mainWindow.signals.update_params()     
        self.mainWindow.signals.draw_signals()  
        
        
        
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                self.mainWindow.cam_list[cam].scan_mode_changed()
        
        
        
        
    def stop_mode_changed(self,mode):
        
        self.stop_mode=mode
        self.stop_mode_manage()        
        
        
    def stop_mode_manage(self):
        
        self.mainWindow.stop_count_box.setEnabled(self.stop_mode==0)
        self.mainWindow.stop_time_box.setEnabled(self.stop_mode==1)
        
    def scan_mode_manage(self):
        
        for i in range(len(self.scan_mode_managed_btns)):
            self.scan_mode_managed_btns[i].setEnabled(self.scan_mode==1)
        
        
    def set_limit_image(self):
        self.limit_image = self.mainWindow.stop_count_box.value()


    def set_limit_time(self):
        self.limit_time = self.mainWindow.stop_time_box.value()
        
        
        
    def startScanning(self):
        
        
        isValid=self.mainWindow.signals.check_params()
        
        
        if isValid:            
            
            QtTest.QTest.qWait(100)
                
            self.scan_started = True            
            
            self.start_t=time.time()
            
            
            self.sync_event=True
            
            # make sure camera starts first
            
            for cam in range(2):
                if self.mainWindow.cam_on_list[cam]:
                    self.mainWindow.cam_list[cam].startScanning()
            
            if any(x for x in self.mainWindow.cam_on_list):
                while self.sync_event:                    
                    QtTest.QTest.qWait(50)                        
            else:
                self.sync_event=False       
                
            # start signal
            
            self.mainWindow.signalthread.start()
            
            
            self.mainWindow.scan_btn.setText("Stop Scan")
            self.mainWindow.scan_btn.clicked.disconnect()
            self.mainWindow.scan_btn.clicked.connect(self.stopScanning)
            
            self.mainWindow.stop_signals_btn.setEnabled(False)
                    
            self.set_btn_state(state=False,mode="scan")
            
                
            for cam in range(2):
                if self.mainWindow.cam_on_list[cam]:
                    try:
                        self.mainWindow.cam_list[cam].reader.reader_stop_signal.disconnect()
                        self.mainWindow.cam_list[cam].reader.reader_stop_signal.connect(self.stopScanning)
                    except:
                        self.mainWindow.cam_list[cam].reader.reader_stop_signal.connect(self.stopScanning)
                    
            
                
        
            
    def stopScanning(self):        
        
        
        self.secure_stop('scan')
        
        
        self.mainWindow.scan_btn.setText("Test Scan")   
        self.mainWindow.scan_btn.clicked.disconnect()
        self.mainWindow.scan_btn.clicked.connect(self.startScanning)        
        self.set_btn_state(state=True,mode="scan")
        
        self.scan_started = False
        self.scan_timer.stop()
        
        
        
    def startRecording(self):
        
        isFolderValid=os.path.isdir(self.mainWindow.save_dir)
        
            
        isParamValid=self.mainWindow.signals.check_params()
        
        
        if isParamValid and isFolderValid:            
            
            # creating a directory for the day
            
            today=datetime.today()
            date=str(today.year)+format(today.month,'02')+format(today.day,'02')
            
            date_dir=self.mainWindow.save_dir+"\\"+date
            
            if not os.path.isdir(date_dir):
                os.mkdir(date_dir)                    
            
            # creating separate directory per experiment
            
            header=self.mainWindow.save_header
            footer=self.mainWindow.save_footer
            exp_num=0
            while True:
                dirname="\\"+header+"Exp"+format(exp_num,'02')+footer
                if not os.path.isdir(date_dir+dirname):
                    break
                exp_num +=1
            
            self.mainWindow.exp_dir=date_dir+dirname
            
            self.mainWindow.exp_date_exp.setText("\\"+date+"\\"+header+"Exp"+format(exp_num,'02')+footer)
            
            os.mkdir(self.mainWindow.exp_dir)
            
            
            # start recording           
            
            self.rec_started=True
            
            self.sync_event=True
            
            # make sure camera starts first
            
            for cam in range(2):
                if self.mainWindow.cam_on_list[cam]:
                    self.mainWindow.cam_list[cam].startRecording()
                    
            if any(x for x in self.mainWindow.cam_on_list):
                while self.sync_event:                    
                    QtTest.QTest.qWait(50)                        
            else:
                self.sync_event=False       
            
            # start signal
        
            self.mainWindow.signalthread.start()
            
            # write out information
            
            self.rec_info_file=self.mainWindow.exp_dir+'//acquisition_info.xml'
            self.mainWindow.setting.write_imaging_params(self.rec_info_file)
            
            self.mainWindow.stop_signals_btn.setEnabled(False)
                    
            self.set_btn_state(state=False,mode="rec")
            
            for i in range(len(self.mainWindow.signals.signal_parameter_box_list)):
                self.mainWindow.signals.signal_parameter_box_list[i].setEnabled(False)
            
            
            self.timer.start(1000)
            self.start_t=time.time()
            
            self.mainWindow.rec_btn.setText("Stop Recording")
            self.mainWindow.rec_btn.clicked.disconnect()
            self.mainWindow.rec_btn.clicked.connect(self.stopRecording)
            
            
            for cam in range(2):
                if self.mainWindow.cam_on_list[cam]:
                    try:
                        self.mainWindow.cam_list[cam].writer.writer_stop_signal.disconnect()
                        self.mainWindow.cam_list[cam].writer.writer_stop_signal.connect(self.stopRecording)
                    except:
                        self.mainWindow.cam_list[cam].writer.writer_stop_signal.connect(self.stopRecording)
            
            
    def stopRecording(self):        
        
        self.rec_stop_time = str(datetime.now())     
        self.rec_started=False
        self.timer.stop()
        
        # make sure camera finishes first        

        self.secure_stop('record')              

        for i in range(len(self.mainWindow.signals.signal_parameter_box_list)):
            if i != 2: # exclude interval button
                self.mainWindow.signals.signal_parameter_box_list[i].setEnabled(True)
         
        self.mainWindow.setting.write_time_rec(self.rec_info_file,self.rec_start_time,self.rec_stop_time)
        
        self.scan_mode_manage()            
        self.set_btn_state(state=True,mode="rec")
        
        self.recording_timer()
        
        self.mainWindow.rec_btn.setText("Start Recording")
        self.mainWindow.rec_btn.clicked.disconnect()
        self.mainWindow.rec_btn.clicked.connect(self.startRecording)
                
    def secure_stop(self,mode):
        
        
        self.sync_event=True
        
                
        self.mainWindow.signal_on=False
        self.mainWindow.signalthread.quit()
        self.mainWindow.signalthread.wait()
        
        
        self.mainWindow.signals.finishing_trigger()     
        
        
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                if mode=='scan':
                    self.mainWindow.cam_list[cam].stopScanning()     
                elif mode=='record':
                    self.mainWindow.cam_list[cam].stopRecording()     
                    
        # a function for preventing camera 
        
                    
        
        while self.sync_event: 
            if any(x for x in self.mainWindow.cam_on_list):                   
                QtTest.QTest.qWait(50)                        
            else:
                self.sync_event=False      
                
        
                
        
                

        # a function for preventing camera 
        
            
        # ending signal        
                
        self.mainWindow.signals.stop_finishing_trigger()
        
            
    
    def set_btn_state(self,state=True,mode=None):
        
        # state=True enables most of buttons
        # state=False disables most of buttons to prevent troubles during recording
        
        for i in range(2):
            if self.mainWindow.cam_on_list[i]:
                self.mainWindow.cam_check_list[i].setEnabled(state)
        
        for i in range(len(self.scan_rec_managed_btns)):
            self.scan_rec_managed_btns[i].setEnabled(state)
        
        if mode == "rec":
            self.mainWindow.scan_btn.setEnabled(state)
        if mode == "scan":
            self.mainWindow.rec_btn.setEnabled(state)
        
        
        
            
    def recording_timer(self):
        
        rtime=time.time()-self.start_t
        
        self.mainWindow.rectime.setText(str(int(rtime))+' s')
            
        nfile=0
        nimage=0
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                nfile=self.mainWindow.cam_list[cam].nfile
                nimage=self.mainWindow.cam_list[cam].nimage
                
                
        if self.scan_mode==0:
            self.mainWindow.recfile.setText(str(int(nimage))+' images, '+str(int(nfile+1))+' files')
            #self.mainWindow.recfile.setText(str(int(nread))+' images, '+ str(int(nimage))+' images, '+str(int(nfile+1))+' files')
            
        else:
            self.mainWindow.recfile.setText(str(int(nimage))+' images, '+str(int(nfile))+' files')
            #self.mainWindow.recfile.setText(str(int(nread))+' images, '+ str(int(nimage))+' images, '+str(int(nfile))+' files')
            
        
        if (self.stop_mode==1) and (rtime>self.limit_time) and (self.rec_started):
            
            self.stopRecording() 
            

            
    def scanning_timer(self):
        
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                if self.mainWindow.cam_list[cam].nread>30:                    
        
                    self.stopScanning()
                    
                    
 
                    

        
        
    