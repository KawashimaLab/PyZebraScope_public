# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtTest, uic,QtTest
from PyQt5.QtCore import QThread, QObject,QEventLoop

import pymmcore
import sys
from queue import Queue
from camview import CamView
import numpy as np
import os
import h5py
import time

class Cam_GUI(QtWidgets.QMainWindow):
    
    # this class is necessary to defining closeEvent for GUI
    
    def __init__(self,parent=None):
        QtWidgets.QMainWindow.__init__(self)
        self.parent=parent

    def closeEvent(self, event):
        self.parent.close_cam_view()
        self.close()

class Reader(QObject):

#Later reader will get readings by the trigger signal#
  
    def __init__(self, parent=None, mmc=None, app=None, qrec=None, qview=None):
        QObject.__init__(self)
        self.qrec = qrec
        self.qview = qview
        self.app = app
        self.mmc = mmc
        self.parent = parent
        self._isRunning=True
        
    def run(self):        
        
        self.nread=0
        self.scan_mode =self.parent.scan_mode
        self.cam_mode = self.parent.cam_mode
        self.stack_size=self.parent.stack_size
        
        if self.scan_mode==1:
            self.parent.cam_win.z_slider.setValue(1)
            
        while self.parent.reader_on:
            
            try:
                last_image = self.mmc.popNextImage()
                
                # check which plane in a stack
                
                if self.scan_mode==0:
                    plane = (self.nread % self.stack_size)  
                else:
                    plane = self.nread % (self.stack_size+1)
                
                # put it in recording queue or in sample_stack
                if self.parent.writer_on:
                    if self.scan_mode==0:
                        self.qrec.put(last_image)                       
                    elif not (plane==self.stack_size):
                        self.qrec.put(np.rot90(last_image,-1)) # correct for directions, this rotation opertion is slow
                else:
                    if (self.scan_mode==1) and (self.nread<self.stack_size):
                        self.qrec.put(np.fliplr(last_image))
                    
                if self.nread % 30 == 0:
                    self.qview.put(np.fliplr(last_image))
                    
                self.nread +=1
                
            except:
                pass
            
            QtTest.QTest.qWait(0.1)
            
            
        
        
        
class Writer(QObject):
    
    def __init__(self, parent=None, cam_number = 0, app=None, qrec=None):
        
        QObject.__init__(self)
        self._isRunning = True
        self.qrec = qrec
        self.cam_number=cam_number
        self.app = app
        self.parent = parent
        
        
    def run(self):
        
        self.target_dir=self.parent.mainWindow.exp_dir
        self.parent.nfile = 0
        self.parent.nimage = 0
        self.image_i = 0
        self.stack_size=self.parent.stack_size
        self.scan_mode=self.parent.scan_mode
        self.limit_count=self.parent.limit_count
        
        while self.parent.writer_on:
            
            digits = len(str(self.parent.nfile))

            name = '\\cam'+str(self.cam_number)+'_' + (5-digits)*'0' + '%d.h5' % self.parent.nfile              
            filename = self.target_dir +  name
            hf = h5py.File(filename,'a')
            
            self.image_i=0
            
            while (self.image_i <self.stack_size) and (self.parent.writer_on):
                
                if not self.qrec.empty():
                    
                    image = self.qrec.get()
                    dataset = 'image%d' % self.image_i
                    self.image_i += 1
                    
                    with h5py.File(filename,'a') as hf:
                        hf.create_dataset(dataset,data=image)
                        
                    self.parent.nimage += 1
                        
                    # limit by image number for single_plane acquisition
                    
                    if (self.scan_mode == 0) and (self.limit_count<=self.parent.nimage):
                        self.parent.mainWindow.scanning.stopRecording()
                    
                QtTest.QTest.qWait(1)
            
            hf.close()
            self.parent.nfile += 1
                
            # limit by file number for stack acquisition
            
            if (self.scan_mode == 1) and (self.limit_count<=self.parent.nfile):
                self.parent.mainWindow.scanning.stopRecording()   
            
            QtTest.QTest.qWait(0.1)                            


        

class Camera(QObject):

    
    def __init__(self, parent=None, app=None, cam_number=0):
        
        super().__init__()
        
        self.mainWindow=parent
        self.cam_number=cam_number
        self.app=app
        self.recstart_t=0
        self.nfile=0
        self.nimage=0
        self.cam_mode="noscan"
        self.cur_exposure=16
        self.stack_size=50
        self.limit_count=1000
        self.rec_mode=0
        self.cam_names=['C15440-20UP','C14440-20UP']
        
        
        sys.path.append('C:\\Program Files\\Micro-Manager-2.0beta')
        mm_dir="C:\Program Files\Micro-Manager-2.0beta"
        
        try:
            self.mmc = pymmcore.CMMCore()
            self.mmc.setDeviceAdapterSearchPaths([mm_dir])
            self.mmc.loadDevice('Camera','HamamatsuHam', 'HamamatsuHam_DCAM')
            self.mmc.initializeAllDevices()
            
            self.cam_name = self.mmc.getProperty('Camera','CameraName') #<-- fast mode
            print(self.cam_name)
            if not self.cam_name == self.cam_names[cam_number-1]:
                self.mmc.reset()
                raise Exception("camera "+str(cam_number)+" not available:")
                
            print('Camera ' + str(self.cam_number) + ' loaded: ' + self.cam_name)
            
            self.mmc.setProperty('Camera', 'ScanMode', '3') #<-- fast mode
            self.mmc.setProperty('Camera', 'TRIGGER ACTIVE', 'SYNCREADOUT') #<-- EDGE, LEVEL, SYNCREADOUT
            self.mmc.setProperty('Camera', 'TRIGGER GLOBAL EXPOSURE', 'DELAYED') #<-- GLOBAL RESET or DELAYED
            self.mmc.setProperty('Camera', 'TRIGGER SOURCE','INTERNAL') ## Switch trigger source
            
            self.roi_dims = self.mmc.getROI()
            self.max_frame_rate=self.calc_max_frame_rate(self.roi_dims[2])
            
            
            self.qrec = Queue()
            self.qview = Queue()
            
            
            self.image_buffer   = np.zeros((2304,2304),dtype=np.single)
            self.overlay_buffer = np.zeros((2304,2304,3),dtype=np.single)
            self.pix_buffer = np.zeros((2304,2304),dtype=np.uint16)
            
            self.image_buffer[0,0] = 1.
            self.overlay_buffer[0,0,0] = 1.
            self.pix_buffer[0,0] = 1
            
            self.target_dir=""
            
            self.readthread = QThread()
            self.reader = Reader(mmc=self.mmc, parent=self, app=self.app, qrec=self.qrec, qview=self.qview)
            self.reader.moveToThread(self.readthread)
            self.reader_on=False
            
            self.writethread = QThread()
            self.writer = Writer(parent=self, cam_number = self.cam_number, app=self.app, qrec=self.qrec)
            self.writer.moveToThread(self.writethread)
            self.writer_on=False
            
            self.readthread.started.connect(self.reader.run)
            self.writethread.started.connect(self.writer.run)
            
            self.cam_window = Cam_GUI(self) #QtWidgets.QMainWindow()
            self.cam_win = CamView(self)
            self.cam_win.setupUi(self.cam_window)
            self.camview_thread = self.cam_win
            self.camview_thread.started.connect(self.updateview)
            
            
            self.cam_on=False
            self.ROI=False
            
            
            self.update_twocam_buttons()
            self.update_roi_buttons()
            self.btn_list=[
                    self.cam_win.startStream_btn,
                    self.cam_win.stopStream_btn,
                    self.cam_win.capture_btn,
                    self.cam_win.resetROI_btn,
                    self.cam_win.setROI_btn,
                    self.cam_win.pushROI_btn,
                    self.cam_win.overlay_btn]
            
            self.overlay=False
            
            self.br_max=100.0
            self.br_min=0.0
            self.vpercentile=100
            self.vabsolute=False
            self.autoscale=True
            self.pix_max=0
            self.stack_max=0
            self.sample_stack=np.zeros((50,2304,2304))
        
                
        except:
            
            self.mmc=None
            print('Camera ' + str(self.cam_number) + ' not available')
                
        
        
        
    def close(self):
        
        if self.mmc:
            if self.mmc.isSequenceRunning():
                print('Camera ' + str(self.cam_number) + ' stopping')
                self.mmc.stopSequenceAcquisition()
                
                  
            self.update_twocam_buttons()
            self.cam_window.close()      
                
                
            self.mmc.reset()
            print('Camera ' + str(self.cam_number) + ' closed')
            
            self.camview_thread.terminate()        
            self.readthread.terminate()
            self.writethread.terminate()
            self.deleteLater()
            
            
            
            
    def start_cam_view(self):
        
        
        
        self.camview_thread.start()
        
        self.cam_window.show()
        
        self.cam_win.imv.updateSignal.connect(self.updateview)
        self.cam_win.setROISignal.connect(self.setROI)
        self.cam_win.captureSignal.connect(self.capture)
        self.cam_win.resetROISignal.connect(self.resetROI)
        self.cam_win.startStreamSignal.connect(self.startStream)
        self.cam_win.stopStreamSignal.connect(self.stopStream)
        self.cam_win.pushROISignal.connect(self.pushROI)
        self.cam_win.overlaySignal.connect(self.setOverlay)
        
        self.update_startstop_buttons()
        self.update_roi_buttons()
        self.update_twocam_buttons()
        self.update_br_console()
        
        self.view_box = self.cam_win.imv.getView()
        self.view_box.invertY(False)
        
        
            
        
    def close_cam_view(self):
        
        self.stopStream()
        self.camview_thread.quit()
        
        
    def setROI(self):
        
        self.ROI=True
        self.cam_win.imv.region_changed()
        self.cam_win.imv.current_roi.hide()
        self.roi_dims = self.cam_win.imv.roi_dimensions
            
        if self.mmc.isSequenceRunning():
            
            self.stop_camera()
            self.mmc.setROI(self.roi_dims[0],self.roi_dims[1],self.roi_dims[2],self.roi_dims[3])
            self.start_camera()
            
        else:
            
            self.mmc.setROI(self.roi_dims[0],self.roi_dims[1],self.roi_dims[2],self.roi_dims[3])
            
        #self.cam_win.imv.region_changed()
        self.update_frame_info()
        self.update_roi_buttons()
        
        
        
    def resetROI(self):
        
        
        self.ROI=False
        
        if self.mmc.isSequenceRunning():
            self.stop_camera()
            self.mmc.clearROI()
            self.roi_dims = str(self.mmc.getROI())
            self.cam_win.imv.current_roi.show()
            self.start_camera()
        else:
            self.mmc.clearROI()
            self.roi_dims = str(self.mmc.getROI())
            self.cam_win.imv.current_roi.show()
        
        self.cam_win.imv.region_changed()
        self.update_frame_info()
        self.update_roi_buttons()
        
        
    
    def pushROI(self):
        
        other_cam=self.mainWindow.cam_list[2-self.cam_number]
        
        if not self.ROI:
            other_cam.resetROI()
        else:
            target_ROI=self.mmc.getROI()
            other_cam.cam_win.imv.current_roi.setPos(target_ROI[1],target_ROI[0])
            other_cam.cam_win.imv.current_roi.setSize([target_ROI[3],target_ROI[2]])
            other_cam.setROI()
        
            
            
    def capture(self):
        
        self.mmc.snapImage()
        self.image_buffer = self.mmc.getImage()
        self.updateview()
        
    

    def updateview(self):
        
            
        
        if self.mmc.isSequenceRunning():
            
            try:
                self.pix_buffer = self.qview.get()                
                with self.qview.mutex:
                    self.qview.queue.clear()
            except:
                pass
                
            if (not self.writer_on) and (not self.cur_exposure == self.mainWindow.signals.ms_exposure_per_plane[0]):
                
                self.mmc.stopSequenceAcquisition()
                self.cur_exposure = self.mainWindow.signals.ms_exposure_per_plane[0]  
                self.mmc.setProperty('Camera', 'Exposure', str(self.cur_exposure))
                self.mmc.startContinuousSequenceAcquisition(1)
                self.cam_win.cur_frame_rate_label.setText("Cur. rate: {:.1f}/s, ".format(1000/self.cur_exposure) + "{:.1f} ms/fr. ".format(self.cur_exposure))
                
            
        self.set_disp_params()
        
        if not self.overlay:
            self.set_image()
            
        else:            
            other_cam=self.mainWindow.cam_list[2-self.cam_number]
            
            ROI1=self.mmc.getROI()
            ROI2=other_cam.mmc.getROI()
            if all((ROI1[i]-ROI2[i])==0 for i in range(4)):
                self.overlay_buffer=np.zeros((ROI1[3],ROI1[2],3))
                self.overlay_buffer[:,:,1]=self.image_buffer
                self.overlay_buffer[:,:,0]=other_cam.image_buffer
                self.overlay_buffer[:,:,2]=self.overlay_buffer[:,:,0]
                
            self.set_image()
        
    
    
    def set_disp_params(self):
        
        self.autoscale=self.cam_win.auto_scale.isChecked()
        
        self.pix_max=self.pix_buffer.max()
        self.stack_max=self.sample_stack.max()
        
        if not self.vabsolute:
            self.br_max=float(self.pix_max)*(self.vpercentile/100)
            self.br_min=float(self.pix_buffer.min())
            self.cam_win.br_max.setValue(int(self.br_max))
            self.cam_win.br_min.setValue(int(self.br_min))
            self.cam_win.br_perc.setText(str(int(self.vpercentile)))
        
        
        if self.br_max > self.br_min:
            self.image_buffer = ((self.pix_buffer.astype(np.single)-self.br_min)/(self.br_max-self.br_min)).clip(0,1)
        else:
            self.image_buffer = (self.pix_buffer.astype(np.single)/self.br_max).clip(0,1)
            
        if self.camview_thread.isRunning():
           self.view_box.invertX(True)
         
        if (self.br_max>62000) or (self.stack_max>62000):
            self.cam_win.warning.setText('Camera saturated: please change settings')
        else:
            self.cam_win.warning.setText('')
            
        self.cam_win.cur_frame_rate_label.setText("Cur. rate: {:.1f}/s, ".format(1000/self.cur_exposure) + "{:.1f} ms/fr. ".format(self.cur_exposure))
           
           
    def set_image(self):
        
        self.cam_win.imv.setImage(self.image_buffer, autoRange=self.autoscale, autoLevels=False)      
                    
   
        
    def start_camera(self):
        
        self.cam_on=True
        
        trigger='EXTERNAL' if (self.cam_mode=="scan") else 'INTERNAL'
        
        self.scan_mode=self.mainWindow.scanning.scan_mode
        
        if not self.mmc.isSequenceRunning():
            
                
            self.cur_exposure=self.mainWindow.signals.ms_exposure_per_plane[0]
            self.mmc.setProperty('Camera', 'TRIGGER SOURCE',trigger) ## Switch trigger source            

            self.mmc.setProperty('Camera', 'TRIGGER ACTIVE', 'SYNCREADOUT') #<-- EDGE, LEVEL, SYNCREADOUT
            self.mmc.setProperty('Camera', 'TRIGGER GLOBAL EXPOSURE', 'DELAYED') #<-- GLOBAL RESET or DELAYED
            self.mmc.setProperty('Camera', 'Exposure', str(self.cur_exposure))
            
                        
            self.mmc.initializeCircularBuffer()
            self.mmc.startContinuousSequenceAcquisition(1)

            print('Camera ' + str(self.cam_number) + ' started')
            
            with self.qview.mutex:
                self.qview.queue.clear()
                
            with self.qrec.mutex:
                self.qrec.queue.clear()       
                
            self.reader_on=True
            self.readthread.start()
                
            
        if not self.cam_win.imv.timer.isActive():
            self.cam_win.imv.timer.start(200)
            
            
        self.update_startstop_buttons()
        
        
        #print(self.mmc.getProperty('Camera','Exposure')) # list properties
        #print(self.mmc.getProperty('Camera','ReadoutTime')) # list properties
            
            
    def stop_camera(self):
        
        self.cam_on=False       
            
        self.reader_on=False  
        self.readthread.quit()
        self.readthread.wait()
        
        
        if self.mmc.isSequenceRunning():
            try:
                
                self.mmc.clearCircularBuffer()
                self.mmc.stopSequenceAcquisition()
                    
                print('Camera ' + str(self.cam_number) + ' stopped')
                #self.mmc.clearCircularBuffer()
            except:
                print('somewhat difficult to stop')
                pass
        
        with self.qview.mutex:
            self.qview.queue.clear()
            
        
        if self.cam_win.imv.timer.isActive():
            self.cam_win.imv.timer.stop()
            
            
        self.update_startstop_buttons()
        
        
            
    def startStream(self):
        
        self.cam_mode = "noscan"
        self.start_camera()
        self.update_frame_info()       
        
    
    def stopStream(self):
        
        self.stop_camera()
        
        
    def startRecording(self):
        
        self.target_dir = self.mainWindow.exp_dir
        self.writer_on=True
        self.cam_mode = "scan" 
            
        self.update_stack_size()        
        self.sample_stack=np.zeros((self.stack_size,self.roi_dims[3],self.roi_dims[2]))
        
        self.start_camera()
        
        self.cam_win.z_slider.setMaximum(self.stack_size)
            
        if self.mainWindow.scanning.stop_mode==0:
            self.limit_count=self.mainWindow.scanning.limit_image
        else:
            self.limit_count=999999999            
            
        self.writethread.start()
        
        self.mainWindow.scanning.sync_event=False        
        self.update_all_buttons(False)
        self.cam_win.z_slider.setEnabled(False)
        
        self.nfile=0
        self.nimage=0
        
    
    def stopRecording(self):
        
        
        self.writer_on=False      
        self.writethread.quit()
        self.writethread.wait()
        
        self.stop_camera()    
        
        with self.qrec.mutex:
            self.qrec.queue.clear()       
            
        
        self.mainWindow.scanning.sync_event=False        
        self.cam_win.z_slider.setEnabled(False)            
        self.update_all_buttons(True)
        self.update_roi_buttons()
        
        
        
    def startScanning(self):
        
        self.cam_mode = "scan"
        self.update_stack_size()    
        
        self.sample_stack=np.zeros((self.stack_size,self.roi_dims[3],self.roi_dims[2]))
            
        self.start_camera()
        
        self.mainWindow.scanning.sync_event=False        
        self.cam_win.z_slider.setEnabled(False)        
        self.update_all_buttons(False)
        
    
    def stopScanning(self):
        
        
        self.stop_camera()
        
        if self.mainWindow.scanning.scan_mode==1:
            for z in range(self.stack_size):
                if not self.qrec.empty():
                    self.sample_stack[z,:,:]=self.qrec.get()     
                    
            self.cam_win.z_slider.setValue(self.stack_size)        
            self.cam_win.z_slider.setEnabled(True)
            
        with self.qrec.mutex:
            self.qrec.queue.clear()       
            
        self.mainWindow.scanning.sync_event=False    
        self.update_all_buttons(True)
        self.update_roi_buttons()
        
            
    def update_startstop_buttons(self):
    
        btn_list=[(self.cam_win.startStream_btn,True),
                  (self.cam_win.capture_btn,True),
                  (self.cam_win.stopStream_btn,False)]
        
        for b in range(len(btn_list)):
            btn_list[b][0].setEnabled(not self.cam_on==btn_list[b][1])
        
        if (self.mainWindow.scanning.scan_started==0) and (self.mainWindow.scanning.rec_started==0):
            self.mainWindow.scan_btn.setEnabled(not self.cam_on)
            self.mainWindow.rec_btn.setEnabled(not self.cam_on)
            
            
            
    def update_roi_buttons(self):
    
        self.cam_win.setROI_btn.setEnabled(not self.ROI)
        self.cam_win.resetROI_btn.setEnabled(self.ROI)
        
    def update_br_console(self):
        
        self.cam_win.br_slide.setEnabled(not self.vabsolute)
        self.cam_win.br_max.setEnabled(self.vabsolute)
        self.cam_win.br_min.setEnabled(self.vabsolute)
        
    def update_stack_size(self):
        
        self.scan_mode=self.mainWindow.scanning.scan_mode
        
        if self.scan_mode==0:
            self.stack_size=50
        else:
            self.stack_size=self.mainWindow.LE_num_planes.value()
        
        self.cam_win.z_slider.setMaximum(self.stack_size)
        
            
            
    def update_all_buttons(self,state):
    
        for b in range(len(self.btn_list)):
            self.btn_list[b].setEnabled(state)
            
        
    
    def update_twocam_buttons(self): # Exp1 means input values
        
        state= all(c for c in self.mainWindow.cam_on_list)
        for c in range(2):
            if self.mainWindow.cam_list[c] is not None:
                self.mainWindow.cam_list[c].cam_win.pushROI_btn.setEnabled(state)
                self.mainWindow.cam_list[c].cam_win.overlay_btn.setEnabled(state)
                
        if self.cam_number==2:
            self.cam_win.overlay_btn.setVisible(False)
            
    def update_frame_info(self):
        
        
        self.cur_exposure= float(self.mmc.getProperty('Camera', 'Exposure'))
        
        self.roi_dims = self.mmc.getROI()
        ''' compute frame rate from ROI '''
        
        self.max_frame_rate=self.calc_max_frame_rate(self.roi_dims[3])
        
        self.cam_win.max_frame_rate_label.setText("(Max rate: {:.1f}/s, ".format(self.max_frame_rate)+ "{:.1f} ms/fr.)".format(1000/self.max_frame_rate))
        self.cam_win.cur_frame_rate_label.setText("Cur. rate: {:.1f}/s, ".format(1000/self.cur_exposure) + "{:.1f} ms/fr. ".format(self.cur_exposure))
        self.cam_win.image_size.setText('Image Size : H'+str(self.roi_dims[3])+' x V'+str(self.roi_dims[2]))
        self.cam_win.x_slide.setValue(self.roi_dims[3])
        self.cam_win.y_slide.setValue(self.roi_dims[2])
        
        
        
    def calc_max_frame_rate(self, Vn=2304, Exp1=0.000017): # Exp1 means input values in Hamamatsu manual
        
        Exp2 = Exp1 - 3.029411e-6 
        H = 4.867647e-6
        return 1/((Vn+np.ceil(Exp2/H)+4)*H)
    
            
    
    def setOverlay(self):
        
        self.overlay= not self.overlay
        
        if self.overlay:
            self.cam_win.overlay_btn.setText('Release \n overlay')
        else:
            self.cam_win.overlay_btn.setText('Overlay')
            
            
        
    def scan_mode_changed(self):
        
        self.scan_mode=self.mainWindow.scanning.scan_mode
        self.cam_win.z_slider.setEnabled(self.scan_mode==1) # default of the software
        
        if self.scan_mode==0:
            self.cam_win.z_slider.setValue(1)
        

            
            