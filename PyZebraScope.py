# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap
import pyqtgraph as pg

import sys, os
import numpy as np

from camera import Camera
from laser import Laser

from threading import Thread
from stages import Stages
from piezo import Piezo
from scanning import Scanning
from nd_filter import ND_Filter
from setting import Setting
from signals import signals
from eye_exclusion import Eye_exclusion
from style import setStyle_CSS

 
root_dir = r'C:\Users\LS_User\Desktop\PyZebraScope'

Ui_MainWindow, QtBaseClass = uic.loadUiType(root_dir + r'\PyZebraScope.ui')

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    
    
    def __init__(self):
        super(QtBaseClass, self).__init__()
        
        self.setStyleSheet(setStyle_CSS())

        self.root_dir=root_dir
        self.setupUi(self)
        self.info_area.setText('Welcome')
        
        self.save_dir="E:\\"
        self.save_header=""
        self.save_footer=""
        
        self.write_directory.setText(self.save_dir)
        self.exp_dir=""
        self.write_directory.textChanged.connect(self.dir_changed)
        self.exp_header.textChanged.connect(self.header_changed)
        self.exp_footer.textChanged.connect(self.footer_changed)
        
        ''' Setting for first tab '''        
        
        ### Camera
        self.cam1 = None
        self.cam2 = None   
        self.cam1_on = False # This sets the initial state of loading
        self.cam2_on = False # This sets the initial state of loading   
        
        self.cam_list =       [self.cam1, self.cam2]
        self.cam_on_list =    [self.cam1_on,self.cam2_on]
        self.cam_check_list = [self.cam1_check, self.cam2_check]
        #self.cam_btn_list =   [self.cam1_view_btn, self.cam2_view_btn]
        
        self.cam1_check.clicked.connect(lambda cam:  self.cam_switch(cam=0))
        self.cam2_check.clicked.connect(lambda cam:  self.cam_switch(cam=1))
        
        
        for cam in range(2):
            self.cam_check_list[cam].setChecked(self.cam_on_list[cam])
            self.cam_switch(cam)
        
        ### setting module
        
        self.setting=Setting(self)
        
        ### Scanning
        
        self.scanning=Scanning(self)
        
        ### Laser
        
        self.lasers=Laser(self)
    
        ### Filters
    
        self.nd_filters=ND_Filter(self)
        
                
        ### Set up waveform ignals        ◘
        
        self.signalthread = QThread()
        self.signals = signals(self)
        self.signals.moveToThread(self.signalthread)
        self.signal_on=False        
        self.signalthread.started.connect(self.signals.start_signals)
        

        
        ### check the status of objective servo
        self.piezo = Piezo(self)
        
        ### stages
                
        self.stages = Stages(self)
        
        ### stages
        
        self.eye_exclusion = Eye_exclusion(self)
        
        
            
    def closeEvent(self, event):
        
        reply = QMessageBox.question(self, 'Quit?', 'Are you sure you want to quit?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
                
            
            # Closing camera instances
          
            for cam in range(2):
                if self.cam_on_list[cam]:
                    self.cam_list[cam].close()
            
            # Closing stages, filters, daq
            
            
            self.scanning.close()
            self.setting.close()
            
            self.nd_filters.close()
            self.signals.close()
            self.piezo.close()
            self.lasers.close()
            self.stages.close()
            self.eye_exclusion.close()
            
            self.deleteLater()
        
            print('PyZebrascope shut down')
            event.accept()
            
        else:
            event.ignore()
        
        
    def cam_switch(self, cam):
        
        self.cam_on_list[cam] = self.cam_check_list[cam].isChecked()
        
        if self.cam_on_list[cam]:           
            self.cam_list[cam] = Camera(parent=self, app=app, cam_number=cam+1)
            self.cam_list[cam].start_cam_view()
            
            if not self.cam_list[cam].mmc:
                
                self.cam_check_list[cam].setChecked(False)
                self.cam_list[cam]=None
                self.cam_on_list[cam]=False
                
        else:
            if self.cam_list[cam] is not None:
                self.cam_list[cam].close()
                
            
            
    def dir_changed(self):
        
        self.save_dir = self.write_directory.text().rstrip('\\')
        
    def header_changed(self):
        
        self.save_header = self.exp_header.text()
        if self.save_header != "":
            self.save_header = self.save_header+"_"
        
    def footer_changed(self):
        
        self.save_footer = self.exp_footer.text()
        if self.save_footer != "":
            self.save_footer = "_"+self.save_footer
        
        
 

if __name__=="__main__":


    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    
    window.show()
    ## sys.exit(app.exec_()) ## only for debugging
    
    

