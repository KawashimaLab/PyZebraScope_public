# -*- coding: utf-8 -*-
"""
Created on Mon May 25 11:07:31 2020

@author: admin
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import QWidget,QGridLayout
from PyQt5.QtGui import QPen, QColor

import pyqtgraph as pg
import sys




class EyeExclude_Event(pg.ImageView):
    

    def __init__(self, parent=None, **kargs):
        
        pg.ImageView.__init__(self, **kargs)
        
        self.setWindowTitle('Eye Exclusion View')

        self.roi_pen=QPen()
        self.roi_pen.setWidth(0);
        self.roi_pen.setColor(QColor("red"));
        
        self.roi1 = pg.EllipseROI([0,0],[20,20], pen=self.roi_pen)
        self.ui.menuBtn.hide()
        self.ui.roiBtn.hide()
        self.ui.histogram.hide()
        self.addItem(self.roi1)
        self.roi1.removeHandle(0) #disable rotation of the ROI
        
        

class eye_exc_win(QtCore.QThread):
    
    
    
    def __init__(self,parent=None):
        
        QtCore.QThread.__init__(self)
        self.eye_main=parent
        
    
    def setupUi(self, MainWindow):
        
        self.image=np.zeros((1200,45)) # blank image
        self.scale_factors = (10,2)

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(320,805)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.layout = QGridLayout()
        self.centralwidget.setLayout(self.layout)
        self.vpercentile=100
        
        self.imv = EyeExclude_Event(parent=MainWindow)
        self.layout.addWidget(self.imv,0,0,1,1)
        self.imv.setObjectName("imv")
        self.imv.adjustSize()        
        self.view_box=self.imv.getView()
        self.view_box.setMouseEnabled(False,False)
        
        self.buttonwidget = QtWidgets.QWidget(MainWindow)
        self.buttonwidget.setObjectName("buttonwidget")
        self.layout.addWidget(self.buttonwidget,1,0,1,1)
        self.layout.setRowStretch(0,1)
        self.layout.setRowStretch(1,0)
        self.layout.setRowMinimumHeight(1,150)
        
        self.acquire_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.acquire_btn.setGeometry(QtCore.QRect(20, 45, 80, 50))
        self.acquire_btn.setObjectName("Acquire_btn")
        self.set_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.set_btn.setGeometry(QtCore.QRect(120, 5, 80, 50))
        self.set_btn.setObjectName("Set_btn")
        
        self.clear_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.clear_btn.setGeometry(QtCore.QRect(120, 85, 80, 50))
        self.clear_btn.setObjectName("Clear_btn")
        
        self.br_slide = QtWidgets.QSlider(self.buttonwidget)
        self.br_slide.setGeometry(QtCore.QRect(250, 40, 22, 100))
        self.br_slide.setMaximum(100)
        self.br_slide.setMinimum(0)
        self.br_slide.setValue(100)
        self.br_slide.setSingleStep(1)
        self.br_slide.setOrientation(QtCore.Qt.Vertical)
        self.br_slide.setObjectName("br_slide")
        self.br_slide.valueChanged.connect(self.br_slider_changed)
        
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        
        self.clear_btn.clicked.connect(self.clear_exclusion)
        self.set_btn.clicked.connect(self.set_exclusion)
        self.acquire_btn.clicked.connect(self.acquire_stack)
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        self.imv.setImage(self.image, axes={'x':1 , 'y':0}, scale=self.scale_factors)
        self.set_button_state()       

        
    def retranslateUi(self, MainWindow):
        
        self._translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(self._translate("MainWindow","Eye exclusion console"))
        self.acquire_btn.setText(self._translate("MainWindow", "Acquire"))
        self.set_btn.setText(self._translate("MainWindow", "Set"))
        self.clear_btn.setText(self._translate("MainWindow", "Clear"))
        
        
    def acquire_stack(self):
        
        
        # acquire stack for 1 time
        
        if self.eye_main.mainWindow.scanning.scan_mode==1:
            

            self.eye_main.mainWindow.scanning.startScanning()
            for cam in range(2):
                if self.eye_main.mainWindow.cam_on_list[cam]:
                    IM=self.eye_main.mainWindow.cam_list[cam].sample_stack
            
            if isinstance(IM, np.ndarray):
            
                IM_MAX= np.flipud(np.max(IM, axis=1).T)
                
                
                # check if the image size is different
                
                image_autorange=False
                if (IM_MAX.shape[0]!=self.image.shape[0]) or (IM_MAX.shape[1]!=self.image.shape[1]):
                    self.view_box.enableAutoRange()
                    image_autorange=True
                    
                    
                
                
                # import image into buffer
                
                self.image = IM_MAX
                signals_handle=self.eye_main.mainWindow.signals
                pix_size_y=signals_handle.pix_size
                pix_size_z=(signals_handle.piezo_end[0]-signals_handle.piezo_start[0])/(signals_handle.num_planes[0]-1)
                self.scale_factors = (pix_size_z,pix_size_y)
                
                
                # set image
                
                self.imv.setImage(self.image, axes={'x':1 , 'y':0}, scale=self.scale_factors,autoRange=image_autorange)
                self.set_level()
                self.view_box.disableAutoRange()
                self.set_button_state()      
        
    def set_level(self):
        
        if self.image.max()>0:
            self.imv.setLevels(min=self.image.min(),max=self.image.max()*float(self.vpercentile)/100)
            
        
        
    def set_exclusion(self):
        
        # calculate ellipse and export exclude_list as a plane-by-plane off signal
        
        if self.eye_main.mainWindow.scanning.scan_mode==1:
            
            image_height=self.image.shape[0]
            image_width=self.image.shape[1]
            roi_info=self.imv.roi1.getAffineSliceParams(self.image, self.imv.getImageItem(), axes=(1,0))
            roi_pos = roi_info[2]
            roi_siz = roi_info[0]
            roi_center=(roi_pos[0]+roi_siz[0]/2, roi_pos[1]+roi_siz[1]/2)        
            
            self.eye_main.exclusion_list = []
            for i in range(int(roi_pos[0]),int(roi_pos[0]+roi_siz[0])+1):
                
                circle_width_squared=1-((i-roi_center[0])/(roi_siz[0]/2))**2
                
                if (i>=0) and (i<image_width) and (circle_width_squared>0):
                
                    circle_width = np.sqrt(circle_width_squared)*(roi_siz[1]/2)
                    h_min = max(roi_center[1]-circle_width,0)
                    h_max = min(roi_center[1]+circle_width,image_height)
                    
                    width=(h_max-h_min)/image_height
                    start=h_min/image_height
                    self.eye_main.exclusion_list.append((i,start,width))                
                
            self.eye_main.exclusion=True
            self.set_button_state()    
            self.eye_main.mainWindow.eye_exclude_status.setText("Eye exclusion set")
        
        
    def clear_exclusion(self):
        
        self.eye_main.exclusion=False        
        self.roi_h=(0,0) ## Z plane
        self.roi_v=(0,0) ## Y boundary
        self.set_button_state()
        self.eye_main.mainWindow.eye_exclude_status.setText("")
        
        
    def br_slider_changed(self):
        self.vpercentile = self.br_slide.value()
        self.set_level()
        
        
    def set_button_state(self):
        self.set_btn.setEnabled(self.eye_main.exclusion==False)
        self.clear_btn.setEnabled(self.eye_main.exclusion==True)
        


class EyeExclusion_GUI(QtWidgets.QMainWindow):
    
    # this class is necessary to defining closeEvent for GUI
    
    def __init__(self,parent=None):
        QtWidgets.QMainWindow.__init__(self)
        self.parent=parent

    def closeEvent(self, event):
        self.parent.close_eye_view()

        

class Eye_exclusion(QObject):

    
    def __init__(self, parent=None, app=None):
        
        super().__init__()
        
        self.mainWindow=parent        
        self.exclusion=False
        
        self.eye_exclusion_window = EyeExclusion_GUI(self) #QtWidgets.QMainWindow()
        self.eye_window = eye_exc_win(self)
        self.eye_window.setupUi(self.eye_exclusion_window)
        self.eye_thread = self.eye_window
        self.mainWindow.eye_exclude_btn.clicked.connect(self.start_eye_view)
        self.exclusion_list=[]
        self.vpercentile=100
        
        
    def close(self):
        
        self.eye_exclusion_window.close()
        
        self.deleteLater()
        
            
            
    def start_eye_view(self):       
        
        if not self.eye_thread.isRunning():
            self.eye_thread.start()
        self.eye_exclusion_window.show()
        
        
    def close_eye_view(self):
        
        self.eye_thread.exit()
        
        

            
            
        